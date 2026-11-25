from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.prompt_word import (
    DanbooruWordImport,
    PromptWordCreate,
    PromptWordResponse,
    WordHiddenUpdate,
)
from app.services.prompt_service import prompt_service

router = APIRouter(prefix="/api", tags=["words"])


@router.get("/statements/{statement_id}/words")
async def list_words(statement_id: int, db: AsyncSession = Depends(get_db)):
    from app.models import PromptWord
    from sqlalchemy import select
    query = select(PromptWord).where(PromptWord.statement_id == statement_id)
    result = await db.execute(query)
    words = result.scalars().all()
    return ApiResponse(data=[PromptWordResponse.model_validate(w).model_dump() for w in words])


@router.post("/statements/{statement_id}/words")
async def create_words(statement_id: int, words: list[PromptWordCreate], db: AsyncSession = Depends(get_db)):
    from app.models import Statement
    stmt = await db.get(Statement, statement_id)
    if not stmt:
        return ApiResponse(code=404, message="Statement not found")
    pwords = await prompt_service.create_words_batch(db, stmt.prompt_id, statement_id, words)
    return ApiResponse(data=[PromptWordResponse.model_validate(w).model_dump() for w in pwords])


@router.post("/words/import")
async def import_danbooru_words(words: list[DanbooruWordImport], db: AsyncSession = Depends(get_db)):
    """Batch-import standalone Danbooru tags. Idempotent: duplicate word_en is skipped."""
    if not words:
        return ApiResponse(data={"inserted": 0, "total": 0})

    rows = [
        {
            "word_en": w.word_en,
            "word_zh": w.word_zh,
            "category": w.category,
            "post_count": w.post_count,
        }
        for w in words
    ]
    count_before = (
        await db.execute(text("SELECT COUNT(*) FROM prompt_words WHERE source = 'danbooru'"))
    ).scalar() or 0

    await db.execute(
        text("""
            INSERT INTO prompt_words (word_en, word_zh, source, category, post_count)
            VALUES (:word_en, :word_zh, 'danbooru', :category, :post_count)
            ON CONFLICT (word_en) WHERE source = 'danbooru' DO NOTHING
        """),
        rows,
    )
    await db.commit()

    count_after = (
        await db.execute(text("SELECT COUNT(*) FROM prompt_words WHERE source = 'danbooru'"))
    ).scalar() or 0
    return ApiResponse(data={"inserted": count_after - count_before, "total": count_after})


@router.patch("/words/hidden")
async def set_words_hidden(payload: WordHiddenUpdate, db: AsyncSession = Depends(get_db)):
    """Only flips the is_hidden flag — no word is ever deleted."""
    if not payload.word_ids:
        return ApiResponse(data={"updated": 0})
    placeholders = ", ".join(f":id{i}" for i in range(len(payload.word_ids)))
    params = {f"id{i}": word_id for i, word_id in enumerate(payload.word_ids)}
    params["hidden"] = payload.hidden
    result = await db.execute(
        text(f"UPDATE prompt_words SET is_hidden = :hidden WHERE id IN ({placeholders})"),
        params,
    )
    await db.commit()
    return ApiResponse(data={"updated": result.rowcount if result.rowcount and result.rowcount > 0 else 0})


@router.delete("/words/{word_id}")
async def delete_word(word_id: int, db: AsyncSession = Depends(get_db)):
    ok = await prompt_service.delete_word(db, word_id)
    if not ok:
        return ApiResponse(code=404, message="Word not found")
    return ApiResponse(message="Deleted")
