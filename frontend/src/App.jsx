import { useEffect, useState } from 'react'
import ApplicationForm from './components/ApplicationForm.jsx'
import PredictorForm from './components/PredictorForm.jsx'
import StatsCards from './components/StatsCards.jsx'
import {
  createApplication,
  deleteApplication,
  fetchApplications,
  fetchStats,
  updateApplication,
} from './api.js'

const STATUSES = ['Applied', 'Shortlisted', 'Interview', 'Offer', 'Rejected']

export default function App() {
  const [applications, setApplications] = useState([])
  const [stats, setStats] = useState(null)
  const [filter, setFilter] = useState('')
  const [editing, setEditing] = useState(null)
  const [error, setError] = useState('')

  async function refresh() {
    try {
      setError('')
      const [apps, statsData] = await Promise.all([
        fetchApplications(filter),
        fetchStats(),
      ])
      setApplications(apps)
      setStats(statsData)
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => {
    refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter])

  async function handleSubmit(form) {
    try {
      if (editing) {
        await updateApplication(editing.id, form)
        setEditing(null)
      } else {
        await createApplication(form)
      }
      await refresh()
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleDelete(id) {
    if (!window.confirm('Delete this application?')) return
    try {
      await deleteApplication(id)
      await refresh()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <main className="layout">
      <header>
        <h1>Placement Tracker</h1>
        <p className="muted">Track applications and check an estimated placement chance.</p>
      </header>

      {error && <p className="error">{error}</p>}

      <StatsCards stats={stats} statuses={STATUSES} />

      <div className="two-column">
        <ApplicationForm
          editing={editing}
          onSubmit={handleSubmit}
          onCancel={() => setEditing(null)}
        />
        <PredictorForm />
      </div>

      <section className="card">
        <div className="list-header">
          <h2>Applications</h2>
          <label>
            Filter by status
            <select value={filter} onChange={(event) => setFilter(event.target.value)}>
              <option value="">All statuses</option>
              {STATUSES.map((status) => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
          </label>
        </div>

        {applications.length === 0 ? (
          <p className="muted">No applications yet. Add your first one above.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Company</th>
                <th>Role</th>
                <th>Type</th>
                <th>Status</th>
                <th>Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {applications.map((app) => (
                <tr key={app.id}>
                  <td>{app.company}</td>
                  <td>{app.role}</td>
                  <td>{app.type}</td>
                  <td><span className={`status status-${app.status.toLowerCase()}`}>{app.status}</span></td>
                  <td>{app.applied_date || '-'}</td>
                  <td className="actions">
                    <button className="secondary" onClick={() => setEditing(app)}>Edit</button>
                    <button className="danger" onClick={() => handleDelete(app.id)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </main>
  )
}
