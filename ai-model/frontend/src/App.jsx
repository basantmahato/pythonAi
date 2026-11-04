import React, { useState, useEffect } from 'react'
import {
  Home,
  Sparkles,
  TrendingUp,
  AlertCircle,
  RefreshCw,
  Calculator,
  Layers,
  ShieldCheck,
  DollarSign,
  KeyRound,
  Percent,
  Server
} from 'lucide-react'

const CORE_BACKEND_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const PRESETS = [
  { name: 'Studio Condo', area: 650, desc: 'Compact urban flat' },
  { name: 'Starter Home', area: 1200, desc: 'Cozy 2-3 bedrooms' },
  { name: 'Suburban House', area: 1850, desc: 'Standard family home' },
  { name: 'Executive Home', area: 2600, desc: 'Spacious 4+ beds' },
  { name: 'Luxury Villa', area: 3800, desc: 'High-end estate' },
]

export default function App() {
  const [area, setArea] = useState(1850)
  const [downPaymentPct, setDownPaymentPct] = useState(20)
  const [valuation, setValuation] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [systemHealth, setSystemHealth] = useState({
    core: 'checking',
    ml: 'checking',
  })
  const [activePreset, setActivePreset] = useState('Suburban House')

  // Check health of both backends
  const checkHealth = async () => {
    try {
      setSystemHealth({ core: 'checking', ml: 'checking' })
      const res = await fetch(`${CORE_BACKEND_URL}/health`, {
        signal: AbortSignal.timeout(3000),
      })
      if (!res.ok) throw new Error('Core Backend returned error')
      const data = await res.json()
      setSystemHealth({
        core: 'connected',
        ml: data.ml_service_connected ? 'connected' : 'disconnected',
      })
    } catch (err) {
      setSystemHealth({
        core: 'disconnected',
        ml: 'unknown',
      })
    }
  }

  useEffect(() => {
    checkHealth()
    fetchValuation(1850, 20)
  }, [])

  const fetchValuation = async (inputArea, downPct = downPaymentPct) => {
    const areaVal = Number(inputArea)
    if (!areaVal || areaVal <= 0) {
      setError('Please enter a valid property area greater than 0 sq ft.')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const res = await fetch(`${CORE_BACKEND_URL}/api/v1/properties/valuation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          area: areaVal,
          down_payment_percent: Number(downPct),
          interest_rate_percent: 6.5,
        }),
      })

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}))
        throw new Error(errorData.detail || `Server error (${res.status})`)
      }

      const data = await res.json()
      setValuation(data)
      setSystemHealth({ core: 'connected', ml: 'connected' })
    } catch (err) {
      setError(
        err.message.includes('Failed to fetch')
          ? 'Cannot connect to Core Backend on port 8000. Please start the backend services.'
          : err.message
      )
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    fetchValuation(area, downPaymentPct)
  }

  const handlePresetSelect = (preset) => {
    setActivePreset(preset.name)
    setArea(preset.area)
    fetchValuation(preset.area, downPaymentPct)
  }

  const handleAreaChange = (val) => {
    const num = Math.max(0, Number(val))
    setArea(num)
    setActivePreset(null)
  }

  return (
    <div className="app-wrapper">
      {/* Top Navigation Bar with Dual Backend Status */}
      <nav className="navbar">
        <div className="navbar-container">
          <div className="logo-group">
            <div className="logo-icon">
              <Home size={22} />
            </div>
            <div>
              <div className="logo-title">HousePrice AI Architecture</div>
              <div className="logo-subtitle">2-Tier Microservices + Authenticated API Key</div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
            {/* Core Backend Status */}
            <span
              className={`badge ${
                systemHealth.core === 'connected' ? 'badge-success' : 'badge-danger'
              }`}
              title="Port 8000: Handles business logic and calls ML Service"
            >
              <Server size={12} />
              Core Backend: {systemHealth.core === 'connected' ? 'Online (8000)' : 'Offline'}
            </span>

            {/* ML Inference Microservice Status */}
            <span
              className={`badge ${
                systemHealth.ml === 'connected' ? 'badge-success' : 'badge-danger'
              }`}
              title="Port 8001: Protected by X-API-Key"
            >
              <KeyRound size={12} />
              ML Service: {systemHealth.ml === 'connected' ? 'Key Verified (8001)' : 'Offline'}
            </span>

            <button
              onClick={checkHealth}
              title="Refresh Service Status"
              style={{
                background: 'none',
                border: '1px solid var(--border)',
                padding: '0.4rem',
                borderRadius: '8px',
                cursor: 'pointer',
                color: 'var(--text-muted)',
              }}
            >
              <RefreshCw size={14} />
            </button>
          </div>
        </div>
      </nav>

      {/* Main Container */}
      <main className="main-content">
        <section className="hero-banner">
          <span className="hero-tag">Dual Backend Microservices • Enterprise AI Architecture</span>
          <h1 className="hero-title">Predict Real Estate Prices & Financials</h1>
          <p className="hero-description">
            React connects to <strong>Core Business Backend (Port 8000)</strong>, which authenticates via private <strong>X-API-Key</strong> with the dedicated <strong>ML Inference Service (Port 8001)</strong>.
          </p>
        </section>

        {error && (
          <div className="alert alert-danger">
            <AlertCircle size={18} style={{ flexShrink: 0 }} />
            <div>{error}</div>
          </div>
        )}

        <div className="grid-layout">
          {/* Left Column: Form & Presets */}
          <div className="card">
            <div className="card-title">
              <Calculator size={20} color="var(--primary)" />
              Property & Financing Inputs
            </div>
            <div className="card-subtitle">
              Adjust living area and mortgage parameters to evaluate properties.
            </div>

            <form onSubmit={handleSubmit}>
              {/* Area Input */}
              <div className="form-group">
                <div className="label-row">
                  <label className="form-label">Total Living Area</label>
                  <span className="area-counter mono">{Number(area).toLocaleString()} sq ft</span>
                </div>

                <div className="input-container">
                  <span className="input-icon">
                    <Layers size={18} />
                  </span>
                  <input
                    type="number"
                    min="100"
                    max="20000"
                    step="50"
                    value={area}
                    onChange={(e) => handleAreaChange(e.target.value)}
                    className="form-input mono"
                    placeholder="Enter area in sq ft..."
                  />
                </div>

                <input
                  type="range"
                  min="400"
                  max="5000"
                  step="50"
                  value={area || 400}
                  onChange={(e) => handleAreaChange(e.target.value)}
                  className="range-slider"
                />
              </div>

              {/* Down Payment Slider */}
              <div className="form-group" style={{ marginTop: '1.25rem' }}>
                <div className="label-row">
                  <label className="form-label">Down Payment (%)</label>
                  <span className="mono" style={{ fontSize: '0.88rem', fontWeight: 700, color: '#047857' }}>
                    {downPaymentPct}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="50"
                  step="5"
                  value={downPaymentPct}
                  onChange={(e) => {
                    const val = Number(e.target.value)
                    setDownPaymentPct(val)
                    if (valuation) fetchValuation(area, val)
                  }}
                  className="range-slider"
                />
              </div>

              {/* Presets */}
              <div className="preset-title">Quick Property Profiles</div>
              <div className="preset-grid">
                {PRESETS.map((preset) => (
                  <button
                    key={preset.name}
                    type="button"
                    className={`preset-btn ${activePreset === preset.name ? 'active' : ''}`}
                    onClick={() => handlePresetSelect(preset)}
                  >
                    <span className="preset-name">{preset.name}</span>
                    <span className="preset-size">{preset.area.toLocaleString()} sq ft • {preset.desc}</span>
                  </button>
                ))}
              </div>

              <button type="submit" className="submit-btn" disabled={loading}>
                {loading ? (
                  <>
                    <div className="spinner"></div> Running Microservices Pipeline...
                  </>
                ) : (
                  <>
                    <Sparkles size={18} /> Request Valuation & Analysis
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Right Column: Prediction Results & Financial Breakdown */}
          <div className="card result-card">
            <div className="card-title">
              <TrendingUp size={20} color="var(--primary)" />
              Market Valuation & Financial Analysis
            </div>
            <div className="card-subtitle">
              Calculated via authenticated ML model + Core Business Logic.
            </div>

            {valuation ? (
              <div>
                {/* Main Price Box */}
                <div className="price-display-box">
                  <div className="price-label">Estimated Market Valuation</div>
                  <div className="price-value mono">{valuation.formatted_price}</div>
                  <div style={{ display: 'flex', justifyContent: 'center', gap: '0.75rem', marginTop: '0.4rem' }}>
                    <span className="badge" style={{ background: '#eff6ff', color: '#1d4ed8' }}>
                      Tier: {valuation.market_tier}
                    </span>
                    <span className="badge" style={{ background: '#ecfdf5', color: '#065f46' }}>
                      Investment Score: {valuation.investment_score} / 10
                    </span>
                  </div>
                </div>

                {/* Financial Breakdown Table */}
                <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-main)', marginBottom: '0.5rem' }}>
                  Core Business Financial Breakdown (30-Yr Fixed @ 6.5%):
                </div>
                <table className="details-table">
                  <tbody>
                    <tr>
                      <td>Down Payment ({downPaymentPct}%)</td>
                      <td className="mono">${valuation.financials.down_payment.toLocaleString()}</td>
                    </tr>
                    <tr>
                      <td>Loan Principal Amount</td>
                      <td className="mono">${valuation.financials.loan_amount.toLocaleString()}</td>
                    </tr>
                    <tr>
                      <td>Monthly Mortgage (P&I)</td>
                      <td className="mono">${valuation.financials.monthly_mortgage_principal_interest.toLocaleString()}/mo</td>
                    </tr>
                    <tr>
                      <td>Estimated Monthly Property Tax</td>
                      <td className="mono">${valuation.financials.monthly_property_tax.toLocaleString()}/mo</td>
                    </tr>
                    <tr>
                      <td>Homeowners Insurance (est.)</td>
                      <td className="mono">${valuation.financials.monthly_insurance.toLocaleString()}/mo</td>
                    </tr>
                    <tr style={{ background: '#f8fafc', fontWeight: 700 }}>
                      <td style={{ color: 'var(--text-main)', fontWeight: 700 }}>Total Estimated Monthly</td>
                      <td className="mono" style={{ color: 'var(--primary)', fontWeight: 800 }}>
                        ${valuation.financials.total_estimated_monthly.toLocaleString()}/mo
                      </td>
                    </tr>
                  </tbody>
                </table>

                {/* Microservice Security Badge */}
                <div
                  style={{
                    background: '#f8fafc',
                    border: '1px solid var(--border)',
                    borderRadius: '8px',
                    padding: '0.75rem',
                    fontSize: '0.78rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.6rem',
                    color: '#334155',
                    marginTop: '0.75rem',
                  }}
                >
                  <ShieldCheck size={18} color="#059669" style={{ flexShrink: 0 }} />
                  <div>
                    <strong>Secure Backend-to-Backend Link:</strong> ML Service responded via <code>X-API-Key</code> on port 8001. Model: <code>Price = ({valuation.model_metadata.slope_per_sqft} × Area) + ${valuation.model_metadata.intercept}</code>
                  </div>
                </div>
              </div>
            ) : (
              <div style={{ padding: '3rem 1rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                <RefreshCw size={36} style={{ opacity: 0.3, marginBottom: '0.75rem' }} />
                <p>Submit property area to initiate microservice pipeline.</p>
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="footer">
        House Price Prediction Architecture • Core Business Backend (8000) ──[X-API-Key]──&gt; ML Inference Service (8001) ──&gt; React UI
      </footer>
    </div>
  )
}
