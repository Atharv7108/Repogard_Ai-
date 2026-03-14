import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
// We'll use the backend API instead of localStorage for auth
// Default to the local Node auth server started by `npm run api`.
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:5174';

export default function Login(){
  const [tab, setTab] = useState<'login'|'register'>('login')
  const [email, setEmail] = useState('')
  const [pw, setPw] = useState('')
  const [pw2, setPw2] = useState('')
  const [msg, setMsg] = useState<string | null>(null)
  const nav = useNavigate()
  // Keep login/register flow pinned to the free app.
  const STREAMLIT_LOGIN_BASE = import.meta.env.VITE_STREAMLIT_LOGIN_BASE || 'http://localhost:8516'

  const redirectToFreeAnalysis = (token: string) => {
    try {
      const u = new URL(STREAMLIT_LOGIN_BASE)
      u.searchParams.set('token', token)
      u.searchParams.set('view', 'analysis')
      window.location.href = u.toString()
    } catch (_) {
      window.location.href = `${STREAMLIT_LOGIN_BASE.replace(/\/+$/,'')}/?token=${encodeURIComponent(token)}&view=analysis`
    }
  }

  const handleRegister = async(e:any)=>{
    e.preventDefault()
    setMsg(null)
    const em = email.trim().toLowerCase()
    if(!em || !em.includes('@')){ setMsg('Invalid email'); return }
    if(pw.length < 6){ setMsg('Password must be at least 6 chars'); return }
    if(pw !== pw2){ setMsg('Passwords do not match'); return }
    try{
      const res = await fetch(`${API_BASE}/api/register`, {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ email: em, password: pw })
      })
      let data: any = {}
      try {
        data = await res.json()
      } catch (e) {
        const txt = await res.text().catch(() => '')
        data = txt ? { error: txt } : {}
      }
      if(!res.ok){ setMsg(data.error || 'Registration failed'); return }
      if (data.token) localStorage.setItem('rg_jwt', data.token)
      setMsg('Account created — signed in')
      // Request a short-lived Streamlit token and open Streamlit analysis.
      // If that fails, fall back to opening Streamlit with the primary JWT.
      try {
        const stRes = await fetch(`${API_BASE}/api/streamlit-token`, { method: 'POST', headers: { 'Authorization': `Bearer ${data.token}`, 'Content-Type':'application/json' }, body: JSON.stringify({}) })
        let stData:any = {}
        try { stData = await stRes.json() } catch(_) { stData = {} }
        if (stRes.ok && stData.token) {
          redirectToFreeAnalysis(stData.token)
          return
        }
        // fallback: open Streamlit with the original JWT if short-lived token not available
        redirectToFreeAnalysis(data.token)
        return
      } catch(err:any){
        // if anything goes wrong, navigate to the React analysis page as an ultimate fallback
        setMsg('Token redirect failed, opening in-app analysis')
        setTimeout(()=>nav('/analysis'),600)
      }
    }catch(err:any){ setMsg(String(err)) }
  }

  const handleLogin = async(e:any)=>{
    e.preventDefault()
    setMsg(null)
    const em = email.trim().toLowerCase()
    try{
      const res = await fetch(`${API_BASE}/api/login`, {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ email: em, password: pw })
      })
      let data: any = {}
      try {
        data = await res.json()
      } catch (e) {
        const txt = await res.text().catch(() => '')
        data = txt ? { error: txt } : {}
      }
      if(!res.ok){ setMsg(data.error || 'Login failed'); return }
      if (data.token) localStorage.setItem('rg_jwt', data.token)
      setMsg('Welcome back')
      // Try to get Streamlit token and open Streamlit analysis; fallback to primary JWT
      try {
        const stRes = await fetch(`${API_BASE}/api/streamlit-token`, { method: 'POST', headers: { 'Authorization': `Bearer ${data.token}`, 'Content-Type':'application/json' }, body: JSON.stringify({}) })
        let stData:any = {}
        try { stData = await stRes.json() } catch(_) { stData = {} }
        if (stRes.ok && stData.token) {
          redirectToFreeAnalysis(stData.token)
          return
        }
        redirectToFreeAnalysis(data.token)
        return
      } catch(err:any){
        setMsg('Token redirect failed, opening in-app analysis')
        setTimeout(()=>nav('/analysis'),400)
      }
    }catch(err:any){ setMsg(String(err)) }
  }

  return (
    <div className="page-login">
      <header className="landing-header">
        <div className="landing-header-inner">
          <a className="landing-header-brand" href="/">RepoGuard</a>
          <div className="landing-header-nav">
            <a className="landing-header-link" href="/pricing">Pricing</a>
          </div>
        </div>
      </header>

      <main className="login-shell">
        <div className="login-hero">
          <h1>Welcome back to RepoGuard</h1>
          <p className="hero-sub">Log in to run analyses, view history, and download reports.</p>
        </div>

        <div className="login-panel">
          <div className="login-card">
          <div className="tabs">
            <button className={tab==='login'? 'active':''} onClick={()=>{setTab('login'); setMsg(null)}}>Log In</button>
            <button className={tab==='register'? 'active':''} onClick={()=>{setTab('register'); setMsg(null)}}>Register</button>
          </div>

          {msg && <div className="form-msg">{msg}</div>}

          {tab==='login' ? (
            <form onSubmit={handleLogin}>
              <label>Email</label>
              <input value={email} onChange={e=>setEmail(e.target.value)} placeholder="you@example.com" />
              <label>Password</label>
              <input type="password" value={pw} onChange={e=>setPw(e.target.value)} />
              <button className="primary" type="submit">Log In</button>
            </form>
          ) : (
            <form onSubmit={handleRegister}>
              <label>Email</label>
              <input value={email} onChange={e=>setEmail(e.target.value)} placeholder="you@example.com" />
              <label>Password</label>
              <input type="password" value={pw} onChange={e=>setPw(e.target.value)} />
              <label>Confirm Password</label>
              <input type="password" value={pw2} onChange={e=>setPw2(e.target.value)} />
              <button className="primary" type="submit">Create Account</button>
            </form>
          )}
          </div>
          <div className="login-aside">
            <div className="aside-title">Why RepoGuard</div>
            <ul>
              <li>Fast AI summaries for every repo</li>
              <li>Security, debt, and bus factor in one view</li>
              <li>Export-ready reporting in minutes</li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  )
}
