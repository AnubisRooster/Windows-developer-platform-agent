// When served from FastAPI (packaged), same origin so '' works. For next dev, set NEXT_PUBLIC_API_URL=http://localhost:8080
const API_BASE = (typeof window !== 'undefined' ? (process.env.NEXT_PUBLIC_API_URL ?? '') : (process.env.NEXT_PUBLIC_API_URL ?? '')) || '';
const API_PREFIX = '/api';

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${API_PREFIX}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export interface StatusResponse {
  ironclaw?: { status: string; details?: string };
  database?: { status: string; details?: string };
  integrations?: Record<string, { status: string; details?: string }>;
}

export interface Event {
  id?: string;
  time?: string;
  source: string;
  type: string;
  payload?: unknown;
}

export interface Workflow {
  id: string;
  name: string;
  trigger: string;
  description?: string;
  enabled: boolean;
  actions?: unknown[];
}

export interface WorkflowRun {
  id: string;
  workflow_id?: string;
  workflow_name?: string;
  status: 'success' | 'failed' | 'running';
  started_at?: string;
  duration_ms?: number;
}

export interface Tool {
  id: string;
  name: string;
  description?: string;
  parameters?: { name: string; type?: string; description?: string }[];
}

export interface Message {
  id?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export interface Conversation {
  id: string;
  messages?: Message[];
  created_at?: string;
}

export interface LogEntry {
  timestamp?: string;
  level: string;
  message: string;
  extra?: unknown;
}

export interface AvailableModel {
  id: string;
  name: string;
  provider?: string;
}

export interface ModelConfig {
  provider?: string;
  model?: string;
  openrouter_api_key_set?: boolean;
  openrouter_api_key_masked?: string;
  ollama_base_url?: string;
  ironclaw_status?: string;
  ironclaw_details?: string;
  available_models?: Record<string, AvailableModel[]>;
}

export interface ModelConfigUpdate {
  provider?: string;
  model?: string;
  openrouter_api_key?: string;
  ollama_base_url?: string;
}

export function fetchStatus(): Promise<StatusResponse> {
  return fetchApi<StatusResponse>('/status');
}

export function fetchEvents(limit?: number): Promise<Event[]> {
  const params = limit != null ? `?limit=${limit}` : '';
  return fetchApi<Event[]>(`/events${params}`);
}

export function fetchWorkflows(): Promise<Workflow[]> {
  return fetchApi<Workflow[]>(`/workflows`);
}

export function fetchWorkflowRuns(limit?: number): Promise<WorkflowRun[]> {
  const params = limit != null ? `?limit=${limit}` : '';
  return fetchApi<WorkflowRun[]>(`/workflow-runs${params}`);
}

export function fetchTools(): Promise<Tool[]> {
  return fetchApi<Tool[]>(`/tools`);
}

export function fetchConversations(limit?: number): Promise<Conversation[]> {
  const params = limit != null ? `?limit=${limit}` : '';
  return fetchApi<Conversation[]>(`/conversations${params}`);
}

export function fetchModelConfig(): Promise<ModelConfig> {
  return fetchApi<ModelConfig>('/model/config');
}

export function updateModelConfig(config: ModelConfigUpdate): Promise<{ ok: boolean }> {
  return fetchApi<{ ok: boolean }>('/model/config', {
    method: 'POST',
    body: JSON.stringify(config),
  });
}

// --- Chat ---

export interface ChatSessionSummary {
  session_id: string;
  title: string;
  created_at?: string;
  updated_at?: string;
  message_count?: number;
}

export interface ChatMessageItem {
  id?: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export function createChatSession(): Promise<{ session_id: string; title: string }> {
  return fetchApi('/chat/new', { method: 'POST' });
}

export function fetchChatSessions(limit?: number): Promise<ChatSessionSummary[]> {
  const params = limit != null ? `?limit=${limit}` : '';
  return fetchApi<ChatSessionSummary[]>(`/chat/sessions${params}`);
}

export function fetchChatMessages(sessionId: string): Promise<ChatMessageItem[]> {
  return fetchApi<ChatMessageItem[]>(`/chat/${sessionId}/messages`);
}

export function sendChatMessage(sessionId: string, message: string): Promise<ChatMessageItem> {
  return fetchApi<ChatMessageItem>(`/chat/${sessionId}/send`, {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
}

export function deleteChatSession(sessionId: string): Promise<{ ok: boolean }> {
  return fetchApi<{ ok: boolean }>(`/chat/${sessionId}`, { method: 'DELETE' });
}

// --- Markets ---

export interface MarketAsset {
  name: string;
  symbol: string;
  price?: number;
  change_24h?: number;
  volume_24h?: number;
  market_cap?: number;
  previous_close?: number;
  currency?: string;
  source?: string;
  error?: string;
}

export interface MarketsResponse {
  assets: Record<string, MarketAsset>;
  updated_at?: string;
}

export function fetchMarkets(): Promise<MarketsResponse> {
  return fetchApi<MarketsResponse>('/markets');
}

export interface HistoryPoint {
  date: string;
  close: number;
}

export interface MarketsHistoryResponse {
  history: Record<string, HistoryPoint[]>;
  updated_at?: string;
}

export function fetchMarketsHistory(): Promise<MarketsHistoryResponse> {
  return fetchApi<MarketsHistoryResponse>('/markets/history');
}

// --- Social Feeds ---

export interface FeedPost {
  id?: string;
  text: string;
  created_at?: string;
  author_name?: string;
  author_username?: string;
  author_avatar?: string;
  author?: string;
  metrics?: { like_count?: number; retweet_count?: number; reply_count?: number };
}

export interface FeedResponse {
  configured: boolean;
  posts: FeedPost[];
  error?: string;
}

export function fetchXFeed(limit?: number): Promise<FeedResponse> {
  const params = limit != null ? `?limit=${limit}` : '';
  return fetchApi<FeedResponse>(`/feeds/x${params}`);
}

export function fetchLinkedInFeed(limit?: number): Promise<FeedResponse> {
  const params = limit != null ? `?limit=${limit}` : '';
  return fetchApi<FeedResponse>(`/feeds/linkedin${params}`);
}

// --- Email Integrations ---

export interface EmailMessage {
  id: string;
  subject: string;
  from_name: string;
  from_email: string;
  received_at: string;
  is_read: boolean;
  preview: string;
}

export interface InboxResponse {
  configured: boolean;
  messages: EmailMessage[];
  error?: string;
}

export function fetchOutlookInbox(limit?: number): Promise<InboxResponse> {
  const params = limit != null ? `?limit=${limit}` : '';
  return fetchApi<InboxResponse>(`/integrations/outlook/inbox${params}`);
}

export function fetchZohoInbox(limit?: number): Promise<InboxResponse> {
  const params = limit != null ? `?limit=${limit}` : '';
  return fetchApi<InboxResponse>(`/integrations/zoho/inbox${params}`);
}

export interface IntegrationsConfig {
  [key: string]: { configured: boolean };
}

export function fetchIntegrationsConfig(): Promise<IntegrationsConfig> {
  return fetchApi<IntegrationsConfig>('/integrations/config');
}

export function fetchLogs(level?: string, limit?: number): Promise<LogEntry[]> {
  const params = new URLSearchParams();
  if (level && level !== 'all') params.set('level', level);
  if (limit != null) params.set('limit', String(limit));
  const qs = params.toString() ? `?${params.toString()}` : '';
  return fetchApi<LogEntry[]>(`/logs${qs}`);
}
