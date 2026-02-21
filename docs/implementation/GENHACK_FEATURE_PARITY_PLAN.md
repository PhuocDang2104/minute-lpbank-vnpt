# Feature Parity Plan: minute_google_gemini_hackathon -> minute-lpbank-vnpt

## 1. Ket qua doi chieu repo

So sanh theo `git ls-files` + checksum cho thay:
- Hai repo co cung danh sach tracked files.
- Khac biet chinh nam o `README.md` va mot so script/docs cu trong `minute-lpbank-vnpt`.

Ket luan:
- Nen tap trung parity o **cau hinh + prompt + quality tuning** thay vi rewrite kien truc.

## 2. Muc tieu parity uu tien

1. Whisper/ASR phai toi uu tieng Viet.
2. Chatbot tra loi on dinh tieng Viet, uu tien evidence.
3. Biên bản hop day du (summary + actions + decisions + risks + next steps).
4. Tai lieu/dev scripts dong bo naming `Minute` (khong con `MeetMate`).

## 3. Thay doi da ap dung trong minute-lpbank-vnpt

### 3.1 ASR/Whisper
- Default model ASR doi sang multilingual (`ggml-base.bin`), bo `tiny.en`.
- Them cau hinh `ASR_LANGUAGE` (backend) va `WHISPER_LANGUAGE` (ASR service).
- Backend gui language hint qua endpoint `/transcribe`.
- Compose ho tro build arg de doi model (`WHISPER_MODEL_URL`, `WHISPER_MODEL_FILE`).

### 3.2 LLM/Chatbot
- Them `LLM_OUTPUT_LANGUAGE` (mac dinh `vi`).
- Bo rule ep chatbot tra loi tieng Anh.
- Prompt summary/minutes da duoc tham so hoa theo ngon ngu output.
- Fallback summary/key points co ban tieng Viet de tranh output lech ngon ngu.

### 3.3 Minutes completeness
- Window summarization khong con hard-code English.
- Pipeline minutes giu du lieu context: transcript + visual + actions/decisions/risks.
- Kien nghi runtime: `prompt_strategy=structured_json` cho output day du.

### 3.4 Docs + setup scripts
- `README.md` da dong bo theo huong minute_google_gemini_hackathon.
- Cap nhat docs setup LLM/ASR/local dev theo stack Minute.
- `scripts/setup_local.sh` da sua DB/container/env minute.

## 4. Checklist go-live cho tieng Viet

- [ ] Set `LLM_OUTPUT_LANGUAGE=vi`
- [ ] Set `ASR_LANGUAGE=vi`, `WHISPER_LANGUAGE=vi`
- [ ] Start stack: `docker compose up -d --build`
- [ ] Health check backend/chat/asr
- [ ] Test audio Vietnamese 5-10 phut, verify transcript
- [ ] Generate minutes voi `structured_json`, verify du 4 phan: actions/decisions/risks/next steps
- [ ] UAT voi 2-3 kịch ban LPBank (dieu phoi, risk review, status meeting)

## 5. De xuat tuning tiep theo (neu can)

- Nang ASR len `ggml-medium.bin` neu cuoc hop dai/nhieu accent.
- Giam `AI_TEMPERATURE` ve 0.1-0.2 cho minutes compliance-heavy.
- Bat buoc review human-in-the-loop truoc khi distribute minutes.
