from pydantic import BaseModel


class StatementCreate(BaseModel):
    text_en: str
    text_zh: str = ""
    sort_order: int = 0
    type_id: int | None = None


class StatementUpdate(BaseModel):
    text_en: str | None = None
    text_zh: str | None = None
    sort_order: int | None = None
    type_id: int | None = None


class StatementResponse(BaseModel):
    id: int
    prompt_id: int
    text_en: str
    text_zh: str
    sort_order: int
    type_id: int | None = None
    words: list["PromptWordResponse"] = []

    model_config = {"from_attributes": True}
