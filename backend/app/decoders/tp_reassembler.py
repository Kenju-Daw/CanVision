"""
J1939 Transport Protocol reassembler.
Handles BAM (Broadcast Announce Message) and basic CMDT (Connection Mode Data Transfer).

J1939-21 TP Control Messages:
  PGN 60416 (0xEC00) = TP.CM — connection management / BAM announce
  PGN 60160 (0xEB00) = TP.DT — data transfer frames

BAM sequence:
  1. TP.CM with control byte 0x20 → announces target PGN + total size + packet count
  2. N x TP.DT frames → data payload bytes
  → reassemble and yield as a single large frame
"""

from dataclasses import dataclass, field
from typing import Iterator, Optional
from ..models.signal import RawFrame

TP_CM_PGN = 0xEC00   # 60416
TP_DT_PGN = 0xEB00   # 60160

BAM_CONTROL_BYTE = 0x20
RTS_CONTROL_BYTE = 0x10
CTS_CONTROL_BYTE = 0x11
EOM_CONTROL_BYTE = 0x13   # End of Message Acknowledge
ABORT_CONTROL_BYTE = 0xFF


@dataclass
class BAMSession:
    source_address: int
    target_pgn: int
    total_bytes: int
    total_packets: int
    ts_start: float
    channel: int
    packets: dict = field(default_factory=dict)  # sequence_num -> 7 bytes

    def is_complete(self) -> bool:
        return len(self.packets) == self.total_packets

    def assemble(self) -> bytes:
        result = bytearray()
        for seq in range(1, self.total_packets + 1):
            result.extend(self.packets.get(seq, b'\xff' * 7))
        return bytes(result[:self.total_bytes])


def _extract_pgn(arbitration_id: int) -> tuple[int, int]:
    """
    Extract PGN and source address from a 29-bit J1939 arbitration ID.
    Returns (pgn, source_address).
    """
    source_address = arbitration_id & 0xFF
    pdu_format = (arbitration_id >> 16) & 0xFF  # PF is bits [23:16]

    if pdu_format < 240:
        # PDU1: destination-specific. PGN does NOT include PDU Specific byte.
        pgn = (arbitration_id >> 8) & 0x3FF00
    else:
        # PDU2: broadcast. PGN includes PDU Specific byte.
        pgn = (arbitration_id >> 8) & 0x3FFFF

    return pgn, source_address


class TPReassembler:
    """
    Stateful J1939 Transport Protocol reassembler.
    Feed frames in order; get back either the original frame or a reassembled large frame.
    """

    def __init__(self):
        # Key: (source_address, channel) -> BAMSession
        self._sessions: dict[tuple, BAMSession] = {}

    def process(self, frame: RawFrame) -> Iterator[RawFrame]:
        """
        Process a single raw CAN frame.
        Yields:
          - The original frame if it's not a TP frame
          - Nothing if it's a TP.CM or TP.DT fragment
          - A reassembled 'virtual' frame when a BAM session completes
        """
        if not frame.is_extended_id or len(frame.data) != 8:
            yield frame
            return

        pgn, sa = _extract_pgn(frame.arbitration_id)

        # TP.CM frame?
        if pgn == TP_CM_PGN:
            yield from self._handle_tp_cm(frame, sa)
            return

        # TP.DT frame?
        if pgn == TP_DT_PGN:
            yield from self._handle_tp_dt(frame, sa)
            return

        # Normal frame — pass through
        yield frame

    def _handle_tp_cm(self, frame: RawFrame, sa: int) -> Iterator[RawFrame]:
        data = frame.data
        control = data[0]
        key = (sa, frame.channel)

        if control == BAM_CONTROL_BYTE:
            total_bytes = data[1] | (data[2] << 8)
            total_packets = data[3]
            # Bytes 4 is 0xFF (reserved)
            target_pgn = data[5] | (data[6] << 8) | (data[7] << 16)

            self._sessions[key] = BAMSession(
                source_address=sa,
                target_pgn=target_pgn,
                total_bytes=total_bytes,
                total_packets=total_packets,
                ts_start=frame.ts,
                channel=frame.channel,
            )

        elif control == ABORT_CONTROL_BYTE:
            self._sessions.pop(key, None)

        # No frame yield for CM messages — they're internal TP overhead
        return
        yield  # make this a generator

    def _handle_tp_dt(self, frame: RawFrame, sa: int) -> Iterator[RawFrame]:
        key = (sa, frame.channel)
        session = self._sessions.get(key)

        if session is None:
            # DT without prior CM — drop it
            return
        yield  # placeholder; real yields below

        seq_num = frame.data[0]  # 1-indexed sequence number
        payload = frame.data[1:8]  # 7 payload bytes per DT frame
        session.packets[seq_num] = bytes(payload)

        if session.is_complete():
            assembled_data = session.assemble()
            del self._sessions[key]

            # Build a synthetic 'virtual' RawFrame with the reassembled PGN
            # Reconstruct a 29-bit arbitration ID for the target PGN:
            # Priority=6, PGN=target_pgn, SA=source_address
            priority = 6
            reconstructed_id = (priority << 26) | (session.target_pgn << 8) | sa

            yield RawFrame(
                ts=session.ts_start,
                arbitration_id=reconstructed_id,
                is_extended_id=True,
                dlc=len(assembled_data),
                data=list(assembled_data),
                channel=session.channel,
            )

    def _handle_tp_dt(self, frame: RawFrame, sa: int) -> Iterator[RawFrame]:  # noqa: F811
        """Corrected implementation (replaces placeholder above)."""
        key = (sa, frame.channel)
        session = self._sessions.get(key)

        if session is None:
            return

        seq_num = frame.data[0]
        payload = bytes(frame.data[1:8])
        session.packets[seq_num] = payload

        if session.is_complete():
            assembled_data = session.assemble()
            del self._sessions[key]

            priority = 6
            reconstructed_id = (priority << 26) | (session.target_pgn << 8) | sa

            yield RawFrame(
                ts=session.ts_start,
                arbitration_id=reconstructed_id,
                is_extended_id=True,
                dlc=len(assembled_data),
                data=list(assembled_data),
                channel=session.channel,
            )

    def clear(self):
        """Reset all sessions (call between file replays)."""
        self._sessions.clear()
