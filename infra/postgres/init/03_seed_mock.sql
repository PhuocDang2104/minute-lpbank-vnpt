-- ============================================
-- MEETMATE MOCK DATA FOR PMO DEMO
-- Scenario: LPBank PMO managing Core Banking, Mobile Banking, LOS projects
-- ============================================

-- ============================================
-- 1. ORGANIZATION & DEPARTMENTS
-- ============================================

-- LPBank Organization
INSERT INTO organization (id, name) VALUES
    ('11111111-1111-1111-1111-111111111111', 'LPBank - Ngân hàng Bưu điện Liên Việt')
ON CONFLICT (id) DO NOTHING;

-- Departments
INSERT INTO department (id, organization_id, name) VALUES
    ('d0000001-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111', 'PMO - Project Management Office'),
    ('d0000002-0000-0000-0000-000000000002', '11111111-1111-1111-1111-111111111111', 'Khối Công nghệ'),
    ('d0000003-0000-0000-0000-000000000003', '11111111-1111-1111-1111-111111111111', 'Khối Kinh doanh'),
    ('d0000004-0000-0000-0000-000000000004', '11111111-1111-1111-1111-111111111111', 'Khối Risk & Compliance'),
    ('d0000005-0000-0000-0000-000000000005', '11111111-1111-1111-1111-111111111111', 'Khối Vận hành')
ON CONFLICT (id) DO NOTHING;

-- Projects
INSERT INTO project (id, organization_id, name, code) VALUES
    ('p0000001-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111', 'Core Banking Modernization', 'CB-2024'),
    ('p0000002-0000-0000-0000-000000000002', '11111111-1111-1111-1111-111111111111', 'Mobile Banking 3.0', 'MB-2024'),
    ('p0000003-0000-0000-0000-000000000003', '11111111-1111-1111-1111-111111111111', 'Loan Origination System', 'LOS-2024'),
    ('p0000004-0000-0000-0000-000000000004', '11111111-1111-1111-1111-111111111111', 'KYC Enhancement', 'KYC-2024')
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 2. USERS (Personas)
-- ============================================

INSERT INTO user_account (id, email, display_name, role, organization_id, department_id) VALUES
    -- PMO Team
    ('u0000001-0000-0000-0000-000000000001', 'nguyenvana@lpbank.vn', 'Nguyễn Văn A - Head of PMO', 'PMO', '11111111-1111-1111-1111-111111111111', 'd0000001-0000-0000-0000-000000000001'),
    ('u0000002-0000-0000-0000-000000000002', 'tranthib@lpbank.vn', 'Trần Thị B - Senior PM', 'PMO', '11111111-1111-1111-1111-111111111111', 'd0000001-0000-0000-0000-000000000001'),
    ('u0000003-0000-0000-0000-000000000003', 'levanc@lpbank.vn', 'Lê Văn C - BA Lead', 'user', '11111111-1111-1111-1111-111111111111', 'd0000001-0000-0000-0000-000000000001'),
    
    -- Tech Team
    ('u0000004-0000-0000-0000-000000000004', 'phamvand@lpbank.vn', 'Phạm Văn D - CTO', 'admin', '11111111-1111-1111-1111-111111111111', 'd0000002-0000-0000-0000-000000000002'),
    ('u0000005-0000-0000-0000-000000000005', 'hoangthie@lpbank.vn', 'Hoàng Thị E - Tech Lead Core Banking', 'user', '11111111-1111-1111-1111-111111111111', 'd0000002-0000-0000-0000-000000000002'),
    ('u0000006-0000-0000-0000-000000000006', 'ngothif@lpbank.vn', 'Ngô Thị F - Tech Lead Mobile', 'user', '11111111-1111-1111-1111-111111111111', 'd0000002-0000-0000-0000-000000000002'),
    
    -- Business Team
    ('u0000007-0000-0000-0000-000000000007', 'vuvang@lpbank.vn', 'Vũ Văn G - Business Director', 'chair', '11111111-1111-1111-1111-111111111111', 'd0000003-0000-0000-0000-000000000003'),
    ('u0000008-0000-0000-0000-000000000008', 'dothih@lpbank.vn', 'Đỗ Thị H - Product Owner', 'user', '11111111-1111-1111-1111-111111111111', 'd0000003-0000-0000-0000-000000000003'),
    
    -- Risk & Compliance Team
    ('u0000009-0000-0000-0000-000000000009', 'buivani@lpbank.vn', 'Bùi Văn I - Chief Risk Officer', 'chair', '11111111-1111-1111-1111-111111111111', 'd0000004-0000-0000-0000-000000000004'),
    ('u0000010-0000-0000-0000-000000000010', 'dangthik@lpbank.vn', 'Đặng Thị K - Compliance Manager', 'user', '11111111-1111-1111-1111-111111111111', 'd0000004-0000-0000-0000-000000000004'),
    
    -- Operations Team
    ('u0000011-0000-0000-0000-000000000011', 'truongvanl@lpbank.vn', 'Trương Văn L - Operations Director', 'user', '11111111-1111-1111-1111-111111111111', 'd0000005-0000-0000-0000-000000000005')
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 3. MEETINGS (Various types PMO handles daily)
-- ============================================

