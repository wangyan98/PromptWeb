from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.statement import StatementCreate, StatementUpdate, StatementResponse
from app.services.prompt_service import prompt_service

router = APIRouter(prefix="/api", tags=["statements"])


@router.get("/prompts/{prompt_id}/statements")
async def list_statements(prompt_id: int, db: AsyncSession = Depends(get_db)):
    prompt = await prompt_service.get_prompt(db, prompt_id)
    if not prompt:
        return ApiResponse(code=404, message="Prompt not found")
    statements = sorted(prompt.statements, key=lambda s: s.sort_order)
    return ApiResponse(data=[StatementResponse.model_validate(s).model_dump() for s in statements])


@router.post("/prompts/{prompt_id}/statements")
async def create_statements(prompt_id: int, statements: list[StatementCreate], db: AsyncSession = Depends(get_db)):
    stmts = await prompt_service.create_statements_batch(db, prompt_id, statements)
    # Use dict response to avoid lazy-loading words relationship (new statements have no words)
    return ApiResponse(data=[
        {"id": s.id, "prompt_id": s.prompt_id, "text_en": s.text_en,
         "text_zh": s.text_zh, "sort_order": s.sort_order, "type_id": s.type_id, "words": []}
        for s in stmts
    ])


@router.put("/statements/{statement_id}")
async def update_statement(statement_id: int, data: StatementUpdate, db: AsyncSession = Depends(get_db)):
    stmt = await prompt_service.update_statement(db, statement_id, data)
    if not stmt:
        return ApiResponse(code=404, message="Statement not found")
    # Return dict to avoid lazy-loading the words relationship (MissingGreenlet)
    return ApiResponse(data={
        "id": stmt.id, "prompt_id": stmt.prompt_id, "text_en": stmt.text_en,
        "text_zh": stmt.text_zh, "sort_order": stmt.sort_order, "type_id": stmt.type_id, "words": []
    })


@router.delete("/statements/{statement_id}")
async def delete_statement(statement_id: int, db: AsyncSession = Depends(get_db)):
    ok = await prompt_service.delete_statement(db, statement_id)
    if not ok:
        return ApiResponse(code=404, message="Statement not found")
    return ApiResponse(message="Deleted")
