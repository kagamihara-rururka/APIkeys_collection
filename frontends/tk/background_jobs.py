"""Small single-flight helpers for Tk background work.

Tk workflows still own user-facing status text and service calls.  This module
only protects a shared invariant: one logical job key should not spawn multiple
daemon threads while it is already active.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

TkJobKey = tuple[str, str, str]


@dataclass(frozen=True)
class TkBackgroundJobStartResult:
    """Structured result for one bounded Tk worker start attempt.

    Existing workflows still use the bool-returning wrapper below.  This
    result object gives diagnostics and future UI surfaces a stable way to tell
    whether a worker started, was rejected as a duplicate, or hit capacity.
    """

    job_key: TkJobKey
    started: bool
    reason: str
    active_job_count: int
    max_active_jobs: int | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_key": list(self.job_key),
            "started": self.started,
            "reason": self.reason,
            "active_job_count": self.active_job_count,
            "max_active_jobs": self.max_active_jobs,
        }


def start_single_flight_thread(
    owner: object,
    job_key: TkJobKey,
    target: Callable[..., None],
    args: tuple[Any, ...],
    *,
    active_jobs_attr: str,
    active_jobs_lock_attr: str,
    on_duplicate: Callable[[], None],
    max_active_jobs: int | None = None,
    on_capacity: Callable[[], None] | None = None,
) -> bool:
    """Start a daemon thread unless the key or owner is already saturated."""

    return start_single_flight_thread_result(
        owner,
        job_key,
        target,
        args,
        active_jobs_attr=active_jobs_attr,
        active_jobs_lock_attr=active_jobs_lock_attr,
        on_duplicate=on_duplicate,
        max_active_jobs=max_active_jobs,
        on_capacity=on_capacity,
    ).started


def start_single_flight_thread_result(
    owner: object,
    job_key: TkJobKey,
    target: Callable[..., None],
    args: tuple[Any, ...],
    *,
    active_jobs_attr: str,
    active_jobs_lock_attr: str,
    on_duplicate: Callable[[], None],
    max_active_jobs: int | None = None,
    on_capacity: Callable[[], None] | None = None,
) -> TkBackgroundJobStartResult:
    """Start a daemon thread and return a diagnostic outcome object."""

    active_jobs = _active_job_set(owner, active_jobs_attr)
    active_jobs_lock = _active_job_lock(owner, active_jobs_lock_attr)
    with active_jobs_lock:
        if job_key in active_jobs:
            on_duplicate()
            return TkBackgroundJobStartResult(
                job_key=job_key,
                started=False,
                reason="duplicate",
                active_job_count=len(active_jobs),
                max_active_jobs=max_active_jobs,
            )
        if max_active_jobs is not None and len(active_jobs) >= max_active_jobs:
            if on_capacity is not None:
                on_capacity()
            else:
                on_duplicate()
            return TkBackgroundJobStartResult(
                job_key=job_key,
                started=False,
                reason="capacity",
                active_job_count=len(active_jobs),
                max_active_jobs=max_active_jobs,
            )
        active_jobs.add(job_key)
        active_job_count = len(active_jobs)

    def runner(*worker_args: Any) -> None:
        try:
            target(*worker_args)
        finally:
            release_single_flight_job(
                owner,
                job_key,
                active_jobs_attr=active_jobs_attr,
                active_jobs_lock_attr=active_jobs_lock_attr,
            )

    try:
        threading.Thread(target=runner, args=args, daemon=True).start()
    except Exception:
        release_single_flight_job(
            owner,
            job_key,
            active_jobs_attr=active_jobs_attr,
            active_jobs_lock_attr=active_jobs_lock_attr,
        )
        raise
    return TkBackgroundJobStartResult(
        job_key=job_key,
        started=True,
        reason="started",
        active_job_count=active_job_count,
        max_active_jobs=max_active_jobs,
    )


def single_flight_job_is_active(
    owner: object,
    job_key: TkJobKey,
    *,
    active_jobs_attr: str,
    on_duplicate: Callable[[], None] | None = None,
) -> bool:
    """Return whether a job key is active, optionally firing duplicate UI feedback."""

    active_jobs = getattr(owner, active_jobs_attr, None)
    if isinstance(active_jobs, set) and job_key in active_jobs:
        if on_duplicate is not None:
            on_duplicate()
        return True
    return False


def release_single_flight_job(
    owner: object,
    job_key: TkJobKey,
    *,
    active_jobs_attr: str,
    active_jobs_lock_attr: str,
) -> None:
    """Release a job key if the owner still has the matching active-job set."""

    active_jobs = getattr(owner, active_jobs_attr, None)
    if not isinstance(active_jobs, set):
        return
    active_jobs_lock = getattr(owner, active_jobs_lock_attr, None)
    if active_jobs_lock is None:
        active_jobs.discard(job_key)
        return
    with active_jobs_lock:
        active_jobs.discard(job_key)


def _active_job_set(owner: object, attr: str) -> set[TkJobKey]:
    active_jobs = getattr(owner, attr, None)
    if not isinstance(active_jobs, set):
        active_jobs = set()
        setattr(owner, attr, active_jobs)
    return active_jobs


def _active_job_lock(owner: object, attr: str) -> threading.Lock:
    active_jobs_lock = getattr(owner, attr, None)
    if active_jobs_lock is None:
        active_jobs_lock = threading.Lock()
        setattr(owner, attr, active_jobs_lock)
    return active_jobs_lock


__all__ = [
    "TkBackgroundJobStartResult",
    "TkJobKey",
    "release_single_flight_job",
    "single_flight_job_is_active",
    "start_single_flight_thread",
    "start_single_flight_thread_result",
]
