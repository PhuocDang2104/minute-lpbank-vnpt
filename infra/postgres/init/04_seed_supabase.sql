-- ============================================
-- MEETMATE SEED DATA FOR SUPABASE
-- Run this in Supabase SQL Editor
-- ============================================

-- 1. ORGANIZATION
INSERT INTO organization (id, name) VALUES
    ('11111111-1111-1111-1111-111111111111', 'LPBank - Ngân hàng Bưu điện Liên Việt')
ON CONFLICT (id) DO NOTHING;

-- 2. DEPARTMENTS
INSERT INTO department (id, organization_id, name) VALUES
    ('d0000001-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111', 'PMO - Project Management Office'),
    ('d0000002-0000-0000-0000-000000000002', '11111111-1111-1111-1111-111111111111', 'Khối Công nghệ'),
    ('d0000003-0000-0000-0000-000000000003', '11111111-1111-1111-1111-111111111111', 'Khối Kinh doanh'),
    ('d0000004-0000-0000-0000-000000000004', '11111111-1111-1111-1111-111111111111', 'Khối Risk & Compliance'),
    ('d0000005-0000-0000-0000-000000000005', '11111111-1111-1111-1111-111111111111', 'Khối Vận hành')
ON CONFLICT (id) DO NOTHING;

-- 3. PROJECTS (fixed UUIDs - use hex only)
INSERT INTO project (id, organization_id, name, code) VALUES
    ('a0000001-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111', 'Core Banking Modernization', 'CB-2024'),
    ('a0000002-0000-0000-0000-000000000002', '11111111-1111-1111-1111-111111111111', 'Mobile Banking 3.0', 'MB-2024'),
    ('a0000003-0000-0000-0000-000000000003', '11111111-1111-1111-1111-111111111111', 'Loan Origination System', 'LOS-2024'),
    ('a0000004-0000-0000-0000-000000000004', '11111111-1111-1111-1111-111111111111', 'KYC Enhancement', 'KYC-2024')
ON CONFLICT (id) DO NOTHING;

-- 4. USERS (fixed UUIDs)
INSERT INTO user_account (id, email, display_name, role, organization_id, department_id) VALUES
    ('b0000001-0000-0000-0000-000000000001', 'nguyenvana@lpbank.vn', 'Nguyễn Văn A - Head of PMO', 'PMO', '11111111-1111-1111-1111-111111111111', 'd0000001-0000-0000-0000-000000000001'),
    ('b0000002-0000-0000-0000-000000000002', 'tranthib@lpbank.vn', 'Trần Thị B - Senior PM', 'PMO', '11111111-1111-1111-1111-111111111111', 'd0000001-0000-0000-0000-000000000001'),
    ('b0000003-0000-0000-0000-000000000003', 'levanc@lpbank.vn', 'Lê Văn C - BA Lead', 'user', '11111111-1111-1111-1111-111111111111', 'd0000001-0000-0000-0000-000000000001'),
    ('b0000004-0000-0000-0000-000000000004', 'phamvand@lpbank.vn', 'Phạm Văn D - CTO', 'admin', '11111111-1111-1111-1111-111111111111', 'd0000002-0000-0000-0000-000000000002'),
    ('b0000005-0000-0000-0000-000000000005', 'hoangthie@lpbank.vn', 'Hoàng Thị E - Tech Lead Core Banking', 'user', '11111111-1111-1111-1111-111111111111', 'd0000002-0000-0000-0000-000000000002'),
    ('b0000006-0000-0000-0000-000000000006', 'ngothif@lpbank.vn', 'Ngô Thị F - Tech Lead Mobile', 'user', '11111111-1111-1111-1111-111111111111', 'd0000002-0000-0000-0000-000000000002'),
    ('b0000007-0000-0000-0000-000000000007', 'vuvang@lpbank.vn', 'Vũ Văn G - Business Director', 'chair', '11111111-1111-1111-1111-111111111111', 'd0000003-0000-0000-0000-000000000003'),
    ('b0000008-0000-0000-0000-000000000008', 'dothih@lpbank.vn', 'Đỗ Thị H - Product Owner', 'user', '11111111-1111-1111-1111-111111111111', 'd0000003-0000-0000-0000-000000000003'),
    ('b0000009-0000-0000-0000-000000000009', 'buivani@lpbank.vn', 'Bùi Văn I - Chief Risk Officer', 'chair', '11111111-1111-1111-1111-111111111111', 'd0000004-0000-0000-0000-000000000004'),
    ('b0000010-0000-0000-0000-000000000010', 'dangthik@lpbank.vn', 'Đặng Thị K - Compliance Manager', 'user', '11111111-1111-1111-1111-111111111111', 'd0000004-0000-0000-0000-000000000004'),
    -- Test users
    ('b0000011-0000-0000-0000-000000000011', 'hoaianthai345@gmail.com', 'Hoài An Thái', 'admin', '11111111-1111-1111-1111-111111111111', 'd0000001-0000-0000-0000-000000000001'),
    ('b0000012-0000-0000-0000-000000000012', 'test@meetmate.ai', 'Test User', 'user', '11111111-1111-1111-1111-111111111111', 'd0000001-0000-0000-0000-000000000001')
