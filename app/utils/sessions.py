import logging
from datetime import datetime, timedelta
from app.models.schemas import CallSession, CallState

logger = logging.getLogger(__name__)

SESSION_TTL = timedelta(hours=1)


class SessionManager:
    def __init__(self):
        self._sessions: dict[str, CallSession] = {}

    def create_session(self, call_id: str, phone_number: str) -> CallSession:
        self._cleanup()
        session = CallSession(call_id=call_id, phone_number=phone_number)
        self._sessions[call_id] = session
        logger.info(f"Session created for call {call_id}")
        return session

    def get_session(self, call_id: str) -> CallSession | None:
        return self._sessions.get(call_id)

    def update_session(self, session: CallSession) -> None:
        self._sessions[session.call_id] = session

    def end_session(self, call_id: str) -> CallSession | None:
        session = self._sessions.get(call_id)
        if session:
            session.state = CallState.COMPLETED
            session.ended_at = datetime.now()
            logger.info(f"Session ended for call {call_id}")
        return session

    def get_all_sessions(self) -> list[CallSession]:
        return list(self._sessions.values())

    def _cleanup(self):
        now = datetime.now()
        expired = [
            cid for cid, s in self._sessions.items()
            if s.state == CallState.COMPLETED
            and s.ended_at
            and (now - s.ended_at) > SESSION_TTL
        ]
        for cid in expired:
            del self._sessions[cid]


session_manager = SessionManager()
