-- ============================================
-- MINUTES TEMPLATE SYSTEM
-- ============================================

-- Enable pgcrypto extension for gen_random_uuid() (if PostgreSQL < 13)
-- For PostgreSQL 13+, gen_random_uuid() is built-in and doesn't need this
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Minutes Template Table
CREATE TABLE IF NOT EXISTS minutes_template (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Basic Info
    name TEXT NOT NULL,
    code TEXT UNIQUE,
    description TEXT,
    
    -- Template Structure (JSON)
    structure JSONB NOT NULL,
    sample_data JSONB,
    
    -- Usage
    meeting_types TEXT[],
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_by UUID REFERENCES user_account(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES user_account(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Versioning (optional)
    version INTEGER DEFAULT 1,
    parent_template_id UUID REFERENCES minutes_template(id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_template_code ON minutes_template(code);
CREATE INDEX IF NOT EXISTS idx_template_meeting_types ON minutes_template USING GIN(meeting_types);
CREATE INDEX IF NOT EXISTS idx_template_active ON minutes_template(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_template_default ON minutes_template(is_default) WHERE is_default = TRUE;

-- Insert Default Templates

-- 1. Default Template
INSERT INTO minutes_template (id, name, code, description, meeting_types, is_default, structure) VALUES
(
    gen_random_uuid(),
    'Biên bản Mặc định',
    'DEFAULT',
    'Template mặc định cho biên bản họp',
    ARRAY['general'],
    TRUE,
    '{
        "sections": [
            {
                "id": "header",
                "title": "THÔNG TIN CUỘC HỌP",
                "order": 1,
                "required": true,
                "fields": [
                    {
                        "id": "meeting_title",
                        "label": "Tên cuộc họp",
                        "type": "text",
                        "required": true,
                        "source": "meeting.title"
                    },
                    {
                        "id": "meeting_date",
                        "label": "Ngày giờ họp",
                        "type": "datetime",
                        "required": true,
                        "source": "meeting.start_time"
                    },
                    {
                        "id": "location",
                        "label": "Địa điểm",
                        "type": "text",
                        "required": false,
                        "source": "meeting.location"
                    }
                ]
            },
            {
                "id": "participants",
                "title": "THÀNH PHẦN THAM GIA",
                "order": 2,
                "required": true,
                "fields": [
                    {
                        "id": "participants_list",
                        "label": "Danh sách người tham gia",
                        "type": "array",
                        "required": true,
                        "source": "meeting.participants"
                    }
                ]
            },
            {
                "id": "summary",
                "title": "TÓM TẮT CUỘC HỌP",
                "order": 3,
                "required": true,
                "fields": [
                    {
                        "id": "executive_summary",
                        "label": "Tóm tắt điều hành",
                        "type": "text",
                        "required": true,
                        "source": "ai_generated"
                    },
                    {
                        "id": "key_points",
                        "label": "Các điểm chính",
                        "type": "array",
                        "required": true,
                        "source": "ai_generated"
                    }
                ]
            }
        ],
        "formatting": {
            "style": "formal",
            "language": "vi",
            "date_format": "dd/mm/yyyy",
            "time_format": "HH:mm"
        }
    }'::jsonb
)
ON CONFLICT (code) DO NOTHING;

-- 2. Board Meeting Template
INSERT INTO minutes_template (id, name, code, description, meeting_types, structure) VALUES
(
    gen_random_uuid(),
    'Biên bản Hội đồng Quản trị',
    'BOARD_MEETING',
    'Template cho cuộc họp Hội đồng Quản trị',
    ARRAY['board', 'governance'],
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
                    {"id": "location", "label": "Địa điểm", "type": "text", "required": false, "source": "meeting.location"}
                ]
            },
            {
                "id": "participants",
                "title": "THÀNH PHẦN THAM GIA",
                "order": 2,
                "required": true,
                "fields": [
                    {"id": "participants_list", "label": "Danh sách người tham gia", "type": "array", "required": true, "source": "meeting.participants"}
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
                    {"id": "key_points", "label": "Các điểm chính", "type": "array", "required": true, "source": "ai_generated"}
                ]
            },
            {
                "id": "decisions",
                "title": "CÁC QUYẾT ĐỊNH",
                "order": 5,
                "required": true,
                "fields": [
                    {"id": "decisions_list", "label": "Danh sách quyết định", "type": "array", "required": true, "source": "ai_generated"}
                ]
            },
            {
                "id": "signatures",
                "title": "CHỮ KÝ",
                "order": 6,
                "required": true,
                "fields": [
                    {"id": "chairman_signature", "label": "Chủ tọa", "type": "signature", "required": false},
                    {"id": "secretary_signature", "label": "Thư ký", "type": "signature", "required": false}
                ]
            }
        ],
        "formatting": {
            "style": "formal",
            "language": "vi",
            "date_format": "dd/mm/yyyy"
        }
    }'::jsonb
)
ON CONFLICT (code) DO NOTHING;

