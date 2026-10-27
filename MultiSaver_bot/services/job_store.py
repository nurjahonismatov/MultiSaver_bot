import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class MediaJob:
    job_id: str
    user_id: int
    files: List[Path]
    media_type: str
    platform: str
    original_url: Optional[str]
    can_extract_audio: bool
    created_at: float = field(default_factory=time.time)


class JobStore:
    """Short-lived store of download jobs (TTL ~ 1 hour)."""

    def __init__(self, ttl_seconds: int = 3600):
        self._jobs: Dict[str, MediaJob] = {}
        self.ttl = ttl_seconds

    def create(
        self,
        user_id: int,
        files: List[Path],
        media_type: str,
        platform: str,
        original_url: Optional[str] = None,
        can_extract_audio: bool = False,
    ) -> str:
        self._cleanup()
        job_id = uuid.uuid4().hex[:12]
        self._jobs[job_id] = MediaJob(
            job_id=job_id,
            user_id=user_id,
            files=files,
            media_type=media_type,
            platform=platform,
            original_url=original_url,
            can_extract_audio=can_extract_audio,
        )
        return job_id

    def get(self, job_id: str, user_id: int) -> Optional[MediaJob]:
        self._cleanup()
        job = self._jobs.get(job_id)
        if job is None:
            return None
        if job.user_id != user_id:
            return None
        return job

    def remove(self, job_id: str) -> None:
        self._jobs.pop(job_id, None)

    def _cleanup(self) -> None:
        now = time.time()
        expired = [k for k, v in self._jobs.items() if now - v.created_at > self.ttl]
        for k in expired:
            del self._jobs[k]


_store: Optional[JobStore] = None


def get_job_store() -> JobStore:
    global _store
    if _store is None:
        _store = JobStore()
    return _store