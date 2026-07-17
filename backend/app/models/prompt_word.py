from sqlalchemy import ForeignKey, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class PromptWord(Base):
    __tablename__ = "prompt_words"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    prompt_id: Mapped[int] = mapped_column(ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False)
    statement_id: Mapped[int] = mapped_column(ForeignKey("statements.id", ondelete="CASCADE"), nullable=False)
    word_en: Mapped[str] = mapped_column(String(200), nullable=False)
    word_zh: Mapped[str] = mapped_column(String(200), default="")
    position_start: Mapped[int] = mapped_column(Integer, nullable=True)
    position_end: Mapped[int] = mapped_column(Integer, nullable=True)

    prompt = relationship("Prompt", back_populates="words")
    statement = relationship("Statement", back_populates="words")
