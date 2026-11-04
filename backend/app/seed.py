from sqlalchemy import select
from app.database import async_session
from app.models import StatementType

PRESET_TYPES = [
    # 图像类
    {"name": "固定开头", "color": "#4fc3f7", "sort_order": 1},
    {"name": "光照氛围", "color": "#ffb74d", "sort_order": 2},
    {"name": "镜头构图", "color": "#81c784", "sort_order": 3},
    {"name": "场景主体", "color": "#e57373", "sort_order": 4},
    {"name": "材质细节", "color": "#ba68c8", "sort_order": 5},
    {"name": "画质风格", "color": "#90a4ae", "sort_order": 6},
    {"name": "色彩色调", "color": "#f06292", "sort_order": 7},
    {"name": "环境背景", "color": "#4db6ac", "sort_order": 8},
    # 视频类
    {"name": "分镜", "color": "#ff7043", "sort_order": 9},
    {"name": "动作", "color": "#ffd54f", "sort_order": 10},
    {"name": "构图", "color": "#4dd0e1", "sort_order": 11},
    {"name": "运镜", "color": "#7e57c2", "sort_order": 12},
    {"name": "光影", "color": "#b0bec5", "sort_order": 13},
    {"name": "导演风格", "color": "#d4e157", "sort_order": 14},
    {"name": "特效", "color": "#ef9a9a", "sort_order": 15},
    {"name": "全局设定", "color": "#64b5f6", "sort_order": 16},
    {"name": "角色技能", "color": "#ffab91", "sort_order": 17},
    {"name": "负面提示词", "color": "#78909c", "sort_order": 18},
    # 参考类
    {"name": "参考画师", "color": "#8d6e63", "sort_order": 20},
    {"name": "参考素材", "color": "#26a69a", "sort_order": 21},
    {"name": "音效台词", "color": "#ec407a", "sort_order": 22},
    {"name": "角色设定", "color": "#5c6bc0", "sort_order": 23},
    # AI 语义分类补充（由 ai_classify.py 引入）
    {"name": "结构标记", "color": "#607d8b", "sort_order": 24},
    {"name": "参数设置", "color": "#8e24aa", "sort_order": 25},
    {"name": "画面文字", "color": "#ef6c00", "sort_order": 26},
    {"name": "设定图", "color": "#00695c", "sort_order": 27},
    {"name": "情绪表情", "color": "#ad1457", "sort_order": 28},
    {"name": "图像编辑", "color": "#283593", "sort_order": 29},
    {"name": "使用说明", "color": "#827717", "sort_order": 30},
    {"name": "氛围基调", "color": "#4e342e", "sort_order": 31},
]


async def seed_statement_types():
    """按 name 幂等补齐预设分类（已存在的跳过，缺的插入）。"""
    async with async_session() as session:
        rows = await session.execute(select(StatementType.name))
        exist = {r[0] for r in rows}
        added = 0
        for t in PRESET_TYPES:
            if t["name"] in exist:
                continue
            session.add(StatementType(**t))
            added += 1
        await session.commit()
        print(f"Seeded {added} statement types ({len(exist)} already existed).")


if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_statement_types())