INSERT INTO meeting (id, external_event_id, title, description, organizer_id, session_date, start_time, end_time, meeting_type, phase, project_id, department_id, location, teams_link) VALUES
    -- Meeting 1: Steering Committee (POST phase - đã họp xong, có transcript)
    ('m0000001-0000-0000-0000-000000000001', 
     'outlook-event-001', 
     'Steering Committee - Core Banking Q4 2024', 
     'Họp chỉ đạo dự án Core Banking: Review tiến độ, budget, risks, và quyết định các milestone quan trọng.',
     'u0000001-0000-0000-0000-000000000001',
     (NOW() - INTERVAL '2 hours')::date,
     NOW() - INTERVAL '2 hours',
     NOW() - INTERVAL '1 hour',
     'steering',
     'post',
     'p0000001-0000-0000-0000-000000000001',
     'd0000001-0000-0000-0000-000000000001',
     'Phòng họp VIP - Tầng 15',
     'https://teams.microsoft.com/l/meetup-join/steering-001'),
    
    -- Meeting 2: Weekly Status (IN phase - đang họp)
    ('m0000002-0000-0000-0000-000000000002',
     'outlook-event-002',
     'Weekly Project Status - Mobile Banking Sprint 23',
     'Review sprint 23, demo features, discuss blockers.',
     'u0000002-0000-0000-0000-000000000002',
     (NOW() - INTERVAL '30 minutes')::date,
     NOW() - INTERVAL '30 minutes',
     NOW() + INTERVAL '30 minutes',
     'weekly_status',
     'in',
     'p0000002-0000-0000-0000-000000000002',
     'd0000002-0000-0000-0000-000000000002',
     'Online - Microsoft Teams',
     'https://teams.microsoft.com/l/meetup-join/weekly-002'),
    
    -- Meeting 3: Risk Review (PRE phase - sắp họp)
    ('m0000003-0000-0000-0000-000000000003',
     'outlook-event-003',
     'Risk Review - LOS Integration với Core Banking',
     'Đánh giá rủi ro tích hợp LOS với Core Banking mới, compliance requirements.',
     'u0000009-0000-0000-0000-000000000009',
     (NOW() + INTERVAL '2 hours')::date,
     NOW() + INTERVAL '2 hours',
     NOW() + INTERVAL '3 hours',
     'risk_review',
     'pre',
     'p0000003-0000-0000-0000-000000000003',
     'd0000004-0000-0000-0000-000000000004',
     'Phòng họp Risk - Tầng 12',
     'https://teams.microsoft.com/l/meetup-join/risk-003'),
    
    -- Meeting 4: Cross-functional Workshop (PRE phase)
    ('m0000004-0000-0000-0000-000000000004',
     'outlook-event-004',
     'Workshop: KYC Enhancement - Business Requirements',
     'Workshop cross-functional để finalize BRD cho module eKYC mới.',
     'u0000007-0000-0000-0000-000000000007',
     (NOW() + INTERVAL '1 day')::date,
     NOW() + INTERVAL '1 day',
     NOW() + INTERVAL '1 day' + INTERVAL '2 hours',
     'workshop',
     'pre',
     'p0000004-0000-0000-0000-000000000004',
     'd0000003-0000-0000-0000-000000000003',
     'Phòng Training - Tầng 3',
     'https://teams.microsoft.com/l/meetup-join/workshop-004'),

    -- Meeting 5: Daily Standup (POST phase - đã họp sáng nay)
    ('m0000005-0000-0000-0000-000000000005',
     'outlook-event-005',
     'Daily Standup - Core Banking Team',
     'Daily standup 15 phút: Yesterday, Today, Blockers.',
     'u0000005-0000-0000-0000-000000000005',
     (NOW() - INTERVAL '4 hours')::date,
     NOW() - INTERVAL '4 hours',
     NOW() - INTERVAL '3 hours 45 minutes',
     'daily',
     'post',
     'p0000001-0000-0000-0000-000000000001',
     'd0000002-0000-0000-0000-000000000002',
     'Online - Microsoft Teams',
     'https://teams.microsoft.com/l/meetup-join/daily-005')
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 4. MEETING PARTICIPANTS
-- ============================================

INSERT INTO meeting_participant (meeting_id, user_id, role, response_status, attended) VALUES
    -- Steering Committee participants
    ('m0000001-0000-0000-0000-000000000001', 'u0000001-0000-0000-0000-000000000001', 'organizer', 'accepted', true),
    ('m0000001-0000-0000-0000-000000000001', 'u0000004-0000-0000-0000-000000000004', 'required', 'accepted', true),
    ('m0000001-0000-0000-0000-000000000001', 'u0000005-0000-0000-0000-000000000005', 'required', 'accepted', true),
    ('m0000001-0000-0000-0000-000000000001', 'u0000007-0000-0000-0000-000000000007', 'required', 'accepted', true),
    ('m0000001-0000-0000-0000-000000000001', 'u0000009-0000-0000-0000-000000000009', 'required', 'accepted', true),
    ('m0000001-0000-0000-0000-000000000001', 'u0000003-0000-0000-0000-000000000003', 'attendee', 'accepted', true),
    
    -- Weekly Status participants
    ('m0000002-0000-0000-0000-000000000002', 'u0000002-0000-0000-0000-000000000002', 'organizer', 'accepted', true),
    ('m0000002-0000-0000-0000-000000000002', 'u0000006-0000-0000-0000-000000000006', 'required', 'accepted', true),
    ('m0000002-0000-0000-0000-000000000002', 'u0000008-0000-0000-0000-000000000008', 'required', 'accepted', true),
    ('m0000002-0000-0000-0000-000000000002', 'u0000001-0000-0000-0000-000000000001', 'optional', 'accepted', true),
    
    -- Risk Review participants
    ('m0000003-0000-0000-0000-000000000003', 'u0000009-0000-0000-0000-000000000009', 'organizer', 'accepted', false),
    ('m0000003-0000-0000-0000-000000000003', 'u0000010-0000-0000-0000-000000000010', 'required', 'accepted', false),
    ('m0000003-0000-0000-0000-000000000003', 'u0000001-0000-0000-0000-000000000001', 'required', 'accepted', false),
    ('m0000003-0000-0000-0000-000000000003', 'u0000005-0000-0000-0000-000000000005', 'required', 'accepted', false),
    
    -- Workshop participants
    ('m0000004-0000-0000-0000-000000000004', 'u0000007-0000-0000-0000-000000000007', 'organizer', 'accepted', false),
    ('m0000004-0000-0000-0000-000000000004', 'u0000008-0000-0000-0000-000000000008', 'required', 'accepted', false),
    ('m0000004-0000-0000-0000-000000000004', 'u0000003-0000-0000-0000-000000000003', 'required', 'accepted', false),
    ('m0000004-0000-0000-0000-000000000004', 'u0000010-0000-0000-0000-000000000010', 'required', 'tentative', false),
    ('m0000004-0000-0000-0000-000000000004', 'u0000006-0000-0000-0000-000000000006', 'optional', 'pending', false)
ON CONFLICT DO NOTHING;

-- ============================================
-- 5. PRE-MEETING: Agenda, Pre-read Documents, Questions
-- ============================================

-- Agenda for upcoming Risk Review meeting
INSERT INTO agenda_proposed (id, meeting_id, generated_agenda, status, approved_by, approved_at) VALUES
    ('a0000001-0000-0000-0000-000000000001',
     'm0000003-0000-0000-0000-000000000003',
     '[
        {"item": "1. Opening & Roll Call", "duration_min": 5, "presenter": "Bùi Văn I"},
        {"item": "2. Review Integration Architecture", "duration_min": 15, "presenter": "Hoàng Thị E"},
        {"item": "3. Risk Assessment Results", "duration_min": 20, "presenter": "Đặng Thị K"},
        {"item": "4. Compliance Requirements Checklist", "duration_min": 15, "presenter": "Đặng Thị K"},
        {"item": "5. Mitigation Plan Discussion", "duration_min": 20, "presenter": "All"},
        {"item": "6. Action Items & Next Steps", "duration_min": 5, "presenter": "Nguyễn Văn A"}
     ]'::jsonb,
     'approved',
     'u0000009-0000-0000-0000-000000000009',
     NOW() - INTERVAL '1 day')
