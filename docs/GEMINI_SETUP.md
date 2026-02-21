# Huong Dan Setup LLM (Gemini/Groq) Cho Minute

Tai lieu nay tap trung cho chatbot + tao bien ban hop tieng Viet.

## 1. Lay API key

### Gemini
1. Mo https://aistudio.google.com
2. Chon `Get API key` -> `Create API key`
3. Copy key (`AIza...`)

### Groq (optional)
1. Mo https://console.groq.com/keys
2. Tao API key (`gsk_...`)

## 2. Cau hinh bien moi truong

Copy mau:

```bash
cp backend/env.example.txt backend/.env.local
```

Cap nhat cac bien quan trong:

```env
# Provider keys
GEMINI_API_KEY=AIza...
GROQ_API_KEY=

# Model text/chat
GEMINI_MODEL=gemini-2.5-flash-lite
LLM_GROQ_CHAT_MODEL=meta-llama/llama-4-scout-17b-16e-instruct

# Chatbot + minutes output language
LLM_OUTPUT_LANGUAGE=vi

# Quality for minutes
AI_TEMPERATURE=0.2
AI_MAX_TOKENS=4096
```

## 3. Chay backend + kiem tra

```bash
cd infra
docker compose up -d --build
curl http://localhost:8000/api/v1/chat/status
curl http://localhost:8000/api/v1/health
```

Neu `provider=mock`, backend chua nhan API key.

## 4. Cau hinh LLM theo tung user (UI Settings)

UI da ho tro:
- provider/model cho text LLM
- visual provider/model cho frame caption
- master prompt
- style/tone/cite evidence

API:
- `GET /api/v1/users/{user_id}/llm-settings`
- `PUT /api/v1/users/{user_id}/llm-settings`

## 5. Khuyen nghi de chatbot tieng Viet on dinh

- Dat `LLM_OUTPUT_LANGUAGE=vi`.
- Master prompt nen yeu cau:
  - trich dan timestamp khi co
  - neu thieu du lieu thi noi ro "chua du bang chung"
  - uu tien output dang bullet ro rang
- Giam `AI_TEMPERATURE` ve 0.1-0.3 khi tao bien ban.

## 6. Khuyen nghi tao bien ban day du

Khi goi `POST /api/v1/minutes/generate`, bat:
- `include_transcript=true`
- `include_actions=true`
- `include_decisions=true`
- `include_risks=true`
- `prompt_strategy=structured_json`
- `format=markdown`

Vi du payload:

```json
{
  "meeting_id": "<meeting_uuid>",
  "include_transcript": true,
  "include_actions": true,
  "include_decisions": true,
  "include_risks": true,
  "prompt_strategy": "structured_json",
  "format": "markdown"
}
```

## 7. Troubleshooting

- Chat tieng Anh du da set `vi`:
  - Kiem tra `LLM_OUTPUT_LANGUAGE` trong container backend.
  - Restart backend sau khi doi env.
- Minutes qua ngan:
  - Tang `AI_MAX_TOKENS`.
  - Dam bao transcript day du va dung speaker labels.
- LLM timeout:
  - Thu model nhanh hon (`gemini-2.5-flash-lite`) hoac rut gon transcript window.
