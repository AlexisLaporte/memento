import { Routes, Route } from 'react-router-dom'
import { useAuth } from '@/hooks/use-auth'
import { AppSidebar } from '@/components/AppSidebar'
import WelcomePage from '@/pages/WelcomePage'
import DashboardPage from '@/pages/DashboardPage'
import NewProjectPage from '@/pages/NewProjectPage'
import AdminPage from '@/pages/AdminPage'
import DocPage from '@/pages/DocPage'
import IssuesPage from '@/pages/IssuesPage'
import SettingsPage from '@/pages/SettingsPage'

export default function App() {
  const { isLoading, isAuthenticated } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-muted-foreground text-sm">Loading...</div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <WelcomePage />
  }

  return (
    <div className="flex h-screen bg-background">
      <AppSidebar />
      <main className="flex-1 overflow-y-auto">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/new" element={<NewProjectPage />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="/:project/settings" element={<SettingsPage />} />
          <Route path="/:project/issues" element={<IssuesPage />} />
          <Route path="/:project/*" element={<DocPage />} />
          <Route path="/:project" element={<DocPage />} />
        </Routes>
      </main>
    </div>
  )
}