ON CONFLICT (id) DO NOTHING;

-- Pre-read documents suggested by RAG
INSERT INTO preread_document (id, meeting_id, title, source, url, snippet, relevance_score, status) VALUES
    ('pr000001-0000-0000-0000-000000000001', 'm0000003-0000-0000-0000-000000000003', 
     'LOS-CoreBanking Integration Architecture v2.1', 'SharePoint', 
     'https://lpbank.sharepoint.com/sites/tech/docs/los-cb-integration-v21.pdf',
     'Tài liệu mô tả kiến trúc tích hợp giữa hệ thống LOS và Core Banking mới, bao gồm API specifications, data flow, và security requirements.',
     0.95, 'accepted'),
    
    ('pr000002-0000-0000-0000-000000000002', 'm0000003-0000-0000-0000-000000000003',
     'Risk Assessment Template - System Integration', 'LOffice',
     'https://loffice.lpbank.vn/docs/risk-assessment-template.docx',
     'Template đánh giá rủi ro cho các dự án tích hợp hệ thống, bao gồm checklist 50+ items.',
     0.88, 'accepted'),
    
    ('pr000003-0000-0000-0000-000000000003', 'm0000003-0000-0000-0000-000000000003',
     'NHNN Circular 09/2020 - IT Risk Management', 'Wiki',
     'https://wiki.lpbank.vn/compliance/nhnn-circular-09-2020',
     'Thông tư 09/2020/TT-NHNN quy định về quản lý rủi ro công nghệ thông tin trong hoạt động ngân hàng.',
     0.82, 'suggested'),
    
    ('pr000004-0000-0000-0000-000000000004', 'm0000004-0000-0000-0000-000000000004',
     'eKYC BRD Draft v0.9', 'SharePoint',
     'https://lpbank.sharepoint.com/sites/business/docs/ekyc-brd-v09.docx',
     'Business Requirements Document cho module eKYC, bao gồm use cases, user journeys, và acceptance criteria.',
     0.92, 'accepted'),
     
    ('pr000005-0000-0000-0000-000000000005', 'm0000004-0000-0000-0000-000000000004',
     'KYC Policy 2024 - Updated', 'LOffice',
     'https://loffice.lpbank.vn/policies/kyc-policy-2024.pdf',
     'Chính sách KYC cập nhật theo quy định mới của NHNN, bao gồm requirements cho remote onboarding.',
     0.89, 'suggested')
ON CONFLICT (id) DO NOTHING;

-- Pre-meeting questions from participants
INSERT INTO pre_meeting_question (id, meeting_id, user_id, question, type, status) VALUES
    ('pq000001-0000-0000-0000-000000000001', 'm0000003-0000-0000-0000-000000000003',
     'u0000005-0000-0000-0000-000000000005',
     'API Gateway hiện tại có đáp ứng được throughput dự kiến 500 TPS không? Cần benchmark lại.',
     'question', 'open'),
    
    ('pq000002-0000-0000-0000-000000000002', 'm0000003-0000-0000-0000-000000000003',
     'u0000010-0000-0000-0000-000000000010',
     'Cần xác nhận lại data retention policy cho transaction logs - 7 năm hay 10 năm theo NHNN?',
     'risk', 'open'),
     
    ('pq000003-0000-0000-0000-000000000003', 'm0000004-0000-0000-0000-000000000004',
     'u0000003-0000-0000-0000-000000000003',
     'Xin demo flow eKYC với NFC chip reading từ CCCD gắn chip.',
     'demo_request', 'open')
ON CONFLICT (id) DO NOTHING;

-- AI Suggestions for meetings
INSERT INTO meeting_suggestion (id, meeting_id, suggestion_type, content, reference_url, reason, confidence_score, status) VALUES
    ('ms000001-0000-0000-0000-000000000001', 'm0000003-0000-0000-0000-000000000003',
     'person', 'Nguyễn Thị M - Security Architect',
     NULL,
     'Cuộc họp liên quan đến integration security, nên mời Security Architect để review API security design.',
     0.85, 'pending'),
    
    ('ms000002-0000-0000-0000-000000000002', 'm0000003-0000-0000-0000-000000000003',
     'document', 'Penetration Test Report - Core Banking API',
     'https://lpbank.sharepoint.com/sites/security/pentest-cb-api-2024.pdf',
     'Báo cáo pentest gần nhất cho Core Banking API, relevant cho việc đánh giá rủi ro tích hợp.',
     0.78, 'accepted'),
     
    ('ms000003-0000-0000-0000-000000000003', 'm0000004-0000-0000-0000-000000000004',
     'policy', 'AML/CFT Guidelines for Digital Onboarding',
     'https://wiki.lpbank.vn/compliance/aml-digital-onboarding',
     'Workshop về eKYC cần tham khảo guidelines về AML/CFT cho digital onboarding.',
     0.81, 'pending')
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 6. IN-MEETING: Transcript for Steering Committee (completed meeting)
-- ============================================

