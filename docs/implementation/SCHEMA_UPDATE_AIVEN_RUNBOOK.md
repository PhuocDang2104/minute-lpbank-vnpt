# Aiven Schema Update Runbook

Runbook này giúp dev khác update schema PostgreSQL trên Aiven an toàn, nhất quán, và có thể rollback.

## 1. Mục tiêu

- Cập nhật schema theo các script SQL trong `infra/postgres/init/`.
- Hỗ trợ 2 chế độ:
  - `Non-destructive`: giữ dữ liệu hiện có.
  - `Reset + strict`: xóa sạch schema `public`, dựng lại từ đầu.
- Tránh lỗi thường gặp như:
  - `relation ... already exists`
  - `column project_id does not exist` khi list project.

## 2. Chuẩn bị

Yêu cầu local:

```bash
psql --version
pg_dump --version
```

Lấy `Service URI` từ Aiven Console (format):

```text
postgres://<USER>:<PASSWORD>@<HOST>:<PORT>/<DB>?sslmode=require
```

Thiết lập biến môi trường:

```bash
export DATABASE_URL='postgres://<USER>:<PASSWORD>@<HOST>:<PORT>/<DB>?sslmode=require'
```

Gợi ý: không hard-code URI vào file source. Dùng env var hoặc secret manager của CI/CD.

## 3. Backup trước khi migrate

Luôn backup trước khi chạy bất kỳ thay đổi nào:

```bash
mkdir -p backups
pg_dump "$DATABASE_URL" --schema=public --format=custom \
  --file "backups/aiven_public_$(date +%Y%m%d_%H%M%S).dump"
```

Kiểm tra nhanh kết nối:

```bash
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -c "SELECT now() AS db_time;"
```

## 4. Chế độ A: Update giữ dữ liệu (khuyến nghị cho production)

Chạy theo thứ tự sau:

```bash
# 1) extension
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f infra/postgres/init/01_init_extensions.sql

# 2) align schema cũ về baseline 02 (non-destructive)
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f infra/postgres/init/12_align_existing_schema_to_02.sql

# 3) auth schema (session, reset token, index auth)
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f infra/postgres/init/05_add_auth.sql

# 4) project workspace columns/tables (fix lỗi project_id khi list project)
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f infra/postgres/init/10_project_workspace.sql
```

Tùy chọn seed data:

```bash
# Demo seed LPBank scenario
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f infra/postgres/init/03_seed_mock.sql

# Hoặc seed supabase format
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f infra/postgres/init/04_seed_supabase.sql
```

## 5. Chế độ B: Reset sạch + chạy strict

Chỉ dùng khi chấp nhận mất toàn bộ dữ liệu trong `public`.

```bash
# Reset toàn bộ schema public
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 <<'SQL'
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO PUBLIC;
GRANT ALL ON SCHEMA public TO CURRENT_USER;
SQL

# Dựng baseline strict
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f infra/postgres/init/01_init_extensions.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f infra/postgres/init/02_schema.sql

# Bổ sung auth + workspace (khuyến nghị)
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f infra/postgres/init/05_add_auth.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f infra/postgres/init/10_project_workspace.sql
```

Lưu ý:

- `02_schema.sql` strict chỉ phù hợp khi schema trống.
- Nếu chạy strict trên DB đã có object, bạn sẽ gặp `already exists`.

## 6. Verify sau migrate

```bash
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 \
  -c "SELECT COUNT(*) AS table_count FROM information_schema.tables WHERE table_schema='public';" \
  -c "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='project' ORDER BY ordinal_position;" \
  -c "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='document' ORDER BY ordinal_position;" \
  -c "SELECT to_regclass('public.project_member') AS project_member_table;"
```

Mốc tối thiểu để UI project hoạt động:

- Bảng `project_member` tồn tại.
- Cột `project.description`, `project.objective`, `project.status`, `project.owner_id` tồn tại.
- Cột `document.project_id` tồn tại.

## 7. Lỗi thường gặp và cách xử lý

### 7.1 `relation ... already exists`

Nguyên nhân: chạy `02_schema.sql` trên DB không trống.

Xử lý:

- Dùng `Chế độ A` (non-destructive), hoặc
- Reset sạch rồi chạy strict (`Chế độ B`).

### 7.2 `column project_id does not exist` khi mở trang Projects

Nguyên nhân: thiếu migration workspace.

Xử lý:

```bash
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f infra/postgres/init/10_project_workspace.sql
```

### 7.3 Đăng ký `409`, đăng nhập `401`

Ý nghĩa:

- `409`: email đã tồn tại.
- `401`: sai email/mật khẩu.

Kiểm tra nhanh:

```sql
SELECT id, email, is_active, (password_hash IS NOT NULL AND password_hash <> '') AS has_password
FROM user_account
WHERE lower(email) = lower('<email>');
```

## 8. Đồng bộ môi trường app

Backend (Render):

- `DATABASE_URL`: trỏ đúng Aiven URI.

Frontend:

- `VITE_API_URL`: trỏ đúng backend URL (không trỏ trực tiếp DB).

## 9. Rollback từ backup

Khôi phục full `public` từ file dump:

```bash
pg_restore --clean --if-exists --no-owner --no-privileges \
  --dbname "$DATABASE_URL" "backups/<your_dump>.dump"
```

## 10. Security checklist

- Không commit `DATABASE_URL`, password, service URI vào repo.
- Nếu credentials đã lộ qua chat/screenshot, rotate password ngay trên Aiven.
- Chỉ share runbook, không share secret.

