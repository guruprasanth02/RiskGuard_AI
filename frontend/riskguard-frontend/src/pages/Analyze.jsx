import { useState } from 'react'
import { Send, Zap, Shield, Bot, CheckCircle2, ChevronRight, AlertTriangle } from 'lucide-react'
import { api } from '../api.js'
import {
  PageHeader, RiskGauge, RiskBadge, ActionBadge,
  ShapBar, Spinner, Alert
} from '../components/ui.jsx'

const DEMO_TRANSACTIONS = [
  {
    label: 'Normal Routine Payment',
    step: 1, type: 'PAYMENT', amount: 9.99,
    oldbalanceOrg: 1000, newbalanceOrig: 990.01,
    oldbalanceDest: 0, newbalanceDest: 9.99,
    nameOrig: 'C1231006815', nameDest: 'M1979574682',
  },
  {
    label: 'Suspicious Large Transfer',
    step: 200, type: 'TRANSFER', amount: 50000,
    oldbalanceOrg: 75000, newbalanceOrig: 25000,
    oldbalanceDest: 0, newbalanceDest: 50000,
    nameOrig: 'C5432167890', nameDest: 'C9876543210',
  },
  {
    label: 'High-Risk Account Drain (Full Balance)',
    step: 397, type: 'TRANSFER', amount: 181,
    oldbalanceOrg: 181, newbalanceOrig: 0,
    oldbalanceDest: 0, newbalanceDest: 0,
    nameOrig: 'C1231006815', nameDest: 'C1979574682',
  },
]

const TYPES = ['PAYMENT', 'TRANSFER', 'CASH-OUT', 'CASH-IN', 'DEBIT']

const defaultForm = {
  step: 1, type: 'TRANSFER', amount: '',
  oldbalanceOrg: '', newbalanceOrig: '',
  oldbalanceDest: '', newbalanceDest: '',
}

function FormField({ label, name, type = 'number', value, onChange, help }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <label style={{
        display: 'block', fontSize: 12, fontWeight: 600,
        color: 'var(--text-secondary)', marginBottom: 6,
        textTransform: 'uppercase', letterSpacing: 0.5,
      }}>
        {label}
      </label>
      {name === 'type' ? (
        <select value={value} onChange={e => onChange(name, e.target.value)}>
          {TYPES.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
      ) : (
        <input
          type={type}
          value={value}
          onChange={e => onChange(name, e.target.value)}
          placeholder={help || ''}
          step={type === 'number' ? 'any' : undefined}
        />
      )}
      {help && name !== 'type' && (
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>{help}</div>
      )}
    </div>
  )
}