ON CONFLICT (id) DO NOTHING;

-- 5. MEETINGS (fixed UUIDs)
INSERT INTO meeting (id, title, description, organizer_id, start_time, end_time, meeting_type, phase, project_id, department_id, location, teams_link) VALUES
    -- Meeting 1: Steering Committee (POST phase)
    ('c0000001-0000-0000-0000-000000000001', 
     'Steering Committee - Core Banking Q4 2024', 
     'Họp chỉ đạo dự án Core Banking: Review tiến độ, budget, risks.',
     'b0000001-0000-0000-0000-000000000001',
     NOW() - INTERVAL '2 hours',
     NOW() - INTERVAL '1 hour',
     'steering',
     'post',
     'a0000001-0000-0000-0000-000000000001',
     'd0000001-0000-0000-0000-000000000001',
     'Phòng họp VIP - Tầng 15',
     'https://teams.microsoft.com/l/meetup-join/steering-001'),
    
    -- Meeting 2: Weekly Status (IN phase)
    ('c0000002-0000-0000-0000-000000000002',
     'Weekly Project Status - Mobile Banking Sprint 23',
     'Review sprint 23, demo features, discuss blockers.',
     'b0000002-0000-0000-0000-000000000002',
     NOW() - INTERVAL '30 minutes',
     NOW() + INTERVAL '30 minutes',
     'weekly_status',
     'in',
     'a0000002-0000-0000-0000-000000000002',
     'd0000002-0000-0000-0000-000000000002',
     'Online - Microsoft Teams',
     'https://teams.microsoft.com/l/meetup-join/weekly-002'),
    
    -- Meeting 3: Risk Review (PRE phase)
    ('c0000003-0000-0000-0000-000000000003',
     'Risk Review - LOS Integration với Core Banking',
     'Đánh giá rủi ro tích hợp LOS với Core Banking mới.',
     'b0000009-0000-0000-0000-000000000009',
     NOW() + INTERVAL '2 hours',
     NOW() + INTERVAL '3 hours',
     'risk_review',
     'pre',
     'a0000003-0000-0000-0000-000000000003',
     'd0000004-0000-0000-0000-000000000004',
     'Phòng họp Risk - Tầng 12',
     'https://teams.microsoft.com/l/meetup-join/risk-003'),
    
    -- Meeting 4: Workshop (PRE phase)
    ('c0000004-0000-0000-0000-000000000004',
     'Workshop: KYC Enhancement - Business Requirements',
     'Workshop cross-functional để finalize BRD cho module eKYC mới.',
     'b0000007-0000-0000-0000-000000000007',
     NOW() + INTERVAL '1 day' + INTERVAL '9 hours',
     NOW() + INTERVAL '1 day' + INTERVAL '11 hours',
     'workshop',
     'pre',
     'a0000004-0000-0000-0000-000000000004',
     'd0000003-0000-0000-0000-000000000003',
     'Phòng Training - Tầng 3',
     'https://teams.microsoft.com/l/meetup-join/workshop-004'),
    
    -- Meeting 5: Daily Standup (POST phase)
    ('c0000005-0000-0000-0000-000000000005',
     'Daily Standup - Core Banking Team',
     'Daily standup 15 phút: Yesterday, Today, Blockers.',
     'b0000005-0000-0000-0000-000000000005',
     NOW() - INTERVAL '4 hours',
     NOW() - INTERVAL '3 hours' - INTERVAL '45 minutes',
     'daily',
     'post',
     'a0000001-0000-0000-0000-000000000001',
     'd0000002-0000-0000-0000-000000000002',
     'Online - Microsoft Teams',
     'https://teams.microsoft.com/l/meetup-join/daily-005')
ON CONFLICT (id) DO NOTHING;

