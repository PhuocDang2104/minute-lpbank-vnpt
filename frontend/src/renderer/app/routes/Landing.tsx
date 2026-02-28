/**
 * Landing Page - Welcome to MINUTE
 */
import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Calendar,
  MessageSquare,
  FileText,
  CheckSquare,
  ArrowRight,
  Info,
  Map,
  BadgeDollarSign,
  Mail,
  Github,
  ExternalLink,
  Globe,
} from 'lucide-react';
import BackgroundRippleEffect from '../../components/ui/background-ripple-effect';
import FloatingNavbar from '../../components/ui/floating-navbar';
import ContactEmailForm from '../../components/ui/contact-email-form';
import { useLanguage } from '../../contexts/LanguageContext';

export const Landing: React.FC = () => {
  const { language, setLanguage } = useLanguage();
  const isVi = language === 'vi';
  const lt = (vi: string, en: string) => (isVi ? vi : en);

  useEffect(() => {
    const root = document.querySelector('.landing-page');
    if (!root) return;
    const elements = Array.from(root.querySelectorAll<HTMLElement>('.reveal-on-scroll'));
    if (elements.length === 0) return;

    if (!('IntersectionObserver' in window)) {
      elements.forEach((el) => el.classList.add('is-visible'));
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        });
      },
      { threshold: 0.2, rootMargin: '0px 0px -10% 0px' },
    );

    elements.forEach((el, index) => {
      const delay = (index % 6) * 90;
      el.style.setProperty('--reveal-delay', `${delay}ms`);
      observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  const scrollToSection = (sectionId: string) => {
    const section = document.getElementById(sectionId);
    if (!section) return;
    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <div className="landing-page public-page">
      <FloatingNavbar
        navItems={[
          { name: lt('Giới thiệu', 'About'), to: '/about', icon: <Info size={18} /> },
          { name: lt('Lộ trình', 'Roadmap'), to: '/roadmap', icon: <Map size={18} /> },
          { name: lt('Bảng giá', 'Pricing'), to: '/pricing', icon: <BadgeDollarSign size={18} /> },
          { name: lt('Liên hệ', 'Contact'), onClick: () => scrollToSection('contact'), icon: <Mail size={18} /> },
        ]}
        action={{ label: lt('Bắt đầu', 'Get started'), to: '/app/meetings', icon: <ArrowRight size={16} /> }}
      />
      {/* Header */}
      <header className="landing-header">
        <div className="landing-header__brand">
          <Link to="/" className="logo" aria-label="Homepage" title="Homepage">
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

      {/* Hero Section */}
      <section className="hero reveal-on-scroll">
        <div className="hero-stage reveal-on-scroll">
          <BackgroundRippleEffect rows={14} cols={30} cellSize={48} />
          <div className="hero-stage__content">
            <h1 className="hero-title">
              {lt('Trợ lý AI đa phương thức cho', 'A multimodal AI assistant for')}{' '}
              <span className="gradient-text">{lt('Cuộc họp & Đào tạo', 'Meetings & Training')}</span>
            </h1>
            <p className="hero-subtitle">
              {lt(
                'MINUTE giúp bạn luôn sẵn sàng và đồng bộ tuyệt đối trong mọi phiên trực tuyến của quy trình làm việc, được vận hành bởi các AI agent tiên tiến tối ưu cho lĩnh vực BFSI.',
                'MINUTE keeps you prepared and perfectly aligned across every online session in your workflow, driven by advanced AI agents tailored for the BFSI industry',
              )}
            </p>
            <div className="hero-actions">
              <Link to="/about" className="btn btn-outline btn-lg hero-cta hero-cta--ghost">
                {lt('Tìm hiểu thêm', 'Learn more')}
                <ArrowRight size={18} />
              </Link>
              <Link to="/app/meetings" className="btn btn-primary btn-lg hero-cta hero-cta--primary hero-login">
                {lt('Bắt đầu', 'Get started')}
                <ArrowRight size={18} />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features">
        <h2 className="reveal-on-scroll">{lt('Năng lực cốt lõi', 'Core Capabilities')}</h2>
        <div className="features-grid">
          <div className="feature-card reveal-on-scroll">
            <div className="feature-card__header">
              <div className="feature-icon">
                <Calendar />
              </div>
              <h3>{lt('Trung tâm phiên & Thu nạp', 'Session Hub & Ingest')}</h3>
              <p className="feature-card__summary">
                {lt(
                  'Chạy phiên trực tiếp hoặc tải bản ghi lên với timeline và artifacts được hợp nhất.',
                  'Run live sessions or upload recordings with unified artifacts and timeline context.',
                )}
              </p>
            </div>
            <div className="feature-card__expanded">
              <div className="feature-card__details">
                <p className="feature-card__desc">
                  {lt(
                    'MINUTE hỗ trợ nhiều loại phiên họp và phiên đào tạo trong cùng một workflow. Nhóm có thể bắt đầu phiên trực tiếp hoặc tải lên bản ghi âm/video để xử lý hậu kỳ, sau đó xem transcript, recap, Q&A và tài liệu đính kèm trên một timeline thống nhất.',
                    'MINUTE supports meeting and study session types in one workflow. Teams can start live sessions or upload audio/video records for offline processing, then review transcript, recap windows, Q&A, and attached references in a single session timeline.',
                  )}
                </p>
                <ul className="feature-card__list">
                  <li>{lt('Phiên họp và phiên đào tạo trong một luồng sản phẩm', 'Meeting and study sessions in one product flow')}</li>
                  <li>{lt('Live capture và offline upload dùng chung một pipeline xử lý', 'Live capture and offline upload for the same processing pipeline')}</li>
                  <li>{lt('Transcript, recap và artifacts đa phương thức theo mốc thời gian', 'Timestamped transcript, recap, and visual moment artifacts')}</li>
                  <li>{lt('Trang chi tiết phiên tập trung cho lịch sử và follow-up', 'Centralized session detail page for history and follow-up')}</li>
                </ul>
              </div>
              <div className="feature-card__media">
                <img src="/landing/pre.png" alt={lt('Tổng quan Session hub và ingest', 'Session hub and ingest overview')} />
              </div>
            </div>
          </div>
          <div className="feature-card reveal-on-scroll">
            <div className="feature-card__header">
              <div className="feature-icon">
                <MessageSquare />
              </div>
              <h3>{lt('Trợ lý đa phương thức thời gian thực', 'Realtime Multimodal Companion')}</h3>
              <p className="feature-card__summary">
                {lt(
                  'Ngữ cảnh âm thanh và hình ảnh được hợp nhất theo từng cửa sổ recap 2 phút.',
                  'Audio and visual context are merged into recap windows every two minutes.',
                )}
              </p>
            </div>
            <div className="feature-card__expanded">
              <div className="feature-card__details">
                <p className="feature-card__desc">
                  {lt(
                    'MINUTE ingest luồng audio thời gian thực và các key frame video, đồng bộ sự kiện theo timebase của server và tạo recap thể hiện đồng thời nội dung nói và nội dung trình chiếu. Timeline cập nhật liên tục trong suốt phiên.',
                    'MINUTE ingests streaming audio and key video frames, aligns events by server timebase, and produces recap windows that reflect both what was said and what was shown. The timeline updates continuously during the session for low-friction tracking.',
                  )}
                </p>
                <ul className="feature-card__list">
                  <li>{lt('ASR streaming với đoạn transcript partial và final', 'ASR streaming with partial and final transcript segments')}</li>
                  <li>{lt('Frame sampling và hiểu ngữ cảnh hình ảnh theo thay đổi slide', 'Frame sampling and slide-change based visual understanding')}</li>
                  <li>{lt('Cửa sổ recap 2 phút kèm citations', 'Two-minute recap windows with citations')}</li>
                  <li>{lt('Trích xuất quyết định/action hoặc nội dung đào tạo ngay trong phiên', 'Meeting decisions/actions or study concepts extracted in-session')}</li>
                </ul>
              </div>
              <div className="feature-card__media">
                <img src="/landing/in.png" alt={lt('Trợ lý đa phương thức thời gian thực', 'Realtime multimodal companion')} />
              </div>
            </div>
          </div>
          <div className="feature-card reveal-on-scroll">
            <div className="feature-card__header">
              <div className="feature-icon">
                <FileText />
              </div>
              <h3>{lt('Bộ máy tổng hợp sau phiên', 'Post-Session Summary Engine')}</h3>
              <p className="feature-card__summary">
                {lt(
                  'Sinh đầu ra có cấu trúc theo loại phiên, với artifacts version hóa để tái sử dụng.',
                  'Generate structured outputs by session type, with versioned artifacts for reuse.',
                )}
              </p>
            </div>
            <div className="feature-card__expanded">
              <div className="feature-card__details">
                <p className="feature-card__desc">
                  {lt(
                    'Sau khi kết thúc phiên, MINUTE tổng hợp transcript cuối cùng, recap timeline và nguồn tham chiếu thành summary lõi, sau đó tách nhánh đầu ra cho phiên họp hoặc phiên đào tạo. Mỗi summary được lưu kèm lịch sử phiên bản để review và cải tiến.',
                    'After a session, MINUTE consolidates final transcript, recap timeline, and references into a core summary, then branches output generation for meetings or study sessions. Each summary is stored with version history to support review and iteration.',
                  )}
                </p>
                <ul className="feature-card__list">
                  <li>{lt('Đầu ra họp: summary, action items và tài liệu liên quan', 'Meeting outputs: summary, action items, and related documents')}</li>
                  <li>{lt('Đầu ra đào tạo: concept, ví dụ và hỗ trợ kiểm tra nhiều lớp', 'Study outputs: concepts, examples, and layered quiz support')}</li>
                  <li>{lt('Artifacts summary version hóa cho cập nhật có kiểm soát', 'Versioned summary artifacts for controlled updates')}</li>
                  <li>{lt('Cấu trúc sẵn sàng export cho pipeline DOCX/PDF', 'Export-oriented structure for DOCX/PDF pipelines')}</li>
                </ul>
              </div>
              <div className="feature-card__media">
                <img src="/landing/post.png" alt={lt('Bộ máy tổng hợp sau phiên', 'Post-session summary engine')} />
              </div>
            </div>
          </div>
          <div className="feature-card reveal-on-scroll">
            <div className="feature-card__header">
              <div className="feature-icon">
                <CheckSquare />
              </div>
              <h3>{lt('Hỏi đáp LightRAG theo tầng', 'Tiered LightRAG Q&A')}</h3>
              <p className="feature-card__summary">
                {lt(
                  'Ưu tiên trả lời grounded theo bằng chứng, chỉ leo thang khi bằng chứng chưa đủ.',
                  'Grounded answers first, controlled escalation only when evidence is insufficient.',
                )}
              </p>
            </div>
            <div className="feature-card__expanded">
              <div className="feature-card__details">
                <p className="feature-card__desc">
                  {lt(
                    'Q&A bắt đầu từ session memory và tài liệu đã tải lên trước khi mở rộng web (nếu được phép). Trợ lý thực hiện self-check, kiểm chứng citation và áp policy gate cùng cơ chế user approval cho tool-calling rủi ro.',
                    'Q&A starts from session memory and uploaded documents before any optional web expansion. The assistant runs self-check and citation validation, and applies policy gates plus user approval for risky tool-calling behavior.',
                  )}
                </p>
                <ul className="feature-card__list">
                  <li>{lt('Retrieval Tier 0 và Tier 1 cho phản hồi grounded nhanh', 'Tier 0 and Tier 1 retrieval for fast grounded responses')}</li>
                  <li>{lt('Tier 2 web search chỉ chạy khi policy cho phép và user xác nhận', 'Tier 2 web search only when policy allows and user approves')}</li>
                  <li>{lt('Tier 3 deep research cho truy vấn đa bước phức tạp', 'Tier 3 deep research for complex multi-hop queries')}</li>
                  <li>{lt('Guardrail no-source-no-answer cho claim quan trọng', 'No-source-no-answer guardrail for critical claims')}</li>
                </ul>
              </div>
              <div className="feature-card__media">
                <img src="/landing/rag.png" alt={lt('Hỏi đáp LightRAG theo tầng', 'Tiered LightRAG Q&A')} />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="benefits">
        <div className="benefits-rail">
          <div className="benefit-item reveal-on-scroll">
            <div className="benefit-value">24/7</div>
            <p className="benefit-desc">
              {lt(
                'Luôn sẵn sàng cho mọi phiên, từ cuộc gọi ad-hoc đến các cuộc họp điều hành định kỳ.',
                'Always ready for every session, from ad-hoc calls to recurring executive reviews.',
              )}
            </p>
          </div>
          <div className="benefit-item reveal-on-scroll">
            <div className="benefit-value">90%</div>
            <p className="benefit-desc">
              {lt(
                'Có thể tự động hóa tới 90% khối lượng ghi chú thủ công và soạn biên bản.',
                'Up to 90% of manual note-taking and minutes drafting can be automated.',
              )}
            </p>
          </div>
          <div className="benefit-item reveal-on-scroll">
            <div className="benefit-value">2x</div>
            <p className="benefit-desc">
              {lt(
                'Chu kỳ ra quyết định và triển khai follow-up có thể tăng tốc gấp đôi nhờ RAG và AI agents.',
                'Decision cycles and follow-up execution move twice as fast with RAG and AI agents.',
              )}
            </p>
          </div>
          <div className="benefit-item reveal-on-scroll">
            <div className="benefit-value">0 lost context</div>
            <p className="benefit-desc">
              {lt(
                'Mọi quyết định đều được ghi nhận, phân công và truy vết đầy đủ khi cần.',
                'Every decision is captured, assigned, and fully traceable when you need it.',
              )}
            </p>
          </div>
        </div>
      </section>

      {/* Comparison Section */}
      <section className="comparison">
        <div className="comparison__header reveal-on-scroll">
          <h2>{lt('Trước và sau khi dùng MINUTE', 'Before and After MINUTE')}</h2>
        </div>
        <div className="comparison-shell">
          <div className="comparison-panel comparison-panel--without reveal-on-scroll">
            <h3 className="comparison-title">{lt('Khi chưa dùng MINUTE', 'Without MINUTE')}</h3>
            <ul className="comparison-list comparison-list--without">
              <li>{lt('Ngữ cảnh realtime bị phân mảnh giữa transcript, slide và ghi chú cá nhân.', 'Realtime context is fragmented across transcript, slides, and personal notes.')}</li>
              <li>{lt('Đội ngũ khó xác minh claim nhanh do thiếu bằng chứng và mốc thời gian.', 'Teams cannot verify claims quickly because evidence and timestamps are missing.')}</li>
              <li>{lt('Web/tool actions bên ngoài có thể chạy mà thiếu cơ chế phê duyệt nhất quán.', 'External web and tool actions may run without a consistent approval gate.')}</li>
              <li>{lt('Action items thường thiếu xác nhận rõ ràng về owner và deadline.', 'Action items often miss clear owner and deadline confirmation.')}</li>
              <li>{lt('Chất lượng sau phiên phụ thuộc từng người, khó mở rộng follow-up.', 'Post-session quality varies by person, making follow-up hard to scale.')}</li>
            </ul>
          </div>
          <div className="comparison-divider">
            <span>VS</span>
          </div>
          <div className="comparison-panel comparison-panel--with reveal-on-scroll">
            <h3 className="comparison-title">{lt('Khi dùng MINUTE', 'With MINUTE')}</h3>
            <ul className="comparison-list comparison-list--with">
              <li>{lt('Một timeline đa phương thức hợp nhất audio, sự kiện hình ảnh và recap 2 phút.', 'One multimodal timeline merges audio, visual events, and 2-minute recap windows.')}</li>
              <li>{lt('Câu trả lời LightRAG được grounded từ session memory và tài liệu tải lên trước.', 'LightRAG answers are grounded in session memory and uploaded documents first.')}</li>
              <li>{lt('Tool call rủi ro tuân theo propose-approve-execute với human-in-the-loop.', 'Risky tool calls follow propose-approve-execute with human-in-the-loop control.')}</li>
              <li>{lt('Đầu ra họp và đào tạo có cấu trúc, version hóa và có bằng chứng đi kèm.', 'Meeting and training outputs are structured, versioned, and evidence-backed.')}</li>
              <li>{lt('Quyết định được đẩy nhanh với phân công rõ ràng, deadline cụ thể và trace sẵn sàng audit.', 'Decisions move faster with clear ownership, deadlines, and audit-ready traces.')}</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Roadmap Section */}
      <section className="landing-roadmap" id="roadmap">
        <div className="landing-roadmap__header reveal-on-scroll">
          <h2>{lt('Lộ trình Minute', 'Minute Roadmap')}</h2>
          <p>{lt('4 đợt phát hành để mở rộng từ độ tin cậy enterprise đến hệ sinh thái sản phẩm hoàn chỉnh.', 'Four release waves to scale from enterprise reliability to a complete product ecosystem.')}</p>
        </div>
        <div className="landing-roadmap__grid">
          <article className="landing-roadmap__column landing-roadmap__column--v1 reveal-on-scroll">
            <div className="landing-roadmap__kicker">{lt('Doanh nghiệp BFSI quy mô lớn', 'Large BFSI Enterprises')}</div>
            <div className="landing-roadmap__card">
              <div className="landing-roadmap__card-top">
                <span className="landing-roadmap__pill">Ver 1</span>
                <h3>Minute 1.0</h3>
              </div>
              <ul className="landing-roadmap__list">
                <li><strong>{lt('Tự động thu và điều phối họp:', 'Auto-capture and meeting orchestration:')}</strong> {lt('bot tự tham gia (Teams/GoMeet), đồng bộ Outlook, gắn tag dự án.', 'bot auto-join (Teams/GoMeet), Outlook sync, project tagging.')}</li>
                <li><strong>{lt('Transcript + diarization:', 'Transcript plus diarization:')}</strong> {lt('gán người nói chính xác, định dạng dễ đọc.', 'accurate speaker attribution and readable formatting.')}</li>
                <li><strong>{lt('Biên bản sẵn sàng BFSI:', 'BFSI-ready minutes:')}</strong> {lt('summary, quyết định, hành động (owner, hạn), và highlights.', 'summary, decisions, actions (owner, due date), and top highlights.')}</li>
                <li><strong>{lt('Xuất bản & phân phối:', 'Export and distribution:')}</strong> {lt('DOCX/PDF, link phân quyền, bản nháp và bản chính thức.', 'DOCX/PDF, permissioned links, and draft/final versions.')}</li>
                <li><strong>{lt('Ứng dụng & mở rộng:', 'Apps and extension:')}</strong> {lt('UX mượt với workflow tùy chỉnh nhanh.', 'smooth UX with fast workflow customization.')}</li>
                <li><strong>{lt('Triển khai & bảo mật:', 'Deployment and security:')}</strong> {lt('tùy chọn VPC/on-prem, RBAC nền tảng, mã hóa và access logs.', 'VPC/on-prem options, baseline RBAC, encryption, and access logs.')}</li>
              </ul>
            </div>
          </article>
          <article className="landing-roadmap__column landing-roadmap__column--v2 reveal-on-scroll">
            <div className="landing-roadmap__kicker">{lt('Doanh nghiệp đa ngành', 'Multi-Industry Enterprises')}</div>
            <div className="landing-roadmap__card">
              <div className="landing-roadmap__card-top">
                <span className="landing-roadmap__pill">Ver 2</span>
                <h3>Minute 2.0</h3>
              </div>
              <ul className="landing-roadmap__list">
                <li><strong>{lt('Nền tảng quản trị:', 'Admin platform:')}</strong> {lt('quản lý đa workspace/chi nhánh theo chính sách vai trò.', 'multi-workspace and branch control with role-based policies.')}</li>
                <li><strong>{lt('Workflow phê duyệt:', 'Approval workflow:')}</strong> {lt('từ người soạn đến reviewer và approver, theo dõi thay đổi/phiên bản.', 'drafter to reviewer to approver with tracked changes and versions.')}</li>
                <li><strong>{lt('Template theo ngành và vai trò:', 'Industry and role templates:')}</strong> {lt('thư viện, taxonomy và từ vựng domain.', 'libraries, taxonomy, and domain vocabulary.')}</li>
                <li><strong>{lt('Tinh chỉnh & review chất lượng:', 'Quality tuning and review:')}</strong> {lt('confidence score và kiểm định action/decision.', 'confidence scoring and action/decision validation.')}</li>
                <li><strong>{lt('Chế độ model & hiểu slide:', 'Model modes and slide awareness:')}</strong> {lt('Fast/Strong modes với OCR và trích xuất metric.', 'Fast/Strong modes with OCR and metric extraction.')}</li>
                <li><strong>{lt('Nhận diện giọng nói (opt-in):', 'Voice identity (opt-in):')}</strong> {lt('nâng độ chính xác mapping người nói với xác thực tùy chọn.', 'stronger speaker mapping with optional identity verification.')}</li>
              </ul>
            </div>
          </article>
          <article className="landing-roadmap__column landing-roadmap__column--v3 reveal-on-scroll">
            <div className="landing-roadmap__kicker">{lt('Gói sản phẩm (Enterprise + SME)', 'Packs (Enterprise + SME)')}</div>
            <div className="landing-roadmap__card">
              <div className="landing-roadmap__card-top">
                <span className="landing-roadmap__pill">Ver 3</span>
                <h3>Minute 3.0</h3>
              </div>
              <div className="landing-roadmap__packs">
                <div className="landing-roadmap__pack">
                  <div className="landing-roadmap__pack-title">{lt('Gói Enterprise', 'Enterprise Pack')}</div>
                  <ul className="landing-roadmap__list">
                    <li><strong>{lt('Knowledge base & agentic RAG:', 'Knowledge base and agentic RAG:')}</strong> {lt('grounding theo dự án/ngành trước và sau phiên.', 'project and industry grounding before and after sessions.')}</li>
                    <li><strong>{lt('Citation & khả năng truy vết:', 'Citation and traceability:')}</strong> {lt('biên bản và trả lời có nguồn cùng timestamp.', 'source-backed minutes and answers with timestamps.')}</li>
                    <li><strong>{lt('eDiscovery nâng cao:', 'Advanced eDiscovery:')}</strong> {lt('lọc theo tiêu chí và export bundle cho audit/điều tra.', 'criteria search and export bundles for audits and investigations.')}</li>
                    <li><strong>{lt('Quản trị hành động:', 'Action governance:')}</strong> {lt('nhắc việc theo policy, escalation và báo blocker.', 'policy-based reminders, escalation, and blocker reporting.')}</li>
                    <li><strong>{lt('Insight liên cuộc họp:', 'Cross-meeting insights:')}</strong> {lt('phát hiện xung đột quyết định, task trùng và chủ đề lặp.', 'detect decision conflicts, duplicate tasks, and repeated topics.')}</li>
                  </ul>
                </div>
                <div className="landing-roadmap__pack landing-roadmap__pack--muted">
                  <div className="landing-roadmap__pack-title">{lt('Gói SME', 'SME Pack')}</div>
                  <ul className="landing-roadmap__list">
                    <li><strong>{lt('Self-serve & auto-share:', 'Self-serve and auto-share:')}</strong> {lt('triển khai nhanh và gửi biên bản qua Slack/Teams.', 'launch quickly and deliver minutes to Slack or Teams.')}</li>
                    <li><strong>{lt('Đồng bộ task thiết yếu:', 'Essential task sync:')}</strong> {lt('đẩy một chạm sang công cụ phổ biến.', 'one-click push to popular work tools.')}</li>
                    <li><strong>{lt('Kiểm soát chi phí & quota:', 'Cost controls and quotas:')}</strong> {lt('giới hạn theo usage, lưu trữ và retention theo gói.', 'usage, storage, and retention by plan.')}</li>
                  </ul>
                </div>
              </div>
            </div>
          </article>
          <article className="landing-roadmap__column landing-roadmap__column--v4 reveal-on-scroll">
            <div className="landing-roadmap__kicker">{lt('Lite + Hệ sinh thái', 'Lite + Ecosystem')}</div>
            <div className="landing-roadmap__card">
              <div className="landing-roadmap__card-top">
                <span className="landing-roadmap__pill">Ver 4</span>
                <h3>{lt('Hệ sinh thái Minute', 'Minute Ecosystem')}</h3>
              </div>
              <div className="landing-roadmap__split">
                <div className="landing-roadmap__pack">
                  <div className="landing-roadmap__pack-title">{lt('Lite', 'Lite')}</div>
                  <ul className="landing-roadmap__list">
                    <li><strong>{lt('Vòng lõi tối giản:', 'Minimal core loop:')}</strong> {lt('từ họp -> summary -> action items với hiệu năng ổn định.', 'meeting to summary to action items with stable performance.')}</li>
                    <li><strong>{lt('Tìm kiếm và chia sẻ:', 'Search and share:')}</strong> {lt('tra theo cuộc họp/biên bản, chia sẻ link hoặc export.', 'find by meeting or minutes, then link or export.')}</li>
                    <li><strong>{lt('Biên bản tối ưu mobile:', 'Mobile-friendly minutes:')}</strong> {lt('review nhanh và checkoff hành động khi di chuyển.', 'quick review and action checkoffs on the go.')}</li>
                  </ul>
                </div>
                <div className="landing-roadmap__pack landing-roadmap__pack--muted">
                  <div className="landing-roadmap__pack-title">{lt('Hệ sinh thái', 'Ecosystem')}</div>
                  <ul className="landing-roadmap__list">
                    <li><strong>{lt('Tích hợp rộng:', 'Broad integrations:')}</strong> {lt('CRM, ticketing, DMS, collaboration chat và calendar.', 'CRM, ticketing, DMS, collaboration chat, and calendars.')}</li>
                    <li><strong>{lt('Marketplace & mô hình đối tác:', 'Marketplace and partner model:')}</strong> {lt('cài đặt theo ngành/doanh nghiệp với phạm vi quyền rõ ràng.', 'install by industry/company with scoped permissions.')}</li>
                    <li><strong>{lt('Đa ngôn ngữ & đa vùng:', 'Multi-language and multi-region:')}</strong> {lt('hỗ trợ rollout toàn cầu và vận hành enterprise.', 'support global rollout and enterprise operations.')}</li>
                    <li><strong>{lt('Workflow triggers:', 'Workflow triggers:')}</strong> {lt('biên bản đã duyệt có thể kích hoạt cập nhật ticket/CRM/thông báo.', 'finalized minutes trigger ticket updates, CRM updates, and notifications.')}</li>
                  </ul>
                </div>
              </div>
            </div>
          </article>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta reveal-on-scroll">
        <h2>{lt('Sẵn sàng nâng cấp mọi phiên làm việc?', 'Ready to upgrade every session?')}</h2>
        <p>{lt('Bắt đầu sử dụng Minute miễn phí ngay hôm nay.', 'Start using Minute for free today.')}</p>
        <Link to="/app/meetings" className="btn btn-primary btn-lg cta-button">
          {lt('Bắt đầu', 'Get Started')}
          <ArrowRight size={20} />
        </Link>
      </section>

      {/* Contact Section */}
      <section className="contact" id="contact">
        <div className="contact-card reveal-on-scroll">
          <div className="contact-content">
            <h2>{lt('Liên hệ', 'Contact')}</h2>
            <p>{lt('Yêu cầu demo, thông tin pricing hoặc tư vấn triển khai cho tổ chức của bạn.', 'Request a demo, pricing details, or implementation consulting for your organization.')}</p>
            <div className="contact-tags">
              <span className="contact-tag">{lt('Demo nhanh', 'Fast demo')}</span>
              <span className="contact-tag">{lt('Tư vấn triển khai', 'Implementation consulting')}</span>
              <span className="contact-tag">{lt('Bảo mật doanh nghiệp', 'Enterprise security')}</span>
            </div>
          </div>
          <div className="contact-panel">
            <ContactEmailForm />
            <div className="contact-actions">
              <Link to="/app/meetings" className="btn btn-primary btn-lg">{lt('Bắt đầu', 'Get Started')}</Link>
              <Link to="/about" className="btn btn-outline btn-lg">{lt('Về chúng tôi', 'About Us')}</Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer reveal-on-scroll">
        <div className="footer-brand">
          <img src="/minute_icon.svg" alt="MINUTE" className="landing-logo__icon landing-logo__icon--sm" />
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

      <style>{`
        .landing-page {
          min-height: 100vh;
          background: var(--bg-base);
          color: var(--text-primary);
        }

        /* Header */
        .landing-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: var(--space-sm) var(--space-xl);
          max-width: 1200px;
          margin: 0 auto;
          gap: var(--space-lg);
        }

        .landing-header__brand {
          display: flex;
          align-items: center;
          gap: var(--space-md);
          flex: 1;
          min-width: 0;
        }

        .logo {
          display: flex;
          align-items: center;
          gap: var(--space-xs);
          font-family: var(--font-heading);
          font-size: 1.5rem;
          font-weight: 700;
          color: var(--accent);
          text-decoration: none;
        }

        .landing-logo__icon {
          width: 32px;
          height: 32px;
          object-fit: contain;
          filter: drop-shadow(0 8px 16px rgba(247, 167, 69, 0.35));
        }

        .landing-logo__icon--sm {
          width: 22px;
          height: 22px;
        }

        .landing-nav {
          display: flex;
          align-items: center;
          gap: var(--space-sm);
          flex-wrap: wrap;
        }

        .landing-nav__link {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 6px 12px;
          font-size: 0.95rem;
          font-weight: 500;
          color: var(--text-secondary);
          background: transparent;
          border: 1px solid transparent;
          border-radius: 999px;
          cursor: pointer;
          text-decoration: none;
          font-family: inherit;
          transition: transform 0.2s ease, color 0.2s ease, background 0.2s ease, border-color 0.2s ease;
        }

        .landing-nav__link:hover {
          color: var(--accent);
          background: var(--accent-subtle);
          border-color: rgba(247, 167, 69, 0.4);
          transform: translateY(-1px);
        }

        .landing-nav__link:focus-visible {
          outline: 2px solid rgba(247, 167, 69, 0.45);
          outline-offset: 2px;
        }

        .landing-actions {
          display: flex;
          align-items: center;
          gap: var(--space-sm);
        }

        .landing-lang-switch {
          display: inline-flex;
          align-items: center;
          border: 1px solid rgba(247, 167, 69, 0.36);
          border-radius: 999px;
          background: rgba(255, 255, 255, 0.84);
          padding: 2px;
          box-shadow: 0 6px 14px rgba(15, 23, 42, 0.08);
        }

        .landing-lang-switch__btn {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 4px;
          min-width: 42px;
          padding: 4px 8px;
          border: 0;
          border-radius: 999px;
          background: transparent;
          color: var(--text-secondary);
          font-size: 0.72rem;
          font-weight: 700;
          letter-spacing: 0.04em;
          text-transform: uppercase;
          cursor: pointer;
          transition: color 0.2s ease, background 0.2s ease;
        }

        .landing-lang-switch__btn:hover {
          color: var(--accent);
        }

        .landing-lang-switch__btn.is-active {
          color: #1f1202;
          background: linear-gradient(120deg, #ffd992 0%, #f7a745 45%, #e47f20 100%);
          box-shadow: 0 4px 10px rgba(247, 167, 69, 0.24);
        }

        /* Hero */
        .hero {
          padding: var(--space-lg) 0;
        }

        .hero-stage {
          width: 100%;
          aspect-ratio: 24 / 9;
          border-radius: 0;
          border: 1px solid var(--border);
          background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(247, 247, 247, 0.9));
          box-shadow: 0 24px 60px rgba(15, 23, 42, 0.15);
          position: relative;
          overflow: hidden;
          display: flex;
          align-items: center;
          justify-content: center;
          margin: 0;
        }

        .hero-stage__content {
          position: relative;
          z-index: 4;
          text-align: center;
          max-width: 720px;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: var(--space-md);
          padding: var(--space-xl) 0;
          pointer-events: none;
        }

        .hero-title {
          font-family: var(--font-heading);
          font-size: 3rem;
          font-weight: 700;
          line-height: 1.15;
          margin: 0;
        }

        .gradient-text {
          background: linear-gradient(135deg, var(--accent), #d9822b);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .hero-subtitle {
          font-size: 1.25rem;
          color: var(--text-secondary);
          line-height: 1.6;
          margin: 0;
          max-width: 620px;
        }

        .hero-actions {
          display: flex;
          flex-direction: row;
          align-items: center;
          gap: var(--space-sm);
          margin-top: var(--space-sm);
          flex-wrap: wrap;
          justify-content: center;
          pointer-events: auto;
        }

        .hero-login {
          min-width: 200px;
        }

        .hero-cta {
          position: relative;
          isolation: isolate;
          overflow: hidden;
          border-radius: 999px;
          font-weight: 600;
          letter-spacing: 0.01em;
          padding: 14px 26px;
          transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease, filter 0.25s ease;
        }

        .hero-cta--primary {
          background: linear-gradient(120deg, #ffd992 0%, #f7a745 34%, #e47f20 68%, #ffd992 100%);
          background-size: 220% 220%;
          color: var(--text-on-accent);
          border: 1px solid rgba(247, 167, 69, 0.5);
          box-shadow: 0 14px 30px rgba(247, 167, 69, 0.38);
          animation: hero-cta-gradient 6s ease infinite;
        }

        .hero-cta--primary::before {
          content: '';
          position: absolute;
          inset: -20%;
          background: linear-gradient(112deg, transparent 15%, rgba(255, 255, 255, 0.55) 50%, transparent 85%);
          transform: translateX(-120%) rotate(8deg);
          opacity: 0;
          transition: opacity 0.2s ease;
          pointer-events: none;
        }

        .hero-cta--primary::after {
          content: '';
          position: absolute;
          inset: -25%;
          background: radial-gradient(circle, rgba(255, 226, 164, 0.45), transparent 64%);
          opacity: 0;
          transform: scale(0.94);
          transition: transform 0.25s ease, opacity 0.25s ease;
          pointer-events: none;
        }

        .hero-cta--primary:hover {
          transform: translateY(-3px) scale(1.03);
          box-shadow: 0 24px 44px rgba(232, 131, 30, 0.5), 0 0 0 1px rgba(247, 167, 69, 0.38);
          filter: saturate(1.15);
          animation-duration: 2.2s;
        }

        .hero-cta--primary:hover::before {
          opacity: 1;
          animation: hero-cta-sheen 0.95s ease forwards;
        }

        .hero-cta--primary:hover::after {
          opacity: 1;
          transform: scale(1.08);
        }

        .landing-get-started {
          position: relative;
          isolation: isolate;
          overflow: hidden;
          border-radius: 999px;
          border: 1px solid rgba(247, 167, 69, 0.46);
          background: linear-gradient(120deg, #ffd992 0%, #f7a745 34%, #e47f20 68%, #ffd992 100%);
          background-size: 220% 220%;
          color: #1f1202;
          box-shadow: 0 12px 28px rgba(247, 167, 69, 0.36);
          animation: hero-cta-gradient 7s ease infinite;
        }

        .landing-get-started::before {
          content: '';
          position: absolute;
          inset: -20%;
          background: linear-gradient(115deg, transparent 15%, rgba(255, 255, 255, 0.45) 52%, transparent 85%);
          transform: translateX(-120%) rotate(7deg);
          pointer-events: none;
          opacity: 0;
        }

        .landing-get-started:hover {
          transform: translateY(-2px) scale(1.02);
          box-shadow: 0 20px 38px rgba(232, 131, 30, 0.48), 0 0 0 1px rgba(247, 167, 69, 0.4);
          filter: saturate(1.12);
          animation-duration: 2.6s;
        }

        .landing-get-started:hover::before {
          opacity: 1;
          animation: hero-cta-sheen 0.95s ease forwards;
        }

        .hero-cta--ghost {
          border: 1px solid rgba(17, 17, 17, 0.2);
          background: rgba(255, 255, 255, 0.75);
          box-shadow: 0 10px 24px rgba(15, 23, 42, 0.12);
        }

        .hero-cta--ghost:hover {
          transform: translateY(-2px);
          border-color: rgba(247, 167, 69, 0.5);
          color: var(--accent);
        }

        /* Features */
        .features {
          max-width: 1200px;
          margin: 0 auto;
          padding: var(--space-2xl) var(--space-xl);
          text-align: center;
        }

        .features h2 {
          font-family: var(--font-heading);
          font-size: 2rem;
          margin-bottom: var(--space-xl);
        }

        .features-grid {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: var(--space-lg);
          align-items: stretch;
          transition: grid-template-columns 0.7s cubic-bezier(0.22, 0.61, 0.36, 1),
            gap 0.4s ease;
        }

        .feature-card {
          background: var(--bg-elevated);
          border: 1px solid var(--border);
          border-radius: var(--radius-lg);
          padding: var(--space-lg);
          text-align: left;
          transition: transform 0.5s cubic-bezier(0.22, 0.61, 0.36, 1),
            border-color 0.35s ease,
            box-shadow 0.35s ease,
            opacity 0.35s ease,
            min-height 0.6s cubic-bezier(0.22, 0.61, 0.36, 1);
          display: flex;
          flex-direction: column;
          gap: var(--space-md);
          min-width: 0;
          position: relative;
          overflow: hidden;
          min-height: 240px;
          will-change: transform;
        }

        .feature-card__header {
          display: flex;
          flex-direction: column;
          gap: var(--space-xs);
        }

        .features-grid:hover .feature-card {
          opacity: 0.7;
        }

        .features-grid:hover .feature-card:hover {
          opacity: 1;
          transform: translateY(-4px);
          border-color: var(--accent);
          box-shadow: 0 18px 40px rgba(15, 23, 42, 0.18);
          min-height: 380px;
        }

        @supports selector(:has(*)) {
          .features-grid:has(.feature-card:nth-child(1):hover) {
            grid-template-columns: 9fr 1fr 1fr 1fr;
          }

          .features-grid:has(.feature-card:nth-child(2):hover) {
            grid-template-columns: 1fr 9fr 1fr 1fr;
          }

          .features-grid:has(.feature-card:nth-child(3):hover) {
            grid-template-columns: 1fr 1fr 9fr 1fr;
          }

          .features-grid:has(.feature-card:nth-child(4):hover) {
            grid-template-columns: 1fr 1fr 1fr 9fr;
          }
        }

        .feature-icon {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 48px;
          height: 48px;
          background: rgba(234, 179, 8, 0.1);
          border-radius: var(--radius-md);
          color: var(--accent);
          margin-bottom: 0;
        }

        .feature-card__header h3 {
          font-family: var(--font-heading);
          font-size: 1.125rem;
          margin: 0;
        }

        .feature-card__summary {
          font-size: 0.9rem;
          color: var(--text-secondary);
          line-height: 1.5;
          margin: 0;
          display: -webkit-box;
          -webkit-line-clamp: 3;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }

        .feature-card__expanded {
          display: grid;
          grid-template-columns: minmax(0, 1fr) minmax(180px, 240px);
          gap: var(--space-md);
          align-items: center;
          margin-top: var(--space-sm);
          opacity: 0;
          max-height: 0;
          transform: translateY(8px);
          transition: none;
          overflow: hidden;
        }

        .feature-card:hover .feature-card__expanded {
          opacity: 1;
          max-height: 420px;
          transform: translateY(0);
          transition: max-height 0.6s cubic-bezier(0.22, 0.61, 0.36, 1),
            opacity 0.35s ease,
            transform 0.45s ease;
        }

        .feature-card__desc {
          font-size: 0.9rem;
          color: var(--text-secondary);
          line-height: 1.6;
          margin: 0 0 var(--space-sm);
        }

        .feature-card__list {
          margin: 0;
          padding-left: 18px;
          display: flex;
          flex-direction: column;
          gap: 6px;
          color: var(--text-secondary);
          font-size: 0.85rem;
          line-height: 1.5;
        }

        .feature-card__media {
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .feature-card__media img {
          width: 100%;
          max-width: 220px;
          height: auto;
          object-fit: contain;
          border-radius: 14px;
          border: 1px solid var(--border);
          background: #fff;
          padding: var(--space-sm);
          box-shadow: 0 12px 24px rgba(15, 23, 42, 0.12);
        }

        /* Benefits */
        .benefits {
          padding: var(--space-2xl) var(--space-xl);
          background:
            radial-gradient(circle at 20% -20%, rgba(247, 167, 69, 0.12), transparent 50%),
            radial-gradient(circle at 80% 120%, rgba(247, 167, 69, 0.1), transparent 55%),
            var(--bg-surface);
          border-top: 1px solid var(--border);
          border-bottom: 1px solid var(--border);
        }

        .benefits-rail {
          max-width: 1200px;
          margin: 0 auto;
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: var(--space-xl);
          position: relative;
          padding: var(--space-lg) 0;
        }

        .benefits-rail::before {
          content: '';
          position: absolute;
          left: 0;
          right: 0;
          top: 6px;
          height: 2px;
          background: linear-gradient(
            90deg,
            transparent 0%,
            rgba(247, 167, 69, 0.35) 20%,
            rgba(247, 167, 69, 0.7) 50%,
            rgba(247, 167, 69, 0.35) 80%,
            transparent 100%
          );
          opacity: 0.7;
          animation: rail-sweep 10s ease-in-out infinite;
        }

        .benefits-rail::after {
          content: '';
          position: absolute;
          left: 0;
          right: 0;
          bottom: 6px;
          height: 1px;
          background: linear-gradient(90deg, transparent, rgba(0, 0, 0, 0.08), transparent);
        }

        .benefit-item {
          position: relative;
          padding: var(--space-lg) var(--space-md) var(--space-lg) var(--space-lg);
          min-height: 160px;
          transition: transform 0.25s ease, color 0.25s ease;
        }

        .benefit-item::before {
          content: '';
          position: absolute;
          left: var(--space-sm);
          top: var(--space-md);
          bottom: var(--space-md);
          width: 1px;
          background: linear-gradient(180deg, transparent, rgba(247, 167, 69, 0.5), transparent);
          opacity: 0.6;
        }

        .benefit-item::after {
          content: '';
          position: absolute;
          left: calc(var(--space-sm) - 3px);
          top: var(--space-md);
          width: 6px;
          height: 6px;
          border-radius: 999px;
          background: var(--accent);
          box-shadow: 0 0 0 6px rgba(247, 167, 69, 0.12);
          transition: transform 0.25s ease, box-shadow 0.25s ease;
        }

        .benefit-item:hover {
          transform: translateY(-6px);
        }

        .benefit-item:hover::after {
          transform: scale(1.15);
          box-shadow: 0 0 0 8px rgba(247, 167, 69, 0.2);
        }

        .benefit-value {
          font-family: var(--font-heading);
          font-size: clamp(1.6rem, 2.4vw, 2.2rem);
          font-weight: 700;
          letter-spacing: 0.02em;
          margin-bottom: var(--space-sm);
          color: var(--text-primary);
          transition: color 0.25s ease;
        }

        .benefit-desc {
          font-size: 0.95rem;
          color: var(--text-secondary);
          line-height: 1.6;
          margin: 0;
          transition: color 0.25s ease;
        }

        .benefit-item:hover .benefit-value {
          color: var(--accent);
        }

        @keyframes rail-sweep {
          0%,
          100% {
            opacity: 0.4;
            transform: translateX(-4%);
          }
          50% {
            opacity: 0.75;
            transform: translateX(4%);
          }
        }

        /* Contact */
        .contact {
          padding: var(--space-2xl) var(--space-xl);
          background: var(--bg-base);
        }

        .contact-card {
          max-width: 1200px;
          margin: 0 auto;
          padding: var(--space-xl);
          border-radius: 24px;
          border: 1px solid var(--border);
          background: linear-gradient(135deg, rgba(247, 167, 69, 0.16), rgba(255, 255, 255, 0.95));
          box-shadow: 0 18px 40px rgba(15, 23, 42, 0.12);
          display: grid;
          grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr);
          align-items: stretch;
          gap: var(--space-lg);
        }

        .contact-content {
          display: flex;
          flex-direction: column;
          gap: var(--space-sm);
          flex: 1;
        }

        .contact-content h2 {
          font-family: var(--font-heading);
          font-size: 2rem;
          margin: 0;
        }

        .contact-content p {
          margin: 0;
          color: var(--text-secondary);
          font-size: 1rem;
          line-height: 1.6;
        }

        .contact-tags {
          display: flex;
          flex-wrap: wrap;
          gap: var(--space-sm);
        }

        .contact-tag {
          padding: 6px 12px;
          border-radius: 999px;
          background: rgba(247, 167, 69, 0.15);
          border: 1px solid rgba(247, 167, 69, 0.4);
          font-size: 0.8rem;
          font-weight: 600;
          color: var(--accent);
        }

        .contact-panel {
          display: flex;
          flex-direction: column;
          gap: var(--space-md);
          padding: var(--space-lg);
          border-radius: 18px;
          background: rgba(255, 255, 255, 0.9);
          border: 1px solid rgba(247, 167, 69, 0.35);
          box-shadow: 0 12px 24px rgba(15, 23, 42, 0.12);
        }

        .contact-panel .contact-form {
          margin-top: 0;
        }

        .contact-actions {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: var(--space-sm);
        }

        .contact-actions .btn {
          width: 100%;
          justify-content: center;
        }

        .reveal-on-scroll {
          opacity: 0;
          transform: translateY(18px) scale(0.98);
          transition: opacity 0.6s ease, transform 0.6s ease;
          transition-delay: var(--reveal-delay, 0ms);
          will-change: opacity, transform;
        }

        .reveal-on-scroll.is-visible {
          opacity: 1;
          transform: translateY(0) scale(1);
        }

        /* Comparison */
        .comparison {
          padding: var(--space-2xl) var(--space-xl);
          background: linear-gradient(180deg, #ffffff 0%, #f8f8f8 100%);
        }

        .comparison__header {
          max-width: 820px;
          margin: 0 auto var(--space-xl);
          text-align: center;
          display: flex;
          flex-direction: column;
          gap: var(--space-sm);
        }

        .comparison__header h2 {
          font-family: var(--font-heading);
          font-size: 2rem;
          margin: 0;
        }

        .comparison-shell {
          max-width: 1200px;
          margin: 0 auto;
          display: grid;
          grid-template-columns: minmax(0, 1fr) 72px minmax(0, 1fr);
          gap: var(--space-lg);
          align-items: stretch;
        }

        .comparison-panel {
          position: relative;
          padding: var(--space-xl);
          border-radius: 22px;
          border: 1px solid var(--border);
          background: #ffffff;
          box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
          display: flex;
          flex-direction: column;
          gap: var(--space-md);
          overflow: hidden;
          transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
        }

        .comparison-panel:hover {
          transform: translateY(-6px);
        }

        .comparison-panel::after {
          content: '';
          position: absolute;
          left: 0;
          right: 0;
          top: 0;
          height: 4px;
          opacity: 0.8;
        }

        .comparison-panel--without {
          background: linear-gradient(180deg, #ffffff 0%, #f7f7f7 100%);
        }

        .comparison-panel--without::after {
          background: linear-gradient(90deg, rgba(239, 68, 68, 0.35), transparent);
        }

        .comparison-panel--with {
          background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(247, 167, 69, 0.1));
          border-color: rgba(247, 167, 69, 0.35);
          box-shadow: 0 24px 50px rgba(247, 167, 69, 0.18);
        }

        .comparison-panel--with::after {
          background: linear-gradient(90deg, rgba(34, 197, 94, 0.4), transparent);
        }

        .comparison-title {
          font-family: var(--font-heading);
          font-size: 1.15rem;
          margin: 0;
        }

        .comparison-list {
          list-style: none;
          margin: 0;
          padding: 0;
          display: flex;
          flex-direction: column;
          gap: var(--space-sm);
        }

        .comparison-list li {
          position: relative;
          padding-left: 28px;
          font-size: 0.95rem;
          color: var(--text-secondary);
          line-height: 1.6;
        }

        .comparison-list li::before {
          content: '';
          position: absolute;
          left: 0;
          top: 6px;
          width: 18px;
          height: 18px;
          border-radius: 999px;
          border: 1px solid transparent;
        }

        .comparison-list--without li::before {
          border-color: rgba(239, 68, 68, 0.5);
          background: rgba(239, 68, 68, 0.08);
        }

        .comparison-list--without li::after {
          content: '';
          position: absolute;
          left: 4px;
          top: 10px;
          width: 10px;
          height: 10px;
          background:
            linear-gradient(45deg, transparent 45%, rgba(239, 68, 68, 0.9) 45%, rgba(239, 68, 68, 0.9) 55%, transparent 55%),
            linear-gradient(-45deg, transparent 45%, rgba(239, 68, 68, 0.9) 45%, rgba(239, 68, 68, 0.9) 55%, transparent 55%);
        }

        .comparison-list--with li::before {
          border-color: rgba(34, 197, 94, 0.45);
          background: rgba(34, 197, 94, 0.08);
        }

        .comparison-list--with li::after {
          content: '';
          position: absolute;
          left: 5px;
          top: 11px;
          width: 8px;
          height: 4px;
          border-left: 2px solid rgba(34, 197, 94, 0.9);
          border-bottom: 2px solid rgba(34, 197, 94, 0.9);
          transform: rotate(-45deg);
        }

        .comparison-divider {
          position: relative;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .comparison-divider::before {
          content: '';
          position: absolute;
          top: 0;
          bottom: 0;
          width: 1px;
          background: linear-gradient(180deg, transparent, rgba(0, 0, 0, 0.15), transparent);
        }

        .comparison-divider span {
          font-size: 0.75rem;
          font-weight: 700;
          letter-spacing: 0.2em;
          text-transform: uppercase;
          color: var(--text-muted);
          background: #ffffff;
          border: 1px solid var(--border);
          border-radius: 999px;
          padding: 6px 12px;
          box-shadow: 0 10px 20px rgba(15, 23, 42, 0.1);
        }

        /* CTA */
        .cta {
          text-align: center;
          padding: var(--space-2xl);
          max-width: 600px;
          margin: 0 auto;
        }

        .cta h2 {
          font-family: var(--font-heading);
          font-size: 2rem;
          margin-bottom: var(--space-sm);
        }

        .cta p {
          color: var(--text-secondary);
          margin-bottom: var(--space-lg);
        }

        /* Footer */
        .landing-footer {
          text-align: center;
          padding: var(--space-xl);
          border-top: 1px solid var(--border);
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: var(--space-xs);
        }

        .footer-brand {
          display: inline-flex;
          align-items: center;
          gap: var(--space-xs);
          font-family: var(--font-heading);
          font-weight: 600;
          color: var(--accent);
        }

        .landing-footer__link {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          font-size: 0.85rem;
          color: var(--text-secondary);
          text-decoration: none;
          transition: color 0.2s ease;
        }

        .landing-footer__link:hover {
          color: var(--accent);
        }

        .landing-footer p {
          font-size: 0.875rem;
          color: var(--text-secondary);
          margin: 0;
        }

        /* Buttons */
        .btn {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: var(--space-xs);
          padding: var(--space-sm) var(--space-md);
          border-radius: var(--radius-sm);
          font-size: 1rem;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
          border: none;
          text-decoration: none;
        }

        .btn-primary {
          background: var(--accent);
          color: #1a1a1a;
        }

        .btn-primary:hover {
          background: var(--accent-hover);
        }

        .btn-outline {
          background: transparent;
          border: 1px solid var(--border);
          color: var(--text-primary);
        }

        .btn-outline:hover {
          border-color: var(--accent);
          color: var(--accent);
        }

        .btn-ghost {
          background: transparent;
          color: var(--text-primary);
        }

        .btn-ghost:hover {
          color: var(--accent);
        }

        .btn-lg {
          padding: var(--space-md) var(--space-lg);
          font-size: 1.125rem;
        }

        .cta-button {
          position: relative;
          overflow: hidden;
          border: 1px solid rgba(247, 167, 69, 0.6);
          background: linear-gradient(135deg, #f9c46a 0%, #f7a745 45%, #c8873b 100%);
          box-shadow: 0 18px 36px rgba(247, 167, 69, 0.38);
          transform: translateZ(0);
          transition: box-shadow 0.2s ease, filter 0.2s ease;
        }

        .cta-button::before {
          content: '';
          position: absolute;
          inset: 0;
          background: linear-gradient(120deg, transparent 0%, rgba(255, 255, 255, 0.6) 50%, transparent 100%);
          transform: translateX(-120%);
          opacity: 0;
        }

        .cta-button::after {
          content: '';
          position: absolute;
          inset: -35%;
          background: radial-gradient(circle, rgba(255, 255, 255, 0.35), transparent 60%);
          opacity: 0;
          transition: opacity 0.2s ease;
        }

        .cta-button:hover {
          box-shadow: 0 26px 48px rgba(247, 167, 69, 0.5), 0 0 0 1px rgba(247, 167, 69, 0.5);
          filter: saturate(1.08);
          animation: cta-rumble 0.35s ease-in-out infinite;
        }

        .cta-button:hover::before {
          opacity: 1;
          animation: cta-sheen 0.9s ease infinite;
        }

        .cta-button:hover::after {
          opacity: 0.9;
        }

        @keyframes cta-sheen {
          0% {
            transform: translateX(-120%);
          }
          60% {
            transform: translateX(120%);
          }
          100% {
            transform: translateX(120%);
          }
        }

        @keyframes hero-cta-sheen {
          0% {
            transform: translateX(-120%) rotate(8deg);
          }
          100% {
            transform: translateX(130%) rotate(8deg);
          }
        }

        @keyframes hero-cta-gradient {
          0% {
            background-position: 0% 50%;
          }
          50% {
            background-position: 100% 50%;
          }
          100% {
            background-position: 0% 50%;
          }
        }

        @keyframes cta-rumble {
          0% {
            transform: translate(0, -3px) scale(1.02);
          }
          25% {
            transform: translate(-1px, -4px) scale(1.02);
          }
          50% {
            transform: translate(1px, -3px) scale(1.02);
          }
          75% {
            transform: translate(-0.5px, -4px) scale(1.02);
          }
          100% {
            transform: translate(0, -3px) scale(1.02);
          }
        }

        /* Responsive */
        @media (max-width: 1024px) {
          .features-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            transition: none;
          }

          .benefits-rail {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }

          .hero-stage {
            aspect-ratio: 18 / 9;
          }

          .features-grid:hover .feature-card {
            opacity: 1;
          }

          .features-grid:hover .feature-card:hover {
            transform: none;
            min-height: auto;
          }

          .feature-card__expanded {
            opacity: 1;
            max-height: none;
            transform: none;
          }
        }

        @media (max-width: 900px) {
          .landing-header {
            flex-direction: column;
            align-items: stretch;
            gap: var(--space-md);
          }

          .landing-header__brand {
            width: 100%;
            justify-content: space-between;
          }

          .landing-actions {
            width: 100%;
            justify-content: flex-end;
          }

          .feature-card__expanded {
            grid-template-columns: 1fr;
          }

          .comparison-shell {
            grid-template-columns: 1fr;
          }

          .comparison-divider {
            display: none;
          }

          .contact-card {
            grid-template-columns: 1fr;
          }
        }

        @media (max-width: 640px) {
          .landing-header {
            padding: var(--space-md);
          }

          .landing-header__brand {
            flex-direction: column;
            align-items: flex-start;
            gap: var(--space-sm);
          }

          .landing-nav {
            display: none;
          }

          .landing-actions {
            width: 100%;
            justify-content: space-between;
          }

          .landing-lang-switch {
            flex: 1;
            max-width: 126px;
          }

          .landing-lang-switch__btn {
            width: 100%;
            min-width: 0;
          }

          .hero-title {
            font-size: 2rem;
          }

          .hero-subtitle {
            font-size: 1rem;
          }

          .hero-stage__content {
            padding: 0;
            max-width: 100%;
          }

          .hero {
            padding: var(--space-md) 0;
          }

          .features-grid {
            grid-template-columns: 1fr;
          }

          .hero-stage {
            aspect-ratio: auto;
            min-height: 70vh;
            padding: var(--space-lg) var(--space-md);
          }

          .hero-actions {
            flex-direction: column;
            width: 100%;
          }

          .hero-cta {
            width: 100%;
            justify-content: center;
          }

          .benefits-rail {
            grid-template-columns: 1fr;
          }

          .comparison {
            padding: var(--space-xl) var(--space-md);
          }

          .contact-actions {
            width: 100%;
            grid-template-columns: 1fr;
            align-items: stretch;
          }

          .contact-actions .btn {
            width: 100%;
          }
        }

        @media (prefers-reduced-motion: reduce) {
          .benefits-rail::before {
            animation: none;
          }

          .reveal-on-scroll {
            opacity: 1;
            transform: none;
            transition: none;
          }

          .benefit-item {
            transition: none;
          }

          .benefit-item::after {
            transition: none;
          }

          .comparison-panel {
            transition: none;
          }

          .cta-button {
            animation: none;
          }

          .cta-button:hover::before {
            animation: none;
          }
        }

      `}</style>
    </div>
  );
};

export default Landing;


