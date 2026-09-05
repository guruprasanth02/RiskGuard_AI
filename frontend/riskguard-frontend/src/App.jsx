import { useState, useEffect, useCallback } from 'react'
import { Routes, Route, NavLink } from 'react-router-dom'
import { 
  Shield, Activity, Search, BarChart2, AlertTriangle, 
  CheckCircle, XCircle, Clock, Menu, X 
} from 'lucide-react'
import Dashboard from './pages/Dashboard.jsx'
import Analyze from './pages/Analyze.jsx'
import Transactions from './pages/Transactions.jsx'
import ModelInfo from './pages/ModelInfo.jsx'
import { api } from './api.js'

function StatusDot({ ready }) {
  return (
    <span style={{
      display: 'inline-block',
      width: 8, height: 8,
      borderRadius: '50%',
      background: ready ? 'var(--accent-green)' : 'var(--accent-red)',
      boxShadow: ready ? '0 0 8px var(--accent-green)' : '0 0 8px var(--accent-red)',
      marginRight: 6,
    }} />
  )
}

export default function App() {
  const [modelReady, setModelReady] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)

  useEffect(() => {
    api.health()
      .then(h => setModelReady(h.model_ready))
      .catch(() => setModelReady(false))
  }, [])

  const navLinks = [
    { to: '/',           icon: BarChart2,    label: 'Dashboard' },
    { to: '/analyze',    icon: Search,       label: 'Analyze Transaction' },
    { to: '/transactions', icon: Activity,   label: 'Transaction Log' },
    { to: '/model',      icon: Shield,       label: 'Model Info' },
  ]

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      {/* Sidebar */}
      <nav style={{
        width: sidebarOpen ? 240 : 60,
        background: 'var(--bg-secondary)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        transition: 'width 0.25s ease',
        flexShrink: 0,
        position: 'sticky',
        top: 0,
        height: '100vh',
        overflow: 'hidden',
      }}>
        {/* Logo */}
        <div style={{ 
          padding: '20px 16px', 
          borderBottom: '1px solid var(--border)',
          display: 'flex', alignItems: 'center', gap: 12,
          minHeight: 68,
        }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0,
          }}>
            <Shield size={18} color="white" />
          </div>
          {sidebarOpen && (
            <div>
              <div style={{ fontWeight: 700, fontSize: 15, color: 'var(--text-primary)' }}>
                RiskGuard
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', letterSpacing: 1 }}>
                AI Risk Manager
              </div>
            </div>
          )}
          <button
            onClick={() => setSidebarOpen(o => !o)}
            style={{
              marginLeft: 'auto', background: 'none', border: 'none',
              color: 'var(--text-muted)', cursor: 'pointer', padding: 4,
              borderRadius: 6, display: 'flex', flexShrink: 0,
            }}
          >
            {sidebarOpen ? <X size={16} /> : <Menu size={16} />}
          </button>
        </div>

        {/* Navigation */}
        <div style={{ flex: 1, padding: '12px 8px', overflowY: 'auto' }}>
          {navLinks.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '10px 12px',
                borderRadius: 8,
                marginBottom: 4,
                textDecoration: 'none',
                color: isActive ? 'var(--accent-blue)' : 'var(--text-secondary)',
                background: isActive ? 'var(--accent-blue-glow)' : 'transparent',
                fontWeight: isActive ? 600 : 400,
                fontSize: 14,
                transition: 'all 0.15s',
                overflow: 'hidden',
                whiteSpace: 'nowrap',
              })}
            >
              <Icon size={18} style={{ flexShrink: 0 }} />
              {sidebarOpen && label}
            </NavLink>
          ))}
        </div>

        {/* Status */}
        {sidebarOpen && (
          <div style={{
            padding: '12px 16px',
            borderTop: '1px solid var(--border)',
            fontSize: 12,
            color: 'var(--text-muted)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: 4 }}>
              <StatusDot ready={modelReady === true} />
              {modelReady === null ? 'Checking...' : modelReady ? 'Model Ready' : 'Model Not Loaded'}
            </div>
            <div style={{ fontSize: 10, opacity: 0.6 }}>PaySim Dataset · Prototype</div>
          </div>
        )}
      </nav>

      {/* Main content */}
      <main style={{ flex: 1, overflow: 'auto', background: 'var(--bg-primary)' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/analyze" element={<Analyze />} />
          <Route path="/transactions" element={<Transactions />} />
          <Route path="/model" element={<ModelInfo />} />
        </Routes>
      </main>
    </div>
  )
}
