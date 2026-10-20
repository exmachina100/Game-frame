"""Load and validate portable GameFrame Pong shot plans."""
from __future__ import annotations
import json
from pathlib import Path
from .timeline import Beat

SCHEMA = "gameframe.pong.shots.v1"


def load_shot_plan(path: str | Path) -> list[Beat]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA or payload.get("system") != "pong":
        raise ValueError("Unsupported GameFrame shot plan")
    rows = payload.get("beats")
    if not isinstance(rows, list) or not rows or len(rows) > 1000:
        raise ValueError("Shot plan requires 1–1000 beats")
    return [Beat(**row) for row in rows]
