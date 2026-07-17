from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class Prompt(Base, TimestampMixin):
    __tablename__ = "prompts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), default="")
    text_en_full: Mapped[str] = mapped_column(Text, nullable=False)
    text_zh_full: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(200), default="")
    source_file: Mapped[str] = mapped_column(String(500), default="")

    statements = relationship("Statement", back_populates="prompt", cascade="all, delete-orphan")
    words = relationship("PromptWord", back_populates="prompt", cascade="all, delete-orphan")
    images = relationship("PromptImage", back_populates="prompt", cascade="all, delete-orphan")