-- 3. Compliance/Audit Template
INSERT INTO minutes_template (id, name, code, description, meeting_types, structure) VALUES
(
    gen_random_uuid(),
    'Biên bản Tuân thủ/Kiểm toán',
    'COMPLIANCE_AUDIT',
    'Template cho cuộc họp tuân thủ và kiểm toán',
    ARRAY['compliance', 'audit'],
    '{
        "sections": [
            {
                "id": "header",
                "title": "THÔNG TIN CUỘC HỌP",
                "order": 1,
                "required": true,
                "fields": [
                    {"id": "meeting_title", "label": "Tên cuộc họp", "type": "text", "required": true, "source": "meeting.title"},
                    {"id": "meeting_date", "label": "Ngày giờ họp", "type": "datetime", "required": true, "source": "meeting.start_time"}
                ]
            },
            {
                "id": "participants",
                "title": "THÀNH PHẦN THAM GIA",
                "order": 2,
                "required": true,
                "fields": [
                    {"id": "participants_list", "label": "Danh sách người tham gia", "type": "array", "required": true, "source": "meeting.participants"}
                ]
            },
            {
                "id": "summary",
                "title": "TÓM TẮT CUỘC HỌP",
                "order": 3,
                "required": true,
                "fields": [
                    {"id": "executive_summary", "label": "Tóm tắt điều hành", "type": "text", "required": true, "source": "ai_generated"}
                ]
            },
            {
                "id": "risks",
                "title": "RỦI RO ĐÃ NHẬN DIỆN",
                "order": 4,
                "required": true,
                "fields": [
                    {"id": "risks_list", "label": "Danh sách rủi ro", "type": "array", "required": true, "source": "ai_generated"}
                ]
            },
            {
                "id": "actions",
                "title": "HÀNH ĐỘNG KHẮC PHỤC",
                "order": 5,
                "required": true,
                "fields": [
                    {"id": "action_items", "label": "Danh sách hành động", "type": "array", "required": true, "source": "ai_generated"}
                ]
            }
        ],
        "formatting": {
            "style": "formal",
            "language": "vi"
        }
    }'::jsonb
)
ON CONFLICT (code) DO NOTHING;

-- 4. Progress Review Template
INSERT INTO minutes_template (id, name, code, description, meeting_types, structure) VALUES
(
    gen_random_uuid(),
    'Biên bản Theo dõi Tiến độ',
    'PROGRESS_REVIEW',
    'Template cho cuộc họp theo dõi tiến độ dự án',
    ARRAY['progress', 'status', 'sprint'],
    '{
        "sections": [
            {
                "id": "header",
                "title": "THÔNG TIN CUỘC HỌP",
                "order": 1,
                "required": true,
                "fields": [
                    {"id": "meeting_title", "label": "Tên cuộc họp", "type": "text", "required": true, "source": "meeting.title"},
                    {"id": "meeting_date", "label": "Ngày giờ họp", "type": "datetime", "required": true, "source": "meeting.start_time"}
                ]
            },
            {
                "id": "participants",
                "title": "THÀNH PHẦN THAM GIA",
                "order": 2,
                "required": true,
                "fields": [
                    {"id": "participants_list", "label": "Danh sách người tham gia", "type": "array", "required": true, "source": "meeting.participants"}
                ]
            },
            {
                "id": "summary",
                "title": "TÓM TẮT CUỘC HỌP",
                "order": 3,
                "required": true,
                "fields": [
                    {"id": "executive_summary", "label": "Tóm tắt điều hành", "type": "text", "required": true, "source": "ai_generated"},
                    {"id": "key_points", "label": "Các điểm chính", "type": "array", "required": true, "source": "ai_generated"}
                ]
            },
            {
                "id": "actions",
                "title": "CÔNG VIỆC",
                "order": 4,
                "required": true,
                "fields": [
                    {"id": "action_items", "label": "Danh sách công việc", "type": "array", "required": true, "source": "ai_generated"}
                ]
            },
            {
                "id": "next_meeting",
                "title": "CUỘC HỌP TIẾP THEO",
                "order": 5,
                "required": false,
                "fields": [
                    {"id": "next_meeting_date", "label": "Ngày giờ họp tiếp theo", "type": "datetime", "required": false, "source": "meeting.end_time"}
                ]
            }
        ],
        "formatting": {
            "style": "formal",
            "language": "vi"
        }
    }'::jsonb
)
ON CONFLICT (code) DO NOTHING;