INSERT INTO transcript_chunk (id, meeting_id, chunk_index, start_time, end_time, speaker, speaker_user_id, text, confidence, language) VALUES
    -- Opening
    ('tc000001-0000-0000-0000-000000000001', 'm0000001-0000-0000-0000-000000000001', 1, 0, 45,
     'Nguyễn Văn A', 'u0000001-0000-0000-0000-000000000001',
     'Xin chào các anh chị, hôm nay chúng ta họp Steering Committee cho dự án Core Banking Q4. Xin mời anh Phạm Văn D báo cáo tình hình tiến độ.',
     0.95, 'vi'),
    
    ('tc000002-0000-0000-0000-000000000002', 'm0000001-0000-0000-0000-000000000001', 2, 46, 180,
     'Phạm Văn D', 'u0000004-0000-0000-0000-000000000004',
     'Cảm ơn anh A. Hiện tại dự án Core Banking đang ở milestone 3, tiến độ overall là 68%. Module Account Management đã hoàn thành UAT tuần trước. Module Transaction Processing đang trong giai đoạn SIT, dự kiến hoàn thành vào 15/12. Tuy nhiên, chúng ta đang gặp một số issues với performance của batch processing, cần thêm 2 tuần để optimize.',
     0.92, 'vi'),
    
    ('tc000003-0000-0000-0000-000000000003', 'm0000001-0000-0000-0000-000000000001', 3, 181, 240,
     'Vũ Văn G', 'u0000007-0000-0000-0000-000000000007',
     'Anh D ơi, việc delay 2 tuần có ảnh hưởng đến timeline go-live không? Business đang rất cần module này để support chiến dịch cuối năm.',
     0.94, 'vi'),
    
    ('tc000004-0000-0000-0000-000000000004', 'm0000001-0000-0000-0000-000000000001', 4, 241, 350,
     'Phạm Văn D', 'u0000004-0000-0000-0000-000000000004',
     'Nếu không có thêm resources, go-live sẽ phải lùi từ 01/01 sang 15/01. Tuy nhiên, nếu được approve thêm 2 senior developers từ team Mobile, chúng ta có thể giữ nguyên timeline. Team Hoàng Thị E đang cần support gấp.',
     0.91, 'vi'),
    
    ('tc000005-0000-0000-0000-000000000005', 'm0000001-0000-0000-0000-000000000001', 5, 351, 420,
     'Hoàng Thị E', 'u0000005-0000-0000-0000-000000000005',
     'Đúng rồi anh. Em cần 2 người có experience với batch processing và Oracle optimization. Nếu có người từ team Mobile qua support 3-4 tuần là đủ.',
     0.93, 'vi'),
    
    ('tc000006-0000-0000-0000-000000000006', 'm0000001-0000-0000-0000-000000000001', 6, 421, 510,
     'Bùi Văn I', 'u0000009-0000-0000-0000-000000000009',
     'Tôi có concern về security của module Transaction Processing. Penetration test đã pass hết chưa? Và data encryption at rest đã implement theo standard của NHNN chưa?',
     0.94, 'vi'),
    
    ('tc000007-0000-0000-0000-000000000007', 'm0000001-0000-0000-0000-000000000001', 7, 511, 600,
     'Hoàng Thị E', 'u0000005-0000-0000-0000-000000000005',
     'Dạ anh I, pentest đã pass 95% test cases, còn 3 medium issues đang fix. Data encryption đã implement AES-256 theo chuẩn. Em sẽ gửi báo cáo chi tiết cho anh sau meeting.',
     0.92, 'vi'),
    
    ('tc000008-0000-0000-0000-000000000008', 'm0000001-0000-0000-0000-000000000001', 8, 601, 680,
     'Nguyễn Văn A', 'u0000001-0000-0000-0000-000000000001',
     'OK, tôi đề xuất chúng ta approve việc điều chuyển 2 senior developers từ team Mobile sang hỗ trợ Core Banking trong 4 tuần. Anh chị đồng ý không?',
     0.95, 'vi'),
    
    ('tc000009-0000-0000-0000-000000000009', 'm0000001-0000-0000-0000-000000000001', 9, 681, 720,
     'Vũ Văn G', 'u0000007-0000-0000-0000-000000000007',
     'Tôi đồng ý, nhưng cần đảm bảo Mobile Banking Sprint 24 không bị ảnh hưởng. Anh chị Mobile team có OK không?',
     0.93, 'vi'),
    
    ('tc000010-0000-0000-0000-000000000010', 'm0000001-0000-0000-0000-000000000001', 10, 721, 800,
     'Ngô Thị F', 'u0000006-0000-0000-0000-000000000006',
     'Team Mobile có thể adjust scope Sprint 24, đưa một số features non-critical sang Sprint 25. Chúng em sẽ re-plan và gửi updated roadmap trong ngày mai.',
     0.91, 'vi'),
    
    ('tc000011-0000-0000-0000-000000000011', 'm0000001-0000-0000-0000-000000000001', 11, 801, 900,
     'Nguyễn Văn A', 'u0000001-0000-0000-0000-000000000001',
     'Tốt lắm. Vậy chúng ta có các action items như sau: Một là, team Mobile gửi updated roadmap Sprint 24-25 vào ngày mai. Hai là, HR arrange việc điều chuyển 2 developers trước thứ Hai tuần sau. Ba là, team Core Banking gửi pentest report cho Risk team trong tuần này. Deadline cho tất cả là thứ Sáu tuần này.',
     0.94, 'vi'),
    
    ('tc000012-0000-0000-0000-000000000012', 'm0000001-0000-0000-0000-000000000001', 12, 901, 960,
     'Bùi Văn I', 'u0000009-0000-0000-0000-000000000009',
     'Tôi muốn thêm một action nữa: Cần update Risk Register với timeline mới và resource changes. Deadline cũng thứ Sáu.',
     0.92, 'vi'),
    
    ('tc000013-0000-0000-0000-000000000013', 'm0000001-0000-0000-0000-000000000001', 13, 961, 1020,
     'Nguyễn Văn A', 'u0000001-0000-0000-0000-000000000001',
     'Noted. BA team sẽ update Risk Register. Còn vấn đề gì khác không ạ? Nếu không, chúng ta kết thúc meeting. Biên bản sẽ được gửi trong vòng 2 giờ. Cảm ơn các anh chị.',
     0.95, 'vi')
ON CONFLICT (id) DO NOTHING;

-- Live recap snapshots
INSERT INTO live_recap_snapshot (id, meeting_id, snapshot_time, from_chunk_id, to_chunk_id, summary, key_points) VALUES
    ('lr000001-0000-0000-0000-000000000001', 'm0000001-0000-0000-0000-000000000001',
     NOW() - INTERVAL '90 minutes',
     'tc000001-0000-0000-0000-000000000001',
     'tc000005-0000-0000-0000-000000000005',
     'Dự án Core Banking đạt 68% tiến độ. Module Account Management hoàn thành UAT. Module Transaction Processing đang SIT, có issues performance cần thêm 2 tuần optimize. Đề xuất điều chuyển 2 senior developers từ team Mobile.',
     '["Core Banking tiến độ 68%", "Account Management hoàn thành UAT", "Transaction Processing đang SIT", "Cần thêm 2 senior developers", "Risk: delay 2 tuần nếu không có resources"]'::jsonb),
    
    ('lr000002-0000-0000-0000-000000000002', 'm0000001-0000-0000-0000-000000000001',
     NOW() - INTERVAL '75 minutes',
     'tc000006-0000-0000-0000-000000000006',
     'tc000013-0000-0000-0000-000000000013',
     'Đã approve điều chuyển resources. Pentest pass 95%, còn 3 medium issues. Data encryption đã implement AES-256. Các action items được assign với deadline thứ Sáu.',
     '["Approve điều chuyển 2 developers", "Pentest pass 95%", "AES-256 encryption implemented", "4 action items assigned", "Deadline: Thứ Sáu tuần này"]'::jsonb)
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 7. ACTION ITEMS (Extracted from transcript with traceability)
-- ============================================

