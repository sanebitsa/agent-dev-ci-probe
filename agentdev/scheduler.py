"""Local scheduling reference backend, not a GitHub ownership authority.

GitHub production dispatch must use a serialized, trusted single-writer controller.
File locks here protect only coordinators sharing a filesystem.
"""
from __future__ import annotations

import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4
from .contracts import Task, scopes_overlap


@contextmanager
def locked_state(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    lockpath = path.with_suffix(path.suffix + ".lock")
    with lockpath.open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        state = json.loads(path.read_text()) if path.exists() else {"claimed": {}, "done": []}
        yield state
        fd, name = tempfile.mkstemp(prefix=".state-", dir=path.parent)
        try:
            with os.fdopen(fd, "w") as out:
                json.dump(state, out, indent=2, sort_keys=True)
                out.write("\n")
                out.flush()
                os.fsync(out.fileno())
            os.replace(name, path)
        finally:
            if os.path.exists(name):
                os.unlink(name)
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def _reject_dependency_cycles(tasks: list[Task]) -> None:
    """Fail closed on cycles entirely within the supplied task snapshot."""
    graph = {task.issue_number: set(task.dependencies) for task in tasks}
    visited: set[int] = set()
    visiting: set[int] = set()

    def visit(number: int) -> None:
        if number in visiting:
            raise ValueError("cyclic task dependencies")
        if number in visited:
            return
        visiting.add(number)
        for dep in graph[number]:
            if dep in graph:
                visit(dep)
        visiting.remove(number)
        visited.add(number)

    for number in graph:
        visit(number)


def claim_ready(tasks: list[Task], state_file: Path, *, max_agents: int = 2) -> list[dict]:
    if max_agents not in (1, 2, 3):
        raise ValueError("agent concurrency must be between 1 and 3")
    if len({t.issue_number for t in tasks}) != len(tasks):
        raise ValueError("duplicate issue numbers in input")
    _reject_dependency_cycles(tasks)
    claimed_now = []
    with locked_state(state_file) as state:
        done = set(state["done"])
        claimed = state["claimed"]
        occupied = [entry["write_paths"] for entry in claimed.values()]
        for task in sorted(tasks, key=lambda t: t.issue_number):
            if len(claimed) >= max_agents:
                break
            ident = str(task.issue_number)
            if ident in claimed or task.mode != "AFK" or task.risk == "restricted" or not set(task.dependencies) <= done:
                continue
            if any(scopes_overlap(list(task.write_paths), paths) for paths in occupied):
                continue
            entry = {"run_id": str(uuid4()), "branch": task.branch, "base_sha": task.base_sha,
                     "mode": task.mode,
                     "write_paths": list(task.write_paths), "runtime": task.runtime, "status": "claimed"}
            claimed[ident] = entry
            occupied.append(entry["write_paths"])
            claimed_now.append({"issue_number": task.issue_number, **entry})
    return claimed_now