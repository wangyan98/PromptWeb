from datetime import datetime
from pydantic import BaseModel


class PromptCreate(BaseModel):
    title: str = ""
    text_en_full: str
    text_zh_full: str = ""
    category: str = ""
    source_file: str = ""


class PromptUpdate(BaseModel):
    title: str | None = None
    text_en_full: str | None = None
    text_zh_full: str | None = None
    category: str | None = None


class PromptListItem(BaseModel):
    id: int
    title: str
    text_en_full: str
    text_zh_full: str
    category: str
    thumbnail_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PromptResponse(BaseModel):
    id: int
    title: str
    text_en_full: str
    text_zh_full: str
    category: str
    source_file: str
    created_at: datetime
    updated_at: datetime
    statements: list["StatementResponse"] = []
    words: list["PromptWordResponse"] = []
    images: list["PromptImageResponse"] = []

    model_config = {"from_attributes": True}


from app.schemas.statement import StatementResponse  # noqa: E402
from app.schemas.prompt_word import PromptWordResponse  # noqa: E402
from app.schemas.prompt_image import PromptImageResponse  # noqa: E402
PromptResponse.model_rebuild()
