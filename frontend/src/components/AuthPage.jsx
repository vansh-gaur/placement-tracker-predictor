import { useState } from 'react'
import { login, register, setToken } from '../api.js'

export default function AuthPage({ onLoggedIn }) {
  const [mode, setMode] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setMessage('')
    try {
      if (mode === 'register') {
        await register(email, password)
        setMessage('Account created. You can log in now.')
        setMode('login')
      } else {
        const result = await login(email, password)
        setToken(result.token)
        onLoggedIn(result.email)
      }
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <main className="layout">
      <section className="card">
        <h1>Placement Tracker</h1>
        <p className="muted">
          {mode === 'login'
            ? 'Log in to see your own applications. Each account only sees its own data.'
            : 'Create an account. Passwords are stored hashed, never in plain text.'}
        </p>
        <form onSubmit={handleSubmit}>
          <label>
            Email
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </label>
          <label>
            Password (at least 8 characters)
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </label>
          <button type="submit">{mode === 'login' ? 'Log in' : 'Register'}</button>
        </form>
        {error && <p className="error">{error}</p>}
        {message && <p className="muted">{message}</p>}
        <p className="muted">
          {mode === 'login' ? (
            <button className="secondary" type="button" onClick={() => setMode('register')}>
              Create an account
            </button>
          ) : (
            <button className="secondary" type="button" onClick={() => setMode('login')}>
              Back to log in
            </button>
          )}
        </p>
      </section>
    </main>
  )
}
