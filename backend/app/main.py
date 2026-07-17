from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import prompts, statements, words, images, statement_types, import_

app = FastAPI(title="PromptWeb API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prompts.router)
app.include_router(statements.router)
app.include_router(words.router)
app.include_router(images.router)
app.include_router(statement_types.router)
app.include_router(import_.router)


@app.on_event("startup")
async def startup():
    from app.services.minio_service import minio_service
    await minio_service.ensure_bucket()


@app.get("/api/health")
async def health():
    return {"code": 0, "data": {"status": "ok"}, "message": "healthy"}
