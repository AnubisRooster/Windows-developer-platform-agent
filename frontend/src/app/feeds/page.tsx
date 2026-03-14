'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  fetchXFeed,
  fetchLinkedInFeed,
  fetchOutlookInbox,
  fetchZohoInbox,
  type FeedResponse,
  type FeedPost,
  type InboxResponse,
  type EmailMessage,
} from '@/lib/api';

function NotConfigured({ name, envVar }: { name: string; envVar: string }) {
  return (
    <div className="rounded-lg border border-border bg-surface-800/50 p-6 text-center">
      <p className="text-sm text-slate-400 mb-2">{name} is not configured</p>
      <p className="text-xs text-slate-600">
        Add <code className="rounded bg-surface-700 px-1.5 py-0.5 text-slate-400">{envVar}</code> to your <code className="rounded bg-surface-700 px-1.5 py-0.5 text-slate-400">.env</code> file
      </p>
    </div>
  );
}

function XPost({ post }: { post: FeedPost }) {
  return (
    <div className="card">
      <div className="flex items-start gap-3">
        {post.author_avatar && (
          <img src={post.author_avatar} alt="" className="h-10 w-10 rounded-full" />
        )}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="font-medium text-white text-sm">{post.author_name}</span>
            {post.author_username && (
              <span className="text-xs text-slate-500">@{post.author_username}</span>
            )}
          </div>
          <p className="mt-1 text-sm text-slate-300 whitespace-pre-wrap">{post.text}</p>
          <div className="mt-2 flex items-center gap-4 text-xs text-slate-500">
            {post.created_at && <span>{new Date(post.created_at).toLocaleString()}</span>}
            {post.metrics && (
              <>
                {post.metrics.like_count != null && <span>{post.metrics.like_count} likes</span>}
                {post.metrics.retweet_count != null && <span>{post.metrics.retweet_count} reposts</span>}
                {post.metrics.reply_count != null && <span>{post.metrics.reply_count} replies</span>}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function LinkedInPost({ post }: { post: FeedPost }) {
  return (
    <div className="card">
      <div className="min-w-0">
        {post.author && <span className="font-medium text-white text-sm">{post.author}</span>}
        <p className="mt-1 text-sm text-slate-300 whitespace-pre-wrap">{post.text}</p>
        {post.created_at && (
          <p className="mt-2 text-xs text-slate-500">{new Date(post.created_at).toLocaleString()}</p>
        )}
      </div>
    </div>
  );
}

function EmailRow({ msg }: { msg: EmailMessage }) {
  return (
    <div className={`card ${msg.is_read ? 'opacity-70' : ''}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            {!msg.is_read && <span className="h-2 w-2 rounded-full bg-accent-blue shrink-0" />}
            <h4 className="text-sm font-medium text-white truncate">{msg.subject}</h4>
          </div>
          <p className="mt-0.5 text-xs text-slate-400">
            {msg.from_name || msg.from_email}
          </p>
          <p className="mt-1 text-xs text-slate-500 line-clamp-2">{msg.preview}</p>
        </div>
        <span className="text-xs text-slate-600 whitespace-nowrap shrink-0">
          {msg.received_at ? new Date(msg.received_at).toLocaleString() : ''}
        </span>
      </div>
    </div>
  );
}

type Tab = 'x' | 'linkedin' | 'outlook' | 'zoho';

export default function FeedsPage() {
  const [tab, setTab] = useState<Tab>('x');
  const [xData, setXData] = useState<FeedResponse | null>(null);
  const [liData, setLiData] = useState<FeedResponse | null>(null);
  const [outlookData, setOutlookData] = useState<InboxResponse | null>(null);
  const [zohoData, setZohoData] = useState<InboxResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const loadAll = useCallback(async () => {
    setLoading(true);
    const results = await Promise.allSettled([
      fetchXFeed(20),
      fetchLinkedInFeed(20),
      fetchOutlookInbox(20),
      fetchZohoInbox(20),
    ]);
    if (results[0].status === 'fulfilled') setXData(results[0].value);
    if (results[1].status === 'fulfilled') setLiData(results[1].value);
    if (results[2].status === 'fulfilled') setOutlookData(results[2].value);
    if (results[3].status === 'fulfilled') setZohoData(results[3].value);
    setLoading(false);
  }, []);

  useEffect(() => { loadAll(); }, [loadAll]);

  const tabs: { key: Tab; label: string; badge?: number }[] = [
    { key: 'x', label: 'X Feed', badge: xData?.posts?.length },
    { key: 'linkedin', label: 'LinkedIn', badge: liData?.posts?.length },
    { key: 'outlook', label: 'Outlook', badge: outlookData?.messages?.filter((m) => !m.is_read).length },
    { key: 'zoho', label: 'Zoho Mail', badge: zohoData?.messages?.filter((m) => !m.is_read).length },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Feeds &amp; Email</h1>
        <button
          onClick={loadAll}
          className="rounded-md bg-surface-700 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-surface-700/80 transition-colors"
        >
          Refresh
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 rounded-lg bg-surface-800 p-1 border border-border">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors ${
              tab === t.key
                ? 'bg-surface-700 text-white'
                : 'text-slate-400 hover:text-slate-200 hover:bg-surface-700/40'
            }`}
          >
            {t.label}
            {(t.badge ?? 0) > 0 && (
              <span className="inline-flex h-5 min-w-[20px] items-center justify-center rounded-full bg-accent-blue/20 px-1.5 text-xs font-semibold text-accent-blue">
                {t.badge}
              </span>
            )}
          </button>
        ))}
      </div>

      {loading && <p className="text-slate-400 text-sm">Loading feeds...</p>}

      {/* X Feed */}
      {tab === 'x' && !loading && (
        <div className="space-y-3">
          {!xData?.configured ? (
            <NotConfigured name="X (Twitter)" envVar="X_BEARER_TOKEN" />
          ) : xData.error ? (
            <p className="text-accent-amber text-sm">{xData.error}</p>
          ) : xData.posts.length === 0 ? (
            <p className="text-slate-500 text-sm">No posts in your timeline.</p>
          ) : (
            xData.posts.map((p, i) => <XPost key={p.id ?? i} post={p} />)
          )}
        </div>
      )}

      {/* LinkedIn */}
      {tab === 'linkedin' && !loading && (
        <div className="space-y-3">
          {!liData?.configured ? (
            <NotConfigured name="LinkedIn" envVar="LINKEDIN_ACCESS_TOKEN" />
          ) : liData.error ? (
            <p className="text-accent-amber text-sm">{liData.error}</p>
          ) : liData.posts.length === 0 ? (
            <p className="text-slate-500 text-sm">No posts in your feed.</p>
          ) : (
            liData.posts.map((p, i) => <LinkedInPost key={p.id ?? i} post={p} />)
          )}
        </div>
      )}

      {/* Outlook */}
      {tab === 'outlook' && !loading && (
        <div className="space-y-2">
          {!outlookData?.configured ? (
            <NotConfigured name="Microsoft Outlook" envVar="OUTLOOK_ACCESS_TOKEN" />
          ) : outlookData.error ? (
            <p className="text-accent-amber text-sm">{outlookData.error}</p>
          ) : outlookData.messages.length === 0 ? (
            <p className="text-slate-500 text-sm">Inbox empty.</p>
          ) : (
            outlookData.messages.map((m) => <EmailRow key={m.id} msg={m} />)
          )}
        </div>
      )}

      {/* Zoho Mail */}
      {tab === 'zoho' && !loading && (
        <div className="space-y-2">
          {!zohoData?.configured ? (
            <NotConfigured name="Zoho Mail" envVar="ZOHO_ACCESS_TOKEN" />
          ) : zohoData.error ? (
            <p className="text-accent-amber text-sm">{zohoData.error}</p>
          ) : zohoData.messages.length === 0 ? (
            <p className="text-slate-500 text-sm">Inbox empty.</p>
          ) : (
            zohoData.messages.map((m) => <EmailRow key={m.id} msg={m} />)
          )}
        </div>
      )}
    </div>
  );
}
