const API_URL = import.meta.env.VITE_API_URL || "http://localhost:3333";

let TOKENS = {
  accessToken: localStorage.getItem("nox_access") || null,
  refreshToken: localStorage.getItem("nox_refresh") || null,
};

export function setTokens({ accessToken, refreshToken }) {
  if (accessToken) { TOKENS.accessToken = accessToken; localStorage.setItem("nox_access", accessToken); }
  if (refreshToken) { TOKENS.refreshToken = refreshToken; localStorage.setItem("nox_refresh", refreshToken); }
}
export function getTokens() { return { ...TOKENS }; }
export function clearTokens() {
  TOKENS = { accessToken: null, refreshToken: null };
  localStorage.removeItem("nox_access"); localStorage.removeItem("nox_refresh");
}

export async function api(path, { method = "GET", body, headers } = {}) {
  const h = { "Content-Type": "application/json", ...(headers || {}) };
  if (TOKENS.accessToken) h["Authorization"] = `Bearer ${TOKENS.accessToken}`;
  const res = await fetch(`${API_URL}${path}`, { method, headers: h, body: body ? JSON.stringify(body) : undefined });
  if (res.status === 204) return null;
  const data = await res.json().catch(()=> ({}));
  return { status: res.status, data };
}

// Specific helpers
export const AuthAPI = {
  register: (email, password, name) => api("/auth/register", { method:"POST", body:{ email, password, name } }),
  login: (email, password) => api("/auth/login", { method:"POST", body:{ email, password } }),
  verify2fa: (email, code) => api("/auth/verify-2fa", { method:"POST", body:{ email, code } }),
  me: () => api("/users/me"),
};
export const PortfolioAPI = {
  list: () => api("/portfolios"),
  create: (name, base="BRL") => api("/portfolios", { method:"POST", body:{ name, base } }),
  addTx: (id, { symbol, type, qty, price }) => api(`/portfolios/${id}/transactions`, { method:"POST", body:{ symbol, type, qty, price } }),
};
export const SignalsAPI = {
  latest: () => api("/signals"),
  byAsset: (symbol) => api(`/signals/asset/${symbol}`),
};
export const NewsAPI = { list: () => api("/news") };
