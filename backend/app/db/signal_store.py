"""
Signal store — in-memory state for live signal values and session statistics.
Thread-safe for concurrent WebSocket reads.
"""

import threading
import time
from collections import defaultdict, deque
from ..models.signal import SignalFrame, SignalDefinition


class SignalStats:
    """Running statistics for a single signal within a session."""
    __slots__ = ("min_val", "max_val", "sum_val", "count", "last_ts", "rate_window")

    def __init__(self, initial_value: float, ts: float):
        self.min_val = initial_value
        self.max_val = initial_value
        self.sum_val = initial_value
        self.count = 1
        self.last_ts = ts
        self.rate_window: deque = deque(maxlen=20)  # last 20 timestamps for rate calc
        self.rate_window.append(ts)

    def update(self, value: float, ts: float):
        self.min_val = min(self.min_val, value)
        self.max_val = max(self.max_val, value)
        self.sum_val += value
        self.count += 1
        self.last_ts = ts
        self.rate_window.append(ts)

    @property
    def avg(self) -> float:
        return self.sum_val / self.count if self.count > 0 else 0.0

    @property
    def rate_hz(self) -> float:
        w = self.rate_window
        if len(w) < 2:
            return 0.0
        span = w[-1] - w[0]
        return (len(w) - 1) / span if span > 0 else 0.0


class SignalStore:
    """
    Thread-safe in-memory store for:
    - Latest decoded signal values
    - Per-signal session statistics (min/max/avg/rate)
    - Signal definitions (editable)
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._latest: dict[str, SignalFrame] = {}     # key -> latest frame
        self._stats: dict[str, SignalStats] = {}      # key -> stats
        self._defs: dict[int, SignalDefinition] = {}  # spn -> definition
        self._user_overrides: dict[int, dict] = {}    # spn -> overridden fields

    def _key(self, frame: SignalFrame) -> str:
        return f"{frame.pgn}:{frame.spn}:{frame.source_address}"

    def update(self, frame: SignalFrame):
        """Update store with a new decoded signal frame."""
        if frame.value is None:
            return
        key = self._key(frame)
        with self._lock:
            if key in self._stats:
                self._stats[key].update(frame.value, frame.ts)
            else:
                self._stats[key] = SignalStats(frame.value, frame.ts)
            self._latest[key] = frame

    def get_latest(self) -> list[dict]:
        """Return all latest signal values with statistics as dicts."""
        with self._lock:
            result = []
            for key, frame in self._latest.items():
                stats = self._stats.get(key)
                result.append({
                    **frame.model_dump(),
                    "session_min": round(stats.min_val, 4) if stats else frame.value,
                    "session_max": round(stats.max_val, 4) if stats else frame.value,
                    "session_avg": round(stats.avg, 4) if stats else frame.value,
                    "rate_hz": round(stats.rate_hz, 2) if stats else 0.0,
                })
            return result

    def get_signal_value(self, pgn: int, spn: int, sa: int = 0) -> dict | None:
        key = f"{pgn}:{spn}:{sa}"
        with self._lock:
            frame = self._latest.get(key)
            if frame is None:
                return None
            stats = self._stats.get(key)
            return {
                **frame.model_dump(),
                "session_min": stats.min_val if stats else None,
                "session_max": stats.max_val if stats else None,
                "session_avg": stats.avg if stats else None,
                "rate_hz": stats.rate_hz if stats else 0.0,
            }

    def update_definition(self, spn: int, overrides: dict):
        """Apply user overrides to a signal definition."""
        with self._lock:
            existing = self._user_overrides.get(spn, {})
            existing.update({k: v for k, v in overrides.items() if v is not None})
            self._user_overrides[spn] = existing

    def get_overrides(self, spn: int) -> dict:
        with self._lock:
            return self._user_overrides.get(spn, {})

    def reset_session(self):
        """Clear all signal values and statistics (between file replays)."""
        with self._lock:
            self._latest.clear()
            self._stats.clear()

    def signal_count(self) -> int:
        with self._lock:
            return len(self._latest)
