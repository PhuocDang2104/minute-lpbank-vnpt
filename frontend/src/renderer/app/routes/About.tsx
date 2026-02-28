import {
  ArrowRight,
  BarChart3,
  Brain,
  CheckCircle,
  Database,
  ExternalLink,
  FileText,
  Github,
  Info,
  Layers,
  Lightbulb,
  Mail,
  Map,
  BadgeDollarSign,
  Globe,
  MessageSquare,
  Mic,
  ShieldCheck,
  Sparkles,
  Target,
  Workflow,
  Zap,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import ContactEmailForm from '../../components/ui/contact-email-form'
import FloatingNavbar from '../../components/ui/floating-navbar'
import { useLanguage } from '../../contexts/LanguageContext'

const SECTION_NAV = [
  { id: 'overview', label: 'Overview' },
  { id: 'problem', label: 'Problem' },
  { id: 'solution', label: 'Solution' },
  { id: 'realtime', label: 'Realtime Graph' },
  { id: 'rag', label: 'LightRAG' },
  { id: 'pipelines', label: 'AI Pipelines' },
  { id: 'architecture', label: 'Architecture' },
  { id: 'websocket', label: 'WebSocket API' },
  { id: 'reliability', label: 'Latency & Ops' },
  { id: 'security', label: 'Security' },
  { id: 'roadmap', label: 'Roadmap' },
  { id: 'contact', label: 'Contact' },
]

const About = () => {
  const { language, setLanguage } = useLanguage()
  const isVi = language === 'vi'
  const lt = (vi: string, en: string) => (isVi ? vi : en)
  const [activeSection, setActiveSection] = useState(SECTION_NAV[0]?.id ?? 'overview')

  const scrollToSection = (sectionId: string) => {
    const section = document.getElementById(sectionId)
    if (!section) return
    section.scrollIntoView({ behavior: 'smooth', block: 'start' })
    setActiveSection(sectionId)
  }

  useEffect(() => {
    const targets = SECTION_NAV.map((item) => document.getElementById(item.id)).filter(
      (section): section is HTMLElement => Boolean(section),
    )

    if (targets.length === 0) return

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return
          setActiveSection(entry.target.id)
        })
      },
      { threshold: 0.25, rootMargin: '-20% 0px -60% 0px' },
    )

    targets.forEach((target) => observer.observe(target))

    return () => observer.disconnect()
  }, [])

  return (
    <div className="about-page public-page">
      <FloatingNavbar
        navItems={[
          { name: lt('Giới thiệu', 'About'), to: '/about', icon: <Info size={18} /> },
          { name: lt('Lộ trình', 'Roadmap'), to: '/roadmap', icon: <Map size={18} /> },
          { name: lt('Bảng giá', 'Pricing'), to: '/pricing', icon: <BadgeDollarSign size={18} /> },
          { name: lt('Liên hệ', 'Contact'), onClick: () => scrollToSection('contact'), icon: <Mail size={18} /> },
        ]}
        action={{ label: lt('Bắt đầu', 'Get started'), to: '/app/meetings', icon: <ArrowRight size={16} /> }}
      />
      <header className="landing-header">
        <div className="landing-header__brand">
          <Link to="/" className="logo" aria-label={lt('Trang chủ', 'Homepage')} title={lt('Trang chủ', 'Homepage')}>
            <img src="/minute_icon.svg" alt="Minute" className="landing-logo__icon" />
            <span>Minute</span>
          </Link>
          <nav className="landing-nav">
            <Link to="/about" className="landing-nav__link">{lt('Giới thiệu', 'About')}</Link>
            <Link to="/roadmap" className="landing-nav__link">{lt('Lộ trình', 'Roadmap')}</Link>
            <Link to="/pricing" className="landing-nav__link">{lt('Bảng giá', 'Pricing')}</Link>
            <button type="button" className="landing-nav__link" onClick={() => scrollToSection('contact')}>
              {lt('Liên hệ', 'Contact')}
            </button>
          </nav>
        </div>
        <div className="landing-actions">
          <div className="landing-lang-switch" role="group" aria-label={lt('Chọn ngôn ngữ', 'Select language')}>
            <button
              type="button"
              className={`landing-lang-switch__btn${language === 'vi' ? ' is-active' : ''}`}
              onClick={() => setLanguage('vi')}
            >
              <Globe size={12} />
              VI
            </button>
            <button
              type="button"
              className={`landing-lang-switch__btn${language === 'en' ? ' is-active' : ''}`}
              onClick={() => setLanguage('en')}
            >
              EN
            </button>
          </div>
          <Link to="/app/meetings" className="btn btn-primary landing-get-started">{lt('Bắt đầu', 'Get started')}</Link>
        </div>
      </header>

      <div className="about-container">
        <section className="about-hero" id="overview">
          <div className="about-hero__content">
            <div className="about-hero__badge">
              <Sparkles size={16} />
              Gemini Hackathon 3 | MINUTE Product Blueprint
            </div>
            <h1 className="about-hero__title">
              <span className="about-hero__logo">MINUTE</span>
            </h1>
            <p className="about-hero__tagline">
              Multimodal meeting and study companion powered by Gemini 3 API
            </p>
            <p className="about-hero__description">
              MINUTE is a web application that supports both live sessions and post-session workflows.
              It listens to streaming audio, understands visual context from slides or shared screens,
              and produces evidence-backed recap, Q&A, and summaries with explicit citations.
            </p>
            <div className="about-hero__actions">
              <button
                type="button"
                className="btn btn-primary btn-lg"
                onClick={() => scrollToSection('solution')}
              >
                Explore the solution
              </button>
              <Link to="/roadmap" className="btn btn-outline btn-lg">View roadmap</Link>
            </div>
            <div className="about-hero__metrics">
              <div className="about-metric">
                <span className="about-metric__label">Session lifecycle</span>
                <span className="about-metric__value">In-session + post-session</span>
              </div>
              <div className="about-metric">
                <span className="about-metric__label">Realtime recap cadence</span>
                <span className="about-metric__value">2-minute windows</span>
              </div>
              <div className="about-metric">
                <span className="about-metric__label">Tiered retrieval</span>
                <span className="about-metric__value">LightRAG Tier 0 to Tier 3</span>
              </div>
              <div className="about-metric">
                <span className="about-metric__label">Risk controls</span>
                <span className="about-metric__value">Human approval for risky tools</span>
              </div>
            </div>
          </div>
          <div className="about-hero__visual">
            <img
              src="/minute_ai.png"
              alt="MINUTE product preview"
              className="about-hero__image"
              loading="lazy"
            />
            <div className="about-hero__visual-note">
              Realtime timeline + grounded Q&A + post-session output generation.
            </div>
          </div>
        </section>

        <nav className="about-nav" aria-label="About page sections">
          {SECTION_NAV.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`about-nav__link${activeSection === item.id ? ' is-active' : ''}`}
              aria-current={activeSection === item.id ? 'true' : undefined}
              onClick={() => scrollToSection(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <section className="about-section about-section--no-border">
          <div className="about-section__header">
            <Sparkles size={24} />
            <h2>Core Product Differentiators</h2>
          </div>

          <div className="about-grid about-grid--4 about-grid--highlights">
            <div className="about-ai-card">
              <Workflow size={24} />
              <h4>Multimodal Companion</h4>
              <p>Understands both what is said and what is shown, aligned to timestamps.</p>
            </div>

            <div className="about-ai-card">
              <Zap size={24} />
              <h4>Realtime Timeline</h4>
              <p>Continuously publishes transcript, visual events, and recap windows during live sessions.</p>
            </div>

            <div className="about-ai-card">
              <Database size={24} />
              <h4>LightRAG Tiering</h4>
              <p>Starts from session memory, escalates to uploaded docs, then optional web search.</p>
            </div>

            <div className="about-ai-card">
              <ShieldCheck size={24} />
              <h4>Governed Tool Calling</h4>
              <p>Risky actions use propose-approve-execute with audit traces and policy checks.</p>
            </div>
          </div>
        </section>

        <section className="about-section" id="problem">
          <div className="about-section__header">
            <Target size={24} />
            <h2>Problem Statement</h2>
          </div>

          <div className="about-grid about-grid--2">
            <div className="about-card about-card--problem about-card--accent">
              <h3>Current Friction in Meetings and Study Sessions</h3>
              <ul>
                <li>Manual note-taking is slow, inconsistent, and hard to verify later.</li>
                <li>Important decisions and actions are often not tied to concrete evidence.</li>
                <li>Knowledge is fragmented across transcript, files, and external references.</li>
                <li>Session follow-up quality drops when outputs are not structured or versioned.</li>
                <li>Teams need stronger control over tool actions, access scope, and auditability.</li>
              </ul>
            </div>

            <div className="about-card about-card--solution about-card--accent">
              <h3>MINUTE Response</h3>
              <ul>
                <li>Automates recap, summary, and minutes-grade outputs with citations.</li>
                <li>Links claims to doc sections, pages, timestamps, or visual moments.</li>
                <li>Supports contextual Q&A scoped by session and access control.</li>
                <li>Generates post-session outputs for both meeting and study workflows.</li>
                <li>Uses policy checks and human approvals for high-risk external actions.</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="about-section about-section--features" id="solution">
          <div className="about-section__header">
            <Workflow size={24} />
            <h2>Functional Scope</h2>
          </div>

          <div className="about-grid about-grid--3">
            <div className="about-feature about-feature--in">
              <div className="about-feature__icon about-feature__icon--in">
                <Mic size={28} />
              </div>
              <h3>In-Session Realtime Assistant</h3>
              <p className="about-feature__summary">Live understanding and recap while the session is happening.</p>
              <ul>
                <li>Streaming ASR transcript with partial/final timestamped segments</li>
                <li>Frame sampling and visual event extraction from shared screen/video</li>
                <li>Recap timeline updates every 2 minutes</li>
                <li>In-session Q&A over current session memory and uploaded docs</li>
              </ul>
            </div>

            <div className="about-feature about-feature--post">
              <div className="about-feature__icon about-feature__icon--post">
                <CheckCircle size={28} />
              </div>
              <h3>Post-Session Summary & Outputs</h3>
              <p className="about-feature__summary">Consolidated outputs after live sessions or offline uploads.</p>
              <ul>
                <li>Core summary with key takeaways and structured notes</li>
                <li>Meeting branch: action items + related documents</li>
                <li>Study branch: concepts + examples + layered quiz flow</li>
                <li>Versioned artifacts ready for export workflows</li>
              </ul>
            </div>

            <div className="about-feature about-feature--pre">
              <div className="about-feature__icon about-feature__icon--pre">
                <FileText size={28} />
              </div>
              <h3>Personalization & Settings</h3>
              <p className="about-feature__summary">Configurable assistant behavior for different users and domains.</p>
              <ul>
                <li>Model profiles: Gemini default, plus optional alternatives</li>
                <li>Bring-your-own API key support</li>
                <li>Prompt customization: tone, goals, and personal context</li>
                <li>Session-type aware behavior for meeting and study modes</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="about-section" id="realtime">
          <div className="about-section__header">
            <Zap size={24} />
            <h2>Realtime Graph Overview</h2>
          </div>

          <div className="about-demo-list about-demo-list--modern">
            <div className="about-demo-item">
              <span className="about-demo-number">1</span>
              <div>
                <h4>Audio Lane</h4>
                <p>Audio ingest to ASR streaming to transcript buffer to transcript events.</p>
              </div>
            </div>

            <div className="about-demo-item">
              <span className="about-demo-number">2</span>
              <div>
                <h4>Video Lane</h4>
                <p>Video ingest to frame sampling to slide-change detection to visual events.</p>
              </div>
            </div>

            <div className="about-demo-item">
              <span className="about-demo-number">3</span>
              <div>
                <h4>Merge Lane</h4>
                <p>Event alignment to 2-minute context windows to recap generation to timeline update.</p>
              </div>
            </div>

            <div className="about-demo-item">
              <span className="about-demo-number">4</span>
              <div>
                <h4>In-Session Q&A Lane</h4>
                <p>User query to tiered retrieval to answer with citations to optional escalation.</p>
              </div>
            </div>
          </div>
        </section>

        <section className="about-section about-section--ai" id="rag">
          <div className="about-section__header">
            <MessageSquare size={24} />
            <h2>LightRAG Tiered Retrieval</h2>
          </div>

          <div className="about-grid about-grid--4 about-grid--ai">
            <div className="about-ai-card about-ai-card--tone">
              <Database size={24} />
              <h4>Tier 0</h4>
              <p>Session memory: recap windows, transcript, summary, and visual moments.</p>
            </div>

            <div className="about-ai-card about-ai-card--tone">
              <FileText size={24} />
              <h4>Tier 1</h4>
              <p>Uploaded documents with hybrid retrieval and ACL/session filters.</p>
            </div>

            <div className="about-ai-card about-ai-card--tone">
              <Workflow size={24} />
              <h4>Tier 2</h4>
              <p>Optional web search when evidence is insufficient and policy allows it.</p>
            </div>

            <div className="about-ai-card about-ai-card--tone">
              <Brain size={24} />
              <h4>Tier 3</h4>
              <p>Deep multi-hop research with explicit limitations and source reporting.</p>
            </div>
          </div>
          <p className="about-section__note">
            MINUTE follows a no-source-no-answer principle for critical claims.
          </p>
        </section>

        <section className="about-section" id="pipelines">
          <div className="about-section__header">
            <Brain size={24} />
            <h2>AI Task Router & Pipelines</h2>
          </div>

          <div className="about-grid about-grid--3">
            <div className="about-card about-card--accent">
              <h3><code>realtime_recap</code></h3>
              <ul>
                <li>Builds context windows from transcript and visual events.</li>
                <li>Generates timeline recap every 2 minutes.</li>
                <li>Extracts meeting decisions/actions or study concepts.</li>
              </ul>
            </div>

            <div className="about-card about-card--accent">
              <h3><code>qna</code></h3>
              <ul>
                <li>Runs tiered retrieval with reranking and context packing.</li>
                <li>Performs self-check and citation validation.</li>
                <li>Escalates to web tools only when needed and approved.</li>
              </ul>
            </div>

            <div className="about-card about-card--accent">
              <h3><code>summary_generate</code></h3>
              <ul>
                <li>Consolidates full transcript and recap timeline.</li>
                <li>Branches output by session type: meeting vs study.</li>
                <li>Persists versioned summaries and related artifacts.</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="about-section" id="architecture">
          <div className="about-section__header">
            <Layers size={24} />
            <h2>MVP Architecture & Tech Stack</h2>
          </div>

          <div className="about-architecture">
            <div className="about-arch-layer">
              <h4>Client Web</h4>
              <div className="about-tech-tags">
                <span className="about-tech-tag">React</span>
                <span className="about-tech-tag">TypeScript</span>
                <span className="about-tech-tag">Vite</span>
                <span className="about-tech-tag">Session Hub UI</span>
              </div>
            </div>

            <div className="about-arch-layer">
              <h4>Realtime Gateway</h4>
              <div className="about-tech-tags">
                <span className="about-tech-tag">WebSocket</span>
                <span className="about-tech-tag">Audio chunks</span>
                <span className="about-tech-tag">Frame metadata</span>
                <span className="about-tech-tag">Event streaming</span>
              </div>
            </div>

            <div className="about-arch-layer">
              <h4>AI Orchestration</h4>
              <div className="about-tech-tags">
                <span className="about-tech-tag about-tech-tag--ai">Gemini 3 API</span>
                <span className="about-tech-tag about-tech-tag--ai">Task Router</span>
                <span className="about-tech-tag about-tech-tag--ai">Reflective loop</span>
                <span className="about-tech-tag about-tech-tag--ai">Tool controller</span>
              </div>
            </div>

            <div className="about-arch-layer">
              <h4>Retrieval Layer</h4>
              <div className="about-tech-tags">
                <span className="about-tech-tag">Postgres</span>
                <span className="about-tech-tag">pgvector</span>
                <span className="about-tech-tag">BM25 hybrid</span>
                <span className="about-tech-tag">ACL filters</span>
              </div>
            </div>

            <div className="about-arch-layer">
              <h4>Artifacts & Audit</h4>
              <div className="about-tech-tags">
                <span className="about-tech-tag">Object storage</span>
                <span className="about-tech-tag">Summary versioning</span>
                <span className="about-tech-tag">Event store</span>
                <span className="about-tech-tag">Trace and audit logs</span>
              </div>
            </div>
          </div>

          <div className="about-media-grid">
            <figure className="about-media">
              <img
                src="/about/system-architecture-4-layers.png"
                alt="MINUTE system architecture layers"
                loading="lazy"
              />
              <figcaption>System architecture layers for MVP delivery.</figcaption>
            </figure>
            <figure className="about-media">
              <img
                src="/about/architecture.png"
                alt="MINUTE architecture diagram"
                loading="lazy"
              />
              <figcaption>Realtime and post-session service topology.</figcaption>
            </figure>
          </div>
        </section>

        <section className="about-section" id="websocket">
          <div className="about-section__header">
            <Workflow size={24} />
            <h2>Realtime WebSocket Contract</h2>
          </div>

          <div className="about-grid about-grid--2">
            <div className="about-card about-card--docs">
              <h3>Client to Server Events</h3>
              <ul>
                <li><code>audio_chunk</code>: sequence, payload, timestamp hint</li>
                <li><code>video_frame_meta</code>: frame id, time, ROI, checksum</li>
                <li><code>user_query</code>: query id, text, scope</li>
                <li><code>approve_tool_call</code>: proposal id, decision, constraints</li>
                <li><code>session_control</code>: start, pause, stop</li>
              </ul>
            </div>

            <div className="about-card about-card--docs">
              <h3>Server to Client Events</h3>
              <ul>
                <li><code>transcript_event</code>: partial/final segments with timestamps</li>
                <li><code>slide_change_event</code> and <code>visual_event</code></li>
                <li><code>recap_window</code>: recap text plus citations</li>
                <li><code>tool_call_proposal</code>: reason, risk, suggested queries</li>
                <li><code>qna_answer</code>: answer, citations, tier used</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="about-section about-section--kpi" id="reliability">
          <div className="about-section__header">
            <BarChart3 size={24} />
            <h2>Latency Targets & Observability</h2>
          </div>

          <div className="about-grid about-grid--4 about-grid--kpi">
            <div className="about-metric-card">
              <span className="about-metric-card__label">Transcript</span>
              <h4>1-2s Partial Updates</h4>
              <p>Target response window from speech to partial transcript.</p>
            </div>

            <div className="about-metric-card">
              <span className="about-metric-card__label">Recap</span>
              <h4>5-15s Post Window</h4>
              <p>Recap publication delay after each 2-minute window ends.</p>
            </div>

            <div className="about-metric-card">
              <span className="about-metric-card__label">Q&A</span>
              <h4>Tier 0/1 in 2-6s</h4>
              <p>Fast path with session memory and uploaded document grounding.</p>
            </div>

            <div className="about-metric-card">
              <span className="about-metric-card__label">Ops</span>
              <h4>Traceable Pipeline</h4>
              <p>Metrics on WS latency, ASR lag, recap lag, and tiered Q&A latency.</p>
            </div>
          </div>
        </section>

        <section className="about-section" id="security">
          <div className="about-section__header">
            <ShieldCheck size={24} />
            <h2>Security & Compliance Focus</h2>
          </div>

          <div className="about-grid about-grid--2">
            <div className="about-card about-card--security">
              <h3>MVP Demo Guardrails</h3>
              <ul>
                <li>Use synthetic or scrubbed datasets in public demo environments.</li>
                <li>Avoid uploading sensitive personal or regulated information.</li>
                <li>Maintain evidence-based responses with explicit citation trails.</li>
                <li>Log tool-call proposals and user approvals for traceability.</li>
              </ul>
            </div>

            <div className="about-card about-card--security">
              <h3>Production-Oriented Controls</h3>
              <ul>
                <li>TLS/mTLS, secrets vault, and strict role-based access policies.</li>
                <li>ACL enforcement at retrieval layer and scoped session access.</li>
                <li>PII masking/redaction before external API requests.</li>
                <li>Retention policies, export controls, and full audit trail support.</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="about-section about-section--roadmap" id="roadmap">
          <div className="about-section__header">
            <Lightbulb size={24} />
            <h2>Delivery Roadmap</h2>
          </div>

          <div className="about-roadmap about-roadmap--timeline">
            <article className="about-roadmap__item">
              <span className="about-roadmap__phase">Phase 1</span>
              <h3>Hackathon Core</h3>
              <ul className="about-roadmap__list">
                <li>Realtime transcript, recap windows, and timeline updates.</li>
                <li>Post-session summary generation with citations.</li>
              </ul>
            </article>

            <article className="about-roadmap__item">
              <span className="about-roadmap__phase">Phase 2</span>
              <h3>Tiered Q&A Expansion</h3>
              <ul className="about-roadmap__list">
                <li>Tier 2 web search with approval flow and corrective loop.</li>
                <li>Meeting/study branch outputs with stronger templates.</li>
              </ul>
            </article>

            <article className="about-roadmap__item">
              <span className="about-roadmap__phase">Phase 3</span>
              <h3>Production Hardening</h3>
              <ul className="about-roadmap__list">
                <li>Policy engine, retention control, and export workflows.</li>
                <li>Scalable observability and workspace-level governance.</li>
              </ul>
            </article>

            <article className="about-roadmap__item">
              <span className="about-roadmap__phase">Phase 4</span>
              <h3>Advanced Research Mode</h3>
              <ul className="about-roadmap__list">
                <li>Tier 3 deep research with multi-hop reasoning support.</li>
                <li>Richer educational outputs and adaptive learning guidance.</li>
              </ul>
            </article>
          </div>
        </section>
      </div>

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
              <Link to="/about" className="btn btn-outline btn-lg">Back to About</Link>
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

export default About

