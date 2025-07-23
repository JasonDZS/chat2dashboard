import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { BackendProvider } from './context/BackendContext'
import TopNav from './components/TopNav'
import SideNav from './components/SideNav'
import Dashboard from './pages/Dashboard'
import Analytics from './pages/Analytics'
import Reports from './pages/Reports'
import Settings from './pages/Settings'
import DataManagement from './pages/DataManagement'
import './App.css'

function App() {
  return (
    <BackendProvider>
      <Router>
        <div className="app">
          <TopNav />
          <div className="app-body">
            <SideNav />
            <main className="main-content">
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/reports" element={<Reports />} />
                <Route path="/data" element={<DataManagement />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </main>
          </div>
        </div>
      </Router>
    </BackendProvider>
  )
}

export default App
