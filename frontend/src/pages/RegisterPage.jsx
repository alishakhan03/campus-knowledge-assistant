import { Eye, EyeOff, GraduationCap, Lock, Mail, MessageSquareText, ShieldCheck, Sparkles, User } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Logo from '../components/Logo'
import { useAuth } from '../context/AuthContext'

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register(name, email, password)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="public-shell">
      <div className="auth-hero">
        <div className="auth-hero-content">
          <div className="brand-row">
            <Logo size={30} />
            Campus Knowledge Assistant
          </div>
          <h1>Join your campus knowledge base in seconds.</h1>
          <p>
            Create a student account to start asking questions about attendance, exams, scholarships,
            hostel rules, and placements — grounded in your college's official documents.
          </p>
          <div className="auth-hero-features">
            <div className="auth-hero-feature">
              <span className="feature-icon"><Sparkles size={15} /></span>
              Free to use for every student
            </div>
            <div className="auth-hero-feature">
              <span className="feature-icon"><MessageSquareText size={15} /></span>
              Chat history saved across sessions
            </div>
            <div className="auth-hero-feature">
              <span className="feature-icon"><ShieldCheck size={15} /></span>
              Your data stays private to your account
            </div>
          </div>
        </div>
      </div>

      <div className="auth-form-side">
        <div className="auth-card">
          <div className="brand-row-mobile">
            <Logo size={26} />
            Campus Knowledge Assistant
          </div>
          <h2>Create your account</h2>
          <div className="subtitle">Sign up as a student to get started</div>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Full name</label>
              <div className="input-wrap">
                <User size={16} />
                <input value={name} onChange={(e) => setName(e.target.value)} required minLength={2} autoFocus />
              </div>
            </div>
            <div className="form-group">
              <label>Email</label>
              <div className="input-wrap">
                <Mail size={16} />
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@college.edu" required />
              </div>
            </div>
            <div className="form-group">
              <label>Password</label>
              <div className="input-wrap">
                <Lock size={16} />
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={8}
                  placeholder="At least 8 characters"
                />
                <button
                  type="button"
                  className="toggle-visibility"
                  onClick={() => setShowPassword((s) => !s)}
                  tabIndex={-1}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              <span className="helper-text">At least 8 characters</span>
            </div>
            {error && <div className="error-text" style={{ marginBottom: 14 }}>{error}</div>}
            <button className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
              {loading ? <span className="spinner" /> : <GraduationCap size={16} />}
              {loading ? 'Creating account...' : 'Register'}
            </button>
          </form>

          <div className="auth-switch">
            Already have an account? <Link to="/login">Log in</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
