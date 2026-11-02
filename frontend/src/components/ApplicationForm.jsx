import { useEffect, useState } from 'react'

const emptyForm = {
  company: '',
  role: '',
  type: 'Job',
  status: 'Applied',
  applied_date: '',
  notes: '',
}

export default function ApplicationForm({ editing, onSubmit, onCancel }) {
  const [form, setForm] = useState(emptyForm)

  useEffect(() => {
    setForm(editing ? { ...emptyForm, ...editing } : emptyForm)
  }, [editing])

  function updateField(event) {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
  }

  function handleSubmit(event) {
    event.preventDefault()
    onSubmit(form)
    if (!editing) setForm(emptyForm)
  }

  return (
    <form className="card form" onSubmit={handleSubmit}>
      <h2>{editing ? 'Edit application' : 'Add application'}</h2>
      <div className="form-grid">
        <label>
          Company
          <input name="company" value={form.company} onChange={updateField} required />
        </label>
        <label>
          Role
          <input name="role" value={form.role} onChange={updateField} required />
        </label>
        <label>
          Type
          <select name="type" value={form.type} onChange={updateField}>
            <option value="Job">Job</option>
            <option value="Internship">Internship</option>
          </select>
        </label>
        <label>
          Status
          <select name="status" value={form.status} onChange={updateField}>
            <option value="Applied">Applied</option>
            <option value="Shortlisted">Shortlisted</option>
            <option value="Interview">Interview</option>
            <option value="Offer">Offer</option>
            <option value="Rejected">Rejected</option>
          </select>
        </label>
        <label>
          Applied date
          <input type="date" name="applied_date" value={form.applied_date} onChange={updateField} />
        </label>
        <label className="full-width">
          Notes
          <input name="notes" value={form.notes} onChange={updateField} placeholder="Round details, contact, next step" />
        </label>
      </div>
      <div className="form-actions">
        <button type="submit">{editing ? 'Save changes' : 'Add application'}</button>
        {editing && (
          <button type="button" className="secondary" onClick={onCancel}>
            Cancel
          </button>
        )}
      </div>
    </form>
  )
}
