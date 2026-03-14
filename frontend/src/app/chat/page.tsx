'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import {
  createChatSession,
  deleteChatSession,
  fetchChatMessages,
  fetchChatSessions,
  sendChatMessage,
  type ChatMessageItem,
  type ChatSessionSummary,
} from '@/lib/api';

function MessageBubble({ msg }: { msg: ChatMessageItem }) {
  const isUser = msg.role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-xl px-4 py-3 ${
          isUser
            ? 'bg-accent-blue/20 text-slate-100 border border-accent-blue/30'
            : 'bg-surface-700 text-slate-200 border border-border'
        }`}
      >
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            {msg.role}
          </span>
          {msg.timestamp && (
            <span className="text-xs text-slate-600">{msg.timestamp}</span>
          )}
        </div>
        <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
      </div>
    </div>
  );
}

export default function ChatPage() {
  const [sessions, setSessions] = useState<ChatSessionSummary[]>([]);
  const [activeSession, setActiveSession] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessageItem[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    fetchChatSessions(50)
      .then(setSessions)
      .catch(() => {})
      .finally(() => setLoadingSessions(false));
  }, []);

  const loadSession = useCallback(async (sid: string) => {
    setActiveSession(sid);
    setLoadingMessages(true);
    try {
      const msgs = await fetchChatMessages(sid);
      setMessages(msgs);
    } catch {
      setMessages([]);
    } finally {
      setLoadingMessages(false);
    }
  }, []);

  const handleNewChat = useCallback(async () => {
    try {
      const res = await createChatSession();
      const newSession: ChatSessionSummary = {
        session_id: res.session_id,
        title: res.title,
        message_count: 0,
      };
      setSessions((prev) => [newSession, ...prev]);
      setActiveSession(res.session_id);
      setMessages([]);
    } catch (err) {
      console.error('Failed to create chat session', err);
    }
  }, []);

  const handleSend = useCallback(async () => {
    if (!input.trim() || !activeSession || sending) return;

    const userMsg: ChatMessageItem = { role: 'user', content: input.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setSending(true);

    try {
      const reply = await sendChatMessage(activeSession, userMsg.content);
      setMessages((prev) => [...prev, reply]);
      setSessions((prev) =>
        prev.map((s) =>
          s.session_id === activeSession
            ? {
                ...s,
                title:
                  s.title === 'New Chat'
                    ? userMsg.content.slice(0, 60) + (userMsg.content.length > 60 ? '...' : '')
                    : s.title,
                message_count: (s.message_count ?? 0) + 2,
              }
            : s,
        ),
      );
    } catch (err) {
      const errorMsg: ChatMessageItem = {
        role: 'assistant',
        content: `Error: ${err instanceof Error ? err.message : 'Failed to get response'}`,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setSending(false);
    }
  }, [input, activeSession, sending]);

  const handleDeleteSession = useCallback(
    async (sid: string, e: React.MouseEvent) => {
      e.stopPropagation();
      try {
        await deleteChatSession(sid);
        setSessions((prev) => prev.filter((s) => s.session_id !== sid));
        if (activeSession === sid) {
          setActiveSession(null);
          setMessages([]);
        }
      } catch {
        /* ignore */
      }
    },
    [activeSession],
  );

  return (
    <div className="flex h-[calc(100vh-3rem)] gap-4">
      {/* Session sidebar */}
      <div className="w-64 shrink-0 flex flex-col rounded-lg border border-border bg-surface-800">
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <h2 className="text-sm font-semibold text-white">Chats</h2>
          <button
            onClick={handleNewChat}
            className="rounded-md bg-accent-blue/20 px-3 py-1 text-xs font-medium text-accent-blue hover:bg-accent-blue/30 transition-colors"
          >
            + New
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {loadingSessions ? (
            <p className="text-xs text-slate-500 px-2 py-1">Loading...</p>
          ) : sessions.length === 0 ? (
            <p className="text-xs text-slate-500 px-2 py-1">
              No chats yet. Click &quot;+ New&quot; to start.
            </p>
          ) : (
            sessions.map((s) => (
              <div
                key={s.session_id}
                onClick={() => loadSession(s.session_id)}
                className={`group flex items-center justify-between rounded-md px-3 py-2 text-sm cursor-pointer transition-colors ${
                  activeSession === s.session_id
                    ? 'bg-surface-700 text-white'
                    : 'text-slate-400 hover:bg-surface-700/50 hover:text-slate-200'
                }`}
              >
                <span className="truncate flex-1 mr-2">{s.title || 'Untitled'}</span>
                <button
                  onClick={(e) => handleDeleteSession(s.session_id, e)}
                  className="hidden group-hover:block text-slate-600 hover:text-accent-red text-xs"
                  title="Delete"
                >
                  &times;
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 flex flex-col rounded-lg border border-border bg-surface-800">
        {!activeSession ? (
          <div className="flex flex-1 items-center justify-center">
            <div className="text-center">
              <h2 className="text-lg font-semibold text-white mb-2">Claw Agent Chat</h2>
              <p className="text-slate-500 text-sm mb-4">
                Start a new chat or select an existing one from the sidebar.
              </p>
              <p className="text-slate-600 text-xs">
                Each chat uses its own context window. All messages are saved to long-term memory.
              </p>
            </div>
          </div>
        ) : (
          <>
            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
              {loadingMessages ? (
                <p className="text-slate-500 text-sm">Loading messages...</p>
              ) : messages.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <p className="text-slate-600 text-sm">Send a message to begin.</p>
                </div>
              ) : (
                messages.map((msg, idx) => <MessageBubble key={msg.id ?? idx} msg={msg} />)
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="border-t border-border px-4 py-3">
              <div className="flex gap-3">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  placeholder={sending ? 'Waiting for response...' : 'Type a message...'}
                  disabled={sending}
                  className="flex-1 rounded-lg border border-border bg-surface-900 px-4 py-2.5 text-sm text-slate-100 placeholder-slate-600 focus:border-accent-blue/50 focus:outline-none focus:ring-1 focus:ring-accent-blue/50 disabled:opacity-50"
                />
                <button
                  onClick={handleSend}
                  disabled={sending || !input.trim()}
                  className="rounded-lg bg-accent-blue/80 px-5 py-2.5 text-sm font-medium text-white hover:bg-accent-blue transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {sending ? 'Sending...' : 'Send'}
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
