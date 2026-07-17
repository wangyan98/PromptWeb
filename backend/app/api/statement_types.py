from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.statement_type import StatementTypeCreate, StatementTypeUpdate, StatementTypeResponse
from app.services.statement_type_service import statement_type_service

router = APIRouter(prefix="/api/statement-types", tags=["statement-types"])


@router.get("")
async def list_types(db: AsyncSession = Depends(get_db)):
    types = await statement_type_service.list_types(db)
    return ApiResponse(data=[StatementTypeResponse.model_validate(t).model_dump() for t in types])


@router.post("")
async def create_type(data: StatementTypeCreate, db: AsyncSession = Depends(get_db)):
    st = await statement_type_service.create_type(db, data)
    return ApiResponse(data=StatementTypeResponse.model_validate(st).model_dump())


@router.put("/{type_id}")
async def update_type(type_id: int, data: StatementTypeUpdate, db: AsyncSession = Depends(get_db)):
    st = await statement_type_service.update_type(db, type_id, data)
    if not st:
        return ApiResponse(code=404, message="Not found")
    return ApiResponse(data=StatementTypeResponse.model_validate(st).model_dump())


@router.delete("/{type_id}")
async def delete_type(type_id: int, db: AsyncSession = Depends(get_db)):
    ok = await statement_type_service.delete_type(db, type_id)
    if not ok:
        return ApiResponse(code=404, message="Not found")
    return ApiResponse(message="Deleted")
