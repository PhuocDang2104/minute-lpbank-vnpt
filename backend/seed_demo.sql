-- Enable pgcrypto for UUID generation if not enabled
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

DO $$ 
DECLARE 
    v_org_id UUID;
    v_project_id UUID;
    v_dept_id UUID;
    v_quan_id UUID;
    v_dat_id UUID;
    v_phuoc_id UUID;
    v_meeting_id UUID;
    v_minutes_id UUID;
    v_now TIMESTAMP := NOW();
BEGIN 
    -------------------------------------------------------------------------
    -- 1. Create Organization (VNPT Group)
    -------------------------------------------------------------------------
    SELECT id INTO v_org_id FROM organization WHERE name = 'VNPT Group' LIMIT 1;
    IF v_org_id IS NULL THEN 
        v_org_id := gen_random_uuid();
        INSERT INTO organization (id, name, created_at) 
        VALUES (v_org_id, 'VNPT Group', v_now);
        RAISE NOTICE 'Created Organization: VNPT Group';
    ELSE 
        RAISE NOTICE 'Organization VNPT Group already exists';
    END IF;

    -------------------------------------------------------------------------
    -- 2. Create Project (ORION)
    -------------------------------------------------------------------------
    SELECT id INTO v_project_id FROM project WHERE name = 'ORION' LIMIT 1;
    IF v_project_id IS NULL THEN 
        v_project_id := gen_random_uuid();
        INSERT INTO project (id, organization_id, name, code, description, created_at) 
        VALUES (v_project_id, v_org_id, 'ORION', 'ORION-01', 'Dự án chuyển đổi số quy mô lớn', v_now);
        RAISE NOTICE 'Created Project: ORION';
    ELSE 
        RAISE NOTICE 'Project ORION already exists';
    END IF;

    -------------------------------------------------------------------------
    -- 3. Create Users
    -------------------------------------------------------------------------
    -- Ông Quân (Chair)
    SELECT id INTO v_quan_id FROM user_account WHERE email = 'quan.chair@vnpt.vn' LIMIT 1;
    IF v_quan_id IS NULL THEN 
        v_quan_id := gen_random_uuid();
        INSERT INTO user_account (id, email, display_name, organization_id, role, is_active, created_at) 
        VALUES (v_quan_id, 'quan.chair@vnpt.vn', 'Ông Quân', v_org_id, 'chair', true, v_now);
    END IF;

    -- Ông Đạt (Director)
    SELECT id INTO v_dat_id FROM user_account WHERE email = 'dat.it@vnpt.vn' LIMIT 1;
    IF v_dat_id IS NULL THEN 
        v_dat_id := gen_random_uuid();
        INSERT INTO user_account (id, email, display_name, organization_id, role, is_active, created_at) 
        VALUES (v_dat_id, 'dat.it@vnpt.vn', 'Ông Đạt', v_org_id, 'director', true, v_now);
    END IF;

    -- Ông Phước (Risk Manager)
    SELECT id INTO v_phuoc_id FROM user_account WHERE email = 'phuoc.risk@vnpt.vn' LIMIT 1;
    IF v_phuoc_id IS NULL THEN 
        v_phuoc_id := gen_random_uuid();
        INSERT INTO user_account (id, email, display_name, organization_id, role, is_active, created_at) 
        VALUES (v_phuoc_id, 'phuoc.risk@vnpt.vn', 'Ông Phước', v_org_id, 'risk_manager', true, v_now);
    END IF;

    -------------------------------------------------------------------------
    -- 4. Create Meeting
    -------------------------------------------------------------------------
    SELECT id INTO v_meeting_id FROM meeting WHERE title = 'HỌP HỘI ĐỒNG QUẢN TRỊ DỰ ÁN ORION GIAI ĐOẠN 1' LIMIT 1;
    
    -- If meeting exists, delete it and its related data (CASCADE should handle it usually, but let's be safe/clean)
    IF v_meeting_id IS NOT NULL THEN
        DELETE FROM meeting WHERE id = v_meeting_id;
    END IF;

    -- Create new meeting
    v_meeting_id := gen_random_uuid();
    INSERT INTO meeting (
        id, title, description, organizer_id, project_id, 
        start_time, end_time, meeting_type, location, teams_link, phase,
        created_at
    ) VALUES (
        v_meeting_id,
        'HỌP HỘI ĐỒNG QUẢN TRỊ DỰ ÁN ORION GIAI ĐOẠN 1',
        'Trình và quyết nghị các nội dung giai đoạn 1 của ORION: trần ngân sách, phương án đưa dự toán về đúng trần, điều kiện tuân thủ bắt buộc và cơ chế giám sát/báo cáo.',
        v_quan_id,
        v_project_id,
        '2025-12-01 09:00:00+07',
        '2025-12-01 11:30:00+07',
        'STEERING COMMITTEE',
        'MICROSOFT TEAMS',
        'https://teams.live.com/meet/9392620868227?p=RV8qxyF5TgYYK4joIk',
        'post',
        v_now
    );

    -------------------------------------------------------------------------
    -- 5. Participants
    -------------------------------------------------------------------------
    INSERT INTO meeting_participant (meeting_id, user_id, role, response_status, attended) VALUES
    (v_meeting_id, v_quan_id, 'organizer', 'accepted', true),
    (v_meeting_id, v_dat_id, 'attendee', 'accepted', true),
    (v_meeting_id, v_phuoc_id, 'attendee', 'accepted', true);

    -------------------------------------------------------------------------
    -- 6. Transcript Chunks
    -------------------------------------------------------------------------
    -- We approximate duration as word_count * 0.5s. Times are strictly sequential.
    INSERT INTO transcript_chunk (id, meeting_id, chunk_index, speaker, text, time_start, time_end, confidence, created_at) VALUES 
    (gen_random_uuid(), v_meeting_id, 0, 'Ông Quân', 'Ok, mình khai mạc phiên họp Hội đồng quản trị về dự án ORION giai đoạn 1 nhé. Chương trình họp gồm 3 mục: một là Ban Điều hành trình bày tổng quan ngân sách giai đoạn 1; hai là báo cáo rủi ro trọng yếu và điều kiện tuân thủ trước triển khai; ba là Hội đồng quản trị biểu quyết thông qua nghị quyết và giao nhiệm vụ triển khai. Mời anh Đạt trình bày trước.', 0.0, 30.0, 0.95, v_now),
    (gen_random_uuid(), v_meeting_id, 1, 'Ông Đạt', 'Ok, em chuyển sang phần ngân sách để Hội đồng quản trị nắm bức tranh tổng quan nhé. Tổng dự toán hiện tại là 45,43 tỷ đồng. Nhóm dự án đã chuẩn bị phương án xử lý chênh lệch theo tài liệu chung về xử lý vượt trần. Cụ thể, đề xuất kết hợp 3 phương án với Tổng giảm 0,60 tỷ, đưa dự toán về 44,83 tỷ, thấp hơn trần và không ảnh hưởng các hạng mục tuân thủ bắt buộc.', 30.0, 65.0, 0.95, v_now),
    (gen_random_uuid(), v_meeting_id, 2, 'Ông Phước', 'Ok, tôi chuyển sang phần rủi ro và điều kiện tuân thủ để Hội đồng quản trị quyết nghị kèm điều kiện triển khai nhé. Có 2 rủi ro mức độ đỏ cần điều kiện bắt buộc.', 65.0, 80.0, 0.95, v_now),
    (gen_random_uuid(), v_meeting_id, 3, 'Ông Phước', 'Rủi ro đầu tiên là công ty có rủi ro đáng báo động là vượt trần ngân sách 45,0 tỷ nếu không cập nhật dự toán kịp thời. Rủi ro này có thể làm chậm phê duyệt và dừng triển khai.', 80.0, 105.0, 0.95, v_now),
    (gen_random_uuid(), v_meeting_id, 4, 'Ông Phước', 'Rủi ro thứ hai là chưa đóng đủ các kiến nghị mức độ cao về kiểm soát truy cập, nhật ký giám sát và dữ liệu nhạy cảm. Điều kiện đề xuất là: chỉ được cấp dữ liệu thử nghiệm và triển khai vận hành thử khi đã nộp đủ minh chứng EVD-001 đến EVD-003 theo bảng theo dõi. Tôi đề nghị Hội đồng quản trị đưa các điều kiện này vào nghị quyết để làm cơ sở giám sát và báo cáo định kỳ.', 105.0, 150.0, 0.95, v_now),
    (gen_random_uuid(), v_meeting_id, 5, 'Ông Quân', 'Ok, tôi chuyển sang phần biểu quyết và giao nhiệm vụ nhé. Hội đồng quản trị ghi nhận tổng dự toán hiện tại 45,43 tỷ và thống nhất cần đưa dự toán về không vượt trần 45,0 tỷ trước ngày 15/01/2026.', 150.0, 175.0, 0.95, v_now),
    (gen_random_uuid(), v_meeting_id, 6, 'Ông Quân', 'Vậy chúng ta quyết định rằng: Hội đồng quản trị thông qua Nghị quyết 1 - phê duyệt trần ngân sách giai đoạn 1 là 45,0 tỷ.', 175.0, 190.0, 0.95, v_now),
    (gen_random_uuid(), v_meeting_id, 7, 'Ông Quân', 'Và Nghị quyết 2: thông qua điều kiện triển khai gồm yêu cầu đóng kiến nghị mức độ cao và hoàn tất kiểm thử bảo mật trước vận hành thử.', 190.0, 210.0, 0.95, v_now),
    (gen_random_uuid(), v_meeting_id, 8, 'Ông Quân', 'Tôi giao việc cho anh Đạt chịu trách nhiệm cập nhật dự toán và báo cáo lại; anh Phước theo dõi rủi ro và điều kiện tuân thủ, báo cáo định kỳ cho Hội đồng quản trị. Cuộc họp kết thúc tại đây. Cảm ơn mọi người.', 210.0, 240.0, 0.95, v_now);

    -------------------------------------------------------------------------
    -- 7. Action Items
    -------------------------------------------------------------------------
    INSERT INTO action_item (id, meeting_id, description, owner, due_date, priority, confirmed, created_at) VALUES
    (gen_random_uuid(), v_meeting_id, 'Cập nhật dự toán ngân sách về 45,0 tỷ và báo cáo lại', 'Ông Đạt', '2026-01-15 17:00:00+07', 'high', false, v_now),
    (gen_random_uuid(), v_meeting_id, 'Theo dõi rủi ro và điều kiện tuân thủ, báo cáo định kỳ', 'Ông Phước', null, 'high', false, v_now),
    (gen_random_uuid(), v_meeting_id, 'Nộp đủ minh chứng EVD-001 đến EVD-003', 'Nhóm dự án', null, 'critical', false, v_now);

    -------------------------------------------------------------------------
    -- 8. Decisions
    -------------------------------------------------------------------------
    INSERT INTO decision_item (id, meeting_id, title, rationale, created_at) VALUES
    (gen_random_uuid(), v_meeting_id, 'Phê duyệt trần ngân sách', 'Phê duyệt trần ngân sách giai đoạn 1 là 45,0 tỷ đồng.', v_now),
    (gen_random_uuid(), v_meeting_id, 'Điều kiện triển khai', 'Yêu cầu đóng kiến nghị mức độ cao và hoàn tất kiểm thử bảo mật trước vận hành thử.', v_now),
    (gen_random_uuid(), v_meeting_id, 'Phương án xử lý chênh lệch', 'Thống nhất phương án giảm 0,60 tỷ, đưa dự toán về 44,83 tỷ.', v_now);

    -------------------------------------------------------------------------
    -- 9. Risks
    -------------------------------------------------------------------------
    INSERT INTO risk_item (id, meeting_id, description, severity, created_at) VALUES
    (gen_random_uuid(), v_meeting_id, 'Vượt trần ngân sách 45,0 tỷ nếu không cập nhật kịp thời', 'critical', v_now),
    (gen_random_uuid(), v_meeting_id, 'Chưa đóng đủ kiến nghị mức độ cao về kiểm soát truy cập và dữ liệu nhạy cảm', 'critical', v_now);

    -------------------------------------------------------------------------
    -- 10. Meeting Minutes
    -------------------------------------------------------------------------
    v_minutes_id := gen_random_uuid();
    INSERT INTO meeting_minutes (
        id, meeting_id, version, minutes_text, minutes_html, minutes_markdown, executive_summary, status, generated_at
    ) VALUES (
        v_minutes_id, v_meeting_id, 1, 
        'Cuộc họp Hội đồng Quản trị dự án ORION giai đoạn 1 đã diễn ra để xem xét và quyết nghị các vấn đề trọng yếu về ngân sách và rủi ro. Hội đồng đã thông qua Nghị quyết 1 phê duyệt trần ngân sách 45,0 tỷ đồng và phương án xử lý chênh lệch 0,60 tỷ. Đồng thời, Nghị quyết 2 được thông qua với các điều kiện bắt buộc về an ninh bảo mật (đóng kiến nghị mức độ cao). Ông Đạt và Ông Phước được giao nhiệm vụ cụ thể để triển khai và giám sát tuân thủ.',
        'Cuộc họp Hội đồng Quản trị dự án ORION giai đoạn 1 đã diễn ra để xem xét và quyết nghị các vấn đề trọng yếu về ngân sách và rủi ro. Hội đồng đã thông qua Nghị quyết 1 phê duyệt trần ngân sách 45,0 tỷ đồng và phương án xử lý chênh lệch 0,60 tỷ. Đồng thời, Nghị quyết 2 được thông qua với các điều kiện bắt buộc về an ninh bảo mật (đóng kiến nghị mức độ cao). Ông Đạt và Ông Phước được giao nhiệm vụ cụ thể để triển khai và giám sát tuân thủ.',
        'Cuộc họp Hội đồng Quản trị dự án ORION giai đoạn 1 đã diễn ra để xem xét và quyết nghị các vấn đề trọng yếu về ngân sách và rủi ro. Hội đồng đã thông qua Nghị quyết 1 phê duyệt trần ngân sách 45,0 tỷ đồng và phương án xử lý chênh lệch 0,60 tỷ. Đồng thời, Nghị quyết 2 được thông qua với các điều kiện bắt buộc về an ninh bảo mật (đóng kiến nghị mức độ cao). Ông Đạt và Ông Phước được giao nhiệm vụ cụ thể để triển khai và giám sát tuân thủ.',
        'Cuộc họp Hội đồng Quản trị dự án ORION giai đoạn 1 đã diễn ra để xem xét và quyết nghị các vấn đề trọng yếu về ngân sách và rủi ro. Hội đồng đã thông qua Nghị quyết 1 phê duyệt trần ngân sách 45,0 tỷ đồng và phương án xử lý chênh lệch 0,60 tỷ. Đồng thời, Nghị quyết 2 được thông qua với các điều kiện bắt buộc về an ninh bảo mật (đóng kiến nghị mức độ cao). Ông Đạt và Ông Phước được giao nhiệm vụ cụ thể để triển khai và giám sát tuân thủ.',
        'draft', v_now
    );

    RAISE NOTICE 'SEED COMPLETED SUCCESSFULLY! Meeting ID: %', v_meeting_id;
END $$;
