from typing import Iterator
from .base_parser import BaseParser
from ..models.signal import RawFrame


class MF4Parser(BaseParser):
    """
    Parser for ASAM MDF4 / MF4 files.
    Used by CSS Electronics CANedge and other professional data loggers.
    Extracts raw CAN bus logging channels and yields RawFrame objects.
    """

    SUPPORTED_EXTENSIONS = [".mf4", ".mdf", ".mdf4"]

    def parse(self, filepath: str) -> Iterator[RawFrame]:
        try:
            from asammdf import MDF
            mdf = MDF(filepath)

            # Try to extract CAN bus logging (raw frames)
            # asammdf stores raw CAN frames in CAN_DataFrame channels
            bus_channel_groups = self._find_can_channels(mdf)

            if bus_channel_groups:
                yield from self._parse_bus_channels(mdf, bus_channel_groups)
            else:
                # Fallback: try to find any channel with CAN data
                yield from self._parse_generic(mdf)

            mdf.close()

        except ImportError:
            raise RuntimeError("asammdf not installed. Run: pip install asammdf")
        except Exception as e:
            raise ValueError(f"Failed to parse MF4 file: {e}") from e

    def _find_can_channels(self, mdf) -> list:
        """Find CAN bus logging channel groups in the MDF file."""
        bus_groups = []
        for i, group in enumerate(mdf.groups):
            for channel in group.channels:
                name = getattr(channel, 'name', '') or ''
                if 'CAN_DataFrame' in name or 'CAN_BusStatistics' in name:
                    bus_groups.append(i)
                    break
        return bus_groups

    def _parse_bus_channels(self, mdf, group_indices: list) -> Iterator[RawFrame]:
        """Parse MF4 CAN bus logging format (CANedge native)."""
        for group_idx in group_indices:
            try:
                # Extract the CAN_DataFrame channel group as a DataFrame
                df = mdf.get_group(group_idx, raster=None, time_from_zero=False)

                if df is None or df.empty:
                    continue

                # Typical columns: timestamps (index), CAN_DataFrame.BusChannel,
                # CAN_DataFrame.ID, CAN_DataFrame.DLC, CAN_DataFrame.DataLength,
                # CAN_DataFrame.Dir, CAN_DataFrame.DataBytes
                for ts, row in df.iterrows():
                    try:
                        arb_id = int(row.get('CAN_DataFrame.ID', 0))
                        dlc = int(row.get('CAN_DataFrame.DLC', 0))
                        data_bytes_raw = row.get('CAN_DataFrame.DataBytes', b'')

                        if isinstance(data_bytes_raw, (bytes, bytearray)):
                            data = list(data_bytes_raw[:dlc])
                        elif hasattr(data_bytes_raw, '__iter__'):
                            data = [int(b) for b in list(data_bytes_raw)[:dlc]]
                        else:
                            continue

                        yield RawFrame(
                            ts=float(ts),
                            arbitration_id=arb_id,
                            is_extended_id=(arb_id > 0x7FF),
                            dlc=dlc,
                            data=data,
                            channel=int(row.get('CAN_DataFrame.BusChannel', 0)),
                        )
                    except (TypeError, ValueError, KeyError):
                        continue
            except Exception:
                continue

    def _parse_generic(self, mdf) -> Iterator[RawFrame]:
        """
        Fallback: walk all channel groups looking for timestamp + ID + data columns.
        This handles non-standard MF4 files.
        """
        for i in range(len(mdf.groups)):
            try:
                df = mdf.get_group(i, raster=None)
                if df is None or df.empty:
                    continue

                # Look for columns that look like CAN data
                cols = list(df.columns)
                id_col = next((c for c in cols if 'id' in c.lower() or 'ID' in c), None)
                data_col = next((c for c in cols if 'data' in c.lower() or 'Data' in c), None)

                if id_col and data_col:
                    for ts, row in df.iterrows():
                        try:
                            arb_id = int(row[id_col])
                            raw = row[data_col]
                            data = list(bytes(raw)) if isinstance(raw, (bytes, bytearray)) else []
                            yield RawFrame(
                                ts=float(ts),
                                arbitration_id=arb_id,
                                is_extended_id=(arb_id > 0x7FF),
                                dlc=len(data),
                                data=data,
                                channel=i,
                            )
                        except (TypeError, ValueError):
                            continue
            except Exception:
                continue

    def frame_count(self, filepath: str) -> int:
        count = 0
        try:
            for _ in self.parse(filepath):
                count += 1
        except Exception:
            pass
        return count

    def duration(self, filepath: str) -> float:
        from asammdf import MDF
        try:
            mdf = MDF(filepath)
            # asammdf exposes start/end time
            start = float(mdf.header.start_time.timestamp()) if mdf.header.start_time else 0.0
            end = start
            for group in mdf.groups:
                try:
                    t = mdf.get_master(group.channel_group.acq_source, data=None)
                    if t is not None and len(t) > 0:
                        end = max(end, start + float(t[-1]))
                except Exception:
                    pass
            mdf.close()
            return end - start
        except Exception:
            return 0.0
