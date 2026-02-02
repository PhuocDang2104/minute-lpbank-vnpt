-- ============================================
-- INSERT MINUTES TEMPLATES FROM DOCS
-- Based on Word documents in docs/minutes/
-- ============================================

-- 1. BIÊN BẢN HỌP TUÂN THỦ / KIỂM TOÁN
-- Based on: 1_BIÊN BẢN HỌP TUÂN THỦ _ KIỂM TOÁN.docx
INSERT INTO minutes_template (id, name, code, description, meeting_types, is_active, structure) VALUES
(
    uuid_generate_v4(),
    'Biên bản Họp Tuân thủ / Kiểm toán',
    'COMPLIANCE_AUDIT_V2',
    'Template chi tiết cho cuộc họp tuân thủ và kiểm toán nội bộ',
    ARRAY['compliance', 'audit', 'internal_audit'],
    TRUE,
    '{
        "sections": [
            {
                "id": "header",
                "title": "THÔNG TIN CUỘC HỌP",
                "order": 1,
                "required": true,
                "fields": [
                    {"id": "meeting_title", "label": "Tên cuộc họp", "type": "text", "required": true, "source": "meeting.title"},
                    {"id": "meeting_date", "label": "Ngày giờ họp", "type": "datetime", "required": true, "source": "meeting.start_time"},
                    {"id": "meeting_end_time", "label": "Thời gian kết thúc", "type": "datetime", "required": false, "source": "meeting.end_time"},
                    {"id": "location", "label": "Địa điểm", "type": "text", "required": false, "source": "meeting.location"},
                    {"id": "meeting_type", "label": "Loại cuộc họp", "type": "text", "required": false, "source": "meeting.meeting_type"}
                ]
            },
            {
                "id": "participants",
                "title": "THÀNH PHẦN THAM GIA",
                "order": 2,
                "required": true,
                "fields": [
                    {"id": "participants_list", "label": "Danh sách người tham gia", "type": "array", "required": true, "source": "meeting.participants"},
                    {"id": "organizer", "label": "Người chủ trì", "type": "text", "required": false, "source": "meeting.organizer"},
                    {"id": "secretary", "label": "Thư ký", "type": "text", "required": false, "source": "meeting.secretary"}
                ]
            },
            {
                "id": "agenda",
                "title": "CHƯƠNG TRÌNH HỌP",
                "order": 3,
                "required": true,
                "fields": [
                    {"id": "agenda_items", "label": "Các nội dung thảo luận", "type": "array", "required": true, "source": "ai_generated"}
                ]
            },
            {
                "id": "summary",
                "title": "TÓM TẮT CUỘC HỌP",
                "order": 4,
                "required": true,
                "fields": [
                    {"id": "executive_summary", "label": "Tóm tắt điều hành", "type": "text", "required": true, "source": "ai_generated"},
                    {"id": "key_points", "label": "Các điểm chính", "type": "array", "required": true, "source": "ai_generated"},
                    {"id": "discussion_summary", "label": "Tóm tắt thảo luận", "type": "text", "required": false, "source": "ai_generated"}
                ]
            },
            {
                "id": "compliance_issues",
                "title": "CÁC VẤN ĐỀ TUÂN THỦ",
                "order": 5,
                "required": true,
                "fields": [
                    {"id": "compliance_issues_list", "label": "Danh sách vấn đề tuân thủ", "type": "array", "required": true, "source": "ai_generated"},
                    {"id": "compliance_status", "label": "Tình trạng tuân thủ", "type": "text", "required": false, "source": "ai_generated"}
                ]
            },
            {
                "id": "audit_findings",
                "title": "PHÁT HIỆN KIỂM TOÁN",
                "order": 6,
                "required": true,
                "fields": [
                    {"id": "audit_findings_list", "label": "Danh sách phát hiện", "type": "array", "required": true, "source": "ai_generated"},
                    {"id": "audit_recommendations", "label": "Khuyến nghị", "type": "array", "required": false, "source": "ai_generated"}
                ]
            },
            {
                "id": "risks",
                "title": "RỦI RO ĐÃ NHẬN DIỆN",
                "order": 7,
                "required": true,
                "fields": [
                    {"id": "risks_list", "label": "Danh sách rủi ro", "type": "array", "required": true, "source": "ai_generated"},
                    {"id": "risk_level", "label": "Mức độ rủi ro", "type": "text", "required": false, "source": "ai_generated"}
                ]
            },
            {
                "id": "actions",
                "title": "HÀNH ĐỘNG KHẮC PHỤC",
                "order": 8,
                "required": true,
                "fields": [
                    {"id": "action_items", "label": "Danh sách hành động", "type": "array", "required": true, "source": "ai_generated"},
                    {"id": "action_owners", "label": "Người chịu trách nhiệm", "type": "array", "required": false, "source": "ai_generated"},
                    {"id": "action_deadlines", "label": "Thời hạn hoàn thành", "type": "array", "required": false, "source": "ai_generated"}
                ]
            },
            {
                "id": "decisions",
                "title": "CÁC QUYẾT ĐỊNH",
                "order": 9,
                "required": true,
                "fields": [
                    {"id": "decisions_list", "label": "Danh sách quyết định", "type": "array", "required": true, "source": "ai_generated"}
                ]
            },
            {
                "id": "next_steps",
                "title": "BƯỚC TIẾP THEO",
                "order": 10,
                "required": false,
                "fields": [
                    {"id": "next_meeting_date", "label": "Cuộc họp tiếp theo", "type": "datetime", "required": false, "source": "meeting.end_time"},
                    {"id": "follow_up_items", "label": "Các mục theo dõi", "type": "array", "required": false, "source": "ai_generated"}
                ]
            },
            {
                "id": "signatures",
                "title": "CHỮ KÝ XÁC NHẬN",
                "order": 11,
                "required": true,
                "fields": [
                    {"id": "chairman_signature", "label": "Chủ tọa", "type": "signature", "required": false},
                    {"id": "secretary_signature", "label": "Thư ký", "type": "signature", "required": false},
                    {"id": "approver_signature", "label": "Người phê duyệt", "type": "signature", "required": false}
                ]
            }
        ],
        "formatting": {
            "style": "formal",
            "language": "vi",
            "date_format": "dd/mm/yyyy",
            "time_format": "HH:mm",
            "header_style": "uppercase"
        }
    }'::jsonb
)
ON CONFLICT (code) DO NOTHING;

