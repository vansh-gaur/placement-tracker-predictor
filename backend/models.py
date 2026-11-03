"""Database models. SQLAlchemy handles both SQLite (local) and
PostgreSQL (production) from the same DATABASE_URL."""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    applications = relationship(
        "Application", back_populates="user", cascade="all, delete-orphan"
    )


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    company = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False, default="Job")
    status = Column(String(50), nullable=False, default="Applied")
    applied_date = Column(String(50), nullable=False, default="")
    notes = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="applications")

    def to_dict(self):
        return {
            "id": self.id,
            "company": self.company,
            "role": self.role,
            "type": self.type,
            "status": self.status,
            "applied_date": self.applied_date,
            "notes": self.notes,
        }