INSERT INTO action_item (id, meeting_id, owner_user_id, description, deadline, priority, source_chunk_id, source_text, status, external_task_link, confirmed_by, confirmed_at) VALUES
    ('ai000001-0000-0000-0000-000000000001', 'm0000001-0000-0000-0000-000000000001',
     'u0000006-0000-0000-0000-000000000006',
     'Gửi updated roadmap Sprint 24-25 cho Mobile Banking, re-plan scope sau khi điều chuyển resources',
     CURRENT_DATE + INTERVAL '1 day',
     'high',
     'tc000010-0000-0000-0000-000000000010',
     'Team Mobile có thể adjust scope Sprint 24, đưa một số features non-critical sang Sprint 25. Chúng em sẽ re-plan và gửi updated roadmap trong ngày mai.',
     'confirmed',
     'https://planner.lpbank.vn/tasks/12345',
     'u0000001-0000-0000-0000-000000000001',
     NOW() - INTERVAL '1 hour'),
    
    ('ai000002-0000-0000-0000-000000000002', 'm0000001-0000-0000-0000-000000000001',
     'u0000002-0000-0000-0000-000000000002',
     'Coordinate với HR để arrange điều chuyển 2 senior developers từ team Mobile sang Core Banking',
     CURRENT_DATE + INTERVAL '3 days',
     'critical',
     'tc000011-0000-0000-0000-000000000011',
     'HR arrange việc điều chuyển 2 developers trước thứ Hai tuần sau.',
     'in_progress',
     'https://jira.lpbank.vn/browse/HR-456',
     'u0000001-0000-0000-0000-000000000001',
     NOW() - INTERVAL '1 hour'),
    
    ('ai000003-0000-0000-0000-000000000003', 'm0000001-0000-0000-0000-000000000001',
     'u0000005-0000-0000-0000-000000000005',
     'Gửi Penetration Test Report chi tiết cho team Risk & Compliance',
     CURRENT_DATE + INTERVAL '4 days',
     'high',
     'tc000007-0000-0000-0000-000000000007',
     'Em sẽ gửi báo cáo chi tiết cho anh sau meeting.',
     'confirmed',
     NULL,
     'u0000009-0000-0000-0000-000000000009',
     NOW() - INTERVAL '50 minutes'),
    
    ('ai000004-0000-0000-0000-000000000004', 'm0000001-0000-0000-0000-000000000001',
     'u0000003-0000-0000-0000-000000000003',
     'Update Risk Register với timeline mới và resource allocation changes',
     CURRENT_DATE + INTERVAL '4 days',
     'medium',
     'tc000012-0000-0000-0000-000000000012',
     'Cần update Risk Register với timeline mới và resource changes. Deadline cũng thứ Sáu.',
     'proposed',
     NULL,
     NULL,
     NULL),
     
    -- Action từ meeting trước đang overdue (demo pain point tracking)
    ('ai000005-0000-0000-0000-000000000005', 'm0000005-0000-0000-0000-000000000005',
     'u0000005-0000-0000-0000-000000000005',
     'Fix performance issue trong batch processing module - optimize Oracle queries',
     CURRENT_DATE - INTERVAL '3 days',
     'critical',
     NULL,
     NULL,
     'in_progress',
     'https://jira.lpbank.vn/browse/CB-789',
     'u0000004-0000-0000-0000-000000000004',
     NOW() - INTERVAL '1 week')
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 8. DECISION ITEMS (Extracted with audit trail)
-- ============================================

INSERT INTO decision_item (id, meeting_id, description, rationale, source_chunk_id, source_text, status, confirmed_by, confirmed_at) VALUES
    ('di000001-0000-0000-0000-000000000001', 'm0000001-0000-0000-0000-000000000001',
     'Approve điều chuyển 2 senior developers từ team Mobile sang team Core Banking trong 4 tuần',
     'Để đảm bảo timeline go-live 01/01 cho Core Banking, cần thêm resources để optimize batch processing performance.',
     'tc000008-0000-0000-0000-000000000008',
     'OK, tôi đề xuất chúng ta approve việc điều chuyển 2 senior developers từ team Mobile sang hỗ trợ Core Banking trong 4 tuần.',
     'confirmed',
     'u0000007-0000-0000-0000-000000000007',
     NOW() - INTERVAL '1 hour'),
    
    ('di000002-0000-0000-0000-000000000002', 'm0000001-0000-0000-0000-000000000001',
     'Team Mobile sẽ adjust scope Sprint 24, đưa non-critical features sang Sprint 25',
     'Trade-off để support Core Banking go-live đúng hạn, các features bị defer không ảnh hưởng đến business critical flows.',
     'tc000010-0000-0000-0000-000000000010',
     'Team Mobile có thể adjust scope Sprint 24, đưa một số features non-critical sang Sprint 25.',
     'confirmed',
     'u0000001-0000-0000-0000-000000000001',
     NOW() - INTERVAL '55 minutes')
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 9. RISK ITEMS (Identified during meeting)
-- ============================================

INSERT INTO risk_item (id, meeting_id, description, severity, mitigation, source_chunk_id, source_text, status, owner_user_id) VALUES
    ('ri000001-0000-0000-0000-000000000001', 'm0000001-0000-0000-0000-000000000001',
     'Go-live Core Banking có thể delay 2 tuần nếu không có đủ resources',
     'high',
     'Đã approve điều chuyển 2 senior developers từ team Mobile. Cần monitor tiến độ hàng ngày.',
     'tc000004-0000-0000-0000-000000000004',
     'Nếu không có thêm resources, go-live sẽ phải lùi từ 01/01 sang 15/01.',
     'mitigated',
     'u0000001-0000-0000-0000-000000000001'),
    
    ('ri000002-0000-0000-0000-000000000002', 'm0000001-0000-0000-0000-000000000001',
     'Còn 3 medium security issues từ Penetration Test chưa được fix',
     'medium',
     'Team Core Banking đang fix, target hoàn thành trước go-live. Cần review lại sau khi fix.',
     'tc000007-0000-0000-0000-000000000007',
     'pentest đã pass 95% test cases, còn 3 medium issues đang fix',
     'confirmed',
     'u0000009-0000-0000-0000-000000000009'),
     
    ('ri000003-0000-0000-0000-000000000003', 'm0000001-0000-0000-0000-000000000001',
     'Mobile Banking Sprint 24 có thể bị ảnh hưởng do điều chuyển resources',
     'medium',
     'Team Mobile sẽ re-plan và defer non-critical features sang Sprint 25.',
     'tc000009-0000-0000-0000-000000000009',
     'cần đảm bảo Mobile Banking Sprint 24 không bị ảnh hưởng',
     'mitigated',
     'u0000006-0000-0000-0000-000000000006')
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 10. ASK-AI QUERIES (RAG demo during meeting)
-- ============================================

