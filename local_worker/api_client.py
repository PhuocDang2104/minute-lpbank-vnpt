import requests


class APIClient:
    def __init__(self, base_url: str, session_id: str):
        self.base_url = base_url.rstrip("/")
        self.session_id = session_id

    def send_segments(self, segments):
        payload = {
            "segments": segments,
        }
        try:
            url = f"{self.base_url}/diarization/{self.session_id}"
            print(f"[API] POST {url}")
            resp = requests.post(
                url,
                json=payload,
                timeout=3,
            )
            print(f"[API] diarization {resp.status_code} -> {resp.text[:200]}")
            resp.raise_for_status()
        except Exception as exc:
            print(f"[API] diarization request failed: {exc}")
