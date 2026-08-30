import { Mail, Shield, User as UserIcon } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function ProfilePage() {
  const { user } = useAuth()
  const initials = (user?.name || '?').split(' ').map((p) => p[0]).slice(0, 2).join('').toUpperCase()

  return (
    <>
      <div className="topbar">
        <h1>Profile</h1>
      </div>
      <div className="page-body">
        <div className="card" style={{ maxWidth: 480 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 24 }}>
            <div className="avatar" style={{ width: 52, height: 52, fontSize: 18 }}>{initials}</div>
            <div>
              <div style={{ fontWeight: 700, fontSize: 16 }}>{user?.name}</div>
              <div className="helper-text">{user?.role === 'ADMIN' ? 'Administrator' : 'Student'}</div>
            </div>
          </div>

          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <UserIcon size={14} /> Name
            </label>
            <div>{user?.name}</div>
          </div>
          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Mail size={14} /> Email
            </label>
            <div>{user?.email}</div>
          </div>
          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Shield size={14} /> Role
            </label>
            <div>{user?.role}</div>
          </div>
        </div>
      </div>
    </>
  )
}
