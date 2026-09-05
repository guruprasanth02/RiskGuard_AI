// API client for RiskGuard AI backend
const API_BASE = '/api';

async function request(method, path, body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) opts.body = JSON.stringify(body);

  const res = await fetch(`${API_BASE}${path}`, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  health: () => request('GET', '/health'),
  predict: (transaction) => request('POST', '/predict', transaction),
  investigate: (evidence) => request('POST', '/investigate', evidence),
  getTransactions: (limit = 100) => request('GET', `/transactions?limit=${limit}`),
  getStats: () => request('GET', '/stats'),
  getModelInfo: () => request('GET', '/model/info'),
  getDemoTransactions: () => request('GET', '/demo/transactions'),
};