INSERT INTO ask_ai_query (id, meeting_id, user_id, query_text, answer_text, citations, model_used, latency_ms) VALUES
    ('aq000001-0000-0000-0000-000000000001', 'm0000001-0000-0000-0000-000000000001',
     'u0000009-0000-0000-0000-000000000009',
     'Data retention policy cho transaction logs theo quy định NHNN là bao nhiêu năm?',
     'Theo Thông tư 09/2020/TT-NHNN về quản lý rủi ro CNTT, thời gian lưu trữ dữ liệu giao dịch (transaction logs) tối thiểu là **10 năm** kể từ ngày phát sinh giao dịch. Đặc biệt, đối với các giao dịch liên quan đến AML/CFT, thời gian lưu trữ là **ít nhất 5 năm** sau khi kết thúc mối quan hệ với khách hàng.',
     '[{"doc_id": "doc-001", "title": "Thông tư 09/2020/TT-NHNN", "snippet": "Điều 15: Thời gian lưu trữ dữ liệu giao dịch tối thiểu 10 năm...", "page": 12}]'::jsonb,
     'gpt-4o',
     1250),
    
    ('aq000002-0000-0000-0000-000000000002', 'm0000001-0000-0000-0000-000000000001',
     'u0000007-0000-0000-0000-000000000007',
     'CR-2024-015 về việc thay đổi API Gateway đã được approve chưa?',
     'CR-2024-015 (Change Request thay đổi API Gateway từ Kong sang AWS API Gateway) đã được **approved** vào ngày 15/10/2024 trong cuộc họp Change Advisory Board. Người approve: CTO Phạm Văn D. Implementation đã hoàn thành 80%, dự kiến go-live cùng Core Banking.',
     '[{"doc_id": "doc-002", "title": "Change Request CR-2024-015", "snippet": "Status: Approved. Approval Date: 15/10/2024...", "page": 1}, {"doc_id": "doc-003", "title": "CAB Meeting Minutes 15/10/2024", "snippet": "CR-2024-015 được approve với điều kiện...", "page": 3}]'::jsonb,
     'gpt-4o',
     980)
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 11. TOOL CALL LOGS (Integration demo)
-- ============================================

INSERT INTO tool_call_log (id, meeting_id, user_id, tool_name, action, request_payload, response_payload, status, execution_time_ms) VALUES
    ('tl000001-0000-0000-0000-000000000001', 'm0000001-0000-0000-0000-000000000001',
     'u0000001-0000-0000-0000-000000000001',
     'planner',
     'create_task',
     '{"title": "Gửi updated roadmap Sprint 24-25", "assignee": "ngothif@lpbank.vn", "due_date": "2024-12-06", "priority": "high"}'::jsonb,
     '{"task_id": "12345", "status": "created", "url": "https://planner.lpbank.vn/tasks/12345"}'::jsonb,
     'success',
     450),
    
    ('tl000002-0000-0000-0000-000000000002', 'm0000001-0000-0000-0000-000000000001',
     'u0000001-0000-0000-0000-000000000001',
     'jira',
     'create_issue',
     '{"project": "HR", "type": "Task", "summary": "Điều chuyển 2 developers sang Core Banking", "assignee": "tranthib@lpbank.vn"}'::jsonb,
     '{"issue_key": "HR-456", "status": "created", "url": "https://jira.lpbank.vn/browse/HR-456"}'::jsonb,
     'success',
     620),
    
    ('tl000003-0000-0000-0000-000000000003', 'm0000001-0000-0000-0000-000000000001',
     'u0000005-0000-0000-0000-000000000005',
     'sharepoint',
     'open_document',
     '{"doc_url": "https://lpbank.sharepoint.com/sites/security/pentest-cb-api-2024.pdf"}'::jsonb,
     '{"status": "opened", "doc_title": "Penetration Test Report - Core Banking API"}'::jsonb,
     'success',
     380)
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 12. POST-MEETING: Minutes & Distribution
-- ============================================

