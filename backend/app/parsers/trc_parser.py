from typing import Iterator
import can
from .base_parser import BaseParser
from ..models.signal import RawFrame


class TRCParser(BaseParser):
    """
    Parser for PEAK PCAN-Explorer .trc files (v1.1 and v2.0).
    Uses python-can TRCReader under the hood.
    """

    SUPPORTED_EXTENSIONS = [".trc"]

    def parse(self, filepath: str) -> Iterator[RawFrame]:
        try:
            with can.TRCReader(filepath) as reader:
                for msg in reader:
                    if msg is None:
                        continue
                    if msg.is_error_frame:
                        continue
                    yield RawFrame(
                        ts=msg.timestamp,
                        arbitration_id=msg.arbitration_id,
                        is_extended_id=msg.is_extended_id,
                        dlc=msg.dlc,
                        data=list(msg.data),
                        channel=0,
                        is_error_frame=False,
                    )
        except Exception as e:
            raise ValueError(f"Failed to parse TRC file: {e}") from e

    def frame_count(self, filepath: str) -> int:
        count = 0
        try:
            with can.TRCReader(filepath) as reader:
                for msg in reader:
                    if msg and not msg.is_error_frame:
                        count += 1
        except Exception:
            pass
        return count

    def duration(self, filepath: str) -> float:
        first_ts = None
        last_ts = None
        try:
            with can.TRCReader(filepath) as reader:
                for msg in reader:
                    if msg is None:
                        continue
                    if first_ts is None:
                        first_ts = msg.timestamp
                    last_ts = msg.timestamp
        except Exception:
            pass
        if first_ts is not None and last_ts is not None:
            return last_ts - first_ts
        return 0.0