function ResultCard({ result, formState }) {
  const [investigating, setInvestigating] = useState(false)
  const [investigationReport, setInvestigationReport] = useState(null)
  const [invError, setInvError] = useState(null)

  if (!result) return null
  const { transaction_id, fraud_probability, risk_score, risk_level, recommended_action, explanation, model_name, threshold_used } = result
  const topFactors = explanation?.top_factors || []
  const maxImpact = topFactors.length > 0 ? Math.max(...topFactors.map(f => f.impact)) : 1

  const actionColors = {
    ALLOW: 'var(--risk-low)',
    REVIEW: 'var(--risk-medium)',
    BLOCK: 'var(--risk-high)',
  }
  const actionBg = {
    ALLOW: 'rgba(16,185,129,0.08)',
    REVIEW: 'rgba(245,158,11,0.08)',
    BLOCK: 'rgba(239,68,68,0.08)',
  }

  const handleInvestigate = async () => {
    setInvestigating(true)
    setInvError(null)
    try {
      const rep = await api.investigate({
        transaction_id,
        transaction: formState,
        risk_score,
        risk_level,
        recommended_action,
        top_factors: topFactors,
      })
      setInvestigationReport(rep)
    } catch (e) {
      setInvError(e.message)
    } finally {
      setInvestigating(false)
    }
  }

  return (
    <div className="animate-fade-in">
      {/* Decision banner */}
      <div style={{
        background: actionBg[recommended_action],
        border: `1px solid ${actionColors[recommended_action]}40`,
        borderRadius: 12, padding: '20px 24px', marginBottom: 20,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>
            Recommended Action
          </div>
          <div style={{ fontSize: 28, fontWeight: 800, color: actionColors[recommended_action] }}>
            {recommended_action}
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
            Fraud Probability: <strong style={{ color: 'var(--text-primary)' }}>
              {(fraud_probability * 100).toFixed(2)}%
            </strong>
            {' · '}Decision Threshold: {(threshold_used * 100).toFixed(1)}%
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <RiskGauge score={risk_score} />
          <RiskBadge level={risk_level} />
        </div>
      </div>

      {/* SHAP Explanation */}
      {topFactors.length > 0 && (
        <div className="card" style={{ padding: '20px 24px', marginBottom: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
              Explainable Risk Factors (SHAP Feature Attributions)
            </div>
            <span style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              Base: {explanation.base_value}
            </span>
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 20 }}>
            Red indicates factors increasing fraud risk · Green indicates mitigating factors
          </div>
          {topFactors.map(f => (
            <ShapBar key={f.feature} {...f} maxImpact={maxImpact} />
          ))}
        </div>
      )}

      {/* AI Investigator Trigger & Panel */}
      <div className="card" style={{ padding: '20px 24px', marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Bot size={20} color="var(--accent-purple)" />
            <span style={{ fontWeight: 600, fontSize: 14, color: 'var(--text-primary)' }}>
              AI Risk Investigator Assistant
            </span>
          </div>
          {!investigationReport && (
            <button
              className="btn btn-outline"
              onClick={handleInvestigate}
              disabled={investigating}
              style={{ fontSize: 12, padding: '6px 14px' }}
            >
              {investigating ? 'Synthesizing...' : 'Run Investigation'}
            </button>
          )}
        </div>

        {invError && <Alert type="error">{invError}</Alert>}

        {investigationReport ? (
          <div style={{ marginTop: 12, fontSize: 13, borderTop: '1px solid var(--border)', paddingTop: 14 }}>
            <div style={{
              background: 'rgba(139, 92, 246, 0.08)',
              border: '1px solid rgba(139, 92, 246, 0.25)',
              borderRadius: 8, padding: '12px 16px', marginBottom: 14,
            }}>
              <div style={{ fontWeight: 700, color: '#c4b5fd', marginBottom: 4, fontSize: 12, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                Executive Case Summary
              </div>
              <p style={{ color: 'var(--text-primary)', lineHeight: 1.5 }}>
                {investigationReport.executive_summary}
              </p>
            </div>

            <div style={{ marginBottom: 14 }}>
              <div style={{ fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 6, fontSize: 12, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                Analyst Evidence Narrative
              </div>
              <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6, background: 'var(--bg-secondary)', padding: '10px 14px', borderRadius: 6 }}>
                {investigationReport.natural_language_explanation}
              </p>
            </div>

            <div style={{ marginBottom: 12 }}>
              <div style={{ fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8, fontSize: 12, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                Recommended Action Protocol for Risk Team
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {investigationReport.recommended_next_steps.map((step, idx) => (
                  <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, fontSize: 12, color: 'var(--text-primary)' }}>
                    <CheckCircle2 size={15} color="var(--accent-green)" style={{ flexShrink: 0, marginTop: 2 }} />
                    <span>{step}</span>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 12, fontStyle: 'italic' }}>
              {investigationReport.analyst_disclaimer}
            </div>
          </div>
        ) : (
          <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: 0 }}>
            The AI Investigator takes structured evidence from the ML model and SHAP attribution layer to generate human-readable case briefs and triage next steps.
          </p>
        )}
      </div>

      <div style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'right', marginBottom: 12 }}>
        ML Model: {model_name} · Policy Threshold: {(threshold_used * 100).toFixed(1)}%
      </div>

      <Alert type="info">
        ⚠️ This is a prototype risk management system based on PaySim synthetic transaction data. It serves as an explainable decision-support tool and does not execute real-world financial balance transfers.
      </Alert>
    </div>
  )
}

export default function Analyze() {
  const [form, setForm] = useState(defaultForm)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleChange = (name, value) => {
    setForm(f => ({ ...f, [name]: value }))
  }

  const loadDemo = (demo) => {
    const { label, ...txn } = demo
    setForm({ ...defaultForm, ...txn })
    setResult(null)
    setError(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const payload = {
        step: parseInt(form.step) || 1,
        type: form.type,
        amount: parseFloat(form.amount),
        oldbalanceOrg: parseFloat(form.oldbalanceOrg) || 0,
        newbalanceOrig: parseFloat(form.newbalanceOrig) || 0,
        oldbalanceDest: parseFloat(form.oldbalanceDest) || 0,
        newbalanceDest: parseFloat(form.newbalanceDest) || 0,
        nameOrig: form.nameOrig,
        nameDest: form.nameDest,
      }
      const res = await api.predict(payload)
      setResult(res)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <PageHeader
        title="Analyze Transaction"
        subtitle="Submit a transaction for real-time fraud risk scoring, SHAP explainability, and AI investigation"
      />
      <div style={{ padding: '24px 32px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '420px 1fr', gap: 24, alignItems: 'start' }}>
          {/* Form */}
          <div>
            <div className="card" style={{ padding: '16px 20px', marginBottom: 16 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: 1 }}>
                Quick Load Demo Scenario
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {DEMO_TRANSACTIONS.map(demo => (
                  <button
                    key={demo.label}
                    className="btn btn-outline"
                    onClick={() => loadDemo(demo)}
                    style={{ justifyContent: 'flex-start', fontSize: 13 }}
                  >
                    <Zap size={13} />
                    {demo.label}
                  </button>
                ))}
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 10 }}>
                Synthetic PaySim test data · Clear benchmarks
              </div>
            </div>

            <div className="card" style={{ padding: '20px 24px' }}>
              <form onSubmit={handleSubmit}>
                <FormField label="Transaction Type" name="type" value={form.type} onChange={handleChange} />
                <FormField label="Amount (₹)" name="amount" value={form.amount} onChange={handleChange} help="Transaction amount in INR" />
                <FormField label="Time Step" name="step" value={form.step} onChange={handleChange} help="1-744 (1 step = 1 hour)" />
                <div style={{ borderTop: '1px solid var(--border)', margin: '16px 0', paddingTop: 16 }}>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>
                    Account Balance Inputs
                  </div>
                  <FormField label="Originator Balance (Before)" name="oldbalanceOrg" value={form.oldbalanceOrg} onChange={handleChange} />
                  <FormField label="Originator Balance (After)" name="newbalanceOrig" value={form.newbalanceOrig} onChange={handleChange} />
                  <FormField label="Destination Balance (Before)" name="oldbalanceDest" value={form.oldbalanceDest} onChange={handleChange} />
                  <FormField label="Destination Balance (After)" name="newbalanceDest" value={form.newbalanceDest} onChange={handleChange} />
                </div>
                {error && <Alert type="error" style={{ marginBottom: 12 }}>{error}</Alert>}
                <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
                  {loading ? (
                    <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div style={{
                        width: 14, height: 14, borderRadius: '50%',
                        border: '2px solid rgba(255,255,255,0.3)',
                        borderTopColor: 'white',
                        animation: 'spin 0.8s linear infinite',
                      }} />
                      Scoring Transaction...
                    </span>
                  ) : (
                    <><Send size={15} /> Evaluate Risk Score</>
                  )}
                </button>
              </form>
            </div>
          </div>

          {/* Result Card */}
          <div>
            {loading && <Spinner />}
            {!loading && !result && !error && (
              <div style={{
                display: 'flex', flexDirection: 'column', alignItems: 'center',
                justifyContent: 'center', height: 400, color: 'var(--text-muted)',
                textAlign: 'center',
              }}>
                <Shield size={48} style={{ marginBottom: 16, opacity: 0.3 }} />
                <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>
                  Awaiting Transaction Input
                </div>
                <div style={{ fontSize: 13, maxWidth: 320 }}>
                  Select a test scenario or enter custom financial transaction attributes, then click "Evaluate Risk Score"
                </div>
              </div>
            )}
            {!loading && error && (
              <Alert type="error">
                <strong>Error:</strong> {error}
                <br />
                <small>Ensure the FastAPI backend is running at http://localhost:8000</small>
              </Alert>
            )}
            {!loading && result && <ResultCard result={result} formState={form} />}
          </div>
        </div>
      </div>
    </div>
  )
}
