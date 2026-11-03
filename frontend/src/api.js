function authHeaders(extra = {}) {
  const token = localStorage.getItem('placement_token')
  return token ? { ...extra, Authorization: `Bearer ${token}` } : { ...extra }
}

export function getToken() {
  return localStorage.getItem('placement_token')
}

export function setToken(token) {
  if (token) {
    localStorage.setItem('placement_token', token)
  } else {
    localStorage.removeItem('placement_token')
  }
}

async function handleResponse(response) {
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const message = data.error || (data.errors && data.errors.join(', ')) || 'Request failed'
    throw new Error(message)
  }
  return data
}

export async function register(email, password) {
  const response = await fetch('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  return handleResponse(response)
}

export async function login(email, password) {
  const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  return handleResponse(response)
}

export async function fetchApplications(status = '') {
  const query = status ? `?status=${encodeURIComponent(status)}` : ''
  const response = await fetch(`/api/applications${query}`, { headers: authHeaders() })
  return handleResponse(response)
}

export async function fetchStats() {
  const response = await fetch('/api/stats', { headers: authHeaders() })
  return handleResponse(response)
}

export async function createApplication(payload) {
  const response = await fetch('/api/applications', {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  })
  return handleResponse(response)
}

export async function updateApplication(id, payload) {
  const response = await fetch(`/api/applications/${id}`, {
    method: 'PUT',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  })
  return handleResponse(response)
}

export async function deleteApplication(id) {
  const response = await fetch(`/api/applications/${id}`, {
    method: 'DELETE',
    headers: authHeaders(),
  })
  return handleResponse(response)
}

export async function predictPlacement(payload) {
  const response = await fetch('/api/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleResponse(response)
}
