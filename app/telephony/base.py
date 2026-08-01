from abc import ABC, abstractmethod
from typing import AsyncIterator


class TelephonyAdapter(ABC):
    """Abstract base class for telephony providers."""

    @abstractmethod
    async def answer_call(self, call_id: str) -> dict:
        pass

    @abstractmethod
    async def hangup_call(self, call_id: str) -> dict:
        pass

    @abstractmethod
    async def play_audio(self, call_id: str, audio_url: str) -> dict:
        pass

    @abstractmethod
    async def gather_dtmf(self, call_id: str, num_digits: int, timeout: int) -> dict:
        pass

    @abstractmethod
    async def stream_audio(self, call_id: str, audio_chunks: AsyncIterator[bytes]) -> None:
        pass

    @abstractmethod
    def get_webhook_routes(self) -> list:
        pass

    @abstractmethod
    async def start_recording(self, call_id: str) -> str:
        pass

    @abstractmethod
    async def stop_recording(self, call_id: str) -> str:
        pass
