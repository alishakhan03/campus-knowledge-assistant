import { FileText, LayoutGrid, LogOut, Menu, Moon, ShieldPlus, Sun, UploadCloud, Users, X } from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import Logo from './Logo'

export default function AdminLayout() {
  const { user, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const [mobileOpen, setMobileOpen] = useState(false)

  function closeMobile() {
    setMobileOpen(false)
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
          Admin Panel
        </div>
        <button className="icon-btn" onClick={toggleTheme} aria-label="Toggle theme">
          {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
        </button>
      </div>

      <div className={`sidebar-overlay ${mobileOpen ? 'open' : ''}`} onClick={closeMobile} />

      <aside className={`sidebar ${mobileOpen ? 'open' : ''}`}>
        <div className="sidebar-brand">
          <Logo size={24} />
          Admin · Campus Assistant
          <button className="icon-btn" style={{ marginLeft: 'auto', display: mobileOpen ? 'flex' : 'none' }} onClick={closeMobile}>
            <X size={18} />
          </button>
        </div>

        <NavLink to="/admin" end className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`} onClick={closeMobile}>
          <LayoutGrid size={17} />
          Overview
        </NavLink>
        <NavLink to="/admin/documents" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`} onClick={closeMobile}>
          <FileText size={17} />
          Documents
        </NavLink>
        <NavLink to="/admin/documents/upload" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`} onClick={closeMobile}>
          <UploadCloud size={17} />
          Upload Document
        </NavLink>
        <NavLink to="/admin/manage-admins" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`} onClick={closeMobile}>
          <ShieldPlus size={17} />
          Manage Admins
        </NavLink>
        <NavLink to="/dashboard" className="sidebar-link" onClick={closeMobile}>
          <Users size={17} />
          Student View
        </NavLink>

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
              <div className="helper-text">Administrator</div>
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
