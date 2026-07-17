from sqlalchemy import select
from app.database import async_session
from app.models import StatementType

PRESET_TYPES = [
    {"name": "固定开头", "color": "#4fc3f7", "sort_order": 1},
    {"name": "光照氛围", "color": "#ffb74d", "sort_order": 2},
    {"name": "镜头构图", "color": "#81c784", "sort_order": 3},
    {"name": "场景主体", "color": "#e57373", "sort_order": 4},
    {"name": "材质细节", "color": "#ba68c8", "sort_order": 5},
    {"name": "画质风格", "color": "#90a4ae", "sort_order": 6},
    {"name": "色彩色调", "color": "#f06292", "sort_order": 7},
    {"name": "环境背景", "color": "#4db6ac", "sort_order": 8},
]


async def seed_statement_types():
    async with async_session() as session:
        existing = await session.execute(select(StatementType))
        if existing.scalars().first():
            print("Statement types already seeded, skipping.")
            return

        for t in PRESET_TYPES:
            session.add(StatementType(**t))
        await session.commit()
        print(f"Seeded {len(PRESET_TYPES)} statement types.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_statement_types())
