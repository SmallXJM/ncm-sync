from dataclasses import dataclass

@dataclass
class SimpleSession:
    """Helper for passing session data around without attached DB session."""

    id: int
    user_id: str
    cookie: str
    login_type: str

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "cookie": self.cookie,
            "login_type": self.login_type,
        }



