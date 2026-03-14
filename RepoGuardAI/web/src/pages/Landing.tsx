import React from 'react'

export default function Landing(){
  return (
    <div>
      <header className="landing-header">
        <div className="landing-header-inner">
          <a className="landing-header-brand" href="/">RepoGuard</a>
          <div className="landing-header-nav">
            <a className="landing-header-link" href="/login">Login</a>
            <a className="landing-header-link" href="/pricing">Pricing</a>
            <a className="landing-header-btn" href="/login">Try for Free</a>
          </div>
        </div>
      </header>

      <main className="landing-wrap">
        <div className="landing-left">
          <div className="landing-kicker">Engineering Visibility</div>
          <h1 className="landing-title">Repository Intelligence, Designed for Fast Decisions</h1>
          <p className="hero-sub">
            Measure health, security, ownership risk, and debt in one polished analysis surface.
          </p>
          <a className="landing-cta" href="/login">Get Started</a>
        </div>
        <div className="landing-right">
          <div className="landing-image" />
        </div>
      </main>
    </div>
  )
}
