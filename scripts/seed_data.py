"""Seed mock data for MeetMate PMO flows (stub)."""
from __future__ import annotations

import datetime

MOCK_MEETINGS = [
    {
        "id": "meeting-core-001",
        "title": "Core Banking Steering",
        "owner": "pmo@lpbank.vn",
        "start": datetime.datetime.utcnow().isoformat(),
        "phase": "pre",
    },
    {
        "id": "meeting-mobile-ops",
        "title": "Mobile App Ops Review",
        "owner": "pmo@lpbank.vn",
        "start": datetime.datetime.utcnow().isoformat(),
        "phase": "in",
    },
]


def run():
    # TODO: wire into database/pgvector once models/services are ready
    for meeting in MOCK_MEETINGS:
        print(f"Seed placeholder meeting: {meeting['id']} :: {meeting['title']}")


if __name__ == "__main__":
    run()