from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, false
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class PromptWord(Base):
    __tablename__ = "prompt_words"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    prompt_id: Mapped[int | None] = mapped_column(ForeignKey("prompts.id", ondelete="CASCADE"), nullable=True)
    statement_id: Mapped[int | None] = mapped_column(ForeignKey("statements.id", ondelete="CASCADE"), nullable=True)
    word_en: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    word_zh: Mapped[str] = mapped_column(String(200), default="")
    position_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    position_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # "statement" = extracted from a statement; "danbooru" = standalone tag import
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="statement", server_default="statement")
    category: Mapped[int | None] = mapped_column(Integer, nullable=True)
    post_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=false())

    prompt = relationship("Prompt", back_populates="words")
    statement = relationship("Statement", back_populates="words")
