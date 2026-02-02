# Changelog

## [v0.7.0] - 2024-12-07

### 📚 Knowledge Hub - Document Upload & AI Search

Xây dựng trang Knowledge Hub với tính năng upload tài liệu và tìm kiếm AI.

#### ✨ Features

**Knowledge API** (`/api/v1/knowledge`)
- `GET /documents` - Danh sách tài liệu với filters (type, source, category)
- `GET /documents/{id}` - Chi tiết tài liệu (tăng view count)
- `POST /documents/upload` - **Upload tài liệu mới** ✨
- `PUT /documents/{id}` - Cập nhật metadata
- `DELETE /documents/{id}` - Xóa tài liệu
- `POST /search` - Tìm kiếm tài liệu theo query
- `POST /query` - **AI Q&A trên knowledge base** (Gemini)
- `GET /recent-queries` - Lịch sử tìm kiếm gần đây

**Frontend Features**
- **Trang Knowledge Hub** (`/app/knowledge`):
  - Danh sách tài liệu phổ biến với metadata
  - Tìm kiếm real-time với suggestions
  - Lịch sử tìm kiếm gần đây
  - **Upload tài liệu mới**:
    - Form với title, description, type, source, category
    - Hỗ trợ tags (thêm/xóa)
    - File upload (mock - chỉ lưu metadata)
  - Hiển thị kết quả tìm kiếm

#### 📁 New Files

**Backend:**
- `backend/app/schemas/knowledge.py` - Knowledge document schemas
- `backend/app/services/knowledge_service.py` - Knowledge service với mock data
- `backend/app/api/v1/endpoints/knowledge.py` - Knowledge API endpoints

**Frontend:**
- `electron/src/renderer/lib/api/knowledge.ts` - Knowledge API client

#### 🔧 Updated Files

**Backend:**
- `backend/app/main.py` - Added knowledge router
- `backend/app/services/__init__.py` - Export knowledge_service
- `backend/app/api/v1/endpoints/__init__.py` - Export knowledge module

**Frontend:**
- `electron/src/renderer/app/routes/KnowledgeHub.tsx` - Full implementation với search & upload

#### 📝 Mock Data

8 tài liệu mẫu:
- Thông tư 09/2020/TT-NHNN (NHNN)
- LPBank Security Policy v3.0 (SharePoint)
- Core Banking Integration Guide (SharePoint)
- KYC Policy 2024 (LOffice)
- Risk Assessment Template (SharePoint)
- Thông tư 35/2016/TT-NHNN (NHNN)
- Mobile Banking API Documentation (Wiki)
- Change Request Process Guide (SharePoint)

---

## [v0.6.0] - 2024-12-07

### 🎨 Pre-meet AI Q&A Improvements

- User messages hiển thị màu trắng
- AI không còn chào hỏi sau mỗi tin nhắn
- Loại bỏ markdown formatting từ AI responses

---

## [v0.5.0] - 2024-12-06

### 📄 Documents & Agenda Management

Xây dựng hệ thống quản lý tài liệu và agenda với AI generation.

#### ✨ Features

**Documents API** (`/api/v1/documents`)
- `GET /documents/meeting/{meeting_id}` - Lấy danh sách tài liệu của cuộc họp
- `GET /documents/{document_id}` - Lấy chi tiết tài liệu
- `POST /documents/upload` - Upload tài liệu mới (mock implementation)
- `PUT /documents/{document_id}` - Cập nhật metadata tài liệu
- `DELETE /documents/{document_id}` - Xóa tài liệu

**Agenda API** (`/api/v1/agenda`)
- `GET /agenda/meeting/{meeting_id}` - Lấy danh sách agenda items
- `GET /agenda/item/{item_id}` - Lấy chi tiết một agenda item
- `POST /agenda/generate` - **AI tạo agenda tự động với Gemini** ✨
- `POST /agenda/save` - Lưu agenda đã chỉnh sửa
- `POST /agenda/meeting/{meeting_id}/item` - Thêm agenda item mới
- `PUT /agenda/item/{item_id}` - Cập nhật agenda item
- `DELETE /agenda/item/{item_id}` - Xóa agenda item
- `POST /agenda/meeting/{meeting_id}/reorder` - Sắp xếp lại thứ tự items

**Frontend Features**
- **Tab "Chương trình" (Agenda)**:
  - Xem danh sách agenda items với thời lượng
  - AI tạo agenda tự động dựa trên meeting type, duration, participants
  - Chỉnh sửa inline: tiêu đề, người trình bày, thời lượng
  - Thêm/xóa agenda items
  - Lưu thay đổi
  - Hiển thị ghi chú từ AI
  
- **Tab "Tài liệu"**:
  - Xem danh sách tài liệu pre-read
  - Upload tài liệu mới (mock - chỉ lưu metadata)
  - Xóa tài liệu
  - Hiển thị loại file, mô tả

#### 📁 New Files

**Backend:**
- `backend/app/schemas/document.py` - Document schemas
- `backend/app/schemas/agenda.py` - Agenda schemas
- `backend/app/services/document_service.py` - Document service (mock implementation)
- `backend/app/services/agenda_service.py` - Agenda service với AI generation
- `backend/app/api/v1/endpoints/documents.py` - Documents endpoints
- `backend/app/api/v1/endpoints/agenda.py` - Agenda endpoints