INSERT INTO meeting_minutes (id, meeting_id, version, minutes_text, minutes_markdown, executive_summary, status, approved_by, approved_at) VALUES
    ('mm000001-0000-0000-0000-000000000001', 'm0000001-0000-0000-0000-000000000001',
     1,
     'BIÊN BẢN HỌP STEERING COMMITTEE - CORE BANKING Q4 2024

Thời gian: [Ngày họp], 14:00 - 15:00
Địa điểm: Phòng họp VIP - Tầng 15
Chủ trì: Nguyễn Văn A - Head of PMO

THÀNH PHẦN THAM DỰ:
- Nguyễn Văn A - Head of PMO (Chủ trì)
- Phạm Văn D - CTO
- Hoàng Thị E - Tech Lead Core Banking
- Vũ Văn G - Business Director
- Bùi Văn I - Chief Risk Officer
- Lê Văn C - BA Lead (Thư ký)

NỘI DUNG:

1. BÁO CÁO TIẾN ĐỘ
- Tiến độ overall: 68%
- Module Account Management: Hoàn thành UAT
- Module Transaction Processing: Đang SIT, có issues performance

2. CÁC VẤN ĐỀ THẢO LUẬN
- Cần thêm resources để optimize batch processing
- Timeline go-live có risk delay 2 tuần

3. CÁC QUYẾT ĐỊNH
[QĐ-001] Approve điều chuyển 2 senior developers từ team Mobile sang Core Banking (4 tuần)
[QĐ-002] Team Mobile adjust scope Sprint 24, defer non-critical features sang Sprint 25

4. ACTION ITEMS
[AI-001] Team Mobile gửi updated roadmap - Owner: Ngô Thị F - Deadline: Ngày mai
[AI-002] HR arrange điều chuyển developers - Owner: Trần Thị B - Deadline: Thứ Hai tuần sau
[AI-003] Gửi Pentest Report cho Risk team - Owner: Hoàng Thị E - Deadline: Thứ Sáu
[AI-004] Update Risk Register - Owner: Lê Văn C - Deadline: Thứ Sáu

5. RỦI RO ĐÃ NHẬN DIỆN
[R-001] HIGH: Go-live delay nếu không đủ resources → Đã mitigate bằng việc điều chuyển resources
[R-002] MEDIUM: 3 security issues từ Pentest → Đang fix

Cuộc họp kết thúc lúc 15:00.
Thư ký: Lê Văn C',
     
     '# Biên bản họp Steering Committee - Core Banking Q4 2024

## Thông tin chung
- **Thời gian:** [Ngày họp], 14:00 - 15:00
- **Địa điểm:** Phòng họp VIP - Tầng 15
- **Chủ trì:** Nguyễn Văn A - Head of PMO

## Thành phần tham dự
| Họ tên | Chức vụ | Vai trò |
|--------|---------|---------|
| Nguyễn Văn A | Head of PMO | Chủ trì |
| Phạm Văn D | CTO | Tham dự |
| Hoàng Thị E | Tech Lead Core Banking | Báo cáo |
| Vũ Văn G | Business Director | Tham dự |
| Bùi Văn I | Chief Risk Officer | Tham dự |
| Lê Văn C | BA Lead | Thư ký |

## Quyết định
| ID | Nội dung | Người phê duyệt |
|----|----------|-----------------|
| QĐ-001 | Approve điều chuyển 2 senior developers từ team Mobile sang Core Banking trong 4 tuần | Vũ Văn G |
| QĐ-002 | Team Mobile adjust scope Sprint 24, defer non-critical features sang Sprint 25 | Nguyễn Văn A |

## Action Items
| ID | Mô tả | Owner | Deadline | Trạng thái |
|----|-------|-------|----------|------------|
| AI-001 | Gửi updated roadmap Sprint 24-25 | Ngô Thị F | Ngày mai | 🟡 In Progress |
| AI-002 | Coordinate điều chuyển developers với HR | Trần Thị B | Thứ Hai tuần sau | 🟡 In Progress |
| AI-003 | Gửi Pentest Report cho Risk team | Hoàng Thị E | Thứ Sáu | ✅ Confirmed |
| AI-004 | Update Risk Register | Lê Văn C | Thứ Sáu | ⚪ Proposed |

## Rủi ro
| ID | Mô tả | Mức độ | Biện pháp |
|----|-------|--------|-----------|
| R-001 | Go-live delay 2 tuần nếu không đủ resources | 🔴 HIGH | Đã approve điều chuyển resources |
| R-002 | 3 medium security issues từ Pentest | 🟡 MEDIUM | Đang fix, target trước go-live |',
     
     'Dự án Core Banking đạt 68% tiến độ. Đã approve điều chuyển 2 senior developers từ team Mobile để support optimization. 4 action items được giao với deadline trong tuần. 2 risks được identify và có mitigation plan.',
     'approved',
     'u0000007-0000-0000-0000-000000000007',
     NOW() - INTERVAL '30 minutes')
ON CONFLICT (id) DO NOTHING;

-- Minutes distribution log
INSERT INTO minutes_distribution_log (id, minutes_id, meeting_id, user_id, channel, recipient_email, status) VALUES
    ('md000001-0000-0000-0000-000000000001', 'mm000001-0000-0000-0000-000000000001', 'm0000001-0000-0000-0000-000000000001', 'u0000004-0000-0000-0000-000000000004', 'email', 'phamvand@lpbank.vn', 'delivered'),
    ('md000002-0000-0000-0000-000000000002', 'mm000001-0000-0000-0000-000000000001', 'm0000001-0000-0000-0000-000000000001', 'u0000005-0000-0000-0000-000000000005', 'email', 'hoangthie@lpbank.vn', 'delivered'),
    ('md000003-0000-0000-0000-000000000003', 'mm000001-0000-0000-0000-000000000001', 'm0000001-0000-0000-0000-000000000001', 'u0000007-0000-0000-0000-000000000007', 'email', 'vuvang@lpbank.vn', 'read'),
    ('md000004-0000-0000-0000-000000000004', 'mm000001-0000-0000-0000-000000000001', 'm0000001-0000-0000-0000-000000000001', 'u0000009-0000-0000-0000-000000000009', 'teams', 'buivani@lpbank.vn', 'delivered'),
    ('md000005-0000-0000-0000-000000000005', 'mm000001-0000-0000-0000-000000000001', 'm0000001-0000-0000-0000-000000000001', 'u0000006-0000-0000-0000-000000000006', 'email', 'ngothif@lpbank.vn', 'sent')
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 13. TASK SYNC & REMINDERS
-- ============================================

INSERT INTO task_sync_log (id, action_item_id, platform, external_task_id, sync_type, status, request_payload) VALUES
    ('ts000001-0000-0000-0000-000000000001', 'ai000001-0000-0000-0000-000000000001', 'planner', '12345', 'create', 'success',
     '{"title": "Gửi updated roadmap Sprint 24-25", "bucket": "Core Banking Support"}'::jsonb),
    ('ts000002-0000-0000-0000-000000000002', 'ai000002-0000-0000-0000-000000000002', 'jira', 'HR-456', 'create', 'success',
     '{"project": "HR", "issueType": "Task"}'::jsonb),
    ('ts000003-0000-0000-0000-000000000003', 'ai000005-0000-0000-0000-000000000005', 'jira', 'CB-789', 'update', 'success',
     '{"status": "In Progress", "comment": "Đang optimize Oracle queries"}'::jsonb)
ON CONFLICT (id) DO NOTHING;

-- Deadline reminders (demo overdue tracking)
INSERT INTO deadline_reminder_log (id, action_item_id, user_id, reminder_type, channel, sent_at) VALUES
    ('dr000001-0000-0000-0000-000000000001', 'ai000005-0000-0000-0000-000000000005', 'u0000005-0000-0000-0000-000000000005', '1day', 'teams', NOW() - INTERVAL '4 days'),
    ('dr000002-0000-0000-0000-000000000002', 'ai000005-0000-0000-0000-000000000005', 'u0000005-0000-0000-0000-000000000005', 'overdue', 'email', NOW() - INTERVAL '2 days'),
    ('dr000003-0000-0000-0000-000000000003', 'ai000005-0000-0000-0000-000000000005', 'u0000004-0000-0000-0000-000000000004', 'overdue', 'email', NOW() - INTERVAL '2 days')
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 14. HIGHLIGHT CLIPS
-- ============================================

