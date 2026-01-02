from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Admin / moderation
    is_staff = Column(Boolean, default=False)      # staff/admin flag
    is_active = Column(Boolean, default=True)      # soft-terminate accounts
    banned_until = Column(DateTime, nullable=True) # time-out accounts

    created_at = Column(DateTime, default=datetime.utcnow)

    pushups = relationship("PushupLog", back_populates="user", cascade="all, delete-orphan")


class PushupLog(Base):
    __tablename__ = "pushup_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    count = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="pushups")
