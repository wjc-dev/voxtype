from enum import Enum, auto


class InputState(Enum):
    """The complete state surface of the voice-input application."""

    IDLE = auto()
    RECORDING = auto()
    STREAMING = auto()
    PROCESSING = auto()
    WARNING = auto()
    ERROR = auto()

    @property
    def is_recording(self) -> bool:
        return self in (InputState.RECORDING, InputState.STREAMING)

    @property
    def can_start_recording(self) -> bool:
        return self == InputState.IDLE
