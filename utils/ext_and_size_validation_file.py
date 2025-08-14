import os
from fastapi import UploadFile, HTTPException

ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.jpg', '.png', 'jpeg'}

MAX_FILE_SIZE_MB = 8


async def validate_file(file: UploadFile):
    ext = os.path.splitext(file.filename)[1].lower()
    file_content = await file.read()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Недопустимый формат файла: {ext}. Разрешены: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    if len(file_content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"Файл слишком большой. Максимальный размер: {MAX_FILE_SIZE_MB} MB"
        )
