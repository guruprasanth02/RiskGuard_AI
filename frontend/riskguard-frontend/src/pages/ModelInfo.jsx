import { useState, useEffect } from 'react'
import { Shield, TrendingUp, Target, BarChart2, CheckCircle, Info } from 'lucide-react'
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell
} from 'recharts'
import { api } from '../api.js'
import { PageHeader, StatCard, Alert, Spinner, EmptyState } from '../components/ui.jsx'

function MetricCard({ label, value, sub, color }) {
  return (
    <div className="card" style={{ padding: '16px 20px', textAlign: 'center' }}>
      <div style={{ fontSize: 26, fontWeight: 800, color: color || 'var(--accent-blue)', lineHeight: 1 }}>
        {value}
      </div>
      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 6, textTransform: 'uppercase', letterSpacing: 0.8 }}>
        {label}
      </div>
      {sub && <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{sub}</div>}
    </div>
  )
}

export default function ModelInfo() {
  const [info, setInfo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.getModelInfo()
      .then(setInfo)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />

  if (error) {
    return (
      <div>
        <PageHeader title="Model Information" />
        <div style={{ padding: '24px 32px' }}>
          <Alert type="warning">
            <strong>Model not trained yet.</strong><br />
            Run <code style={{ background: 'rgba(0,0,0,0.3)', padding: '2px 6px', borderRadius: 4 }}>
              python src/models/train.py
            </code> to train the model, then refresh.
          </Alert>
        </div>
      </div>
    )
  }

  const tm = info?.test_metrics || {}
  const vm = info?.val_metrics || {}
  const allVal = info?.all_val_metrics || {}

  // Radar chart data
  const radarData = [
    { metric: 'Precision', value: Math.round((tm.precision_fraud || 0) * 100) },
    { metric: 'Recall', value: Math.round((tm.recall_fraud || 0) * 100) },
    { metric: 'F1', value: Math.round((tm.f1_fraud || 0) * 100) },
    { metric: 'PR-AUC', value: Math.round((tm.pr_auc || 0) * 100) },
    { metric: 'ROC-AUC', value: Math.round((tm.roc_auc || 0) * 100) },
  ]

  // Model comparison bar chart
  const modelData = Object.entries(allVal).map(([name, metrics]) => ({
    name: name.replace('LogisticRegression', 'LR').replace('RandomForest', 'RF').replace('XGBoost', 'XGB'),
    'PR-AUC': Math.round((metrics.pr_auc || 0) * 1000) / 10,
    'F1': Math.round((metrics.f1_fraud || 0) * 1000) / 10,
    isSelected: name === info.model_name,
  }))

  return (
    <div>
      <PageHeader
        title="Model Information"
        subtitle={`Selected model: ${info?.model_name || 'N/A'}`}
      />
      <div style={{ padding: '24px 32px' }}>

        {/* Selected model banner */}
        <div className="card" style={{
          padding: '20px 24px', marginBottom: 24,
          background: 'linear-gradient(135deg, rgba(59,130,246,0.1), rgba(139,92,246,0.1))',
          border: '1px solid rgba(59,130,246,0.3)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Shield size={24} color="var(--accent-blue)" />
            <div>
              <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)' }}>
                {info?.model_name}
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 2 }}>
                Selected based on highest Validation PR-AUC · Threshold: {(info?.threshold * 100).toFixed(1)}%
              </div>
            </div>
            <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 2 }}>Dataset</div>
              <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                PaySim Synthetic · {(info?.train_end_step / 744 * 100).toFixed(0)}% train split
              </div>
            </div>
          </div>
        </div>

        {/* Test metrics */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 12 }}>
            Test Set Performance (held-out, steps {info?.val_end_step + 1}–744)
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 12 }}>
            <MetricCard label="Precision" value={`${((tm.precision_fraud || 0) * 100).toFixed(1)}%`} color="var(--accent-blue)" />
            <MetricCard label="Recall" value={`${((tm.recall_fraud || 0) * 100).toFixed(1)}%`} color="var(--accent-green)" />
            <MetricCard label="F1 Score" value={`${((tm.f1_fraud || 0) * 100).toFixed(1)}%`} color="var(--accent-purple)" />
            <MetricCard label="PR-AUC" value={(tm.pr_auc || 0).toFixed(4)} color="var(--accent-blue)" sub="Primary metric" />
            <MetricCard label="ROC-AUC" value={(tm.roc_auc || 0).toFixed(4)} color="var(--accent-yellow)" />
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>
          {/* Radar */}
          <div className="card" style={{ padding: '20px 24px' }}>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16 }}>
              Test Performance Radar
            </div>
            <ResponsiveContainer width="100%" height={250}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="var(--border)" />
                <PolarAngleAxis dataKey="metric" tick={{ fill: 'var(--text-muted)', fontSize: 12 }} />
                <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
                <Radar name="Score" dataKey="value" stroke="var(--accent-blue)" fill="var(--accent-blue)" fillOpacity={0.2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          {/* Model comparison */}
          <div className="card" style={{ padding: '20px 24px' }}>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16 }}>
              Model Comparison (Validation PR-AUC)
            </div>
            {modelData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={modelData} barSize={32}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                  <XAxis dataKey="name" tick={{ fill: 'var(--text-muted)', fontSize: 12 }} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 100]} tick={{ fill: 'var(--text-muted)', fontSize: 12 }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }}
                  />
                  <Bar dataKey="PR-AUC" name="PR-AUC %" radius={[4, 4, 0, 0]}>
                    {modelData.map((d, i) => (
                      <Cell key={i} fill={d.isSelected ? 'var(--accent-blue)' : 'var(--text-muted)'} opacity={d.isSelected ? 1 : 0.5} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState title="Run training to see comparison" />
            )}
          </div>
        </div>

        {/* Confusion matrix */}
        {tm.confusion_matrix && (
          <div className="card" style={{ padding: '20px 24px', marginBottom: 24 }}>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16 }}>
              Confusion Matrix (Test Set)
            </div>
            <div style={{ display: 'inline-grid', gridTemplateColumns: 'auto 1fr 1fr', gap: 8, alignItems: 'center' }}>
              <div></div>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textAlign: 'center' }}>Pred: Legit</div>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textAlign: 'center' }}>Pred: Fraud</div>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}>Actual: Legit</div>
              <div style={{ background: 'rgba(16,185,129,0.15)', border: '2px solid var(--risk-low)', borderRadius: 8, padding: '16px 24px', textAlign: 'center' }}>
                <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--risk-low)' }}>{(tm.confusion_matrix[0][0] || 0).toLocaleString()}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>True Negatives</div>
              </div>
              <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid var(--border)', borderRadius: 8, padding: '16px 24px', textAlign: 'center' }}>
                <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--risk-high)' }}>{(tm.confusion_matrix[0][1] || 0).toLocaleString()}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>False Positives</div>
              </div>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}>Actual: Fraud</div>
              <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid var(--border)', borderRadius: 8, padding: '16px 24px', textAlign: 'center' }}>
                <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--risk-medium)' }}>{(tm.confusion_matrix[1][0] || 0).toLocaleString()}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>False Negatives</div>
              </div>
              <div style={{ background: 'rgba(16,185,129,0.15)', border: '2px solid var(--risk-low)', borderRadius: 8, padding: '16px 24px', textAlign: 'center' }}>
                <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--risk-low)' }}>{(tm.confusion_matrix[1][1] || 0).toLocaleString()}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>True Positives</div>
              </div>
            </div>
          </div>
        )}

        {/* Features used */}
        <div className="card" style={{ padding: '20px 24px', marginBottom: 24 }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16 }}>
            Feature Engineering
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {(info?.feature_cols || []).map(f => (
              <span key={f} style={{
                background: 'var(--bg-secondary)', border: '1px solid var(--border)',
                padding: '4px 12px', borderRadius: 6,
                fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--accent-blue)',
              }}>
                {f}
              </span>
            ))}
          </div>
          <Alert type="info" style={{ marginTop: 16 }}>
            <strong>Data Leakage Note:</strong> newbalanceOrig, newbalanceDest, nameOrig, nameDest,
            and isFlaggedFraud are excluded. See src/features/engineering.py for detailed justification.
          </Alert>
        </div>

        <Alert type="info">
          All metrics are from actual model training on PaySim synthetic data. No metrics have been fabricated.
          The dataset contains 6.3M transactions with &lt;0.13% fraud rate.
        </Alert>
      </div>
    </div>
  )
}
