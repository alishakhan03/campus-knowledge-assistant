import { Eye, EyeOff, GraduationCap, Lock, Mail, MessageSquareText, ShieldCheck, Sparkles } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Logo from '../components/Logo'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
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
      const user = await login(email, password)
      navigate(user.role === 'ADMIN' ? '/admin' : '/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials and try again.')
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
          <h1>Get instant, grounded answers about your college.</h1>
          <p>
            Ask about attendance rules, exam schedules, scholarships, hostel procedures, and placement
            records — answered directly from official college documents, with sources cited every time.
          </p>
          <div className="auth-hero-features">
            <div className="auth-hero-feature">
              <span className="feature-icon"><Sparkles size={15} /></span>
              AI answers grounded in real college documents
            </div>
            <div className="auth-hero-feature">
              <span className="feature-icon"><MessageSquareText size={15} /></span>
              Every answer includes source & page citations
            </div>
            <div className="auth-hero-feature">
              <span className="feature-icon"><ShieldCheck size={15} /></span>
              Never invents rules, dates, or eligibility criteria
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
          <h2>Welcome back</h2>
          <div className="subtitle">Log in to continue to your dashboard</div>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Email</label>
              <div className="input-wrap">
                <Mail size={16} />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@college.edu"
                  required
                  autoFocus
                />
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
                  placeholder="••••••••"
                  required
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
            </div>
            {error && <div className="error-text" style={{ marginBottom: 14 }}>{error}</div>}
            <button className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
              {loading ? <span className="spinner" /> : <GraduationCap size={16} />}
              {loading ? 'Logging in...' : 'Log in'}
            </button>
          </form>

          <div className="auth-switch">
            Don't have an account? <Link to="/register">Create one</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