**Frontend:**
- `electron/src/renderer/lib/api/documents.ts` - Documents API client
- `electron/src/renderer/lib/api/agenda.ts` - Agenda API client

#### 🔧 Updated Files

**Backend:**
- `backend/app/main.py` - Added documents & agenda routers
- `backend/app/services/__init__.py` - Export document_service, agenda_service
- `backend/app/api/v1/endpoints/__init__.py` - Export documents, agenda modules

**Frontend:**
- `electron/src/renderer/features/meetings/components/tabs/PreMeetTab.tsx` - Full implementation với AI generation & editing
- `electron/src/renderer/styles/global.css` - Styles cho editable agenda, upload form

#### 🤖 AI Features

**Agenda Generation:**
- Sử dụng Gemini API để tạo agenda thông minh
- Phân tích meeting type, duration, participants
- Tạo agenda items phù hợp với từng loại cuộc họp:
  - Steering Committee: Review, Budget, Risk, Decisions
  - Weekly Status: Sprint review, Demo, Blockers
  - Workshop: Presentation, Practice, Discussion
- Fallback mock agenda khi AI không available

#### 📝 Mock Data

**Documents:**
- 5 mock documents cho các meetings khác nhau
- Hỗ trợ PDF, DOCX, XLSX, PPTX
- Metadata: title, file_type, file_size, description

**Agenda:**
- 9 mock agenda items cho 2 meetings
- Bao gồm order_index, duration, presenter, status

#### 🔑 Technical Details

- **Mock Storage**: In-memory dictionary (không dùng database)
- **File Upload**: Mock implementation - chỉ lưu metadata, không lưu file thực tế
- **AI Integration**: Gemini 2.5 Flash Lite model
- **Error Handling**: Graceful fallback khi AI không available

---

## [v0.4.0] - 2024-12-06

### 🔐 Authentication System

Xây dựng đầy đủ hệ thống đăng ký và đăng nhập.

#### ✨ Features

**Backend Auth APIs** (`/api/v1/auth`)
- `POST /register` - Đăng ký tài khoản mới
- `POST /login` - Đăng nhập với email/password
- `POST /token` - OAuth2 compatible login (for Swagger)
- `POST /refresh` - Refresh access token
- `GET /me` - Lấy thông tin user hiện tại
- `POST /change-password` - Đổi mật khẩu
- `POST /forgot-password` - Yêu cầu reset password
- `POST /logout` - Đăng xuất
- `GET /verify` - Kiểm tra token hợp lệ

**Security Features**
- Password hashing với bcrypt
- JWT access & refresh tokens
- Token expiration & refresh
- Role-based access control (admin, PMO, chair, user)
- Secure password requirements (min 6 chars)

**Frontend Auth Pages**
- Login page với form validation
- Register page với department selection
- Token storage trong localStorage
- Auto-redirect sau login

#### 📁 New Files

**Backend:**
- `backend/app/core/security.py` - Password hashing, JWT utilities
- `infra/postgres/init/05_add_auth.sql` - Database migration for auth

**Frontend:**
- `electron/src/renderer/app/routes/Auth/Login.tsx`
- `electron/src/renderer/app/routes/Auth/Register.tsx`
- `electron/src/renderer/app/routes/Auth/index.ts`
- `electron/src/renderer/lib/api/auth.ts`

#### 🔧 Updated Files
- `backend/app/schemas/auth.py` - Full auth schemas
- `backend/app/services/auth_service.py` - Real auth logic
- `backend/app/api/v1/endpoints/auth.py` - Auth endpoints
- `backend/requirements.txt` - Added python-jose, bcrypt
- `electron/src/renderer/app/router/index.tsx` - Auth routes
- `electron/src/renderer/lib/api/users.ts` - Export utilities

#### 🔑 Demo Account
- Email: `nguyenvana@lpbank.vn`
- Password: `demo123`

---

## [v0.3.0] - 2024-12-06

### 🚀 Backend APIs - Meeting Management Complete

Xây dựng đầy đủ backend APIs cho 3 tab: Pre-meet, In-meet, Post-meet.

#### ✨ New Features

**Action Items API** (`/api/v1/items/actions`)
- CRUD operations for action items
- Confirm/reject workflow
- Owner assignment & deadline tracking

**Decisions API** (`/api/v1/items/decisions`)
- CRUD operations for decisions
- Rationale tracking
- Confirmation workflow

**Risks API** (`/api/v1/items/risks`)
- CRUD operations for risks
- Severity classification
- Mitigation tracking

**Transcripts API** (`/api/v1/transcripts`)
- Chunk management
- AI extraction (actions, decisions, risks)
- Live recap generation

**Participants API** (`/api/v1/participants`)
- Add/remove participants
- Attendance tracking
- Join/leave timestamps

**Minutes API** (`/api/v1/minutes`)
- AI-powered generation
- Version control
- Distribution logging

---

## [v0.2.0] - 2024-12-06

### 🎨 Frontend 3-Tab Meeting Detail

Redesign trang quản lý cuộc họp thành 3 tabs: Pre-meet, In-meet, Post-meet.

---

## [v0.1.0] - 2024-12-05

### 🚀 Initial Setup & AI Integration

- Project scaffold với FastAPI + React/Electron
- Database schema với PostgreSQL + pgvector
- Gemini AI integration cho chat & generation
- Mock data cho demo PMO use case

---

## API Documentation

Sau khi chạy backend, truy cập:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

