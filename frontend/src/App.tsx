import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './contexts/AuthContext'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import ChatPage from './pages/ChatPage'
import TemplatesPage from './pages/TemplatesPage'
import DueDiligencePage from './pages/DueDiligencePage'
import EditorPage from './pages/EditorPage'
import AdminPage from './pages/AdminPage'
import { Box, CircularProgress } from '@mui/material'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    )
  }
  
  return user ? <>{children}</> : <Navigate to="/login" />
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    )
  }
  
  if (!user) return <Navigate to="/login" />
  if (user.role !== 'admin') return <Navigate to="/" />
  
  return <>{children}</>
}

function App() {
  const { user } = useAuth()
  
  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" /> : <LoginPage />} />
      
      <Route path="/" element={
        <PrivateRoute>
          <Layout />
        </PrivateRoute>
      }>
        <Route index element={<DashboardPage />} />
        <Route path="chat" element={<ChatPage />} />
        <Route path="chat/:sessionId" element={<ChatPage />} />
        <Route path="templates" element={<TemplatesPage />} />
        <Route path="due-diligence" element={<DueDiligencePage />} />
        <Route path="due-diligence/:checkId" element={<DueDiligencePage />} />
        <Route path="editor" element={<EditorPage />} />
        <Route path="editor/:documentId" element={<EditorPage />} />
        <Route path="admin/*" element={
          <AdminRoute>
            <AdminPage />
          </AdminRoute>
        } />
      </Route>
    </Routes>
  )
}

export default App

