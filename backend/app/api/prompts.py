from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.prompt import PromptCreate, PromptUpdate, PromptResponse, PromptListItem
from app.services.prompt_service import prompt_service

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


@router.get("")
async def list_prompts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query(""),
    category: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    prompts, total = await prompt_service.list_prompts(
        db, page=page, page_size=page_size, search=search, category=category
    )
    items = []
    for p in prompts:
        thumb = None
        if p.images:
            sorted_imgs = sorted(p.images, key=lambda x: x.sort_order)
            thumb = sorted_imgs[0].url
        items.append(PromptListItem(
            id=p.id, title=p.title, text_en_full=p.text_en_full,
            text_zh_full=p.text_zh_full, category=p.category,
            thumbnail_url=thumb, created_at=p.created_at, updated_at=p.updated_at,
        ))
    return ApiResponse(data=PaginatedResponse(items=items, total=total, page=page, page_size=page_size).model_dump())


@router.post("")
async def create_prompt(data: PromptCreate, db: AsyncSession = Depends(get_db)):
    prompt = await prompt_service.create_prompt(db, data)
    return ApiResponse(data=PromptResponse.model_validate(prompt).model_dump())


@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_db)):
    categories = await prompt_service.get_categories(db)
    return ApiResponse(data=categories)


@router.get("/{prompt_id}")
async def get_prompt(prompt_id: int, db: AsyncSession = Depends(get_db)):
    prompt = await prompt_service.get_prompt(db, prompt_id)
    if not prompt:
        return ApiResponse(code=404, message="Prompt not found")
    return ApiResponse(data=PromptResponse.model_validate(prompt).model_dump())


@router.put("/{prompt_id}")
async def update_prompt(prompt_id: int, data: PromptUpdate, db: AsyncSession = Depends(get_db)):
    prompt = await prompt_service.update_prompt(db, prompt_id, data)
    if not prompt:
        return ApiResponse(code=404, message="Prompt not found")
    return ApiResponse(data=PromptResponse.model_validate(prompt).model_dump())


@router.delete("/{prompt_id}")
async def delete_prompt(prompt_id: int, db: AsyncSession = Depends(get_db)):
    ok = await prompt_service.delete_prompt(db, prompt_id)
    if not ok:
        return ApiResponse(code=404, message="Prompt not found")
    return ApiResponse(message="Deleted")
