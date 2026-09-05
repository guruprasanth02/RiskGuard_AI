import { useState, useEffect } from 'react'
import {
  BarChart2, AlertTriangle, CheckCircle, Clock,
  Activity, TrendingUp, ShieldAlert, Eye
} from 'lucide-react'
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import { api } from '../api.js'
import { PageHeader, StatCard, RiskBadge, ActionBadge, Spinner, EmptyState } from '../components/ui.jsx'

const COLORS = {
  LOW: '#10b981',
  MEDIUM: '#f59e0b',
  HIGH: '#ef4444',
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border)',
      borderRadius: 8, padding: '10px 14px', fontSize: 12,
    }}>
      <div style={{ color: 'var(--text-muted)', marginBottom: 4 }}>{label}</div>
      {payload.map(p => (
        <div key={p.name} style={{ color: p.color, fontWeight: 600 }}>
          {p.name}: {p.value}
        </div>
      ))}
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)

  const refresh = () => {
    Promise.all([api.getStats(), api.getTransactions(50)])
      .then(([s, t]) => {
        setStats(s)
        setTransactions(t.transactions || [])
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    refresh()
    const interval = setInterval(refresh, 10000) // refresh every 10s
    return () => clearInterval(interval)
  }, [])

  if (loading) return <Spinner />

  // Chart data
  const pieData = stats ? [
    { name: 'High Risk', value: stats.high_risk, color: COLORS.HIGH },
    { name: 'Medium Risk', value: stats.medium_risk, color: COLORS.MEDIUM },
    { name: 'Low Risk', value: stats.low_risk, color: COLORS.LOW },
  ].filter(d => d.value > 0) : []

  const actionData = stats ? [
    { name: 'Allowed', value: stats.allowed, fill: COLORS.LOW },
    { name: 'Review', value: stats.reviewed, fill: COLORS.MEDIUM },
    { name: 'Blocked', value: stats.blocked, fill: COLORS.HIGH },
  ] : []

  // Recent activity for sparkline
  const activityData = transactions.slice(0, 20).reverse().map((t, i) => ({
    i,
    score: t.risk_score,
  }))

  return (
    <div style={{ animation: 'fadeIn 0.3s ease' }}>
      <PageHeader
        title="Risk Dashboard"
        subtitle="Real-time transaction risk monitoring"
      >
        <button className="btn btn-outline" onClick={refresh} style={{ fontSize: 13 }}>
          <Activity size={14} /> Refresh
        </button>
      </PageHeader>

      <div style={{ padding: '24px 32px' }}>
        {/* Stats grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: 16, marginBottom: 24,
        }}>
          <StatCard
            label="Total Analyzed"
            value={(stats?.total_analyzed || 0).toLocaleString()}
            icon={Activity}
            color="var(--accent-blue)"
          />
          <StatCard
            label="High Risk"
            value={(stats?.high_risk || 0).toLocaleString()}
            sub="Needs immediate review"
            icon={ShieldAlert}
            color="var(--risk-high)"
          />
          <StatCard
            label="Under Review"
            value={(stats?.medium_risk || 0).toLocaleString()}
            sub="Analyst attention required"
            icon={Eye}
            color="var(--risk-medium)"
          />
          <StatCard
            label="Cleared"
            value={(stats?.low_risk || 0).toLocaleString()}
            sub="Low risk transactions"
            icon={CheckCircle}
            color="var(--risk-low)"
          />
          <StatCard
            label="Blocked"
            value={(stats?.blocked || 0).toLocaleString()}
            icon={AlertTriangle}
            color="var(--risk-high)"
          />
        </div>

        {/* Charts row */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, marginBottom: 24 }}>
          {/* Risk distribution pie */}
          <div className="card" style={{ padding: '20px 24px' }}>
            <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 16, color: 'var(--text-primary)' }}>
              Risk Distribution
            </div>
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={80}
                    paddingAngle={3} dataKey="value">
                    {pieData.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }}
                  />
                  <Legend wrapperStyle={{ fontSize: 12, color: 'var(--text-secondary)' }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState title="No data yet" description="Submit transactions to see risk distribution" />
            )}
          </div>

          {/* Action distribution bar */}
          <div className="card" style={{ padding: '20px 24px' }}>
            <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 16, color: 'var(--text-primary)' }}>
              Actions Taken
            </div>
            {actionData.some(d => d.value > 0) ? (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={actionData} barSize={40}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                  <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 12 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 12 }} axisLine={false} tickLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="value" name="Count" radius={[4, 4, 0, 0]}>
                    {actionData.map((d, i) => <Cell key={i} fill={d.fill} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState title="No data yet" />
            )}
          </div>

          {/* Risk score trend */}
          <div className="card" style={{ padding: '20px 24px' }}>
            <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 16, color: 'var(--text-primary)' }}>
              Recent Risk Scores
            </div>
            {activityData.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={activityData}>
                  <defs>
                    <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis hide />
                  <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-muted)', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="score" name="Risk Score"
                    stroke="#3b82f6" fill="url(#scoreGrad)" strokeWidth={2} dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState title="No data yet" description="Submit transactions to see score trend" />
            )}
          </div>
        </div>

        {/* Recent Transactions Table */}
        <div className="card" style={{ padding: '20px 24px' }}>
          <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 16, color: 'var(--text-primary)' }}>
            Recent Transactions
          </div>
          {transactions.length === 0 ? (
            <EmptyState
              icon={Activity}
              title="No transactions analyzed yet"
              description="Use the 'Analyze Transaction' page to submit transactions for risk scoring."
            />
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    {['Transaction ID', 'Timestamp', 'Type', 'Amount', 'Risk Score', 'Risk Level', 'Action'].map(h => (
                      <th key={h} style={{
                        textAlign: 'left', padding: '8px 12px',
                        color: 'var(--text-muted)', fontWeight: 600,
                        fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.8,
                      }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((t, i) => (
                    <tr key={i} style={{
                      borderBottom: '1px solid var(--border-subtle)',
                      transition: 'background 0.15s',
                    }}
                      onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-card-hover)'}
                      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                    >
                      <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', fontSize: 12, color: 'var(--accent-blue)' }}>
                        {t.transaction_id?.slice(0, 12)}...
                      </td>
                      <td style={{ padding: '10px 12px', color: 'var(--text-muted)', fontSize: 11 }}>
                        {new Date(t.timestamp).toLocaleTimeString()}
                      </td>
                      <td style={{ padding: '10px 12px' }}>
                        <span style={{
                          background: 'var(--bg-secondary)', padding: '2px 8px',
                          borderRadius: 4, fontSize: 11, fontWeight: 600,
                          color: 'var(--text-secondary)',
                        }}>{t.type}</span>
                      </td>
                      <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)' }}>
                        ₹{Number(t.amount).toLocaleString('en-IN')}
                      </td>
                      <td style={{ padding: '10px 12px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <div style={{
                            width: 40, height: 4, borderRadius: 2,
                            background: 'var(--border)', overflow: 'hidden',
                          }}>
                            <div style={{
                              height: '100%',
                              width: `${t.risk_score}%`,
                              background: t.risk_level === 'HIGH' ? 'var(--risk-high)' :
                                t.risk_level === 'MEDIUM' ? 'var(--risk-medium)' : 'var(--risk-low)',
                            }} />
                          </div>
                          <span style={{ fontWeight: 600 }}>{t.risk_score}</span>
                        </div>
                      </td>
                      <td style={{ padding: '10px 12px' }}>
                        <RiskBadge level={t.risk_level} />
                      </td>
                      <td style={{ padding: '10px 12px' }}>
                        <ActionBadge action={t.recommended_action} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
