from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models import Prompt, Statement, StatementType, PromptWord, PromptImage
from app.schemas.prompt import PromptCreate, PromptUpdate
from app.schemas.statement import StatementCreate, StatementUpdate
from app.schemas.prompt_word import PromptWordCreate
from app.schemas.prompt_image import PromptImageCreate


class PromptService:
    async def list_prompts(
        self, db: AsyncSession, *, page: int = 1, page_size: int = 20,
        search: str = "", category: str = ""
    ) -> tuple[list[Prompt], int]:
        query = select(Prompt)
        count_query = select(func.count(Prompt.id))

        if search:
            filter_clause = Prompt.text_en_full.ilike(f"%{search}%") | Prompt.title.ilike(f"%{search}%")
            query = query.where(filter_clause)
            count_query = count_query.where(filter_clause)

        if category:
            query = query.where(Prompt.category == category)
            count_query = count_query.where(Prompt.category == category)

        total = (await db.execute(count_query)).scalar() or 0

        query = query.order_by(Prompt.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        # Eager load first image for thumbnail
        query = query.options(selectinload(Prompt.images))

        result = await db.execute(query)
        prompts = list(result.scalars().unique())

        return prompts, total

    async def get_prompt(self, db: AsyncSession, prompt_id: int) -> Prompt | None:
        query = (
            select(Prompt)
            .options(
                selectinload(Prompt.statements).selectinload(Statement.words),
                selectinload(Prompt.words),
                selectinload(Prompt.images),
            )
            .where(Prompt.id == prompt_id)
        )
        result = await db.execute(query)
        return result.scalars().first()

    async def create_prompt(self, db: AsyncSession, data: PromptCreate) -> Prompt:
        prompt = Prompt(**data.model_dump())
        db.add(prompt)
        await db.commit()
        await db.refresh(prompt)
        return prompt

    async def update_prompt(self, db: AsyncSession, prompt_id: int, data: PromptUpdate) -> Prompt | None:
        prompt = await self.get_prompt(db, prompt_id)
        if not prompt:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(prompt, key, value)
        await db.commit()
        await db.refresh(prompt)
        return prompt

    async def delete_prompt(self, db: AsyncSession, prompt_id: int) -> bool:
        prompt = await self.get_prompt(db, prompt_id)
        if not prompt:
            return False
        await db.delete(prompt)
        await db.commit()
        return True

    async def create_statements_batch(
        self, db: AsyncSession, prompt_id: int, statements: list[StatementCreate]
    ) -> list[Statement]:
        stmts = [
            Statement(prompt_id=prompt_id, **s.model_dump())
            for s in statements
        ]
        db.add_all(stmts)
        await db.commit()
        return stmts

    async def update_statement(
        self, db: AsyncSession, statement_id: int, data: StatementUpdate
    ) -> Statement | None:
        stmt = await db.get(Statement, statement_id)
        if not stmt:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(stmt, key, value)
        await db.commit()
        await db.refresh(stmt)
        return stmt

    async def delete_statement(self, db: AsyncSession, statement_id: int) -> bool:
        stmt = await db.get(Statement, statement_id)
        if not stmt:
            return False
        await db.delete(stmt)
        await db.commit()
        return True

    async def create_words_batch(
        self, db: AsyncSession, prompt_id: int, statement_id: int, words: list[PromptWordCreate]
    ) -> list[PromptWord]:
        pwords = [
            PromptWord(prompt_id=prompt_id, statement_id=statement_id, **w.model_dump())
            for w in words
        ]
        db.add_all(pwords)
        await db.commit()
        return pwords

    async def delete_word(self, db: AsyncSession, word_id: int) -> bool:
        word = await db.get(PromptWord, word_id)
        if not word:
            return False
        await db.delete(word)
        await db.commit()
        return True

    async def add_image(self, db: AsyncSession, prompt_id: int, data: PromptImageCreate) -> PromptImage:
        image = PromptImage(prompt_id=prompt_id, **data.model_dump())
        db.add(image)
        await db.commit()
        await db.refresh(image)
        return image

    async def delete_image(self, db: AsyncSession, image_id: int) -> PromptImage | None:
        image = await db.get(PromptImage, image_id)
        if not image:
            return None
        await db.delete(image)
        await db.commit()
        return image

    async def get_categories(self, db: AsyncSession) -> list[str]:
        query = select(Prompt.category).distinct().where(Prompt.category != "")
        result = await db.execute(query)
        return [row[0] for row in result.all() if row[0]]


prompt_service = PromptService()
