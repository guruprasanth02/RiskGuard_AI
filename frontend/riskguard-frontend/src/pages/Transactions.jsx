import { useState, useEffect } from 'react'
import { Activity, RefreshCw, Filter } from 'lucide-react'
import { api } from '../api.js'
import { PageHeader, RiskBadge, ActionBadge, Spinner, EmptyState } from '../components/ui.jsx'

export default function Transactions() {
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('ALL')

  const load = () => {
    api.getTransactions(200)
      .then(d => setTransactions(d.transactions || []))
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const filtered = filter === 'ALL'
    ? transactions
    : transactions.filter(t => t.risk_level === filter)

  return (
    <div>
      <PageHeader
        title="Transaction Log"
        subtitle={`${transactions.length} transactions analyzed this session`}
      >
        <div style={{ display: 'flex', gap: 8 }}>
          <select
            value={filter}
            onChange={e => setFilter(e.target.value)}
            style={{ width: 'auto', padding: '8px 12px', fontSize: 13 }}
          >
            <option value="ALL">All Levels</option>
            <option value="LOW">Low Risk</option>
            <option value="MEDIUM">Medium Risk</option>
            <option value="HIGH">High Risk</option>
          </select>
          <button className="btn btn-outline" onClick={load}>
            <RefreshCw size={14} />
          </button>
        </div>
      </PageHeader>

      <div style={{ padding: '24px 32px' }}>
        {loading ? <Spinner /> : (
          <div className="card" style={{ overflow: 'hidden' }}>
            {filtered.length === 0 ? (
              <EmptyState
                icon={Activity}
                title="No transactions"
                description="Transactions analyzed via the API will appear here."
              />
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                  <thead>
                    <tr style={{ background: 'var(--bg-secondary)' }}>
                      {['#', 'Transaction ID', 'Time', 'Type', 'Amount', 'Risk Score', 'Risk Level', 'Action', 'Probability'].map(h => (
                        <th key={h} style={{
                          textAlign: 'left', padding: '12px 16px',
                          color: 'var(--text-muted)', fontWeight: 600,
                          fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.8,
                          borderBottom: '1px solid var(--border)',
                        }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((t, i) => (
                      <tr key={i}
                        style={{ borderBottom: '1px solid var(--border-subtle)', transition: 'background 0.15s' }}
                        onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-card-hover)'}
                        onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                      >
                        <td style={{ padding: '11px 16px', color: 'var(--text-muted)', fontSize: 11 }}>
                          {filtered.length - i}
                        </td>
                        <td style={{ padding: '11px 16px', fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--accent-blue)', maxWidth: 160 }}>
                          <span title={t.transaction_id}>{t.transaction_id?.slice(0, 14)}…</span>
                        </td>
                        <td style={{ padding: '11px 16px', color: 'var(--text-muted)', fontSize: 11, whiteSpace: 'nowrap' }}>
                          {new Date(t.timestamp).toLocaleString()}
                        </td>
                        <td style={{ padding: '11px 16px' }}>
                          <span style={{
                            background: 'var(--bg-secondary)', padding: '2px 8px',
                            borderRadius: 4, fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)',
                          }}>{t.type}</span>
                        </td>
                        <td style={{ padding: '11px 16px', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                          ₹{Number(t.amount || 0).toLocaleString('en-IN')}
                        </td>
                        <td style={{ padding: '11px 16px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <div style={{
                              width: 48, height: 5, borderRadius: 3,
                              background: 'var(--border)', overflow: 'hidden',
                            }}>
                              <div style={{
                                height: '100%', width: `${t.risk_score}%`,
                                background: t.risk_level === 'HIGH' ? 'var(--risk-high)' :
                                  t.risk_level === 'MEDIUM' ? 'var(--risk-medium)' : 'var(--risk-low)',
                              }} />
                            </div>
                            <span style={{ fontWeight: 700, fontSize: 13 }}>{t.risk_score}</span>
                          </div>
                        </td>
                        <td style={{ padding: '11px 16px' }}><RiskBadge level={t.risk_level} /></td>
                        <td style={{ padding: '11px 16px' }}><ActionBadge action={t.recommended_action} /></td>
                        <td style={{ padding: '11px 16px', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
                          {(t.fraud_probability * 100).toFixed(2)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
