from flask_login import UserMixin
from enum import Enum, auto

class Role(Enum):
    STUDENT = auto()
    TEACHER = auto()
    ADMIN = auto()

class User(UserMixin):
    def __init__(self, user_id, name, role):
        self.id = user_id        # Flask-Login requires 'id' attribute
        self.user_id = user_id   # Keep original attribute too
        self.name = name
        self.role = role