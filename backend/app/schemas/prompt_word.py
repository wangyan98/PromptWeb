from pydantic import BaseModel


class PromptWordCreate(BaseModel):
    word_en: str
    word_zh: str = ""
    position_start: int | None = None
    position_end: int | None = None


class DanbooruWordImport(BaseModel):
    """One standalone tag from the Danbooru dictionary."""
    word_en: str
    word_zh: str = ""
    category: int | None = None
    post_count: int | None = None


class PromptWordResponse(BaseModel):
    id: int
    prompt_id: int | None = None
    statement_id: int | None = None
    word_en: str
    word_zh: str
    position_start: int | None = None
    position_end: int | None = None
    source: str = "statement"
    category: int | None = None
    post_count: int | None = None
    is_hidden: bool = False

    model_config = {"from_attributes": True}


class WordHiddenUpdate(BaseModel):
    word_ids: list[int]
    hidden: bool = True
