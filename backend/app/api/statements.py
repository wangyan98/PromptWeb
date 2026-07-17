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
    return ApiResponse(data=[StatementResponse.model_validate(s).model_dump() for s in stmts])


@router.put("/statements/{statement_id}")
async def update_statement(statement_id: int, data: StatementUpdate, db: AsyncSession = Depends(get_db)):
    stmt = await prompt_service.update_statement(db, statement_id, data)
    if not stmt:
        return ApiResponse(code=404, message="Statement not found")
    return ApiResponse(data=StatementResponse.model_validate(stmt).model_dump())


@router.delete("/statements/{statement_id}")
async def delete_statement(statement_id: int, db: AsyncSession = Depends(get_db)):
    ok = await prompt_service.delete_statement(db, statement_id)
    if not ok:
        return ApiResponse(code=404, message="Statement not found")
    return ApiResponse(message="Deleted")
