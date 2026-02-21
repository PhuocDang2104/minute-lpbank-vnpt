# Render Backend Env Sync (Aiven DB + Supabase Storage)

Tai lieu nay de dong bo `minute-lpbank-vnpt` voi ha tang dang dung tu `minute_google_gemini_hackathon`.

## 1) Co dung lai DB server cua minute_genhack duoc khong?

Duoc. Ban co the dung lai Aiven Postgres URL sau lam `DATABASE_URL` tren Render:

```env
DATABASE_URL=postgres://avnadmin:<YOUR_PASSWORD>@pg-minute-meetmate.a.aivencloud.com:26101/defaultdb?sslmode=require
```

Ghi chu:
- App da ho tro `postgres://...` va tu dong doi sang `postgresql://...` khi khoi dong.
- Khong commit secret nhay cam vao repo; dung Secret Manager cua Render.

## 2) Supabase "storage" co phai URL PostgreSQL khong?

Khong. URL dang:

```env
postgresql://postgres:<YOUR_PASSWORD>@db.<project-ref>.supabase.co:5432/postgres
```

la **Supabase Database URL**, khong phai Storage.

Neu ban muon dung Supabase lam DB thi dat URL nay vao `DATABASE_URL`.

Neu ban muon dung **Supabase Storage** thi phai set bo S3-compatible env (muc 4).

## 3) Render backend: env vars bat buoc

Toi thieu:

```env
ENV=production
DATABASE_URL=<AIVEN_OR_SUPABASE_DB_URL>
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=5
SECRET_KEY=<RANDOM_32_PLUS_CHARS>
CORS_ORIGINS=https://<your-frontend-domain>

GEMINI_API_KEY=<YOUR_KEY>
GEMINI_MODEL=gemini-2.5-flash-lite
LLM_OUTPUT_LANGUAGE=vi
AI_TEMPERATURE=0.2
AI_MAX_TOKENS=4096
```

Neu backend khong co ASR service rieng tren Render, dat `ASR_URL` den endpoint ASR khac:

```env
ASR_URL=https://<your-asr-service-domain>
ASR_LANGUAGE=vi
```

## 4) Render backend: env vars cho Supabase Storage (S3)

```env
SUPABASE_S3_ENDPOINT=https://<project-ref>.supabase.co/storage/v1/s3
SUPABASE_S3_REGION=ap-southeast-1
SUPABASE_S3_BUCKET=<bucket-name>
SUPABASE_S3_ACCESS_KEY=<supabase-s3-access-key>
SUPABASE_S3_SECRET_KEY=<supabase-s3-secret-key>
```

Lay cac gia tri nay trong Supabase Dashboard:
- Storage -> S3 Configuration
- Buckets -> ten bucket dung de luu video/asset

## 5) Goi y profile de tranh nham lan

### Profile A (khuyen nghi cho ban hien tai)
- DB: Aiven (`DATABASE_URL=postgres://avnadmin...sslmode=require`)
- Storage: Supabase S3 (`SUPABASE_S3_*`)

### Profile B
- DB: Supabase Postgres (`DATABASE_URL=postgresql://postgres:...@db...supabase.co:5432/postgres`)
- Storage: Supabase S3 (`SUPABASE_S3_*`)

## 6) Checklist sau khi cap nhat env tren Render

1. Redeploy backend service.
2. Kiem tra health:
   - `GET /api/v1/health`
   - `GET /api/v1/chat/status`
3. Kiem tra DB:
   - tao meeting thu
   - doc danh sach meetings
4. Kiem tra storage:
   - upload 1 file video/asset
   - xac nhan co object trong bucket

## 7) Bao mat

- Neu URL Aiven da duoc chia se trong kenh cong cong, nen rotate password/token sau khi setup.
- Khong dat secret trong `render.yaml` hoac file tracked.
