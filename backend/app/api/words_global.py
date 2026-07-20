from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/api", tags=["words-global"])


@router.get("/words/global")
async def list_words_global(
    search: str = Query(""),
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    # Build WHERE clause
    params = {}
    where_clause = "1=1"
    if search:
        where_clause = "(pw.word_en ILIKE :search OR pw.word_zh ILIKE :search2)"
        params["search"] = f"%{search}%"
        params["search2"] = f"%{search}%"

    # Count: distinct word_en groups
    count_sql = f"""
        SELECT COUNT(*) FROM (
            SELECT 1 FROM prompt_words pw
            WHERE {where_clause}
            GROUP BY pw.word_en
        ) sub
    """
    total_result = await db.execute(text(count_sql), params)
    total = total_result.scalar() or 0

    # Main query: GROUP BY word_en, pick most common word_zh, collect prompt_ids
    # Uses CTEs to avoid nested aggregate functions (ARRAY_AGG + COUNT)
    main_sql = f"""
        WITH group_counts AS (
            SELECT
                pw.word_en,
                pw.word_zh,
                COUNT(*) AS combo_count
            FROM prompt_words pw
            WHERE {where_clause}
            GROUP BY pw.word_en, pw.word_zh
        ),
        best_per_word_en AS (
            SELECT DISTINCT ON (word_en)
                word_en,
                word_zh
            FROM group_counts
            ORDER BY word_en, combo_count DESC
        ),
        all_by_word_en AS (
            SELECT
                pw.word_en,
                ARRAY_AGG(DISTINCT pw.prompt_id ORDER BY pw.prompt_id) AS prompt_ids,
                COUNT(*)::int AS total_count
            FROM prompt_words pw
            WHERE {where_clause}
            GROUP BY pw.word_en
        )
        SELECT
            a.word_en,
            COALESCE(b.word_zh, '') AS word_zh,
            a.prompt_ids,
            a.total_count
        FROM all_by_word_en a
        LEFT JOIN best_per_word_en b ON a.word_en = b.word_en
        ORDER BY a.total_count DESC, a.word_en
        LIMIT :limit OFFSET :offset
    """
    params["limit"] = page_size
    params["offset"] = (page - 1) * page_size

    result = await db.execute(text(main_sql), params)
    rows = result.mappings().all()

    if not rows:
        return ApiResponse(data={
            "items": [], "total": total, "page": page, "page_size": page_size
        })

    # Second query: get type breakdown for the words in this page
    word_list = [row["word_en"] for row in rows]
    placeholders = ", ".join(f":w{i}" for i in range(len(word_list)))
    types_params = {f"w{i}": w for i, w in enumerate(word_list)}
    types_params.update({k: v for k, v in params.items() if k not in ("limit", "offset")})

    types_sql = f"""
        SELECT
            pw.word_en,
            st.id AS type_id,
            st.name AS type_name,
            st.color AS type_color,
            COUNT(*)::int AS count
        FROM prompt_words pw
        JOIN statements s ON pw.statement_id = s.id
        LEFT JOIN statement_types st ON s.type_id = st.id
        WHERE pw.word_en IN ({placeholders})
        GROUP BY pw.word_en, st.id, st.name, st.color
        ORDER BY pw.word_en, count DESC
    """

    types_result = await db.execute(text(types_sql), types_params)
    types_rows = types_result.mappings().all()

    # Build types lookup: word_en -> list of types
    types_map: dict[str, list[dict]] = {}
    for tr in types_rows:
        w = tr["word_en"]
        if w not in types_map:
            types_map[w] = []
        types_map[w].append({
            "type_id": tr["type_id"],
            "type_name": tr["type_name"] or "",
            "type_color": tr["type_color"] or "#3b82f6",
            "count": tr["count"],
        })

    items = [
        {
            "word_en": row["word_en"],
            "word_zh": row["word_zh"] or "",
            "total_count": row["total_count"],
            "types": types_map.get(row["word_en"], []),
            "prompt_ids": list(row["prompt_ids"] or []),
        }
        for row in rows
    ]

    return ApiResponse(data={
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    })
