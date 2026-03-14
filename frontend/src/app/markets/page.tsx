'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
} from 'recharts';
import {
  fetchMarkets,
  fetchMarketsHistory,
  type MarketsResponse,
  type MarketAsset,
  type HistoryPoint,
} from '@/lib/api';

// ── Formatting helpers ──────────────────────────────────────────────────────

function formatPrice(price: number | undefined, symbol: string): string {
  if (price == null) return '—';
  if (symbol === 'BTC') return `$${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  if (symbol === 'SI') return `$${price.toFixed(3)}`;
  return `$${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatLargeNumber(n: number | undefined): string {
  if (n == null) return '—';
  if (n >= 1e12) return `$${(n / 1e12).toFixed(2)}T`;
  if (n >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
  return `$${n.toLocaleString()}`;
}

function shortDate(d: string): string {
  const [, m, day] = d.split('-');
  return `${parseInt(m)}/${parseInt(day)}`;
}

// ── Price card ──────────────────────────────────────────────────────────────

function PriceCard({ asset }: { asset: MarketAsset }) {
  const changePositive = (asset.change_24h ?? 0) >= 0;
  const changeColor = changePositive ? 'text-accent-green' : 'text-accent-red';
  const changeBg = changePositive ? 'bg-accent-green/10 border-accent-green/30' : 'bg-accent-red/10 border-accent-red/30';

  if (asset.error) {
    return (
      <div className="card">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-lg font-semibold text-white">{asset.name}</h3>
            <span className="text-xs text-slate-500">{asset.symbol}</span>
          </div>
        </div>
        <p className="text-sm text-accent-amber">{asset.error}</p>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-white">{asset.name}</h3>
          <span className="text-xs text-slate-500">{asset.symbol}</span>
        </div>
        {asset.change_24h != null && (
          <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold ${changeBg} ${changeColor}`}>
            {changePositive ? '+' : ''}{asset.change_24h.toFixed(2)}%
          </span>
        )}
      </div>

      <p className="text-3xl font-bold text-white tracking-tight mb-4">
        {formatPrice(asset.price, asset.symbol)}
      </p>

      <div className="grid grid-cols-2 gap-3 text-xs">
        {asset.previous_close != null && (
          <div>
            <span className="text-slate-500">Prev Close</span>
            <p className="text-slate-300 font-medium">{formatPrice(asset.previous_close, asset.symbol)}</p>
          </div>
        )}
        {asset.volume_24h != null && (
          <div>
            <span className="text-slate-500">24h Volume</span>
            <p className="text-slate-300 font-medium">{formatLargeNumber(asset.volume_24h)}</p>
          </div>
        )}
        {asset.market_cap != null && (
          <div>
            <span className="text-slate-500">Market Cap</span>
            <p className="text-slate-300 font-medium">{formatLargeNumber(asset.market_cap)}</p>
          </div>
        )}
        {asset.source && (
          <div>
            <span className="text-slate-500">Source</span>
            <p className="text-slate-300 font-medium capitalize">{asset.source}</p>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Tooltip ─────────────────────────────────────────────────────────────────

function ChartTooltip({
  active,
  payload,
  label,
  symbol,
}: {
  active?: boolean;
  payload?: { value: number }[];
  label?: string;
  symbol: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-border bg-surface-800 px-3 py-2 shadow-lg">
      <p className="text-xs text-slate-400 mb-1">{label}</p>
      <p className="text-sm font-semibold text-white">{formatPrice(payload[0].value, symbol)}</p>
    </div>
  );
}

// ── Chart ────────────────────────────────────────────────────────────────────

interface PriceChartProps {
  name: string;
  symbol: string;
  data: HistoryPoint[];
  loading: boolean;
  currentPrice?: number;
}

function PriceChart({ name, symbol, data, loading, currentPrice }: PriceChartProps) {
  if (loading) {
    return (
      <div className="card mt-4">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-white">{name} — 30-Day History</h3>
        </div>
        <div className="h-48 flex items-center justify-center">
          <p className="text-xs text-slate-500">Loading chart...</p>
        </div>
      </div>
    );
  }

  if (!data.length) {
    return (
      <div className="card mt-4">
        <p className="text-xs text-slate-500">{name} chart data unavailable</p>
      </div>
    );
  }

  const prices = data.map((d) => d.close);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const padding = (maxPrice - minPrice) * 0.08;
  const firstClose = prices[0];
  const lastClose = prices[prices.length - 1];
  const overallUp = lastClose >= firstClose;
  const strokeColor = overallUp ? '#22c55e' : '#ef4444';
  const gradientId = `grad-${symbol}`;

  // Show every ~5th label to avoid crowding
  const tickInterval = Math.floor(data.length / 6);

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-white">{name} — 30-Day History</h3>
        <div className="flex items-center gap-3 text-xs text-slate-500">
          <span>
            Low: <span className="text-slate-300">{formatPrice(minPrice, symbol)}</span>
          </span>
          <span>
            High: <span className="text-slate-300">{formatPrice(maxPrice, symbol)}</span>
          </span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data} margin={{ top: 4, right: 8, left: 8, bottom: 0 }}>
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={strokeColor} stopOpacity={0.25} />
              <stop offset="95%" stopColor={strokeColor} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2e3a" vertical={false} />
          <XAxis
            dataKey="date"
            tickFormatter={shortDate}
            interval={tickInterval}
            tick={{ fill: '#64748b', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            domain={[minPrice - padding, maxPrice + padding]}
            tickFormatter={(v) => formatPrice(v, symbol)}
            tick={{ fill: '#64748b', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={symbol === 'BTC' ? 80 : 60}
          />
          <Tooltip content={<ChartTooltip symbol={symbol} />} />
          {currentPrice != null && (
            <ReferenceLine
              y={currentPrice}
              stroke="#3b82f6"
              strokeDasharray="4 3"
              strokeOpacity={0.7}
              label={{ value: 'Now', fill: '#3b82f6', fontSize: 10, position: 'insideTopRight' }}
            />
          )}
          <Area
            type="monotone"
            dataKey="close"
            stroke={strokeColor}
            strokeWidth={2}
            fill={`url(#${gradientId})`}
            dot={false}
            activeDot={{ r: 4, fill: strokeColor, stroke: '#0f1117', strokeWidth: 2 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

const ASSET_ORDER = ['btc', 'sp500', 'silver'] as const;

export default function MarketsPage() {
  const [data, setData] = useState<MarketsResponse | null>(null);
  const [history, setHistory] = useState<Record<string, HistoryPoint[]>>({});
  const [loading, setLoading] = useState(true);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [countdown, setCountdown] = useState(30);

  const loadPrices = useCallback(() => {
    fetchMarkets()
      .then((d) => { setData(d); setError(null); })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load'))
      .finally(() => setLoading(false));
  }, []);

  const loadHistory = useCallback(() => {
    fetchMarketsHistory()
      .then((d) => setHistory(d.history))
      .catch(() => {})
      .finally(() => setHistoryLoading(false));
  }, []);

  useEffect(() => {
    loadPrices();
    loadHistory();
    const interval = setInterval(() => {
      loadPrices();
      setCountdown(30);
    }, 30000);
    return () => clearInterval(interval);
  }, [loadPrices, loadHistory]);

  useEffect(() => {
    const tick = setInterval(() => setCountdown((c) => Math.max(0, c - 1)), 1000);
    return () => clearInterval(tick);
  }, []);

  const assets = data?.assets ?? {};

  const assetMeta: Record<string, { name: string; symbol: string }> = {
    btc: { name: 'Bitcoin', symbol: 'BTC' },
    sp500: { name: 'S&P 500', symbol: 'SPX' },
    silver: { name: 'Silver Futures', symbol: 'SI' },
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-white">Markets</h1>
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-500">Refreshing in {countdown}s</span>
          <button
            onClick={() => { loadPrices(); setCountdown(30); }}
            className="rounded-md bg-surface-700 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-surface-700/80 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {loading && !data && <p className="text-slate-400">Loading market data...</p>}
      {error && <p className="text-accent-red text-sm">{error}</p>}

      {/* Price cards row */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {ASSET_ORDER.map((key) => {
          const asset = assets[key];
          if (!asset) return null;
          return <PriceCard key={key} asset={asset} />;
        })}
      </div>

      {/* Charts — one per asset, full width */}
      <div className="space-y-4">
        {ASSET_ORDER.map((key) => {
          const meta = assetMeta[key];
          const asset = assets[key];
          return (
            <PriceChart
              key={key}
              name={meta.name}
              symbol={meta.symbol}
              data={history[key] ?? []}
              loading={historyLoading}
              currentPrice={asset?.price}
            />
          );
        })}
      </div>

      {data?.updated_at && (
        <p className="text-xs text-slate-600">
          Prices updated: {new Date(data.updated_at).toLocaleString()}
        </p>
      )}
    </div>
  );
}
