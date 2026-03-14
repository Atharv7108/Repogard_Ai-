import React, { useEffect, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:5174'

export default function Pricing(){
  const [keyId, setKeyId] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // reflect whether user is currently signed in (simple localStorage check)
    const current = localStorage.getItem('rg_jwt')
    if (current) setLoading(false)

    const loadKey = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/razorpay-key`)
        const data = await res.json()
        if (res.ok && data.key_id) setKeyId(data.key_id)
        else setError(data.error || 'Razorpay key not available')
      } catch (err:any) {
        setError(String(err))
      }
    }
    loadKey()
  }, [])

  const loadScript = () => new Promise<boolean>((resolve) => {
    const existing = document.getElementById('razorpay-checkout')
    if (existing) return resolve(true)
    const script = document.createElement('script')
    script.id = 'razorpay-checkout'
    script.src = 'https://checkout.razorpay.com/v1/checkout.js'
    script.onload = () => resolve(true)
    script.onerror = () => resolve(false)
    document.body.appendChild(script)
  })

  const startCheckout = async () => {
    setError(null)
    setLoading(true)
    const jwt = localStorage.getItem('rg_jwt')
    if (!jwt) {
      setLoading(false)
      setError('Please sign in before upgrading to Pro.')
      window.location.href = '/login'
      return
    }
    const ok = await loadScript()
    if (!ok) {
      setLoading(false)
      setError('Failed to load Razorpay checkout')
      return
    }
    if (!keyId) {
      setLoading(false)
      setError('Razorpay key not available')
      return
    }
    try {
      const orderRes = await fetch(`${API_BASE}/api/razorpay-order`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plan: 'pro' })
      })
      const order = await orderRes.json()
      if (!orderRes.ok) throw new Error(order.error || 'Order creation failed')

      const STREAMLIT_BASE = import.meta.env.VITE_STREAMLIT_BASE || 'http://localhost:8516'
      const STREAMLIT_PRO_BASE = import.meta.env.VITE_STREAMLIT_PRO_BASE || STREAMLIT_BASE
      const rzp = new (window as any).Razorpay({
        key: keyId,
        amount: order.amount,
        currency: order.currency,
        name: 'RepoGuard AI',
        description: order.label,
        order_id: order.order_id,
        handler: async () => {
          // On successful payment, attempt to upgrade the account server-side.
          // We already ensured the user is signed in above, so a jwt should exist.
          try {
            const jwtNow = localStorage.getItem('rg_jwt')
            if (jwtNow) {
              const upgradeRes = await fetch(`${API_BASE}/api/upgrade-plan`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${jwtNow}` }
              })
              const upgrade = await upgradeRes.json()
              if (upgradeRes.ok && upgrade.token) {
                localStorage.setItem('rg_jwt', upgrade.token)
              }
            }
          } catch (_){}
          const finalJwt = localStorage.getItem('rg_jwt')
          try {
            const redirectUrl = new URL(STREAMLIT_PRO_BASE)
            // Ensure we always set the view and token via search params
            redirectUrl.searchParams.set('view', 'analysis')
            if (finalJwt) redirectUrl.searchParams.set('token', finalJwt)
            window.location.href = redirectUrl.toString()
          } catch (e) {
            // Fallback to the old string concat if URL isn't available
            const tokenParam = finalJwt ? `&token=${encodeURIComponent(finalJwt)}` : ''
            window.location.href = `${STREAMLIT_BASE.replace(/\/+$/,'')}/?view=analysis${tokenParam}`
          }
        },
        theme: { color: '#00c2a8' }
      })
      rzp.open()
    } catch (err:any) {
      setError(String(err))
    }
    setLoading(false)
  }

  return (
    <div className="pricing-shell">
      <header className="landing-header">
        <div className="landing-header-inner">
          <a className="landing-header-brand" href="/">RepoGuard</a>
          <div className="landing-header-nav">
            <a className="landing-header-link" href="/login">Login</a>
            <a className="landing-header-btn" href="/login">Try for Free</a>
          </div>
        </div>
      </header>

      <main className="pricing-hero">
        <div className="pricing-hero-inner">
          <div className="pricing-kicker">Pricing</div>
          <h1 className="pricing-title">Plans that scale with your engineering team</h1>
          <p className="pricing-sub">
            Start free and upgrade when you need deeper analysis history, higher limits, and priority AI runs.
          </p>
        </div>
      </main>

      <section className="pricing-grid">
        <article className="pricing-card">
          <div className="pricing-tag">Free</div>
          <div className="pricing-price">Rs 0 <span>/ month</span></div>
          <ul className="pricing-list">
            <li>Daily analysis limits</li>
            <li>Core health + risk metrics</li>
            <li>Basic charts and exports</li>
          </ul>
          <a className="pricing-cta" href="/login">Get Started</a>
        </article>

        <article className="pricing-card pricing-card--pro">
          <div className="pricing-tag">Pro</div>
          <div className="pricing-price">Rs 499 <span>/ month</span></div>
          <ul className="pricing-list">
            <li>Higher daily analysis limits</li>
            <li>Full AI insights + reports</li>
            <li>Priority processing</li>
          </ul>
          { !localStorage.getItem('rg_jwt') ? (
            <div>
              <a className="pricing-cta" href="/login">Sign in to upgrade</a>
            </div>
          ) : (
            <button className="pricing-cta pricing-cta--pay" onClick={startCheckout} disabled={loading || !keyId}>
              {loading ? 'Opening Razorpay...' : 'Upgrade to Pro'}
            </button>
          )}
          {!keyId && <div className="pricing-note">Razorpay not configured yet.</div>}
        </article>
      </section>

      {error && <div className="pricing-error">{error}</div>}
    </div>
  )
}
