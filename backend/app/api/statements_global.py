from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/api", tags=["statements-global"])


@router.get("/statements/global")
async def list_statements_global(
    type_id: int | None = Query(None),
    search: str = Query(""),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    # Build WHERE clauses
    where_parts = ["1=1"]
    params = {}

    if type_id is not None:
        where_parts.append("s.type_id = :type_id")
        params["type_id"] = type_id

    if search:
        where_parts.append("(s.text_en ILIKE :search OR s.text_zh ILIKE :search2)")
        params["search"] = f"%{search}%"
        params["search2"] = f"%{search}%"

    where_clause = " AND ".join(where_parts)

    # Count query: number of distinct text_en groups
    count_sql = f"""
        SELECT COUNT(*) FROM (
            SELECT 1 FROM statements s
            WHERE {where_clause}
            GROUP BY s.text_en
        ) sub
    """
    total_result = await db.execute(text(count_sql), params)
    total = total_result.scalar() or 0

    # Main query: GROUP BY text_en, take the most common type_id
    # Uses CTEs to avoid nested aggregate functions (ARRAY_AGG + COUNT)
    main_sql = f"""
        WITH group_counts AS (
            SELECT
                s.text_en,
                s.text_zh,
                s.type_id,
                COUNT(*) AS combo_count
            FROM statements s
            WHERE {where_clause}
            GROUP BY s.text_en, s.text_zh, s.type_id
        ),
        best_per_text_en AS (
            SELECT DISTINCT ON (text_en)
                text_en,
                text_zh,
                type_id
            FROM group_counts
            ORDER BY text_en, combo_count DESC
        ),
        all_by_text_en AS (
            SELECT
                s.text_en,
                ARRAY_AGG(DISTINCT s.id ORDER BY s.id) AS statement_ids,
                ARRAY_AGG(DISTINCT s.prompt_id ORDER BY s.prompt_id) AS prompt_ids,
                COUNT(*)::int AS count
            FROM statements s
            WHERE {where_clause}
            GROUP BY s.text_en
        )
        SELECT
            a.text_en,
            COALESCE(b.text_zh, '') AS text_zh,
            b.type_id,
            COALESCE(st.name, '') AS type_name,
            COALESCE(st.color, '#3b82f6') AS type_color,
            a.statement_ids,
            a.prompt_ids,
            a.count
        FROM all_by_text_en a
        LEFT JOIN best_per_text_en b ON a.text_en = b.text_en
        LEFT JOIN statement_types st ON b.type_id = st.id
        ORDER BY a.text_en
        LIMIT :limit OFFSET :offset
    """
    params["limit"] = page_size
    params["offset"] = (page - 1) * page_size

    result = await db.execute(text(main_sql), params)
    rows = result.mappings().all()

    items = [
        {
            "text_en": row["text_en"],
            "text_zh": row["text_zh"] or "",
            "type_id": row["type_id"],
            "type_name": row["type_name"] or "",
            "type_color": row["type_color"] or "#3b82f6",
            "statement_ids": list(row["statement_ids"] or []),
            "prompt_ids": list(row["prompt_ids"] or []),
            "count": row["count"],
        }
        for row in rows
    ]

    return ApiResponse(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })
