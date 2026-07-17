from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/api/import", tags=["import"])


@router.post("/excel")
async def import_excel_preview(file: UploadFile = File(...)):
    import openpyxl
    from io import BytesIO

    content = await file.read()
    wb = openpyxl.load_workbook(BytesIO(content), data_only=True)

    sheets_data = {}
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = []
        for row in ws.iter_rows(values_only=True):
            if any(cell is not None for cell in row):
                rows.append([str(cell) if cell is not None else "" for cell in row])
        if rows:
            sheets_data[sheet_name] = rows

    await file.seek(0)
    return ApiResponse(data={
        "filename": file.filename,
        "sheets": sheets_data,
    })


@router.post("/confirm")
async def import_confirm(data: list[dict], db: AsyncSession = Depends(get_db)):
    from app.services.prompt_service import prompt_service
    from app.schemas.prompt import PromptCreate

    created = []
    for item in data:
        prompt_data = PromptCreate(
            title=item.get("title", ""),
            text_en_full=item.get("text_en_full", ""),
            text_zh_full=item.get("text_zh_full", ""),
            category=item.get("category", ""),
            source_file=item.get("source_file", ""),
        )
        prompt = await prompt_service.create_prompt(db, prompt_data)
        created.append({"id": prompt.id, "title": prompt.title})

    return ApiResponse(data={"imported": len(created), "items": created})
