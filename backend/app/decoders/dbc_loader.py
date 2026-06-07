"""
DBC Loader using cantools.
Merges user-uploaded DBC with the built-in open J1939 base database.
Priority: user DBC > J1939 open DB > unknown.
"""

import json
import os
import cantools
from cantools.database import Database, Message, Signal
from ..models.signal import SignalDefinition, SignalSource, GaugeType

# Path to bundled open J1939 base database
_J1939_BASE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "data", "j1939_base.json"
)


class DBCLoader:
    """
    Manages the merged signal definition database.
    Thread-safe for reads; writes (upload) should be serialized.
    """

    def __init__(self):
        self._user_db: Database | None = None
        self._j1939_base: dict = {}       # pgn_hex -> {pgn_name, spns: {spn_id -> def}}
        self._signal_defs: dict[int, SignalDefinition] = {}  # spn -> SignalDefinition
        self._pgn_to_msg: dict[int, Message] = {}            # pgn -> cantools Message

        self._load_j1939_base()

    def _load_j1939_base(self):
        """Load the bundled open-source J1939 PGN/SPN database."""
        try:
            if os.path.exists(_J1939_BASE_PATH):
                with open(_J1939_BASE_PATH, "r") as f:
                    self._j1939_base = json.load(f)
                self._rebuild_signal_defs()  # Populate defs immediately
        except Exception as e:
            print(f"[DBCLoader] Could not load J1939 base DB: {e}")

    def load_dbc(self, filepath: str) -> int:
        """
        Load a user DBC file. Returns number of messages loaded.
        Merges with J1939 base; user DBC takes priority on conflicts.
        """
        try:
            db = cantools.database.load_file(filepath)
            self._user_db = db
            self._rebuild_signal_defs()
            return len(db.messages)
        except Exception as e:
            raise ValueError(f"Failed to load DBC file: {e}") from e

    def _rebuild_signal_defs(self):
        """Rebuild the merged signal definition lookup table."""
        self._signal_defs.clear()
        self._pgn_to_msg.clear()

        # 1. Load J1939 base definitions first (lower priority)
        for pgn_hex, pgn_def in self._j1939_base.get("pgns", {}).items():
            try:
                pgn = int(pgn_hex, 16) if pgn_hex.startswith("0x") else int(pgn_hex)
                for spn_str, spn_def in pgn_def.get("spns", {}).items():
                    spn = int(spn_str)
                    self._signal_defs[spn] = SignalDefinition(
                        pgn=pgn,
                        pgn_name=pgn_def.get("name", f"PGN_{pgn}"),
                        spn=spn,
                        spn_name=spn_def.get("name", f"SPN_{spn}"),
                        scale=float(spn_def.get("scale", 1.0)),
                        offset=float(spn_def.get("offset", 0.0)),
                        unit=spn_def.get("unit", ""),
                        min_value=float(spn_def.get("min", 0.0)),
                        max_value=float(spn_def.get("max", 0.0)),
                        display_min=float(spn_def.get("min", 0.0)),
                        display_max=float(spn_def.get("max", 100.0)),
                        gauge_type=GaugeType(spn_def.get("gauge_type", "numeric")),
                        source=SignalSource.J1939_STANDARD,
                    )
            except (ValueError, KeyError):
                continue

        # 2. Layer user DBC on top (higher priority)
        if self._user_db is not None:
            for msg in self._user_db.messages:
                pgn = self._pgn_from_message(msg)
                if pgn is not None:
                    self._pgn_to_msg[pgn] = msg

                for sig in msg.signals:
                    # Try to extract SPN from signal comment or name
                    spn = self._spn_from_signal(sig)
                    sig_def = SignalDefinition(
                        pgn=pgn if pgn is not None else msg.frame_id,
                        pgn_name=msg.name or f"MSG_{msg.frame_id:04X}",
                        spn=spn,
                        spn_name=sig.name,
                        scale=float(sig.scale) if sig.scale else 1.0,
                        offset=float(sig.offset) if sig.offset else 0.0,
                        unit=sig.unit or "",
                        min_value=float(sig.minimum) if sig.minimum is not None else 0.0,
                        max_value=float(sig.maximum) if sig.maximum is not None else 0.0,
                        display_min=float(sig.minimum) if sig.minimum is not None else 0.0,
                        display_max=float(sig.maximum) if sig.maximum is not None else 100.0,
                        source=SignalSource.USER_DBC,
                    )
                    # Use SPN as key if available, else use signal name hash
                    key = spn if spn > 0 else hash(f"{pgn}_{sig.name}")
                    self._signal_defs[key] = sig_def

    def _pgn_from_message(self, msg: Message) -> int | None:
        """Extract PGN from a J1939-mode cantools message."""
        try:
            # cantools J1939 mode stores PGN in message frame_id (after masking)
            if hasattr(msg, 'protocol') and msg.protocol == 'j1939':
                return msg.pgn
            # Manual extraction from extended ID
            fid = msg.frame_id
            if fid > 0x7FF:  # extended
                pdu_format = (fid >> 8) & 0xFF
                if pdu_format >= 240:
                    return (fid >> 8) & 0x3FFFF
                else:
                    return (fid >> 8) & 0x3FF00
        except Exception:
            pass
        return None

    def _spn_from_signal(self, sig: Signal) -> int:
        """Try to extract SPN number from signal name or comment."""
        # Many J1939 DBCs encode SPN in signal name like "SPN_190" or "EngineSpeed_190"
        import re
        patterns = [
            r'SPN[_\s]?(\d+)',
            r'[Ss]pn[_\s]?(\d+)',
            r'_(\d{3,5})$',
        ]
        name = sig.name or ""
        comment = sig.comment or ""
        for text in [name, comment]:
            for pat in patterns:
                m = re.search(pat, text)
                if m:
                    return int(m.group(1))
        return 0

    def decode_frame(self, frame_id: int, data: bytes) -> list[dict]:
        """
        Attempt to decode a CAN frame using the user DBC first, then J1939 base.
        Returns list of decoded signal dicts.
        """
        results = []

        # Try user DBC
        if self._user_db is not None:
            try:
                msg = self._user_db.get_message_by_id(frame_id)
                decoded = msg.decode(data, decode_choices=False, allow_truncated=True)
                for sig_name, value in decoded.items():
                    sig = msg.get_signal_by_name(sig_name)
                    results.append({
                        "signal_name": sig_name,
                        "value": float(value) if isinstance(value, (int, float)) else None,
                        "unit": sig.unit or "",
                        "source": SignalSource.USER_DBC,
                    })
                return results
            except (KeyError, cantools.database.errors.DecodeError):
                pass

        return results

    def get_signal_def(self, spn: int) -> SignalDefinition | None:
        return self._signal_defs.get(spn)

    def get_all_signal_defs(self) -> list[SignalDefinition]:
        return list(self._signal_defs.values())

    def get_pgn_message(self, pgn: int) -> Message | None:
        return self._pgn_to_msg.get(pgn)

    def has_user_dbc(self) -> bool:
        return self._user_db is not None

    def signal_count(self) -> int:
        return len(self._signal_defs)
