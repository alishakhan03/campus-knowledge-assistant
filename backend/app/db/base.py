"""
Declarative base + import hub for Alembic autogenerate.

Alembic's env.py imports Base.metadata from here, so every model module
must be imported below or migrations won't detect new tables.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import models so they register on Base.metadata (used by Alembic autogenerate)
from app.models.user import User  # noqa: E402,F401
from app.models.document import Document  # noqa: E402,F401
from app.models.conversation import Conversation  # noqa: E402,F401
from app.models.message import Message, MessageFeedback, MessageSource  # noqa: E402,F401
