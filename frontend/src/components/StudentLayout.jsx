import {
  LayoutDashboard,
  LogOut,
  Menu,
  MessageSquarePlus,
  Moon,
  Shield,
  Sun,
  Trash2,
  User as UserIcon,
  X,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { NavLink, Outlet, useNavigate, useParams } from 'react-router-dom'
import { chatApi } from '../api/endpoints'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import Logo from './Logo'

export default function StudentLayout() {
  const { user, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const navigate = useNavigate()
  const { conversationId } = useParams()
  const [conversations, setConversations] = useState([])
  const [mobileOpen, setMobileOpen] = useState(false)

  async function loadConversations() {
    const res = await chatApi.listConversations()
    setConversations(res.data)
  }

  useEffect(() => {
    loadConversations()
  }, [conversationId])

  function closeMobile() {
    setMobileOpen(false)
  }

  async function handleNewChat() {
    const res = await chatApi.createConversation(null)
    setConversations((prev) => [res.data, ...prev])
    navigate(`/chat/${res.data.id}`)
    closeMobile()
  }

  async function handleDelete(id, e) {
    e.preventDefault()
    e.stopPropagation()
    if (!window.confirm('Delete this conversation?')) return
    await chatApi.deleteConversation(id)
    setConversations((prev) => prev.filter((c) => c.id !== id))
    if (String(id) === conversationId) navigate('/chat')
  }

  const initials = (user?.name || '?').split(' ').map((p) => p[0]).slice(0, 2).join('').toUpperCase()

  return (
    <div className="app-shell">
      <div className="mobile-topbar">
        <button className="icon-btn" onClick={() => setMobileOpen(true)} aria-label="Open menu">
          <Menu size={20} />
        </button>
        <div className="sidebar-brand" style={{ padding: 0 }}>
          <Logo size={22} />
          Campus Assistant
        </div>
        <button className="icon-btn" onClick={toggleTheme} aria-label="Toggle theme">
          {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
        </button>
      </div>

      <div className={`sidebar-overlay ${mobileOpen ? 'open' : ''}`} onClick={closeMobile} />

      <aside className={`sidebar ${mobileOpen ? 'open' : ''}`}>
        <div className="sidebar-brand">
          <Logo size={24} />
          Campus Assistant
          <button className="icon-btn" style={{ marginLeft: 'auto', display: mobileOpen ? 'flex' : 'none' }} onClick={closeMobile}>
            <X size={18} />
          </button>
        </div>

        <button className="sidebar-link primary-action" onClick={handleNewChat}>
          <MessageSquarePlus size={17} />
          New Chat
        </button>
        <NavLink to="/dashboard" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`} onClick={closeMobile}>
          <LayoutDashboard size={17} />
          Dashboard
        </NavLink>
        <NavLink to="/profile" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`} onClick={closeMobile}>
          <UserIcon size={17} />
          Profile
        </NavLink>
        {user?.role === 'ADMIN' && (
          <NavLink to="/admin" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`} onClick={closeMobile}>
            <Shield size={17} />
            Admin Panel
          </NavLink>
        )}

        <div className="sidebar-section-title">Conversations</div>
        <div className="conversation-list">
          {conversations.length === 0 && (
            <div className="helper-text" style={{ padding: '4px 11px' }}>No conversations yet</div>
          )}
          {conversations.map((c) => (
            <NavLink
              key={c.id}
              to={`/chat/${c.id}`}
              className={({ isActive }) => `conversation-item ${isActive ? 'active' : ''}`}
              onClick={closeMobile}
            >
              <span className="conversation-title">{c.title}</span>
              <button className="icon-btn" onClick={(e) => handleDelete(c.id, e)} title="Delete conversation">
                <Trash2 size={14} />
              </button>
            </NavLink>
          ))}
        </div>

        <div className="sidebar-footer">
          <button className="sidebar-link" onClick={toggleTheme}>
            {theme === 'light' ? <Moon size={17} /> : <Sun size={17} />}
            {theme === 'light' ? 'Dark theme' : 'Light theme'}
          </button>
          <div className="sidebar-user">
            <div className="avatar">{initials}</div>
            <div style={{ overflow: 'hidden' }}>
              <div style={{ fontSize: 13, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {user?.name}
              </div>
              <div className="helper-text">Student</div>
            </div>
          </div>
          <button className="sidebar-link" onClick={logout}>
            <LogOut size={17} />
            Logout
          </button>
        </div>
      </aside>

      <div className="main-content">
        <Outlet />
      </div>
    </div>
  )
}
