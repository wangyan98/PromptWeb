from pydantic import BaseModel


class StatementTypeCreate(BaseModel):
    name: str
    color: str = "#4fc3f7"
    sort_order: int = 0


class StatementTypeUpdate(BaseModel):
    name: str | None = None
    color: str | None = None
    sort_order: int | None = None


class StatementTypeResponse(BaseModel):
    id: int
    name: str
    color: str
    sort_order: int

    model_config = {"from_attributes": True}
