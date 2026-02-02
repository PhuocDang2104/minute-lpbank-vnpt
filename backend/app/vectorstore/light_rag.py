from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import math


@dataclass
class RagDoc:
    doc_id: str
    project_id: Optional[str]
    topic_id: Optional[str]
    bucket: str  # meeting / project / global
    title: str
    snippet: str
    score: float
    metadata: Dict[str, Any]


# Seeded LPBank-oriented snippets (mock pgvector rows)
SEED_DOCS: List[RagDoc] = [
    RagDoc(
        doc_id="lpb-core-001",
        project_id="proj-core",
        topic_id="performance",
        bucket="project",
        title="Core Banking Batch Performance SOP",
        snippet="Tối ưu batch window 00:30-03:00, ưu tiên queue LOS trước Core settlement.",
        score=0.82,
        metadata={"doc_type": "SOP", "effective_date": "2024-08-01"},
    ),
    RagDoc(
        doc_id="lpb-risk-009",
        project_id="proj-core",
        topic_id="risk",
        bucket="project",
        title="Risk playbook - Core Banking",
        snippet="Rủi ro latency > 2s với LOS integration; yêu cầu load test 10k TPS.",
        score=0.78,
        metadata={"doc_type": "Risk", "severity": "high"},
    ),
    RagDoc(
        doc_id="lpb-policy-012",
        project_id=None,
        topic_id=None,
        bucket="global",
        title="NHNN Circular 09/2020 - Data retention",
        snippet="Lưu trữ log giao dịch tối thiểu 10 năm, phân vùng dữ liệu nhạy cảm.",
        score=0.7,
        metadata={"doc_type": "Policy", "page": 12},
    ),
    RagDoc(
        doc_id="lpb-meet-2024-11",
        project_id="proj-mobile",
        topic_id="roadmap",
        bucket="meeting",
        title="Biên bản Mobile Banking Sprint 23",
        snippet="Team Mobile đề xuất re-plan scope Sprint 24-25 do chuyển resource sang Core.",
        score=0.76,
        metadata={"doc_type": "Minutes", "meeting_id": "mock-meeting-mobile-23"},
    ),
]


class LightRAGRetriever:
    def __init__(self, docs: Optional[List[RagDoc]] = None) -> None:
        self.docs = docs or SEED_DOCS

    def retrieve(self, question: str, meeting_id: str | None = None, project_id: str | None = None, topic_id: str | None = None) -> List[Dict[str, Any]]:
        """Return prioritized snippets by bucket: meeting > project/topic > global."""
        query_tokens = set((question or "").lower().split())

        def score_doc(doc: RagDoc) -> float:
            base = doc.score
            bucket_bonus = {"meeting": 0.25, "project": 0.15, "global": 0.0}.get(doc.bucket, 0.0)
            topic_bonus = 0.1 if topic_id and doc.topic_id and topic_id in doc.topic_id else 0.0
            token_overlap = len(query_tokens.intersection(set(doc.snippet.lower().split()))) * 0.01
            return base + bucket_bonus + topic_bonus + token_overlap

        candidates: List[RagDoc] = []
        for doc in self.docs:
            # Bucket filter / assignment
            if meeting_id and doc.bucket == "meeting":
                candidates.append(doc)
            elif project_id and doc.project_id == project_id:
                candidates.append(doc)
            elif doc.bucket == "global":
                candidates.append(doc)
            else:
                candidates.append(doc)

        ranked = sorted(
            candidates,
            key=lambda d: score_doc(d),
            reverse=True,
        )

        results: List[Dict[str, Any]] = []
        for doc in ranked[:8]:
            results.append(
                {
                    "doc_id": doc.doc_id,
                    "title": doc.title,
                    "snippet": doc.snippet,
                    "bucket": doc.bucket,
                    "topic_id": doc.topic_id,
                    "project_id": doc.project_id,
                    "score": round(score_doc(doc), 3),
                    "metadata": doc.metadata,
                }
            )
        return results
