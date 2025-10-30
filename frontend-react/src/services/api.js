const BASE = import.meta?.env?.VITE_API_BASE_URL || 'http://localhost:8002'

function authHeaders(token) {
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function login(email, password) {
  const res = await fetch(`${BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  })
  if (!res.ok) throw new Error((await res.json()).detail || 'Login failed')
  return res.json()
}

export async function me(token) {
  const res = await fetch(`${BASE}/api/auth/me`, { headers: authHeaders(token) })
  if (!res.ok) throw new Error('Unauthorized')
  return res.json()
}

export async function ask(token, question) {
  const res = await fetch(`${BASE}/api/chat/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders(token) },
    body: JSON.stringify({ question })
  })
  if (!res.ok) throw new Error('Ask failed')
  return res.json()
}

