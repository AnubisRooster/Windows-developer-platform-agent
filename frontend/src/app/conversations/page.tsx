'use client';

import { useEffect, useState } from 'react';
import { fetchConversations, type Conversation, type Message } from '@/lib/api';

function MessageBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === 'user';
  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 ${
          isUser ? 'bg-accent-blue/20 text-slate-200' : 'bg-surface-700 text-slate-200'
        }`}
      >
        <p className="text-xs font-medium text-slate-500 capitalize">{msg.role}</p>
        <p className="mt-1 text-sm whitespace-pre-wrap">{msg.content}</p>
        {msg.timestamp && (
          <p className="mt-1 text-xs text-slate-500">{msg.timestamp}</p>
        )}
      </div>
    </div>
  );
}

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchConversations(20)
      .then(setConversations)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load conversations'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-white">Conversations</h1>
        <p className="text-slate-400">Loading…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-white">Conversations</h1>
        <p className="text-accent-red">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-white">Conversations</h1>

      {conversations.length === 0 ? (
        <p className="text-slate-500">No conversations</p>
      ) : (
        <div className="space-y-6">
          {conversations.map((conv) => (
            <div key={conv.id} className="card">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="font-medium text-white">Conversation {conv.id}</h3>
                {conv.created_at && (
                  <span className="text-xs text-slate-500">{conv.created_at}</span>
                )}
              </div>
              <div className="space-y-3">
                {(conv.messages ?? []).length === 0 ? (
                  <p className="text-sm text-slate-500">No messages</p>
                ) : (
                  (conv.messages ?? []).map((msg, i) => (
                    <MessageBubble key={msg.id ?? i} msg={msg} />
                  ))
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
