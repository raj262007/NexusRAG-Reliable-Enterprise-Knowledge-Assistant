import time
from typing import List, Dict, Any, Optional
from uuid import uuid4


class ConversationManager:
    """
    In-memory conversation manager for multi-turn sessions with bounded history.
    """
    def __init__(self, max_history_turns: int = 6, ttl_seconds: int = 86400):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.max_history_turns = max_history_turns
        self.ttl_seconds = ttl_seconds

    def create_session(self, session_id: Optional[str] = None) -> str:
        s_id = session_id or str(uuid4())
        self.sessions[s_id] = {
            "session_id": s_id,
            "created_at": time.time(),
            "updated_at": time.time(),
            "messages": []
        }
        return s_id

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        if session_id not in self.sessions:
            return []
        self._touch(session_id)
        messages = self.sessions[session_id]["messages"]
        # Return bounded window
        return messages[-self.max_history_turns:]

    def add_turn(self, session_id: str, user_message: str, assistant_message: str, citations: Optional[List[Dict[str, Any]]] = None):
        if session_id not in self.sessions:
            self.create_session(session_id)

        self._touch(session_id)
        session = self.sessions[session_id]
        session["messages"].append({
            "role": "user",
            "content": user_message
        })
        session["messages"].append({
            "role": "assistant",
            "content": assistant_message,
            "citations": citations or []
        })

    def clear_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def _touch(self, session_id: str):
        if session_id in self.sessions:
            self.sessions[session_id]["updated_at"] = time.time()
