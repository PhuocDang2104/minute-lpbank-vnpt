import { ArrowRight, ExternalLink, Github, Info, Mail, Map } from 'lucide-react'
import { Link } from 'react-router-dom'
import ContactEmailForm from '../../components/ui/contact-email-form'
import FloatingNavbar from '../../components/ui/floating-navbar'

const Pricing = () => {
  const scrollToSection = (sectionId: string) => {
    const section = document.getElementById(sectionId)
    if (!section) return
    section.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <div className="pricing-page public-page">
      <FloatingNavbar
        navItems={[
          { name: 'About', to: '/about', icon: <Info size={18} /> },
          { name: 'Roadmap', to: '/roadmap', icon: <Map size={18} /> },
          { name: 'Contact', onClick: () => scrollToSection('contact'), icon: <Mail size={18} /> },
        ]}
        action={{ label: 'Get Started', to: '/app/meetings', icon: <ArrowRight size={16} /> }}
      />
      <header className="landing-header">
        <div className="landing-header__brand">
          <Link to="/" className="logo" aria-label="Homepage" title="Homepage">
            <img src="/minute_icon.svg" alt="Minute" className="landing-logo__icon" />
            <span>MINUTE</span>
          </Link>
          <nav className="landing-nav">
            <Link to="/about" className="landing-nav__link">About</Link>
            <Link to="/roadmap" className="landing-nav__link">Roadmap</Link>
            <button type="button" className="landing-nav__link" onClick={() => scrollToSection('contact')}>
              Contact
            </button>
          </nav>
        </div>
        <div className="landing-actions">
          <Link to="/app/meetings" className="btn btn-primary landing-get-started">Get Started</Link>
        </div>
      </header>

      <header className="pricing-hero">
        <h1 className="pricing-hero__title">Flexible Plans for Every Team</h1>
        <p className="pricing-hero__subtitle">
          Start quickly, then scale governance, integrations, and support as adoption grows.
        </p>
        <div className="pricing-hero__actions">
          <Link to="/app/meetings" className="btn btn-primary">
            Get Started
          </Link>
          <Link to="/about" className="btn btn-outline">
            About MINUTE
          </Link>
        </div>
      </header>

      <section className="pricing">
        <div className="pricing__header">
          <h2>Simple Pricing Structure</h2>
          <p>Choose the plan that matches your current workflow and scale up when needed.</p>
        </div>
        <div className="pricing-grid">
          <div className="pricing-card">
            <div className="pricing-tier">Pilot</div>
            <div className="pricing-price">Trial</div>
            <p className="pricing-desc">For small teams that want to validate workflow fit quickly.</p>
            <ul className="pricing-list">
              <li>Fast setup in 1-2 weeks</li>
              <li>Core in-session and post-session features</li>
              <li>Guided onboarding support</li>
            </ul>
            <Link to="/app/meetings" className="btn btn-outline pricing-cta">
              Get Started
            </Link>
          </div>
          <div className="pricing-card pricing-card--featured">
            <div className="pricing-tier">Business</div>
            <div className="pricing-price">By plan</div>
            <p className="pricing-desc">For departments and PMO teams operating at steady meeting volume.</p>
            <ul className="pricing-list">
              <li>Calendar and document repository integrations</li>
              <li>Workflow customization by session type</li>
              <li>Business-hours support SLA</li>
            </ul>
            <Link to="/app/meetings" className="btn btn-primary pricing-cta">
              Get Started
            </Link>
          </div>
          <div className="pricing-card">
            <div className="pricing-tier">Enterprise</div>
            <div className="pricing-price">Contact us</div>
            <p className="pricing-desc">For large-scale deployments with advanced security and governance requirements.</p>
            <ul className="pricing-list">
              <li>SSO, access control, and audit trails</li>
              <li>Customized RAG setup for internal knowledge</li>
              <li>24/7 support with dedicated delivery team</li>
            </ul>
            <Link to="/app/meetings" className="btn btn-outline pricing-cta">
              Get Started
            </Link>
          </div>
        </div>
      </section>

      <section className="contact" id="contact">
        <div className="contact-card">
          <div className="contact-content">
            <h2>Contact</h2>
            <p>Request a demo or discuss rollout options for your team.</p>
            <div className="contact-tags">
              <span className="contact-tag">Rapid onboarding</span>
              <span className="contact-tag">Security-focused rollout</span>
              <span className="contact-tag">Enterprise governance</span>
            </div>
          </div>
          <div className="contact-panel">
            <ContactEmailForm />
            <div className="contact-actions">
              <Link to="/app/meetings" className="btn btn-primary btn-lg">Get Started</Link>
              <Link to="/about" className="btn btn-outline btn-lg">About MINUTE</Link>
            </div>
          </div>
        </div>
      </section>

      <footer className="landing-footer">
        <div className="footer-brand">
          <img src="/minute_icon.svg" alt="Minute" className="landing-logo__icon landing-logo__icon--sm" />
          <span>MINUTE</span>
        </div>
        <a
          className="landing-footer__link"
          href="https://github.com/PhuocDang2104/minute_google_gemini_hackathon"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Github size={18} />
          GitHub
          <ExternalLink size={14} />
        </a>
        <p>(c) 2026 MINUTE | Gemini 3 Multimodal Meeting and Study Assistant</p>
      </footer>
    </div>
  )
}

export default Pricing

