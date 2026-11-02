async function handleResponse(response) {
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const message = data.error || (data.errors && data.errors.join(', ')) || 'Request failed'
    throw new Error(message)
  }
  return data
}

export async function fetchApplications(status = '') {
  const query = status ? `?status=${encodeURIComponent(status)}` : ''
  const response = await fetch(`/api/applications${query}`)
  return handleResponse(response)
}

export async function fetchStats() {
  const response = await fetch('/api/stats')
  return handleResponse(response)
}

export async function createApplication(payload) {
  const response = await fetch('/api/applications', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleResponse(response)
}

export async function updateApplication(id, payload) {
  const response = await fetch(`/api/applications/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return handleResponse(response)
}

export async function deleteApplication(id) {
  const response = await fetch(`/api/applications/${id}`, { method: 'DELETE' })
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