-- 6. MEETING PARTICIPANTS
INSERT INTO meeting_participant (meeting_id, user_id, role) VALUES
    -- Steering Committee participants
    ('c0000001-0000-0000-0000-000000000001', 'b0000001-0000-0000-0000-000000000001', 'organizer'),
    ('c0000001-0000-0000-0000-000000000001', 'b0000004-0000-0000-0000-000000000004', 'participant'),
    ('c0000001-0000-0000-0000-000000000001', 'b0000005-0000-0000-0000-000000000005', 'participant'),
    ('c0000001-0000-0000-0000-000000000001', 'b0000007-0000-0000-0000-000000000007', 'chair'),
    ('c0000001-0000-0000-0000-000000000001', 'b0000009-0000-0000-0000-000000000009', 'participant'),
    
    -- Weekly Status participants
    ('c0000002-0000-0000-0000-000000000002', 'b0000002-0000-0000-0000-000000000002', 'organizer'),
    ('c0000002-0000-0000-0000-000000000002', 'b0000006-0000-0000-0000-000000000006', 'participant'),
    ('c0000002-0000-0000-0000-000000000002', 'b0000008-0000-0000-0000-000000000008', 'participant'),
    
    -- Risk Review participants
    ('c0000003-0000-0000-0000-000000000003', 'b0000009-0000-0000-0000-000000000009', 'organizer'),
    ('c0000003-0000-0000-0000-000000000003', 'b0000010-0000-0000-0000-000000000010', 'participant'),
    ('c0000003-0000-0000-0000-000000000003', 'b0000001-0000-0000-0000-000000000001', 'participant'),
    ('c0000003-0000-0000-0000-000000000003', 'b0000005-0000-0000-0000-000000000005', 'participant')
ON CONFLICT DO NOTHING;

-- 7. ACTION ITEMS
INSERT INTO action_item (id, meeting_id, owner_user_id, description, deadline, priority, status, source_text) VALUES
    ('e0000001-0000-0000-0000-000000000001',
     'c0000001-0000-0000-0000-000000000001',
     'b0000006-0000-0000-0000-000000000006',
     'Gửi updated roadmap Sprint 24-25 cho Mobile Banking, re-plan scope sau khi điều chuyển resources',
     NOW() + INTERVAL '1 day',
     'high',
     'confirmed',
     'Team Mobile có thể adjust scope Sprint 24, đưa một số features non-critical sang Sprint 25.'),
    
    ('e0000002-0000-0000-0000-000000000002',
     'c0000001-0000-0000-0000-000000000001',
     'b0000002-0000-0000-0000-000000000002',
     'Coordinate với HR để arrange điều chuyển 2 senior developers từ team Mobile sang Core Banking',
     NOW() + INTERVAL '3 days',
     'critical',
     'in_progress',
     'HR arrange việc điều chuyển 2 developers trước thứ Hai tuần sau.'),
    
    ('e0000003-0000-0000-0000-000000000003',
     'c0000001-0000-0000-0000-000000000001',
     'b0000005-0000-0000-0000-000000000005',
     'Gửi Penetration Test Report chi tiết cho team Risk & Compliance',
     NOW() + INTERVAL '4 days',
     'high',
     'confirmed',
     'Em sẽ gửi báo cáo chi tiết cho anh sau meeting.')
ON CONFLICT (id) DO NOTHING;

-- 8. DECISIONS
INSERT INTO decision_item (id, meeting_id, description, rationale, confirmed_by, status) VALUES
    ('f0000001-0000-0000-0000-000000000001',
     'c0000001-0000-0000-0000-000000000001',
     'Approve điều chuyển 2 senior developers từ team Mobile sang team Core Banking trong 4 tuần',
     'Để đảm bảo timeline go-live 01/01 cho Core Banking, cần thêm resources để optimize batch processing.',
     'b0000007-0000-0000-0000-000000000007',
     'confirmed'),
    
    ('f0000002-0000-0000-0000-000000000002',
     'c0000001-0000-0000-0000-000000000001',
     'Team Mobile sẽ adjust scope Sprint 24, đưa non-critical features sang Sprint 25',
     'Trade-off để support Core Banking go-live đúng hạn.',
     'b0000001-0000-0000-0000-000000000001',
     'confirmed')
ON CONFLICT (id) DO NOTHING;

-- 9. RISKS
INSERT INTO risk_item (id, meeting_id, description, severity, mitigation, status, owner_user_id) VALUES
    ('aa000001-0000-0000-0000-000000000001',
     'c0000001-0000-0000-0000-000000000001',
     'Go-live Core Banking có thể delay 2 tuần nếu không có đủ resources',
     'high',
     'Đã approve điều chuyển 2 senior developers từ team Mobile.',
     'mitigated',
     'b0000001-0000-0000-0000-000000000001'),
    
    ('aa000002-0000-0000-0000-000000000002',
     'c0000001-0000-0000-0000-000000000001',
     'Còn 3 medium security issues từ Penetration Test chưa được fix',
     'medium',
     'Team Core Banking đang fix, target hoàn thành trước go-live.',
     'confirmed',
     'b0000009-0000-0000-0000-000000000009'),
    
    ('aa000003-0000-0000-0000-000000000003',
     'c0000001-0000-0000-0000-000000000001',
     'Mobile Banking Sprint 24 có thể bị ảnh hưởng do điều chuyển resources',
     'medium',
     'Team Mobile sẽ re-plan và defer non-critical features.',
     'mitigated',
     'b0000006-0000-0000-0000-000000000006')
