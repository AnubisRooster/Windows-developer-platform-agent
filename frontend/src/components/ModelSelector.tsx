'use client';

import { useState, useEffect, useMemo } from 'react';
import {
  fetchModelConfig,
  updateModelConfig,
  type ModelConfig,
  type AvailableModel,
} from '@/lib/api';

const PROVIDERS = [
  { id: 'ironclaw', label: 'IronClaw (NEAR AI)' },
  { id: 'openrouter', label: 'OpenRouter' },
  { id: 'ollama', label: 'Ollama (Local)' },
] as const;

export default function ModelSelector() {
  const [config, setConfig] = useState<ModelConfig | null>(null);
  const [provider, setProvider] = useState('ironclaw');
  const [model, setModel] = useState('');
  const [customModel, setCustomModel] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [ollamaUrl, setOllamaUrl] = useState('http://localhost:11434');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveMsg, setSaveMsg] = useState<string | null>(null);
  const [showApiKey, setShowApiKey] = useState(false);

  useEffect(() => {
    fetchModelConfig()
      .then((cfg) => {
        setConfig(cfg);
        setProvider(cfg.provider ?? 'ironclaw');
        setModel(cfg.model ?? '');
        setOllamaUrl(cfg.ollama_base_url ?? 'http://localhost:11434');
      })
      .catch((err) =>
        setError(err instanceof Error ? err.message : 'Failed to load config'),
      )
      .finally(() => setLoading(false));
  }, []);

  const models: AvailableModel[] = useMemo(() => {
    if (!config?.available_models) return [];
    return config.available_models[provider] ?? [];
  }, [config, provider]);

  const isKnownModel = useMemo(
    () => models.some((m) => m.id === model),
    [models, model],
  );

  const handleProviderChange = (newProvider: string) => {
    setProvider(newProvider);
    const providerModels = config?.available_models?.[newProvider] ?? [];
    if (providerModels.length > 0) {
      setModel(providerModels[0].id);
    } else {
      setModel('');
    }
    setCustomModel('');
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setSaveMsg(null);
    try {
      const finalModel = isKnownModel || !customModel ? model : customModel;
      const update: Record<string, string> = { provider, model: finalModel };
      if (provider === 'openrouter' && apiKey) {
        update.openrouter_api_key = apiKey;
      }
      if (provider === 'ollama') {
        update.ollama_base_url = ollamaUrl;
      }
      await updateModelConfig(update);
      setSaveMsg('Configuration saved');
      setApiKey('');
      const refreshed = await fetchModelConfig();
      setConfig(refreshed);
      setTimeout(() => setSaveMsg(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="card">
        <p className="text-sm text-slate-400">Loading model config&hellip;</p>
      </div>
    );
  }

  return (
    <div className="card space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-medium text-white">Model Configuration</h3>
        {config?.ironclaw_status && (
          <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${
              config.ironclaw_status === 'healthy'
                ? 'bg-green-900/40 text-green-400'
                : 'bg-yellow-900/40 text-yellow-400'
            }`}
          >
            IronClaw: {config.ironclaw_status}
          </span>
        )}
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}
      {saveMsg && <p className="text-sm text-green-400">{saveMsg}</p>}

      {/* Provider */}
      <div>
        <label className="mb-1 block text-xs font-medium text-slate-400">
          Provider
        </label>
        <div className="flex flex-wrap gap-2">
          {PROVIDERS.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => handleProviderChange(p.id)}
              className={`rounded-lg border px-3 py-1.5 text-sm transition-colors ${
                provider === p.id
                  ? 'border-blue-500 bg-blue-500/20 text-blue-300'
                  : 'border-slate-600 bg-slate-800 text-slate-300 hover:border-slate-500'
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Model list */}
      <div>
        <label
          htmlFor="model-select"
          className="mb-1 block text-xs font-medium text-slate-400"
        >
          Model
        </label>
        {models.length > 0 ? (
          <select
            id="model-select"
            value={isKnownModel ? model : '__custom__'}
            onChange={(e) => {
              if (e.target.value === '__custom__') {
                setModel('');
              } else {
                setModel(e.target.value);
                setCustomModel('');
              }
            }}
            className="w-full rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            {models.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name}
              </option>
            ))}
            <option value="__custom__">Custom model&hellip;</option>
          </select>
        ) : (
          <input
            id="model-select"
            type="text"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder="Enter model name"
            className="w-full rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        )}
        {!isKnownModel && models.length > 0 && (
          <input
            type="text"
            value={customModel || model}
            onChange={(e) => {
              setCustomModel(e.target.value);
              setModel(e.target.value);
            }}
            placeholder="e.g. my-org/custom-model:latest"
            className="mt-2 w-full rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        )}
      </div>

      {/* OpenRouter API key */}
      {provider === 'openrouter' && (
        <div>
          <label
            htmlFor="api-key"
            className="mb-1 block text-xs font-medium text-slate-400"
          >
            OpenRouter API Key
          </label>
          {config?.openrouter_api_key_set && !apiKey && (
            <p className="mb-1 text-xs text-green-400">
              Key configured: {config.openrouter_api_key_masked}
            </p>
          )}
          <div className="relative">
            <input
              id="api-key"
              type={showApiKey ? 'text' : 'password'}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={
                config?.openrouter_api_key_set
                  ? 'Enter new key to replace existing'
                  : 'sk-or-...'
              }
              className="w-full rounded-md border border-slate-600 bg-slate-800 px-3 py-2 pr-16 text-sm text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <button
              type="button"
              onClick={() => setShowApiKey(!showApiKey)}
              className="absolute right-2 top-1/2 -translate-y-1/2 rounded px-2 py-0.5 text-xs text-slate-400 hover:text-white"
            >
              {showApiKey ? 'Hide' : 'Show'}
            </button>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Get a key at{' '}
            <a
              href="https://openrouter.ai/keys"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:underline"
            >
              openrouter.ai/keys
            </a>
          </p>
        </div>
      )}

      {/* Ollama URL */}
      {provider === 'ollama' && (
        <div>
          <label
            htmlFor="ollama-url"
            className="mb-1 block text-xs font-medium text-slate-400"
          >
            Ollama Base URL
          </label>
          <input
            id="ollama-url"
            type="text"
            value={ollamaUrl}
            onChange={(e) => setOllamaUrl(e.target.value)}
            placeholder="http://localhost:11434"
            className="w-full rounded-md border border-slate-600 bg-slate-800 px-3 py-2 text-sm text-white placeholder-slate-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>
      )}

      {/* Save button */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={handleSave}
          disabled={saving}
          className="rounded-md bg-blue-600 px-5 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50"
        >
          {saving ? 'Saving\u2026' : 'Save Configuration'}
        </button>
        <span className="text-xs text-slate-500">
          Active: <span className="text-slate-300">{config?.model || 'none'}</span>{' '}
          via <span className="text-slate-300">{config?.provider || 'none'}</span>
        </span>
      </div>
    </div>
  );
}
