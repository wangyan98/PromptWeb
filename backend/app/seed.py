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
    # 参考/音频
    {"name": "参考画师", "color": "#8d6e63", "sort_order": 20},
    {"name": "参考素材", "color": "#26a69a", "sort_order": 21},
    {"name": "音效台词", "color": "#ec407a", "sort_order": 22},
    # 角色外貌细分（头 → 脚 → 随身）
    {"name": "眉毛", "color": "#e9a4a4", "sort_order": 23},
    {"name": "眼睛", "color": "#a4e9b8", "sort_order": 24},
    {"name": "口鼻", "color": "#cca4e9", "sort_order": 25},
    {"name": "胡须", "color": "#e9e1a4", "sort_order": 26},
    {"name": "脸型轮廓", "color": "#a4dee9", "sort_order": 27},
    {"name": "发型发色", "color": "#e9a4c9", "sort_order": 28},
    {"name": "妆容", "color": "#b5e9a4", "sort_order": 29},
    {"name": "肤色肤质", "color": "#a7a4e9", "sort_order": 30},
    {"name": "体型身材", "color": "#e9bba4", "sort_order": 31},
    {"name": "衣服", "color": "#a4e9cf", "sort_order": 32},
    {"name": "裤子", "color": "#e3a4e9", "sort_order": 33},
    {"name": "鞋袜", "color": "#dbe9a4", "sort_order": 34},
    {"name": "帽子头饰", "color": "#a4c6e9", "sort_order": 35},
    {"name": "配饰首饰", "color": "#e9a4b2", "sort_order": 36},
    {"name": "武器装备", "color": "#a4e9aa", "sort_order": 37},
    {"name": "尾巴", "color": "#bea4e9", "sort_order": 38},
    {"name": "犄角", "color": "#e9d2a4", "sort_order": 39},
    {"name": "翅膀", "color": "#a4e9e6", "sort_order": 40},
    {"name": "鱼鳍", "color": "#e9a4d8", "sort_order": 41},
    {"name": "道具", "color": "#c3e9a4", "sort_order": 42},
    {"name": "综合外貌", "color": "#a4afe9", "sort_order": 43},
    {"name": "角色设定", "color": "#e9ada4", "sort_order": 44},
    # 结构/其它
    {"name": "结构标记", "color": "#cfd8dc", "sort_order": 45},
    {"name": "参数设置", "color": "#d1c4e9", "sort_order": 46},
    {"name": "画面文字", "color": "#ffe082", "sort_order": 47},
    {"name": "设定图", "color": "#80cbc4", "sort_order": 48},
    {"name": "情绪表情", "color": "#f8bbd0", "sort_order": 49},
    {"name": "图像编辑", "color": "#9fa8da", "sort_order": 50},
    {"name": "使用说明", "color": "#e6ee9c", "sort_order": 51},
    {"name": "氛围基调", "color": "#d7ccc8", "sort_order": 52},
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
