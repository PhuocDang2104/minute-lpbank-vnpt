# Handoff 2026-02-24 - Auth, Session, Google Login

Tai lieu nay dung de chuyen context sang AI/nguoi tiep theo ma khong mat trang thai cong viec.

## 1) Muc tieu da lam trong session nay

- Bo auth mock, chuyen sang auth that (backend + frontend).
- Co luong dang ky/dang nhap, luu user, JWT access/refresh.
- Co Google sign-in (ID token) va map vao `user_account`.
- Bao ve route `/app/*` bang auth guard.

## 2) Trang thai implementation hien tai

### Backend

Da them auth router/service day du:

- File moi:
  - `backend/app/api/v1/endpoints/auth.py`
  - `backend/app/services/auth_service.py`
- Da wire router:
  - `backend/app/main.py`
  - `backend/app/api/v1/endpoints/__init__.py`
- Da bo sung schema auth:
  - `backend/app/schemas/auth.py`
- Da bo sung config Google:
  - `backend/app/core/config.py` (`google_oauth_client_id`)
  - `backend/env.example.txt`
  - `backend/render.yaml`

Auth endpoint da co:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/google`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/change-password`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/verify`

Bao mat da ap dung:

- bcrypt hash/verify mat khau.
- check `is_active` truoc khi cap token.
- cap access + refresh token.
- throttle co ban login fail theo `email + ip` (in-memory, khong persistent).

### Frontend

Da thay auth mock bang API that:

- `frontend/src/renderer/lib/api/auth.ts` (token/user storage + auth API wrapper)
- `frontend/src/renderer/lib/apiClient.ts` (auto refresh token khi 401)
- `frontend/src/renderer/context/AuthContext.tsx` (init tu token, refresh user)

Da them man hinh auth:

- `frontend/src/renderer/app/routes/Login.tsx`
- `frontend/src/renderer/app/routes/Register.tsx`

Da bat auth guard:

- `frontend/src/renderer/app/router/index.tsx` (`RequireAuth` cho `/app`)
- `frontend/src/renderer/main.tsx` (wrap `AuthProvider`)

Da them env frontend:

- `frontend/src/renderer/config/env.ts` (`VITE_GOOGLE_CLIENT_ID`)
- `frontend/README.md` cap nhat huong dan env.

## 3) Cac lenh verify da chay

Backend:

```bash
python3 -m compileall backend/app
cd backend && python3 -c "import app.main; print('ok')"
```

Frontend:

```bash
cd frontend && npm run build
```

KQ:

- Backend import/compile OK.
- Frontend build OK (co canh bao chunk size cua Vite, khong phai loi compile).

## 4) Cau hinh env de deploy dong bo (Render backend + frontend)

### Render backend (bat buoc)

- `DATABASE_URL=<Aiven Postgres URL>`  
  Vi du dang dung: `postgres://...@pg-minute-meetmate.a.aivencloud.com:26101/defaultdb?sslmode=require`
- `SECRET_KEY=<strong random key >= 32 chars>`
- `CORS_ORIGINS=<frontend domain>`
- `GOOGLE_OAUTH_CLIENT_ID=<Google Web Client ID>`

Neu dung AI/STT/Storage:

- `GROQ_API_KEY`, `GEMINI_API_KEY`
- `ASR_URL`, `ASR_LANGUAGE`
- `SUPABASE_S3_ENDPOINT`, `SUPABASE_S3_REGION`, `SUPABASE_S3_BUCKET`, `SUPABASE_S3_ACCESS_KEY`, `SUPABASE_S3_SECRET_KEY`

### Frontend (Vite)

- `VITE_API_URL=<backend base url>`
- `VITE_GOOGLE_CLIENT_ID=<Google Web Client ID>`

## 5) Ghi chu quan trong ve Database va Storage

- Co the dung lai DB server cu (Aiven) neu schema co `user_account` va cot auth.
- Storage Supabase phai dung bo bien `SUPABASE_S3_*`.
- URL `postgresql://postgres:...@db....supabase.co:5432/postgres` la DB connection, KHONG phai storage endpoint.

SQL nen dam bao da chay:

- `infra/postgres/init/02_schema.sql`
- `infra/postgres/init/05_add_auth.sql`

## 6) Danh sach thay doi auth de AI sau tiep tuc nhanh

Backend:

- `backend/app/services/auth_service.py` (business logic auth)
- `backend/app/api/v1/endpoints/auth.py` (REST contract)
- `backend/app/schemas/auth.py` (request/response model)
- `backend/app/main.py` (router include)

Frontend:

- `frontend/src/renderer/lib/api/auth.ts`
- `frontend/src/renderer/lib/apiClient.ts`
- `frontend/src/renderer/context/AuthContext.tsx`
- `frontend/src/renderer/app/routes/Login.tsx`
- `frontend/src/renderer/app/routes/Register.tsx`
- `frontend/src/renderer/app/router/index.tsx`

## 7) Risk / han che hien tai

- Login rate-limit dang in-memory (1 instance). Neu scale nhieu instance se khong dong bo counter.
- Token luu localStorage (de nhanh cho web/electron), can danh gia them neu can model bao mat cao hon.
- `git status` hien tai co nhieu file dang modified tu cong viec khac (minutes/post-meeting), khong duoc revert khi tiep tuc.

## 8) Checklist cho AI tiep theo

1. Kiem tra env tren Render da set du chua (dac biet `SECRET_KEY`, `DATABASE_URL`, `GOOGLE_OAUTH_CLIENT_ID`).
2. Smoke test auth API bang Postman/curl (`register/login/me/refresh/verify`).
3. Smoke test UI:
   - `/login` dang nhap email/password.
   - `/register` tao user moi.
   - Neu co Google Client ID: test button Google login.
4. Kiem tra route guard:
   - Chua login vao `/app/*` phai bi day ve `/login`.
5. Neu user yeu cau tiep: them forgot/reset password + session revoke server-side.

