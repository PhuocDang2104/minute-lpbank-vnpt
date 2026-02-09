import { ArrowRight, ExternalLink, Github, Info, Mail, Map } from 'lucide-react'
import { Link } from 'react-router-dom'
import ContactEmailForm from '../../components/ui/contact-email-form'
import FloatingNavbar from '../../components/ui/floating-navbar'

const Roadmap = () => {
  const scrollToSection = (sectionId: string) => {
    const section = document.getElementById(sectionId)
    if (!section) return
    section.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <div className="roadmap-page public-page">
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

      <header className="roadmap-hero">
        <h1 className="roadmap-hero__title">Product Roadmap</h1>
        <p className="roadmap-hero__subtitle">
          A staged path from hackathon MVP to enterprise-grade reliability, governance, and ecosystem integrations.
        </p>
        <div className="roadmap-hero__actions">
          <Link to="/app/meetings" className="btn btn-primary">
            Get Started
          </Link>
          <Link to="/about" className="btn btn-outline">
            About MINUTE
          </Link>
        </div>
      </header>

      <section className="landing-roadmap" id="roadmap">
        <div className="landing-roadmap__header">
          <h2>MINUTE Roadmap</h2>
          <p>Four release waves to scale from core reliability to a complete product ecosystem.</p>
        </div>
        <div className="landing-roadmap__grid">
          <article className="landing-roadmap__column landing-roadmap__column--v1">
            <div className="landing-roadmap__kicker">Large BFSI Enterprises</div>
            <div className="landing-roadmap__card">
              <div className="landing-roadmap__card-top">
                <span className="landing-roadmap__pill">Ver 1</span>
                <h3>Minute 1.0</h3>
              </div>
              <ul className="landing-roadmap__list">
                <li><strong>Auto-capture and meeting orchestration:</strong> bot auto-join (Teams/GoMeet), Outlook sync, project tagging.</li>
                <li><strong>Transcript plus diarization:</strong> accurate speaker attribution and readable formatting.</li>
                <li><strong>BFSI-ready minutes:</strong> summary, decisions, actions (owner, due date), and top highlights.</li>
                <li><strong>Export and distribution:</strong> DOCX/PDF, permissioned links, and draft/final versions.</li>
                <li><strong>Apps and extension:</strong> smooth UX with fast workflow customization.</li>
                <li><strong>Deployment and security:</strong> VPC/on-prem options, baseline RBAC, encryption, and access logs.</li>
              </ul>
            </div>
          </article>
          <article className="landing-roadmap__column landing-roadmap__column--v2">
            <div className="landing-roadmap__kicker">Multi-Industry Enterprises</div>
            <div className="landing-roadmap__card">
              <div className="landing-roadmap__card-top">
                <span className="landing-roadmap__pill">Ver 2</span>
                <h3>Minute 2.0</h3>
              </div>
              <ul className="landing-roadmap__list">
                <li><strong>Admin platform:</strong> multi-workspace and branch control with role-based policies.</li>
                <li><strong>Approval workflow:</strong> drafter to reviewer to approver with tracked changes and versions.</li>
                <li><strong>Industry and role templates:</strong> libraries, taxonomy, and domain vocabulary.</li>
                <li><strong>Quality tuning and review:</strong> confidence scoring and action/decision validation.</li>
                <li><strong>Model modes and slide awareness:</strong> Fast/Strong modes with OCR and metric extraction.</li>
                <li><strong>Voice identity (opt-in):</strong> stronger speaker mapping with optional identity verification.</li>
              </ul>
            </div>
          </article>
          <article className="landing-roadmap__column landing-roadmap__column--v3">
            <div className="landing-roadmap__kicker">Packs (Enterprise + SME)</div>
            <div className="landing-roadmap__card">
              <div className="landing-roadmap__card-top">
                <span className="landing-roadmap__pill">Ver 3</span>
                <h3>Minute 3.0</h3>
              </div>
              <div className="landing-roadmap__packs">
                <div className="landing-roadmap__pack">
                  <div className="landing-roadmap__pack-title">Enterprise Pack</div>
                  <ul className="landing-roadmap__list">
                    <li><strong>Knowledge base and agentic RAG:</strong> project and industry grounding before and after sessions.</li>
                    <li><strong>Citation and traceability:</strong> source-backed minutes and answers with timestamps.</li>
                    <li><strong>Advanced eDiscovery:</strong> criteria search and export bundles for audits and investigations.</li>
                    <li><strong>Action governance:</strong> policy-based reminders, escalation, and blocker reporting.</li>
                    <li><strong>Cross-meeting insights:</strong> detect decision conflicts, duplicate tasks, and repeated topics.</li>
                  </ul>
                </div>
                <div className="landing-roadmap__pack landing-roadmap__pack--muted">
                  <div className="landing-roadmap__pack-title">SME Pack</div>
                  <ul className="landing-roadmap__list">
                    <li><strong>Self-serve and auto-share:</strong> launch quickly and deliver minutes to Slack or Teams.</li>
                    <li><strong>Essential task sync:</strong> one-click push to popular work tools.</li>
                    <li><strong>Cost controls and quotas:</strong> usage, storage, and retention by plan.</li>
                  </ul>
                </div>
              </div>
            </div>
          </article>
          <article className="landing-roadmap__column landing-roadmap__column--v4">
            <div className="landing-roadmap__kicker">Lite + Ecosystem</div>
            <div className="landing-roadmap__card">
              <div className="landing-roadmap__card-top">
                <span className="landing-roadmap__pill">Ver 4</span>
                <h3>Minute Ecosystem</h3>
              </div>
              <div className="landing-roadmap__split">
                <div className="landing-roadmap__pack">
                  <div className="landing-roadmap__pack-title">Lite</div>
                  <ul className="landing-roadmap__list">
                    <li><strong>Minimal core loop:</strong> meeting to summary to action items with stable performance.</li>
                    <li><strong>Search and share:</strong> find by meeting or minutes, then link or export.</li>
                    <li><strong>Mobile-friendly minutes:</strong> quick review and action checkoffs on the go.</li>
                  </ul>
                </div>
                <div className="landing-roadmap__pack landing-roadmap__pack--muted">
                  <div className="landing-roadmap__pack-title">Ecosystem</div>
                  <ul className="landing-roadmap__list">
                    <li><strong>Broad integrations:</strong> CRM, ticketing, DMS, collaboration chat, and calendars.</li>
                    <li><strong>Marketplace and partner extensions:</strong> industry-specific integrations with governed permission scopes.</li>
                    <li><strong>Multi-language and multi-region:</strong> expansion for global teams and enterprise operations.</li>
                    <li><strong>Workflow triggers:</strong> finalized minutes can create and update tickets or notifications automatically.</li>
                  </ul>
                </div>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section className="contact" id="contact">
        <div className="contact-card">
          <div className="contact-content">
            <h2>Contact</h2>
            <p>Request a demo or discuss collaboration for meeting and study intelligence workflows.</p>
            <div className="contact-tags">
              <span className="contact-tag">Realtime assistant</span>
              <span className="contact-tag">Tiered LightRAG</span>
              <span className="contact-tag">Evidence-backed outputs</span>
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

export default Roadmap