-- 2. BIÊN BẢN HỌP HỘI ĐỒNG QUẢN TRỊ
-- Based on: 2_BIÊN BẢN HỌP HỘI ĐỒNG QUẢN TRỊ.docx
INSERT INTO minutes_template (id, name, code, description, meeting_types, is_active, structure) VALUES
(
    uuid_generate_v4(),
    'Biên bản Họp Hội đồng Quản trị',
    'BOARD_MEETING_V2',
    'Template chi tiết cho cuộc họp Hội đồng Quản trị',
    ARRAY['board', 'governance', 'board_of_directors'],
    TRUE,
    '{
        "sections": [
            {
                "id": "header",
                "title": "THÔNG TIN CUỘC HỌP",
                "order": 1,
                "required": true,
                "fields": [
                    {"id": "meeting_title", "label": "Tên cuộc họp", "type": "text", "required": true, "source": "meeting.title"},
                    {"id": "meeting_number", "label": "Số cuộc họp", "type": "text", "required": false, "source": "meeting.code"},
                    {"id": "meeting_date", "label": "Ngày giờ họp", "type": "datetime", "required": true, "source": "meeting.start_time"},
                    {"id": "meeting_end_time", "label": "Thời gian kết thúc", "type": "datetime", "required": false, "source": "meeting.end_time"},
                    {"id": "location", "label": "Địa điểm", "type": "text", "required": false, "source": "meeting.location"},
                    {"id": "meeting_type", "label": "Loại cuộc họp", "type": "text", "required": false, "source": "meeting.meeting_type"}
                ]
            },
            {
                "id": "participants",
                "title": "THÀNH PHẦN THAM GIA",
                "order": 2,
                "required": true,
                "fields": [
                    {"id": "participants_list", "label": "Danh sách thành viên tham gia", "type": "array", "required": true, "source": "meeting.participants"},
                    {"id": "chairman", "label": "Chủ tịch HĐQT", "type": "text", "required": false, "source": "meeting.organizer"},
                    {"id": "vice_chairman", "label": "Phó Chủ tịch", "type": "text", "required": false, "source": "meeting.participants"},
                    {"id": "secretary", "label": "Thư ký", "type": "text", "required": false, "source": "meeting.secretary"},
                    {"id": "absent_members", "label": "Thành viên vắng mặt", "type": "array", "required": false, "source": "meeting.participants"}
                ]
            },
            {
                "id": "agenda",
                "title": "CHƯƠNG TRÌNH HỌP",
                "order": 3,
                "required": true,
                "fields": [
                    {"id": "agenda_items", "label": "Các nội dung thảo luận", "type": "array", "required": true, "source": "ai_generated"},
                    {"id": "agenda_summary", "label": "Tóm tắt chương trình", "type": "text", "required": false, "source": "ai_generated"}
                ]
            },
            {
                "id": "summary",
                "title": "TÓM TẮT CUỘC HỌP",
                "order": 4,
                "required": true,
                "fields": [
                    {"id": "executive_summary", "label": "Tóm tắt điều hành", "type": "text", "required": true, "source": "ai_generated"},
                    {"id": "key_points", "label": "Các điểm chính", "type": "array", "required": true, "source": "ai_generated"},
                    {"id": "discussion_summary", "label": "Tóm tắt thảo luận", "type": "text", "required": false, "source": "ai_generated"}
                ]
            },
            {
                "id": "reports",
                "title": "BÁO CÁO TRÌNH BÀY",
                "order": 5,
                "required": false,
                "fields": [
                    {"id": "reports_list", "label": "Danh sách báo cáo", "type": "array", "required": false, "source": "ai_generated"},
                    {"id": "report_presenters", "label": "Người trình bày", "type": "array", "required": false, "source": "ai_generated"}
                ]
            },
            {
                "id": "decisions",
                "title": "CÁC QUYẾT ĐỊNH",
                "order": 6,
                "required": true,
                "fields": [
                    {"id": "decisions_list", "label": "Danh sách quyết định", "type": "array", "required": true, "source": "ai_generated"},
                    {"id": "decision_votes", "label": "Kết quả biểu quyết", "type": "array", "required": false, "source": "ai_generated"},
                    {"id": "decision_resolutions", "label": "Nghị quyết", "type": "array", "required": false, "source": "ai_generated"}
                ]
            },
            {
                "id": "strategic_items",
                "title": "CÁC VẤN ĐỀ CHIẾN LƯỢC",
                "order": 7,
                "required": false,
                "fields": [
                    {"id": "strategic_discussions", "label": "Thảo luận chiến lược", "type": "array", "required": false, "source": "ai_generated"},
                    {"id": "strategic_decisions", "label": "Quyết định chiến lược", "type": "array", "required": false, "source": "ai_generated"}
                ]
            },
            {
                "id": "risks",
                "title": "RỦI RO VÀ CƠ HỘI",
                "order": 8,
                "required": false,
                "fields": [
                    {"id": "risks_list", "label": "Danh sách rủi ro", "type": "array", "required": false, "source": "ai_generated"},
                    {"id": "opportunities_list", "label": "Danh sách cơ hội", "type": "array", "required": false, "source": "ai_generated"}
                ]
            },
            {
                "id": "actions",
                "title": "CÔNG VIỆC VÀ HÀNH ĐỘNG",
                "order": 9,
                "required": true,
                "fields": [
                    {"id": "action_items", "label": "Danh sách công việc", "type": "array", "required": true, "source": "ai_generated"},
                    {"id": "action_owners", "label": "Người chịu trách nhiệm", "type": "array", "required": false, "source": "ai_generated"},
                    {"id": "action_deadlines", "label": "Thời hạn hoàn thành", "type": "array", "required": false, "source": "ai_generated"}
                ]
            },
            {
                "id": "next_meeting",
                "title": "CUỘC HỌP TIẾP THEO",
                "order": 10,
                "required": false,
                "fields": [
                    {"id": "next_meeting_date", "label": "Ngày giờ họp tiếp theo", "type": "datetime", "required": false, "source": "meeting.end_time"},
                    {"id": "next_meeting_agenda", "label": "Nội dung dự kiến", "type": "text", "required": false, "source": "ai_generated"}
                ]
            },
            {
                "id": "signatures",
                "title": "CHỮ KÝ XÁC NHẬN",
                "order": 11,
                "required": true,
                "fields": [
                    {"id": "chairman_signature", "label": "Chủ tịch HĐQT", "type": "signature", "required": false},
                    {"id": "secretary_signature", "label": "Thư ký", "type": "signature", "required": false},
                    {"id": "board_members_signatures", "label": "Các thành viên HĐQT", "type": "array", "required": false, "source": "meeting.participants"}
                ]
            }
        ],
        "formatting": {
            "style": "formal",
            "language": "vi",
            "date_format": "dd/mm/yyyy",
            "time_format": "HH:mm",
            "header_style": "uppercase",
            "numbering": true
        }
    }'::jsonb
)
ON CONFLICT (code) DO NOTHING;

