import { ArrowRight, ExternalLink, Github, Info, Mail, Map, BadgeDollarSign, Globe } from 'lucide-react'
import { Link } from 'react-router-dom'
import ContactEmailForm from '../../components/ui/contact-email-form'
import FloatingNavbar from '../../components/ui/floating-navbar'
import { useLanguage } from '../../contexts/LanguageContext'

const Pricing = () => {
  const { language, setLanguage } = useLanguage()
  const isVi = language === 'vi'
  const lt = (vi: string, en: string) => (isVi ? vi : en)
  const scrollToSection = (sectionId: string) => {
    const section = document.getElementById(sectionId)
    if (!section) return
    section.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <div className="pricing-page public-page">
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

      <header className="pricing-hero">
        <h1 className="pricing-hero__title">{lt('Gói linh hoạt cho mọi đội ngũ', 'Flexible Plans for Every Team')}</h1>
        <p className="pricing-hero__subtitle">
          {lt('Khởi động nhanh, sau đó mở rộng quản trị, tích hợp và hỗ trợ theo đà tăng trưởng sử dụng.', 'Start quickly, then scale governance, integrations, and support as adoption grows.')}
        </p>
        <div className="pricing-hero__actions">
          <Link to="/app/meetings" className="btn btn-primary">
            {lt('Bắt đầu', 'Get Started')}
          </Link>
          <Link to="/about" className="btn btn-outline">
            {lt('Về MINUTE', 'About MINUTE')}
          </Link>
        </div>
      </header>

      <section className="pricing">
        <div className="pricing__header">
          <h2>{lt('Bảng giá theo quy mô triển khai', 'Simple Pricing Structure')}</h2>
          <p>{lt('Chọn gói phù hợp với nhu cầu hiện tại và nâng cấp khi cần.', 'Choose the plan that matches your current workflow and scale up when needed.')}</p>
        </div>
        <div className="pricing-grid">
          <div className="pricing-card">
            <div className="pricing-tier">Pilot</div>
            <div className="pricing-price">{lt('Dùng thử', 'Trial')}</div>
            <p className="pricing-desc">{lt('Dành cho nhóm nhỏ cần xác thực mức phù hợp workflow trong thời gian ngắn.', 'For small teams that want to validate workflow fit quickly.')}</p>
            <ul className="pricing-list">
              <li>{lt('Thiết lập nhanh trong 1-2 tuần', 'Fast setup in 1-2 weeks')}</li>
              <li>{lt('Tính năng lõi trong phiên và sau phiên', 'Core in-session and post-session features')}</li>
              <li>{lt('Hỗ trợ onboarding có hướng dẫn', 'Guided onboarding support')}</li>
            </ul>
            <Link to="/app/meetings" className="btn btn-outline pricing-cta">
              {lt('Bắt đầu', 'Get Started')}
            </Link>
          </div>
          <div className="pricing-card pricing-card--featured">
            <div className="pricing-tier">Business</div>
            <div className="pricing-price">{lt('Theo gói', 'By plan')}</div>
            <p className="pricing-desc">{lt('Dành cho phòng ban và PMO vận hành khối lượng họp ổn định.', 'For departments and PMO teams operating at steady meeting volume.')}</p>
            <ul className="pricing-list">
              <li>{lt('Tích hợp lịch và kho tài liệu', 'Calendar and document repository integrations')}</li>
              <li>{lt('Tùy biến workflow theo loại phiên', 'Workflow customization by session type')}</li>
              <li>{lt('SLA hỗ trợ giờ hành chính', 'Business-hours support SLA')}</li>
            </ul>
            <Link to="/app/meetings" className="btn btn-primary pricing-cta">
              {lt('Bắt đầu', 'Get Started')}
            </Link>
          </div>
          <div className="pricing-card">
            <div className="pricing-tier">Enterprise</div>
            <div className="pricing-price">{lt('Liên hệ', 'Contact us')}</div>
            <p className="pricing-desc">{lt('Dành cho triển khai quy mô lớn với yêu cầu bảo mật và quản trị nâng cao.', 'For large-scale deployments with advanced security and governance requirements.')}</p>
            <ul className="pricing-list">
              <li>{lt('SSO, kiểm soát truy cập và audit trails', 'SSO, access control, and audit trails')}</li>
              <li>{lt('Tùy chỉnh RAG cho tri thức nội bộ', 'Customized RAG setup for internal knowledge')}</li>
              <li>{lt('Hỗ trợ 24/7 với đội triển khai chuyên trách', '24/7 support with dedicated delivery team')}</li>
            </ul>
            <Link to="/app/meetings" className="btn btn-outline pricing-cta">
              {lt('Bắt đầu', 'Get Started')}
            </Link>
          </div>
        </div>
      </section>

      <section className="contact" id="contact">
        <div className="contact-card">
          <div className="contact-content">
            <h2>{lt('Liên hệ', 'Contact')}</h2>
            <p>{lt('Nhận demo hoặc trao đổi phương án triển khai phù hợp cho đội ngũ của bạn.', 'Request a demo or discuss rollout options for your team.')}</p>
            <div className="contact-tags">
              <span className="contact-tag">{lt('Onboarding nhanh', 'Rapid onboarding')}</span>
              <span className="contact-tag">{lt('Triển khai ưu tiên bảo mật', 'Security-focused rollout')}</span>
              <span className="contact-tag">{lt('Quản trị enterprise', 'Enterprise governance')}</span>
            </div>
          </div>
          <div className="contact-panel">
            <ContactEmailForm />
            <div className="contact-actions">
              <Link to="/app/meetings" className="btn btn-primary btn-lg">{lt('Bắt đầu', 'Get Started')}</Link>
              <Link to="/about" className="btn btn-outline btn-lg">{lt('Về MINUTE', 'About MINUTE')}</Link>
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
        <p>{lt('(c) 2026 MINUTE - Trợ lý AI cho cuộc họp doanh nghiệp', '(c) 2026 MINUTE - AI Meeting Assistant for Enterprise')}</p>
      </footer>
    </div>
  )
}

export default Pricing

