import { CheckCircle2, Mail, ShieldPlus, User } from 'lucide-react'
import { useState } from 'react'
import { authApi } from '../api/endpoints'

export default function AdminManageAdminsPage() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)
    try {
      const res = await authApi.registerAdmin({ name, email, password })
      setSuccess(`${res.data.name} (${res.data.email}) can now log in as an admin.`)
      setName('')
      setEmail('')
      setPassword('')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create admin account')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <div className="topbar">
        <h1>Manage Admins</h1>
      </div>
      <div className="page-body">
        <form className="card" style={{ maxWidth: 480 }} onSubmit={handleSubmit}>
          <p className="helper-text" style={{ marginTop: 0, marginBottom: 20 }}>
            Create another administrator account. They'll be able to upload, reprocess, and delete
            documents, and create further admin accounts of their own.
          </p>

          <div className="form-group">
            <label>Full name</label>
            <div className="input-wrap">
              <User size={16} />
              <input value={name} onChange={(e) => setName(e.target.value)} required minLength={2} />
            </div>
          </div>
          <div className="form-group">
            <label>Email</label>
            <div className="input-wrap">
              <Mail size={16} />
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
          </div>
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              placeholder="At least 8 characters"
            />
          </div>

          {error && <div className="error-text" style={{ marginBottom: 14 }}>{error}</div>}
          {success && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                color: 'var(--success)',
                background: 'var(--success-bg)',
                padding: '8px 11px',
                borderRadius: 8,
                marginBottom: 14,
                fontSize: 13.5,
              }}
            >
              <CheckCircle2 size={15} />
              {success}
            </div>
          )}

          <button className="btn btn-primary" disabled={loading}>
            {loading ? <span className="spinner" /> : <ShieldPlus size={16} />}
            {loading ? 'Creating...' : 'Create admin account'}
          </button>
        </form>
      </div>
    </>
  )
}