-- 3. MẪU TỔI GIẢN BIÊN BẢN THEO DÕI TIẾN ĐỘ NỘI BỘ
-- Based on: 03_Mau_Toi_gian_Bien_ban_Theo_doi_tien_do_noi_bo_Tieng_Viet.docx
INSERT INTO minutes_template (id, name, code, description, meeting_types, is_active, structure) VALUES
(
    uuid_generate_v4(),
    'Mẫu Tối giản - Biên bản Theo dõi Tiến độ Nội bộ',
    'PROGRESS_REVIEW_SIMPLE',
    'Template tối giản cho cuộc họp theo dõi tiến độ dự án nội bộ',
    ARRAY['progress', 'status', 'sprint', 'internal', 'standup'],
    TRUE,
    '{
        "sections": [
            {
                "id": "header",
                "title": "THÔNG TIN CUỘC HỌP",
                "order": 1,
                "required": true,
                "fields": [
                    {"id": "meeting_title", "label": "Tên cuộc họp", "type": "text", "required": true, "source": "meeting.title"},
                    {"id": "meeting_date", "label": "Ngày giờ họp", "type": "datetime", "required": true, "source": "meeting.start_time"},
                    {"id": "meeting_end_time", "label": "Thời gian kết thúc", "type": "datetime", "required": false, "source": "meeting.end_time"},
                    {"id": "location", "label": "Địa điểm", "type": "text", "required": false, "source": "meeting.location"},
                    {"id": "project_name", "label": "Dự án", "type": "text", "required": false, "source": "meeting.project"}
                ]
            },
            {
                "id": "participants",
                "title": "THÀNH PHẦN THAM GIA",
                "order": 2,
                "required": true,
                "fields": [
                    {"id": "participants_list", "label": "Danh sách người tham gia", "type": "array", "required": true, "source": "meeting.participants"},
                    {"id": "organizer", "label": "Người chủ trì", "type": "text", "required": false, "source": "meeting.organizer"}
                ]
            },
            {
                "id": "summary",
                "title": "TÓM TẮT CUỘC HỌP",
                "order": 3,
                "required": true,
                "fields": [
                    {"id": "executive_summary", "label": "Tóm tắt", "type": "text", "required": true, "source": "ai_generated"},
                    {"id": "key_points", "label": "Các điểm chính", "type": "array", "required": true, "source": "ai_generated"}
                ]
            },
            {
                "id": "progress_status",
                "title": "TÌNH HÌNH TIẾN ĐỘ",
                "order": 4,
                "required": true,
                "fields": [
                    {"id": "completed_items", "label": "Công việc đã hoàn thành", "type": "array", "required": true, "source": "ai_generated"},
                    {"id": "in_progress_items", "label": "Công việc đang thực hiện", "type": "array", "required": true, "source": "ai_generated"},
                    {"id": "blocked_items", "label": "Công việc bị chặn", "type": "array", "required": false, "source": "ai_generated"},
                    {"id": "progress_percentage", "label": "Phần trăm hoàn thành", "type": "text", "required": false, "source": "ai_generated"}
                ]
            },
            {
                "id": "milestones",
                "title": "MỐC QUAN TRỌNG",
                "order": 5,
                "required": false,
                "fields": [
                    {"id": "milestones_list", "label": "Danh sách mốc", "type": "array", "required": false, "source": "ai_generated"},
                    {"id": "milestone_status", "label": "Tình trạng mốc", "type": "array", "required": false, "source": "ai_generated"}
                ]
            },
            {
                "id": "issues",
                "title": "VẤN ĐỀ VÀ RỦI RO",
                "order": 6,
                "required": false,
                "fields": [
                    {"id": "issues_list", "label": "Danh sách vấn đề", "type": "array", "required": false, "source": "ai_generated"},
                    {"id": "risks_list", "label": "Danh sách rủi ro", "type": "array", "required": false, "source": "ai_generated"},
                    {"id": "blockers", "label": "Các chướng ngại", "type": "array", "required": false, "source": "ai_generated"}
                ]
            },
            {
                "id": "actions",
                "title": "CÔNG VIỆC",
                "order": 7,
                "required": true,
                "fields": [
                    {"id": "action_items", "label": "Danh sách công việc", "type": "array", "required": true, "source": "ai_generated"},
                    {"id": "action_owners", "label": "Người chịu trách nhiệm", "type": "array", "required": false, "source": "ai_generated"},
                    {"id": "action_deadlines", "label": "Thời hạn", "type": "array", "required": false, "source": "ai_generated"},
                    {"id": "action_priorities", "label": "Độ ưu tiên", "type": "array", "required": false, "source": "ai_generated"}
                ]
            },
            {
                "id": "decisions",
                "title": "QUYẾT ĐỊNH",
                "order": 8,
                "required": false,
                "fields": [
                    {"id": "decisions_list", "label": "Danh sách quyết định", "type": "array", "required": false, "source": "ai_generated"}
                ]
            },
            {
                "id": "next_meeting",
                "title": "CUỘC HỌP TIẾP THEO",
                "order": 9,
                "required": false,
                "fields": [
                    {"id": "next_meeting_date", "label": "Ngày giờ họp tiếp theo", "type": "datetime", "required": false, "source": "meeting.end_time"},
                    {"id": "next_meeting_focus", "label": "Trọng tâm cuộc họp tiếp theo", "type": "text", "required": false, "source": "ai_generated"}
                ]
            }
        ],
        "formatting": {
            "style": "simple",
            "language": "vi",
            "date_format": "dd/mm/yyyy",
            "time_format": "HH:mm",
            "header_style": "normal",
            "compact": true
        }
    }'::jsonb
)
ON CONFLICT (code) DO NOTHING;

-- Summary
SELECT 
    'Inserted ' || COUNT(*) || ' new templates' as result
FROM minutes_template
WHERE code IN ('COMPLIANCE_AUDIT_V2', 'BOARD_MEETING_V2', 'PROGRESS_REVIEW_SIMPLE');

