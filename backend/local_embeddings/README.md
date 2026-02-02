# Local Embeddings (CPU)

Thư mục này dùng để đặt các script/service chạy embedding ngay trên máy local (CPU) khi không muốn gọi API bên ngoài.

Gợi ý setup tối thiểu:
- Máy local ≥ 2 vCPU, ≥ 4 GB RAM.
- Python 3.10+ và thư viện: `torch`, `sentence-transformers`, `psycopg2-binary`.
- Model gợi ý: `Alibaba-NLP/gte-small` (384 chiều) để chạy nhanh trên CPU. Nếu dùng model này, chỉnh cột `knowledge_chunk.embedding` thành `vector(384)`.

Mẫu lệnh cài đặt:
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install torch==2.2.0 sentence-transformers==2.2.2 psycopg2-binary==2.9.9
```

Mẫu script ingest đơn giản (chèn 1 chunk) có sẵn ở `ingest_local.py`:
```bash
DATABASE_URL="postgresql://..." \
python backend/local_embeddings/ingest_local.py --file /path/to/doc.txt --title "Sample"
```

Nếu muốn chạy như service: tạo một FastAPI nhỏ `/embed` dùng model trên, backend sẽ gọi HTTP đến `http://localhost:<port>/embed`.

# Local embedding server (FastAPI)
Có sẵn `backend/local_embeddings/server.py`.

Chạy:
```bash
cd backend
source .venv/bin/activate  # nếu đã tạo venv
MODEL_NAME="Alibaba-NLP/gte-small" uvicorn backend.local_embeddings.server:app --host 0.0.0.0 --port 8001
```

API:
- `GET /health`
- `POST /embed` body `{"texts": ["..."], "normalize": true}` → trả về `embeddings` (list float)
