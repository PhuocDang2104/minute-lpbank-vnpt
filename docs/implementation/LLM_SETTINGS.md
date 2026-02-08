# LLM Settings (Provider/Model/API Key)

Tài liệu này mô tả các file và luồng xử lý liên quan đến chức năng **chọn nhà cung cấp LLM (Groq/Google Gemini), model và API key của người dùng** trong màn Settings. Mục tiêu là để dev hiểu rõ kiến trúc và mở rộng sau này.

## Mục tiêu tính năng
- Người dùng chọn **provider** (Gemini/Groq).
- Người dùng chọn **model** theo provider.
- Người dùng nhập **API key riêng**.
- **Bảo mật key**: không lưu localStorage, chỉ lưu trên server (mã hoá), frontend chỉ nhận trạng thái key.

## Tổng quan luồng
1. **Frontend Settings load**
   - Gọi `GET /api/v1/users/{user_id}/llm-settings`.
   - Server trả về: `provider`, `model`, `api_key_set`, `api_key_last4`.
2. **User chỉnh & lưu**
   - `PUT /api/v1/users/{user_id}/llm-settings` với `provider`, `model`, `api_key` (hoặc `clear_api_key`).
   - Server mã hoá key và lưu vào `user_account.preferences.llm`.
3. **Sử dụng key khi gọi LLM**
   - Khi tạo minutes, backend lấy `organizer_id` -> đọc `preferences.llm` -> giải mã key -> override LLM config.
   - Nếu không có key riêng, fallback về key môi trường (`GEMINI_API_KEY` / `GROQ_API_KEY`).

## Backend: File chính

### 1) `backend/app/schemas/llm_settings.py`
Định nghĩa schema cho API settings.
- `LlmSettings`: provider, model, api_key_set, api_key_last4.
- `LlmSettingsUpdate`: payload cập nhật (provider/model/api_key/clear_api_key).

### 2) `backend/app/utils/crypto.py`
Mã hoá/giải mã API key.
- Sử dụng `cryptography.Fernet` với key dẫn xuất từ `settings.secret_key`.
- Mã hoá lưu dưới dạng `v1:<token>`.
- Nếu đổi `SECRET_KEY` sẽ **không giải mã được key cũ**.

### 3) `backend/app/services/user_service.py`
Xử lý đọc/ghi `preferences.llm`:
- `get_llm_settings(db, user_id)` -> trả về LlmSettings (không trả key).
- `update_llm_settings(db, user_id, payload)` -> mã hoá key, lưu JSON.
- `get_user_llm_override(db, user_id)` -> trả về `{provider, model, api_key}` để dùng nội bộ khi gọi LLM.

### 4) `backend/app/api/v1/endpoints/users.py`
API endpoints:
- `GET /users/{user_id}/llm-settings`
- `PUT /users/{user_id}/llm-settings`

### 5) `backend/app/llm/gemini_client.py`
Cấp hỗ trợ **override provider/model/api_key** cho LLM:
- `LLMConfig` dataclass
- `call_llm_sync(..., llm_config=...)`
- `GeminiChat(..., llm_config=...)`
- `MeetingAIAssistant(..., llm_config=...)`

### 6) `backend/app/services/minutes_service.py`
Khi generate minutes:
- Lấy `organizer_id` từ bảng `meeting`.
- Gọi `user_service.get_user_llm_override`.
- Nếu có override -> truyền `LLMConfig` vào `MeetingAIAssistant`.

## Frontend: File chính

### 1) `frontend/src/renderer/app/routes/Settings.tsx`
UI Settings:
- Dropdown chọn provider & model.
- Input API key (ẩn/hiện).
- Nút xoá key (clear), hiển thị trạng thái lưu (last4).
- Không lưu key vào localStorage.

### 2) `frontend/src/renderer/lib/api/users.ts`
- `getLlmSettings(id)`
- `updateLlmSettings(id, payload)`

### 3) `frontend/src/renderer/shared/dto/user.ts`
Khai báo types:
- `LlmProvider`, `LlmSettings`, `LlmSettingsUpdate`.

## Data model lưu trữ
`user_account.preferences` (JSONB)
```json
{
  "llm": {
    "provider": "gemini",
    "model": "gemini-1.5-flash",
    "api_key": "v1:<encrypted>",
    "api_key_last4": "1234"
  }
}
```

## API payload mẫu

### GET
`/api/v1/users/{user_id}/llm-settings`
```json
{
  "provider": "gemini",
  "model": "gemini-1.5-flash",
  "api_key_set": true,
  "api_key_last4": "1234"
}
```

### PUT
```json
{
  "provider": "groq",
  "model": "meta-llama/llama-4-scout-17b-16e-instruct",
  "api_key": "gsk_xxx..."
}
```
Hoặc xoá key:
```json
{
  "provider": "gemini",
  "model": "gemini-1.5-flash",
  "clear_api_key": true
}
```

## Bảo mật & lưu ý vận hành
- **Không lưu key ở client**. Frontend chỉ giữ tạm trong state.
- **Server lưu key mã hoá** bằng `SECRET_KEY`. Cần set `SECRET_KEY` ổn định ở môi trường production.
- Nếu đổi `SECRET_KEY` -> key cũ không giải mã được.
- Biến model Groq cho chatbot đã đổi tên sang `LLM_GROQ_CHAT_MODEL`.
- Có thể khai báo thêm `LLM_GROQ_VISION_MODEL` nếu tách model vision riêng.
- Alias cũ vẫn hỗ trợ: `LLM_GROQ_MODEL`, `GROQ_MODEL`.

## Điểm mở rộng
- Hiện tại **minutes generation** dùng override theo organizer. Có thể mở rộng sang:
  - RAG (`backend/app/llm/chains/rag_chain.py`)
  - Chat (`backend/app/llm/gemini_client.py` khi xử lý chat)
  - Agenda, Knowledge, In-meeting.
- Nếu muốn nhiều profile LLM theo project/meeting, có thể chuyển lưu vào `meeting` hoặc `project` thay vì `user_account.preferences`.

## Troubleshooting
- `404 user not found` -> user_id frontend không tồn tại trong DB.
- `api_key_set=false` dù đã lưu -> kiểm tra `SECRET_KEY` và payload.
- LLM vẫn dùng key env -> check `user_account.preferences.llm` có provider/model/api_key.