ON CONFLICT (id) DO NOTHING;

-- 10. PREREAD DOCUMENTS
INSERT INTO preread_document (id, meeting_id, title, source, url, snippet, relevance_score, status) VALUES
    ('ab000001-0000-0000-0000-000000000001',
     'c0000003-0000-0000-0000-000000000003',
     'LOS-CoreBanking Integration Architecture v2.1',
     'SharePoint',
     'https://lpbank.sharepoint.com/sites/tech/docs/los-cb-integration-v21.pdf',
     'Tài liệu mô tả kiến trúc tích hợp giữa hệ thống LOS và Core Banking mới.',
     0.95,
     'accepted'),
    
    ('ab000002-0000-0000-0000-000000000002',
     'c0000003-0000-0000-0000-000000000003',
     'Risk Assessment Template - System Integration',
     'LOffice',
     'https://loffice.lpbank.vn/docs/risk-assessment-template.docx',
     'Template đánh giá rủi ro cho các dự án tích hợp hệ thống.',
     0.88,
     'accepted'),
    
    ('ab000003-0000-0000-0000-000000000003',
     'c0000003-0000-0000-0000-000000000003',
     'NHNN Circular 09/2020 - IT Risk Management',
     'Wiki',
     'https://wiki.lpbank.vn/compliance/nhnn-circular-09-2020',
     'Thông tư 09/2020/TT-NHNN quy định về quản lý rủi ro CNTT.',
     0.82,
     'suggested')
ON CONFLICT (id) DO NOTHING;

-- 11. TRANSCRIPT CHUNKS (for Meeting 1)
INSERT INTO transcript_chunk (id, meeting_id, chunk_index, start_time, end_time, speaker_user_id, text) VALUES
    ('ac000001-0000-0000-0000-000000000001',
     'c0000001-0000-0000-0000-000000000001',
     1, 0, 45,
     'b0000001-0000-0000-0000-000000000001',
     'Xin chào các anh chị, hôm nay chúng ta họp Steering Committee cho dự án Core Banking Q4.'),
    
    ('ac000002-0000-0000-0000-000000000002',
     'c0000001-0000-0000-0000-000000000001',
     2, 46, 180,
     'b0000004-0000-0000-0000-000000000004',
     'Cảm ơn anh A. Hiện tại dự án Core Banking đang ở milestone 3, tiến độ overall là 68%. Module Account Management đã hoàn thành UAT tuần trước.'),
    
    ('ac000003-0000-0000-0000-000000000003',
     'c0000001-0000-0000-0000-000000000001',
     3, 181, 240,
     'b0000007-0000-0000-0000-000000000007',
     'Anh D ơi, việc delay 2 tuần có ảnh hưởng đến timeline go-live không? Business đang rất cần module này.'),
    
    ('ac000004-0000-0000-0000-000000000004',
     'c0000001-0000-0000-0000-000000000001',
     4, 241, 350,
     'b0000004-0000-0000-0000-000000000004',
     'Nếu không có thêm resources, go-live sẽ phải lùi từ 01/01 sang 15/01. Tuy nhiên, nếu được approve thêm 2 senior developers từ team Mobile, chúng ta có thể giữ nguyên timeline.'),
    
    ('ac000005-0000-0000-0000-000000000005',
     'c0000001-0000-0000-0000-000000000001',
     5, 351, 420,
     'b0000005-0000-0000-0000-000000000005',
     'Em cần 2 người có experience với batch processing và Oracle optimization. Nếu có người từ team Mobile qua support 3-4 tuần là đủ.')
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- ADD PASSWORD_HASH COLUMN AND SET DEMO PASSWORDS
-- ============================================

-- Add password_hash column if not exists
DO $$ 
BEGIN 
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'user_account' AND column_name = 'password_hash'
    ) THEN
        ALTER TABLE user_account ADD COLUMN password_hash TEXT;
    END IF;
END $$;

-- Set demo password for all users: "demo123"
-- bcrypt hash for "demo123"
UPDATE user_account 
SET password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiLXCJJH7pWe'
WHERE password_hash IS NULL;

-- Done!
SELECT 'Seed completed successfully!' as status;
