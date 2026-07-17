from pydantic import BaseModel


class PromptImageCreate(BaseModel):
    url: str | None = None
    storage_type: str = "minio"
    sort_order: int = 0
    width: int | None = None
    height: int | None = None


class PromptImageResponse(BaseModel):
    id: int
    prompt_id: int
    url: str
    storage_type: str
    sort_order: int
    width: int | None = None
    height: int | None = None

    model_config = {"from_attributes": True}
