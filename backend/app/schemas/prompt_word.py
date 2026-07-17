from pydantic import BaseModel


class PromptWordCreate(BaseModel):
    word_en: str
    word_zh: str = ""
    position_start: int | None = None
    position_end: int | None = None


class PromptWordResponse(BaseModel):
    id: int
    prompt_id: int
    statement_id: int
    word_en: str
    word_zh: str
    position_start: int | None = None
    position_end: int | None = None

    model_config = {"from_attributes": True}
