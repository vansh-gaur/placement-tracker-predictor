import { useState } from 'react'
import { predictPlacement } from '../api.js'

// Defaults are a mid-range synthetic profile, not a guaranteed outcome.
// Ranges match the backend validation.
const emptyInputs = {
  cgpa: 7.5,
  internships: 1,
  projects: 2,
  dsa_score: 60,
  communication_score: 65,
  backlogs: 0,
}

export default function PredictorForm() {
  const [inputs, setInputs] = useState(emptyInputs)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  function updateField(event) {
    const { name, value } = event.target
    setInputs((current) => ({ ...current, [name]: Number(value) }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setResult(null)
    try {
      setResult(await predictPlacement(inputs))
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section className="card">
      <h2>Placement chance predictor</h2>
      <p className="muted">
        Enter your profile details to get an estimated placement chance from
        the model trained on synthetic data (see the README). This is an
        estimate, not a guarantee.
      </p>
      <form className="form-grid" onSubmit={handleSubmit}>
        <label>
          CGPA (out of 10)
          <input type="number" step="0.1" min="0" max="10" name="cgpa" value={inputs.cgpa} onChange={updateField} required />
        </label>
        <label>
          Internships
          <input type="number" min="0" max="10" name="internships" value={inputs.internships} onChange={updateField} required />
        </label>
        <label>
          Projects
          <input type="number" min="0" max="20" name="projects" value={inputs.projects} onChange={updateField} required />
        </label>
        <label>
          DSA score (0-100)
          <input type="number" min="0" max="100" name="dsa_score" value={inputs.dsa_score} onChange={updateField} required />
        </label>
        <label>
          Communication score (0-100)
          <input type="number" min="0" max="100" name="communication_score" value={inputs.communication_score} onChange={updateField} required />
        </label>
        <label>
          Backlogs
          <input type="number" min="0" max="10" name="backlogs" value={inputs.backlogs} onChange={updateField} required />
        </label>
        <button type="submit" className="full-width">Predict</button>
      </form>

      {error && <p className="error">{error}</p>}
      {result && (
        <div className="prediction-result">
          <strong>{result.percentage}%</strong>
          <span>{result.band} chance</span>
          <p className="muted">{result.note}</p>
        </div>
      )}
    </section>
  )
}
