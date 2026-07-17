from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import StatementType
from app.schemas.statement_type import StatementTypeCreate, StatementTypeUpdate


class StatementTypeService:
    async def list_types(self, db: AsyncSession) -> list[StatementType]:
        query = select(StatementType).order_by(StatementType.sort_order)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def create_type(self, db: AsyncSession, data: StatementTypeCreate) -> StatementType:
        st = StatementType(**data.model_dump())
        db.add(st)
        await db.commit()
        await db.refresh(st)
        return st

    async def update_type(self, db: AsyncSession, type_id: int, data: StatementTypeUpdate) -> StatementType | None:
        st = await db.get(StatementType, type_id)
        if not st:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(st, key, value)
        await db.commit()
        await db.refresh(st)
        return st

    async def delete_type(self, db: AsyncSession, type_id: int) -> bool:
        st = await db.get(StatementType, type_id)
        if not st:
            return False
        await db.delete(st)
        await db.commit()
        return True


statement_type_service = StatementTypeService()
