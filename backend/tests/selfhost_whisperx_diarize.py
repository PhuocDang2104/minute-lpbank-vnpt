import os
import json
from typing import List, Dict, Any

import torch
import whisperx

AUDIO_PATH = r"C:\Users\ADMIN\Desktop\vnpt_meetmate\vnpt_ai_hackathon\backend\tests\resources\Chapter-1-Conversation-2.mp3"
LANGUAGE = "vi"          # "vi" or None for auto-detect
MODEL_NAME = "large-v3"  # can use "medium", "small" for faster
MIN_SPEAKERS = 2
MAX_SPEAKERS = 2

HF_TOKEN = os.environ.get("HF_TOKEN")  # Hugging Face token for pyannote diarization


def fmt_ts(t: float) -> str:
    if t is None:
        return "00:00.000"
    m = int(t // 60)
    s = t - m * 60
    return f"{m:02d}:{s:06.3f}"


def group_utterances_by_speaker(
    segments: List[Dict[str, Any]],
    gap_split_s: float = 1.0,
) -> List[Dict[str, Any]]:
    """
    Merge consecutive segments by same speaker and small gaps to make it look like a conversation.
    """
    if not segments:
        return []

    merged: List[Dict[str, Any]] = []

    cur = {
        "speaker": segments[0].get("speaker", "SPEAKER_00"),
        "start": float(segments[0].get("start", 0.0)),
        "end": float(segments[0].get("end", 0.0)),
        "text": (segments[0].get("text") or "").strip(),
    }

    for seg in segments[1:]:
        spk = seg.get("speaker", "SPEAKER_00")
        st = float(seg.get("start", 0.0))
        en = float(seg.get("end", 0.0))
        tx = (seg.get("text") or "").strip()

        gap = st - cur["end"]

        if spk == cur["speaker"] and gap <= gap_split_s:
            if tx:
                cur["text"] = (cur["text"] + " " + tx).strip()
            cur["end"] = max(cur["end"], en)
        else:
            if cur["text"]:
                merged.append(cur)
            cur = {"speaker": spk, "start": st, "end": en, "text": tx}

    if cur["text"]:
        merged.append(cur)

    return merged


def main():
    if not os.path.isfile(AUDIO_PATH):
        raise FileNotFoundError(AUDIO_PATH)

    if not HF_TOKEN:
        raise RuntimeError(
            "HF_TOKEN is not set. Set environment variable HF_TOKEN to enable diarization.\n"
            "PowerShell:  $env:HF_TOKEN='hf_xxx...'\n"
            "CMD:         set HF_TOKEN=hf_xxx..."
        )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"

    print(f"Device: {device} | compute_type: {compute_type}")
    print(f"Audio : {AUDIO_PATH}")
    print(f"Model : {MODEL_NAME} | Language: {LANGUAGE}")

    # 1) Load ASR model
    print("1) Loading ASR model...")
    # Note: whisperx.load_model signature commonly is load_model(model_name, device, ...)
    model = whisperx.load_model(
        MODEL_NAME,
        device,
        compute_type=compute_type,
        language=LANGUAGE,
    )

    # 2) Load audio
    print("2) Loading audio...")
    audio = whisperx.load_audio(AUDIO_PATH)

    # 3) Transcribe
    print("3) Transcribing...")
    result = model.transcribe(audio, batch_size=16)

    detected_lang = result.get("language")
    print(f"   Detected language: {detected_lang}")
    print(f"   Raw segments     : {len(result.get('segments', []))}")

    # 4) Align (word-level timestamps)
    print("4) Aligning (word-level timestamps)...")
    align_model, metadata = whisperx.load_align_model(language_code=detected_lang, device=device)
    result_aligned = whisperx.align(result["segments"], align_model, metadata, audio, device)

    # 5) Diarization
    print("5) Diarizing (speaker separation)...")
    diarize_pipeline = whisperx.DiarizationPipeline(use_auth_token=HF_TOKEN, device=device)
    diarize_segments = diarize_pipeline(audio, min_speakers=MIN_SPEAKERS, max_speakers=MAX_SPEAKERS)

    # 6) Assign speakers to words/segments
    print("6) Assigning speakers to transcript segments...")
    result_diarized = whisperx.assign_word_speakers(diarize_segments, result_aligned)

    segments = result_diarized.get("segments", [])
    print(f"   Diarized segments: {len(segments)}")

    # Merge into conversation-like turns
    merged_turns = group_utterances_by_speaker(segments, gap_split_s=1.0)

    print("\n=== CONVERSATION (merged turns) ===")
    for t in merged_turns:
        print(f"[{fmt_ts(t['start'])} – {fmt_ts(t['end'])}] {t['speaker']}: {t['text']}")

    # Save JSON output
    out = {
        "audio_path": AUDIO_PATH,
        "language": detected_lang,
        "model": MODEL_NAME,
        "min_speakers": MIN_SPEAKERS,
        "max_speakers": MAX_SPEAKERS,
        "turns": [
            {
                "speaker": t["speaker"],
                "time_start": t["start"],
                "time_end": t["end"],
                "time_start_ts": fmt_ts(t["start"]),
                "time_end_ts": fmt_ts(t["end"]),
                "transcript": t["text"],
                "is_final": True,
            }
            for t in merged_turns
        ],
    }

    out_path = "meetmate_whisperx_diarized_turns.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"\nSaved JSON -> {os.path.abspath(out_path)}")


if __name__ == "__main__":
    main()
