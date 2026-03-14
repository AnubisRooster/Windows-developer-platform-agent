"""
Event Bus with Redis backing and in-memory fallback.

Supports wildcard topic subscriptions (e.g., github.*, *.opened).
Redis streams provide durable, distributed event delivery.
Falls back to in-memory pub/sub when Redis is unavailable.
"""

from __future__ import annotations

import asyncio
import fnmatch
import json
import logging
import os
from collections import defaultdict
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)

EventHandler = Callable[[dict[str, Any]], Awaitable[None]]

REDIS_STREAM_KEY = "platform:events"
REDIS_CONSUMER_GROUP = "platform-workers"


class EventBus:
    """
    Async event bus with Redis stream backing and wildcard subscription support.

    When Redis is available, events are published to a Redis stream and
    consumed by worker groups. Local handlers are still invoked for
    in-process subscribers (webhooks, workflow triggers).
    """

    def __init__(self, persist: bool = False, redis_url: str | None = None) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._persist = persist
        self._persist_fn: Callable[[dict[str, Any]], Awaitable[None]] | None = None
        self._redis_url = redis_url or os.environ.get("REDIS_URL", "")
        self._redis = None
        self._consumer_task: asyncio.Task | None = None

    async def _get_redis(self):
        """Lazily connect to Redis."""
        if self._redis is not None:
            return self._redis
        if not self._redis_url:
            return None
        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
            await self._redis.ping()
            try:
                await self._redis.xgroup_create(REDIS_STREAM_KEY, REDIS_CONSUMER_GROUP, id="0", mkstream=True)
            except Exception:
                pass  # group may already exist
            logger.info("Connected to Redis at %s", self._redis_url)
            return self._redis
        except Exception as e:
            logger.warning("Redis unavailable (%s), using in-memory bus", e)
            self._redis = None
            return None

    def subscribe(self, topic: str, handler: EventHandler) -> None:
        self._handlers[topic].append(handler)
        logger.debug("Subscribed handler to topic: %s", topic)

    def set_persister(self, fn: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        self._persist_fn = fn

    def _match_topic(self, event_topic: str, pattern: str) -> bool:
        return fnmatch.fnmatch(event_topic, pattern)

    def _build_topic(self, event: dict[str, Any]) -> str:
        source = event.get("source", "internal")
        event_type = event.get("type") or event.get("event_type", "unknown")
        if hasattr(source, "value"):
            source = source.value
        return f"{source}.{event_type}"

    async def publish(self, event: dict[str, Any]) -> None:
        """
        Publish an event to Redis stream and invoke local handlers.

        Event must have 'source' and 'type' (or 'event_type') keys.
        """
        if self._persist and self._persist_fn:
            try:
                await self._persist_fn(event)
            except Exception as e:
                logger.exception("Failed to persist event: %s", e)

        redis = await self._get_redis()
        if redis:
            try:
                await redis.xadd(
                    REDIS_STREAM_KEY,
                    {"data": json.dumps(event, default=str)},
                    maxlen=10000,
                )
            except Exception as e:
                logger.warning("Redis publish failed: %s", e)

        await self._dispatch_local(event)

    async def _dispatch_local(self, event: dict[str, Any]) -> None:
        """Dispatch event to all matching local handlers."""
        topic = self._build_topic(event)
        matched = 0
        for pattern, handlers in list(self._handlers.items()):
            if self._match_topic(topic, pattern):
                for handler in handlers:
                    try:
                        await handler(event)
                        matched += 1
                    except Exception as e:
                        logger.exception("Event handler failed for %s: %s", pattern, e)
        logger.debug("Published event %s, %d local handlers invoked", topic, matched)

    async def start_consumer(self, consumer_name: str = "worker-1") -> None:
        """Start consuming events from Redis stream in background."""
        redis = await self._get_redis()
        if not redis:
            logger.info("No Redis available, skipping stream consumer")
            return

        async def _consume():
            while True:
                try:
                    messages = await redis.xreadgroup(
                        REDIS_CONSUMER_GROUP,
                        consumer_name,
                        {REDIS_STREAM_KEY: ">"},
                        count=10,
                        block=5000,
                    )
                    for stream_name, entries in messages:
                        for msg_id, fields in entries:
                            try:
                                event = json.loads(fields.get("data", "{}"))
                                await self._dispatch_local(event)
                                await redis.xack(REDIS_STREAM_KEY, REDIS_CONSUMER_GROUP, msg_id)
                            except Exception as e:
                                logger.exception("Failed to process stream message %s: %s", msg_id, e)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.warning("Redis consumer error: %s, retrying...", e)
                    await asyncio.sleep(2)

        self._consumer_task = asyncio.create_task(_consume())
        logger.info("Started Redis stream consumer: %s", consumer_name)

    async def stop_consumer(self) -> None:
        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
            self._consumer_task = None

    async def close(self) -> None:
        await self.stop_consumer()
        if self._redis:
            await self._redis.close()
            self._redis = None
