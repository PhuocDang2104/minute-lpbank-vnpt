import { ArrowRight, ExternalLink, Github, Info, Mail, Map, BadgeDollarSign, Globe } from 'lucide-react'
import { Link } from 'react-router-dom'
import ContactEmailForm from '../../components/ui/contact-email-form'
import FloatingNavbar from '../../components/ui/floating-navbar'
import { useLanguage } from '../../contexts/LanguageContext'

const Roadmap = () => {
  const { language, setLanguage } = useLanguage()
  const isVi = language === 'vi'
  const lt = (vi: string, en: string) => (isVi ? vi : en)
  const scrollToSection = (sectionId: string) => {
    const section = document.getElementById(sectionId)
    if (!section) return
    section.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <div className="roadmap-page public-page">
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

      <section className="landing-roadmap" id="roadmap">
        <div className="landing-roadmap__header">
          <h2>{lt('Lộ trình MINUTE', 'MINUTE Roadmap')}</h2>
          <p>{lt('Bốn đợt phát hành để mở rộng từ năng lực cốt lõi đến hệ sinh thái sản phẩm hoàn chỉnh.', 'Four release waves to scale from core reliability to a complete product ecosystem.')}</p>
        </div>
        <div className="landing-roadmap__grid">
          <article className="landing-roadmap__column landing-roadmap__column--v1">
            <div className="landing-roadmap__kicker">{lt('Doanh nghiệp BFSI quy mô lớn', 'Large BFSI Enterprises')}</div>
            <div className="landing-roadmap__card">
              <div className="landing-roadmap__card-top">
                <span className="landing-roadmap__pill">{lt('Bản 1', 'Ver 1')}</span>
                <h3>Minute 1.0</h3>
              </div>
              <ul className="landing-roadmap__list">
                <li><strong>{lt('Tự động thu nhận và điều phối họp:', 'Auto-capture and meeting orchestration:')}</strong> {lt('bot tự tham gia (Teams/GoMeet), đồng bộ Outlook, gắn thẻ dự án.', 'bot auto-join (Teams/GoMeet), Outlook sync, project tagging.')}</li>
                <li><strong>{lt('Transcript kèm phân tách người nói:', 'Transcript plus diarization:')}</strong> {lt('gán speaker chính xác và định dạng dễ đọc.', 'accurate speaker attribution and readable formatting.')}</li>
                <li><strong>{lt('Biên bản sẵn sàng cho BFSI:', 'BFSI-ready minutes:')}</strong> {lt('summary, quyết định, action (owner, hạn), và highlights chính.', 'summary, decisions, actions (owner, due date), and top highlights.')}</li>
                <li><strong>{lt('Xuất bản và phân phối:', 'Export and distribution:')}</strong> {lt('DOCX/PDF, link theo quyền, bản nháp và bản chốt.', 'DOCX/PDF, permissioned links, and draft/final versions.')}</li>
                <li><strong>{lt('Ứng dụng và mở rộng:', 'Apps and extension:')}</strong> {lt('trải nghiệm mượt, tùy biến workflow nhanh.', 'smooth UX with fast workflow customization.')}</li>
                <li><strong>{lt('Triển khai và bảo mật:', 'Deployment and security:')}</strong> {lt('tùy chọn VPC/on-prem, RBAC nền tảng, mã hóa và log truy cập.', 'VPC/on-prem options, baseline RBAC, encryption, and access logs.')}</li>
              </ul>
            </div>
          </article>
          <article className="landing-roadmap__column landing-roadmap__column--v2">
            <div className="landing-roadmap__kicker">{lt('Doanh nghiệp đa ngành', 'Multi-Industry Enterprises')}</div>
            <div className="landing-roadmap__card">
              <div className="landing-roadmap__card-top">
                <span className="landing-roadmap__pill">{lt('Bản 2', 'Ver 2')}</span>
                <h3>Minute 2.0</h3>
              </div>
              <ul className="landing-roadmap__list">
                <li><strong>{lt('Nền tảng quản trị:', 'Admin platform:')}</strong> {lt('đa workspace, đa chi nhánh, chính sách theo vai trò.', 'multi-workspace and branch control with role-based policies.')}</li>
                <li><strong>{lt('Quy trình phê duyệt:', 'Approval workflow:')}</strong> {lt('soạn thảo -> rà soát -> phê duyệt, theo dõi thay đổi và phiên bản.', 'drafter to reviewer to approver with tracked changes and versions.')}</li>
                <li><strong>{lt('Template theo ngành và vai trò:', 'Industry and role templates:')}</strong> {lt('thư viện mẫu, taxonomy và từ vựng miền nghiệp vụ.', 'libraries, taxonomy, and domain vocabulary.')}</li>
                <li><strong>{lt('Tinh chỉnh chất lượng và review:', 'Quality tuning and review:')}</strong> {lt('confidence scoring và kiểm định action/decision.', 'confidence scoring and action/decision validation.')}</li>
                <li><strong>{lt('Chế độ model và hiểu slide:', 'Model modes and slide awareness:')}</strong> {lt('Fast/Strong kèm OCR và trích xuất chỉ số.', 'Fast/Strong modes with OCR and metric extraction.')}</li>
                <li><strong>{lt('Định danh giọng nói (tùy chọn):', 'Voice identity (opt-in):')}</strong> {lt('mapping speaker mạnh hơn với xác minh danh tính tùy chọn.', 'stronger speaker mapping with optional identity verification.')}</li>
              </ul>
            </div>
          </article>
          <article className="landing-roadmap__column landing-roadmap__column--v3">
            <div className="landing-roadmap__kicker">{lt('Gói (Enterprise + SME)', 'Packs (Enterprise + SME)')}</div>
            <div className="landing-roadmap__card">
              <div className="landing-roadmap__card-top">
                <span className="landing-roadmap__pill">{lt('Bản 3', 'Ver 3')}</span>
                <h3>Minute 3.0</h3>
              </div>
              <div className="landing-roadmap__packs">
                <div className="landing-roadmap__pack">
                  <div className="landing-roadmap__pack-title">{lt('Gói Enterprise', 'Enterprise Pack')}</div>
                  <ul className="landing-roadmap__list">
                    <li><strong>{lt('Knowledge base và Agentic RAG:', 'Knowledge base and agentic RAG:')}</strong> {lt('grounding theo dự án/ngành trước và sau phiên.', 'project and industry grounding before and after sessions.')}</li>
                    <li><strong>{lt('Trích dẫn và truy vết:', 'Citation and traceability:')}</strong> {lt('biên bản và câu trả lời có nguồn chứng cứ kèm timestamp.', 'source-backed minutes and answers with timestamps.')}</li>
                    <li><strong>{lt('eDiscovery nâng cao:', 'Advanced eDiscovery:')}</strong> {lt('tìm theo tiêu chí và export bundle cho audit/điều tra.', 'criteria search and export bundles for audits and investigations.')}</li>
                    <li><strong>{lt('Quản trị hành động:', 'Action governance:')}</strong> {lt('nhắc việc theo chính sách, escalation và báo blocker.', 'policy-based reminders, escalation, and blocker reporting.')}</li>
                    <li><strong>{lt('Insight liên cuộc họp:', 'Cross-meeting insights:')}</strong> {lt('phát hiện xung đột quyết định, task trùng lặp và chủ đề lặp lại.', 'detect decision conflicts, duplicate tasks, and repeated topics.')}</li>
                  </ul>
                </div>
                <div className="landing-roadmap__pack landing-roadmap__pack--muted">
                  <div className="landing-roadmap__pack-title">{lt('Gói SME', 'SME Pack')}</div>
                  <ul className="landing-roadmap__list">
                    <li><strong>{lt('Tự triển khai và tự chia sẻ:', 'Self-serve and auto-share:')}</strong> {lt('khởi chạy nhanh và gửi biên bản lên Slack hoặc Teams.', 'launch quickly and deliver minutes to Slack or Teams.')}</li>
                    <li><strong>{lt('Đồng bộ tác vụ thiết yếu:', 'Essential task sync:')}</strong> {lt('đẩy một chạm sang các công cụ làm việc phổ biến.', 'one-click push to popular work tools.')}</li>
                    <li><strong>{lt('Kiểm soát chi phí và hạn mức:', 'Cost controls and quotas:')}</strong> {lt('quản trị usage, dung lượng và retention theo gói.', 'usage, storage, and retention by plan.')}</li>
                  </ul>
                </div>
              </div>
            </div>
          </article>
          <article className="landing-roadmap__column landing-roadmap__column--v4">
            <div className="landing-roadmap__kicker">{lt('Lite + Hệ sinh thái', 'Lite + Ecosystem')}</div>
            <div className="landing-roadmap__card">
              <div className="landing-roadmap__card-top">
                <span className="landing-roadmap__pill">{lt('Bản 4', 'Ver 4')}</span>
                <h3>{lt('Hệ sinh thái Minute', 'Minute Ecosystem')}</h3>
              </div>
              <div className="landing-roadmap__split">
                <div className="landing-roadmap__pack">
                  <div className="landing-roadmap__pack-title">Lite</div>
                  <ul className="landing-roadmap__list">
                    <li><strong>{lt('Vòng lõi tinh gọn:', 'Minimal core loop:')}</strong> {lt('họp -> summary -> action items với hiệu năng ổn định.', 'meeting to summary to action items with stable performance.')}</li>
                    <li><strong>{lt('Tìm kiếm và chia sẻ:', 'Search and share:')}</strong> {lt('tìm theo cuộc họp hoặc biên bản rồi chia sẻ link/xuất file.', 'find by meeting or minutes, then link or export.')}</li>
                    <li><strong>{lt('Biên bản thân thiện di động:', 'Mobile-friendly minutes:')}</strong> {lt('xem nhanh và xác nhận action khi di chuyển.', 'quick review and action checkoffs on the go.')}</li>
                  </ul>
                </div>
                <div className="landing-roadmap__pack landing-roadmap__pack--muted">
                  <div className="landing-roadmap__pack-title">{lt('Hệ sinh thái', 'Ecosystem')}</div>
                  <ul className="landing-roadmap__list">
                    <li><strong>{lt('Tích hợp diện rộng:', 'Broad integrations:')}</strong> {lt('CRM, ticketing, DMS, chat cộng tác và lịch.', 'CRM, ticketing, DMS, collaboration chat, and calendars.')}</li>
                    <li><strong>{lt('Marketplace và mở rộng đối tác:', 'Marketplace and partner extensions:')}</strong> {lt('tích hợp theo ngành với phạm vi quyền được kiểm soát.', 'industry-specific integrations with governed permission scopes.')}</li>
                    <li><strong>{lt('Đa ngôn ngữ, đa khu vực:', 'Multi-language and multi-region:')}</strong> {lt('mở rộng cho đội ngũ toàn cầu và vận hành enterprise.', 'expansion for global teams and enterprise operations.')}</li>
                    <li><strong>{lt('Workflow triggers:', 'Workflow triggers:')}</strong> {lt('biên bản chốt có thể tự tạo/cập nhật ticket hoặc thông báo.', 'finalized minutes can create and update tickets or notifications automatically.')}</li>
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
            <h2>{lt('Liên hệ', 'Contact')}</h2>
            <p>{lt('Nhận demo hoặc trao đổi phương án triển khai cho luồng họp và đào tạo bằng AI.', 'Request a demo or discuss rollout for meeting and training intelligence workflows.')}</p>
            <div className="contact-tags">
              <span className="contact-tag">{lt('Trợ lý realtime', 'Realtime assistant')}</span>
              <span className="contact-tag">{lt('LightRAG phân tầng', 'Tiered LightRAG')}</span>
              <span className="contact-tag">{lt('Đầu ra có trích dẫn', 'Evidence-backed outputs')}</span>
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

export default Roadmap

