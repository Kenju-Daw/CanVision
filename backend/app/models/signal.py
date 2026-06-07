from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum


class SignalSource(str, Enum):
    USER_DBC = "user_dbc"
    J1939_STANDARD = "j1939_standard"
    UNKNOWN = "unknown"


class GaugeType(str, Enum):
    TACHOMETER = "tachometer"
    SPEEDOMETER = "speedometer"
    THERMOMETER = "thermometer"
    BAR = "bar"
    NUMERIC = "numeric"
    LED = "led"


class SignalDefinition(BaseModel):
    pgn: int
    pgn_name: str = ""
    spn: int = 0
    spn_name: str = ""
    start_bit: int = 0
    length: int = 0
    scale: float = 1.0
    offset: float = 0.0
    unit: str = ""
    min_value: float = 0.0
    max_value: float = 0.0
    display_min: float = 0.0
    display_max: float = 100.0
    warn_threshold: Optional[float] = None
    crit_threshold: Optional[float] = None
    byte_start: int = 0
    byte_len: int = 1
    gauge_type: GaugeType = GaugeType.NUMERIC
    source: SignalSource = SignalSource.UNKNOWN
    enabled: bool = True


class SignalDefinitionUpdate(BaseModel):
    pgn_name: Optional[str] = None
    spn_name: Optional[str] = None
    scale: Optional[float] = None
    offset: Optional[float] = None
    unit: Optional[str] = None
    display_min: Optional[float] = None
    display_max: Optional[float] = None
    warn_threshold: Optional[float] = None
    crit_threshold: Optional[float] = None
    gauge_type: Optional[GaugeType] = None
    enabled: Optional[bool] = None


class RawFrame(BaseModel):
    """A raw CAN frame as parsed from a log file."""
    ts: float                    # Unix timestamp or relative seconds
    arbitration_id: int
    is_extended_id: bool = True
    dlc: int
    data: list[int]              # 0-8 bytes
    channel: int = 0
    is_error_frame: bool = False


class SignalFrame(BaseModel):
    """A decoded signal value ready for WebSocket broadcast."""
    type: Literal["signal"] = "signal"
    ts: float
    pgn: int
    pgn_name: str
    spn: int
    spn_name: str
    value: Optional[float]
    unit: str
    raw_hex: str
    source_address: int
    source: SignalSource
    channel: int = 0


class UnknownFrame(BaseModel):
    """A raw frame that couldn't be decoded."""
    type: Literal["unknown"] = "unknown"
    ts: float
    arbitration_id: int
    arbitration_id_hex: str
    pgn: int
    pgn_hex: str
    source_address: int
    dlc: int
    data_hex: str


class StatusMessage(BaseModel):
    type: Literal["status"] = "status"
    event: str
    detail: str = ""


class FileInfo(BaseModel):
    file_id: str
    filename: str
    format: str
    size_bytes: int
    frame_count: Optional[int] = None
    duration_s: Optional[float] = None


class ReplayConfig(BaseModel):
    file_id: str
    speed: float = Field(default=1.0, ge=0.1, le=100.0)
    start_ts: Optional[float] = None
    end_ts: Optional[float] = None
