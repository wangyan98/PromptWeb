from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.prompt_word import PromptWordCreate, PromptWordResponse
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


@router.delete("/words/{word_id}")
async def delete_word(word_id: int, db: AsyncSession = Depends(get_db)):
    ok = await prompt_service.delete_word(db, word_id)
    if not ok:
        return ApiResponse(code=404, message="Word not found")
    return ApiResponse(message="Deleted")