INSERT INTO highlight_clip (id, meeting_id, start_time, end_time, reason, title, description, transcript_text) VALUES
    ('hc000001-0000-0000-0000-000000000001', 'm0000001-0000-0000-0000-000000000001',
     601, 720,
     'decision',
     'Quyết định điều chuyển resources',
     'Thời điểm quan trọng khi Steering Committee approve việc điều chuyển 2 developers và adjust scope Sprint 24.',
     'OK, tôi đề xuất chúng ta approve việc điều chuyển 2 senior developers từ team Mobile sang hỗ trợ Core Banking trong 4 tuần...'),
    
    ('hc000002-0000-0000-0000-000000000002', 'm0000001-0000-0000-0000-000000000001',
     801, 960,
     'action-density',
     'Phân công Action Items',
     'Đoạn tổng hợp và phân công tất cả action items với deadlines rõ ràng.',
     'Vậy chúng ta có các action items như sau: Một là, team Mobile gửi updated roadmap...')
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 15. DOCUMENTS FOR RAG
-- ============================================

INSERT INTO document (id, title, source, source_url, file_type, content_text, metadata, organization_id, uploaded_by) VALUES
    ('dc000001-0000-0000-0000-000000000001',
     'Thông tư 09/2020/TT-NHNN - Quản lý rủi ro CNTT',
     'wiki',
     'https://wiki.lpbank.vn/compliance/nhnn-circular-09-2020',
     'pdf',
     'Thông tư quy định về quản lý rủi ro công nghệ thông tin trong hoạt động ngân hàng. Điều 15: Thời gian lưu trữ dữ liệu giao dịch tối thiểu 10 năm kể từ ngày phát sinh giao dịch...',
     '{"department": "Compliance", "tags": ["NHNN", "regulation", "IT risk"], "access_level": "internal"}'::jsonb,
     '11111111-1111-1111-1111-111111111111',
     'u0000010-0000-0000-0000-000000000010'),
    
    ('dc000002-0000-0000-0000-000000000002',
     'Change Request CR-2024-015 - API Gateway Migration',
     'sharepoint',
     'https://lpbank.sharepoint.com/sites/tech/cr/CR-2024-015.docx',
     'docx',
     'Change Request: Thay đổi API Gateway từ Kong sang AWS API Gateway. Status: Approved. Approval Date: 15/10/2024. Approver: Phạm Văn D - CTO. Impact Assessment: Medium...',
     '{"department": "Technology", "project": "CB-2024", "tags": ["CR", "API", "infrastructure"], "access_level": "tech-team"}'::jsonb,
     '11111111-1111-1111-1111-111111111111',
     'u0000005-0000-0000-0000-000000000005'),
    
    ('dc000003-0000-0000-0000-000000000003',
     'KYC Policy 2024',
     'loffice',
     'https://loffice.lpbank.vn/policies/kyc-policy-2024.pdf',
     'pdf',
     'Chính sách KYC (Know Your Customer) năm 2024. Cập nhật theo quy định mới của NHNN về định danh khách hàng từ xa. Bao gồm: eKYC requirements, video call verification, NFC chip reading từ CCCD gắn chip...',
     '{"department": "Compliance", "tags": ["KYC", "policy", "eKYC"], "access_level": "all"}'::jsonb,
     '11111111-1111-1111-1111-111111111111',
     'u0000010-0000-0000-0000-000000000010'),
     
    ('dc000004-0000-0000-0000-000000000004',
     'Penetration Test Report - Core Banking API Q3 2024',
     'sharepoint',
     'https://lpbank.sharepoint.com/sites/security/pentest-cb-api-2024.pdf',
     'pdf',
     'Báo cáo kiểm thử xâm nhập cho Core Banking API. Tổng số test cases: 150. Pass: 142 (95%). Fail: 5 (3 Medium, 2 Low). Medium issues: SQL Injection potential in search API, Insufficient rate limiting, Missing security headers...',
     '{"department": "Security", "project": "CB-2024", "tags": ["security", "pentest", "API"], "access_level": "security-team"}'::jsonb,
     '11111111-1111-1111-1111-111111111111',
     'u0000004-0000-0000-0000-000000000004')
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- 16. AUDIT LOGS
-- ============================================

INSERT INTO item_confirmation_log (id, item_type, item_id, confirmed_by, action, previous_status, new_status, comment) VALUES
    ('ic000001-0000-0000-0000-000000000001', 'action', 'ai000001-0000-0000-0000-000000000001', 'u0000001-0000-0000-0000-000000000001', 'confirm', 'proposed', 'confirmed', 'Approved and synced to Planner'),
    ('ic000002-0000-0000-0000-000000000002', 'action', 'ai000002-0000-0000-0000-000000000002', 'u0000001-0000-0000-0000-000000000001', 'confirm', 'proposed', 'in_progress', 'Created Jira ticket HR-456'),
    ('ic000003-0000-0000-0000-000000000003', 'decision', 'di000001-0000-0000-0000-000000000001', 'u0000007-0000-0000-0000-000000000007', 'confirm', 'proposed', 'confirmed', 'Business Director approved'),
    ('ic000004-0000-0000-0000-000000000004', 'risk', 'ri000001-0000-0000-0000-000000000001', 'u0000001-0000-0000-0000-000000000001', 'confirm', 'proposed', 'mitigated', 'Mitigation plan approved')
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- SUMMARY: What this mock data demonstrates
-- ============================================
-- 
-- 1. MINUTES & ACTION ITEMS PAIN:
--    - Meeting m0000001 có full transcript → AI extract actions/decisions/risks
--    - Actions có source_chunk_id → truy vết được "ai nói gì, phút nào"
--    - Action ai000005 đang OVERDUE → demo pain point tracking
--
-- 2. ACTION TRACKING PAIN:
--    - Actions sync sang Planner/Jira (tool_call_log, task_sync_log)
--    - Deadline reminders đã gửi cho action overdue
--    - Actions nằm rải rác nhiều meetings → cần centralized view
--
-- 3. INFORMATION FRAGMENTATION PAIN:
--    - Documents ở nhiều nguồn: SharePoint, LOffice, Wiki
--    - ASK-AI queries demo việc tìm policy/CR ngay trong meeting
--    - Pre-read documents gợi ý trước meeting
--
-- 4. AUDIT/GOVERNANCE:
--    - item_confirmation_log → ai confirm gì, lúc nào
--    - minutes_distribution_log → gửi cho ai, status
--    - Decisions có source_chunk_id → chứng minh được context
--
-- 5. MEETING LIFECYCLE:
--    - m0000003, m0000004: PRE phase (có agenda, pre-reads, questions)
--    - m0000002: IN phase (đang họp)
--    - m0000001, m0000005: POST phase (có minutes, highlights)
-- ============================================
