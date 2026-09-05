// Shared UI components for RiskGuard AI
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

export function PageHeader({ title, subtitle, children }) {
  return (
    <div style={{
      padding: '28px 32px 20px',
      borderBottom: '1px solid var(--border)',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      background: 'var(--bg-secondary)',
    }}>
      <div>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 4 }}>
          {title}
        </h1>
        {subtitle && (
          <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>{subtitle}</p>
        )}
      </div>
      {children}
    </div>
  )
}

export function StatCard({ label, value, sub, icon: Icon, color = 'var(--accent-blue)', trend }) {
  return (
    <div className="card" style={{ padding: '20px 24px', transition: 'all 0.2s' }}
      onMouseEnter={e => e.currentTarget.style.borderColor = color}
      onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
            {label}
          </div>
          <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1 }}>
            {value}
          </div>
          {sub && <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 6 }}>{sub}</div>}
        </div>
        {Icon && (
          <div style={{
            width: 40, height: 40, borderRadius: 10,
            background: `${color}20`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Icon size={20} color={color} />
          </div>
        )}
      </div>
    </div>
  )
}

export function RiskBadge({ level }) {
  const map = {
    LOW: { cls: 'badge-low', label: 'LOW' },
    MEDIUM: { cls: 'badge-medium', label: 'MEDIUM' },
    HIGH: { cls: 'badge-high', label: 'HIGH' },
  }
  const { cls, label } = map[level] || map['LOW']
  return <span className={`badge ${cls}`}>{label}</span>
}

export function ActionBadge({ action }) {
  const styles = {
    ALLOW: { color: 'var(--risk-low)', bg: 'rgba(16,185,129,0.1)', border: 'rgba(16,185,129,0.3)' },
    REVIEW: { color: 'var(--risk-medium)', bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.3)' },
    BLOCK: { color: 'var(--risk-high)', bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.3)' },
  }
  const s = styles[action] || styles['ALLOW']
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      padding: '3px 10px', borderRadius: 999,
      fontSize: 12, fontWeight: 700, letterSpacing: 0.5,
      color: s.color, background: s.bg,
      border: `1px solid ${s.border}`,
    }}>
      {action}
    </span>
  )
}

export function RiskGauge({ score }) {
  const angle = (score / 100) * 180 - 90
  const color = score < 30 ? 'var(--risk-low)' : score < 60 ? 'var(--risk-medium)' : 'var(--risk-high)'

  return (
    <div style={{ textAlign: 'center', padding: '20px 0' }}>
      <svg width="200" height="110" viewBox="0 0 200 110">
        {/* Background arc */}
        <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="var(--border)" strokeWidth="16" strokeLinecap="round" />
        {/* Risk zones */}
        <path d="M 20 100 A 80 80 0 0 1 80 25" fill="none" stroke="rgba(16,185,129,0.4)" strokeWidth="16" strokeLinecap="round" />
        <path d="M 80 25 A 80 80 0 0 1 140 25" fill="none" stroke="rgba(245,158,11,0.4)" strokeWidth="16" strokeLinecap="round" />
        <path d="M 140 25 A 80 80 0 0 1 180 100" fill="none" stroke="rgba(239,68,68,0.4)" strokeWidth="16" strokeLinecap="round" />
        {/* Needle */}
        <line
          x1="100" y1="100"
          x2={100 + 60 * Math.cos((angle * Math.PI) / 180)}
          y2={100 + 60 * Math.sin((angle * Math.PI) / 180)}
          stroke={color} strokeWidth="3" strokeLinecap="round"
        />
        <circle cx="100" cy="100" r="6" fill={color} />
      </svg>
      <div style={{ fontSize: 40, fontWeight: 800, color, marginTop: -8, lineHeight: 1 }}>
        {score}
      </div>
      <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>Risk Score</div>
    </div>
  )
}

export function ShapBar({ feature, impact, direction, maxImpact }) {
  const pct = Math.min((Math.abs(impact) / maxImpact) * 100, 100)
  const isRisk = direction === 'increases_risk'
  const color = isRisk ? 'var(--risk-high)' : 'var(--risk-low)'

  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontSize: 13, color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>
          {feature}
        </span>
        <span style={{ fontSize: 12, color, fontWeight: 600 }}>
          {isRisk ? '+' : '-'}{Math.abs(impact).toFixed(4)}
        </span>
      </div>
      <div style={{ height: 6, background: 'var(--border)', borderRadius: 3, overflow: 'hidden' }}>
        <div style={{
          height: '100%', width: `${pct}%`,
          background: color,
          borderRadius: 3,
          transition: 'width 0.5s ease',
          boxShadow: `0 0 8px ${color}60`,
        }} />
      </div>
    </div>
  )
}

export function Spinner() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
      <div style={{
        width: 36, height: 36, borderRadius: '50%',
        border: '3px solid var(--border)',
        borderTopColor: 'var(--accent-blue)',
        animation: 'spin 0.8s linear infinite',
      }} />
    </div>
  )
}

export function EmptyState({ icon: Icon, title, description }) {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      justifyContent: 'center', padding: '60px 20px', textAlign: 'center',
      color: 'var(--text-muted)',
    }}>
      {Icon && <Icon size={48} style={{ marginBottom: 16, opacity: 0.4 }} />}
      <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>{title}</div>
      {description && <div style={{ fontSize: 13, maxWidth: 300 }}>{description}</div>}
    </div>
  )
}

export function Alert({ type = 'info', children }) {
  const styles = {
    info: { bg: 'rgba(59,130,246,0.1)', border: 'rgba(59,130,246,0.3)', color: '#93c5fd' },
    warning: { bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.3)', color: '#fcd34d' },
    error: { bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.3)', color: '#fca5a5' },
    success: { bg: 'rgba(16,185,129,0.1)', border: 'rgba(16,185,129,0.3)', color: '#6ee7b7' },
  }
  const s = styles[type]
  return (
    <div style={{
      padding: '12px 16px', borderRadius: 8,
      background: s.bg, border: `1px solid ${s.border}`,
      color: s.color, fontSize: 13,
    }}>
      {children}
    </div>
  )
}
