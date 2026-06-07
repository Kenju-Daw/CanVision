"""
J1939 Decoder.
Handles PGN extraction from 29-bit arbitration IDs,
SPN decoding via cantools + DBC, and J1939 validity checks (0xFF/0xFE).
"""

import cantools
from ..models.signal import RawFrame, SignalFrame, UnknownFrame, SignalSource
from .dbc_loader import DBCLoader

# J1939 SPN invalid indicators
INVALID_BYTE = 0xFF          # Parameter not available
ERROR_BYTE   = 0xFE          # Parameter in error condition


def extract_pgn(arbitration_id: int) -> tuple[int, int]:
    """
    Extract (pgn, source_address) from a 29-bit J1939 CAN ID.

    29-bit layout:
    [28:26] Priority (3 bits)
    [25]    Reserved (1 bit)
    [24]    Data Page (1 bit)
    [23:16] PDU Format / PF (8 bits)
    [15:8]  PDU Specific / PS (8 bits) — destination addr (PDU1) or group ext (PDU2)
    [7:0]   Source Address (8 bits)
    """
    source_address = arbitration_id & 0xFF
    pdu_format = (arbitration_id >> 16) & 0xFF  # PF is bits [23:16]

    if pdu_format < 240:
        # PDU1: peer-to-peer. PS = destination SA. PGN = DP + PF only.
        pgn = (arbitration_id >> 8) & 0x3FF00
    else:
        # PDU2: broadcast. PS = group extension. PGN includes PS.
        pgn = (arbitration_id >> 8) & 0x3FFFF

    return pgn, source_address


def is_valid_spn_value(raw_value: float, max_raw: float) -> bool:
    """
    Check if a decoded SPN value is valid (not 0xFF / 0xFE indicator).
    For simplicity we flag values at the maximum range boundary.
    """
    return raw_value is not None and raw_value < max_raw * 0.99


class J1939Decoder:
    """
    Decodes raw CAN frames into J1939 signal frames using:
    1. User DBC (via DBCLoader)
    2. Built-in cantools J1939 database
    3. Fallback to raw unknown frame
    """

    def __init__(self, dbc_loader: DBCLoader):
        self._dbc = dbc_loader

    def decode(self, frame: RawFrame) -> list[SignalFrame | UnknownFrame]:
        """
        Decode a single raw frame.
        Returns a list of SignalFrame (one per SPN) or a single UnknownFrame.
        """
        if not frame.is_extended_id:
            # Standard 11-bit frames — not J1939, try user DBC only
            return self._decode_standard(frame)

        pgn, sa = extract_pgn(frame.arbitration_id)
        data = bytes(frame.data)

        # --- Attempt 1: User DBC via cantools ---
        results = self._decode_via_dbc(frame, pgn, sa, data)
        if results:
            return results

        # --- Attempt 2: J1939 base database lookup ---
        results = self._decode_via_j1939_base(frame, pgn, sa, data)
        if results:
            return results

        # --- Fallback: Unknown frame ---
        return [UnknownFrame(
            ts=frame.ts,
            arbitration_id=frame.arbitration_id,
            arbitration_id_hex=f"0x{frame.arbitration_id:08X}",
            pgn=pgn,
            pgn_hex=f"0x{pgn:04X}",
            source_address=sa,
            dlc=frame.dlc,
            data_hex=" ".join(f"{b:02X}" for b in frame.data),
        )]

    def _decode_via_dbc(
        self, frame: RawFrame, pgn: int, sa: int, data: bytes
    ) -> list[SignalFrame]:
        """Try cantools user DBC decode."""
        if not self._dbc.has_user_dbc():
            return []

        results = self._dbc.decode_frame(frame.arbitration_id, data)
        if not results:
            return []

        signal_frames = []
        for r in results:
            signal_frames.append(SignalFrame(
                ts=frame.ts,
                pgn=pgn,
                pgn_name=r.get("pgn_name", f"PGN_{pgn:04X}"),
                spn=r.get("spn", 0),
                spn_name=r.get("signal_name", ""),
                value=r.get("value"),
                unit=r.get("unit", ""),
                raw_hex=" ".join(f"{b:02X}" for b in frame.data),
                source_address=sa,
                source=SignalSource.USER_DBC,
                channel=frame.channel,
            ))
        return signal_frames

    def _decode_via_j1939_base(
        self, frame: RawFrame, pgn: int, sa: int, data: bytes
    ) -> list[SignalFrame]:
        """
        Decode using the built-in open J1939 signal definitions.
        We look up the PGN, then manually decode each SPN from raw bytes.
        """
        # Get all signal defs for this PGN
        all_defs = self._dbc.get_all_signal_defs()
        pgn_defs = [d for d in all_defs if d.pgn == pgn and d.source == SignalSource.J1939_STANDARD]

        if not pgn_defs:
            return []

        signal_frames = []
        for sig_def in pgn_defs:
            try:
                # Use cantools-style bit extraction
                value = self._extract_signal_value(
                    data,
                    sig_def.scale,
                    sig_def.offset,
                    byte_start=sig_def.byte_start,
                    byte_len=sig_def.byte_len,
                )
                if value is None:
                    continue

                signal_frames.append(SignalFrame(
                    ts=frame.ts,
                    pgn=pgn,
                    pgn_name=sig_def.pgn_name,
                    spn=sig_def.spn,
                    spn_name=sig_def.spn_name,
                    value=round(value, 4),
                    unit=sig_def.unit,
                    raw_hex=" ".join(f"{b:02X}" for b in frame.data),
                    source_address=sa,
                    source=SignalSource.J1939_STANDARD,
                    channel=frame.channel,
                ))
            except Exception:
                continue

        return signal_frames

    def _extract_signal_value(
        self,
        data: bytes,
        scale: float,
        offset: float,
        byte_start: int = 0,
        byte_len: int = 1,
    ) -> float | None:
        """
        Extract a signal value from J1939 payload bytes.
        J1939 uses Intel (little-endian) byte order.
        Skips 0xFF (not available) and 0xFE (error) indicators.
        """
        if not data or byte_start + byte_len > len(data):
            return None
        raw_bytes = data[byte_start: byte_start + byte_len]
        raw = int.from_bytes(raw_bytes, byteorder='little')
        max_raw = (1 << (byte_len * 8)) - 1
        # Skip J1939 invalid (0xFF...) and error (0xFE...) indicators
        if raw >= max_raw - 1:
            return None
        return raw * scale + offset

    def _decode_standard(self, frame: RawFrame) -> list[UnknownFrame]:
        """Handle standard 11-bit frames (non-J1939)."""
        return [UnknownFrame(
            ts=frame.ts,
            arbitration_id=frame.arbitration_id,
            arbitration_id_hex=f"0x{frame.arbitration_id:03X}",
            pgn=frame.arbitration_id,
            pgn_hex=f"0x{frame.arbitration_id:03X}",
            source_address=0,
            dlc=frame.dlc,
            data_hex=" ".join(f"{b:02X}" for b in frame.data),
        )]
