import logging
import json
from datetime import datetime
from pathlib import Path
from app.models.schemas import CallSession

logger = logging.getLogger(__name__)


class CallLogger:
    def __init__(self, log_dir: str = "./data/calls"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_call(self, session: CallSession):
        log_data = {
            "call_id": session.call_id,
            "phone_number": session.phone_number,
            "language": session.language.value if session.language else None,
            "state": session.state.value,
            "started_at": session.started_at.isoformat(),
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "transcript": [
                {
                    "role": entry.role,
                    "text": entry.text,
                    "timestamp": entry.timestamp.isoformat(),
                    "language": entry.language.value if entry.language else None,
                }
                for entry in session.transcript
            ],
            "recording_url": session.recording_url,
            "metadata": session.metadata,
        }

        log_file = self.log_dir / f"{session.call_id}.json"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Call logged: {session.call_id}")

    def get_call_log(self, call_id: str) -> dict | None:
        log_file = self.log_dir / f"{call_id}.json"
        if not log_file.exists():
            return None

        with open(log_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_all_call_logs(self) -> list[dict]:
        logs = []
        for log_file in self.log_dir.glob("*.json"):
            with open(log_file, "r", encoding="utf-8") as f:
                logs.append(json.load(f))
        return logs
