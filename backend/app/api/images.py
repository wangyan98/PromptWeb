from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.prompt_image import PromptImageCreate, PromptImageResponse
from app.services.prompt_service import prompt_service
from app.services.minio_service import minio_service

router = APIRouter(prefix="/api", tags=["images"])


@router.post("/prompts/{prompt_id}/images")
async def upload_image(
    prompt_id: int,
    file: UploadFile | None = File(None),
    url: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
):
    if url and not file:
        # External URL image
        data = PromptImageCreate(url=url, storage_type="url")
    elif file:
        await minio_service.ensure_bucket()
        object_url = await minio_service.upload(file, prompt_id)
        data = PromptImageCreate(url=object_url, storage_type="minio")
    else:
        return ApiResponse(code=400, message="Provide file or url")

    image = await prompt_service.add_image(db, prompt_id, data)
    return ApiResponse(data=PromptImageResponse.model_validate(image).model_dump())


@router.delete("/images/{image_id}")
async def delete_image(image_id: int, db: AsyncSession = Depends(get_db)):
    image = await prompt_service.delete_image(db, image_id)
    if not image:
        return ApiResponse(code=404, message="Image not found")
    if image.storage_type == "minio":
        object_name = minio_service.get_object_name_from_url(image.url)
        minio_service.delete(object_name)
    return ApiResponse(message="Deleted")


@router.get("/images/file/{object_name:path}")
async def get_image_file(object_name: str):
    try:
        response = minio_service.client.get_object(minio_service.bucket, object_name)
        return StreamingResponse(
            response.stream(32 * 1024),
            media_type=response.headers.get("Content-Type", "image/png"),
        )
    except Exception:
        return ApiResponse(code=404, message="File not found")
