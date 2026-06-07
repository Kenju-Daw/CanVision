from abc import ABC, abstractmethod
from typing import Iterator
from ..models.signal import RawFrame


class BaseParser(ABC):
    """
    Abstract base class for all CAN log file parsers.
    Each parser must yield RawFrame objects in chronological order.
    """

    SUPPORTED_EXTENSIONS: list[str] = []

    @abstractmethod
    def parse(self, filepath: str) -> Iterator[RawFrame]:
        """
        Parse a log file and yield RawFrame objects.
        Timestamps should be in seconds (relative or absolute).
        """
        ...

    @abstractmethod
    def frame_count(self, filepath: str) -> int:
        """Return total number of frames in the file (may require full scan)."""
        ...

    @abstractmethod
    def duration(self, filepath: str) -> float:
        """Return duration of the log in seconds."""
        ...

    @classmethod
    def supports(cls, filename: str) -> bool:
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        return ext in cls.SUPPORTED_EXTENSIONS
