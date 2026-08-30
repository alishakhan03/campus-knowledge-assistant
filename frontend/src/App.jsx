import { Navigate, Route, Routes } from 'react-router-dom'
import AdminLayout from './components/AdminLayout'
import { RequireAdmin, RequireAuth } from './components/RouteGuards'
import StudentLayout from './components/StudentLayout'
import { useAuth } from './context/AuthContext'
import AdminDocumentsPage from './pages/AdminDocumentsPage'
import AdminManageAdminsPage from './pages/AdminManageAdminsPage'
import AdminOverviewPage from './pages/AdminOverviewPage'
import AdminUploadPage from './pages/AdminUploadPage'
import ChatPage from './pages/ChatPage'
import DashboardPage from './pages/DashboardPage'
import LoginPage from './pages/LoginPage'
import ProfilePage from './pages/ProfilePage'
import RegisterPage from './pages/RegisterPage'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route
        element={
          <RequireAuth>
            <StudentLayout />
          </RequireAuth>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/chat/:conversationId" element={<ChatPage />} />
      </Route>

      <Route
        path="/admin"
        element={
          <RequireAdmin>
            <AdminLayout />
          </RequireAdmin>
        }
      >
        <Route index element={<AdminOverviewPage />} />
        <Route path="documents" element={<AdminDocumentsPage />} />
        <Route path="documents/upload" element={<AdminUploadPage />} />
        <Route path="manage-admins" element={<AdminManageAdminsPage />} />
      </Route>

      <Route path="/" element={<RoleAwareRedirect />} />
      <Route path="*" element={<RoleAwareRedirect />} />
    </Routes>
  )
}

function RoleAwareRedirect() {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/login" replace />
  return <Navigate to={user.role === 'ADMIN' ? '/admin' : '/dashboard'} replace />
}
