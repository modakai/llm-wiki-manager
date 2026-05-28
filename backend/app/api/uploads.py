from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.schemas.upload import UploadResponse
from app.services.parser_service import ParserError, parse_document
from app.services.storage_service import save_parsed_text, save_upload_bytes

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


@router.post("", response_model=UploadResponse)
async def upload_file(request: Request, file: UploadFile = File(...)) -> UploadResponse:
    """保存上传文件并提取文本，失败时保留明确错误。"""

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="上传文件为空。")

    paths = request.app.state.paths
    saved = save_upload_bytes(paths, file.filename or "upload", content)
    try:
        parsed = parse_document(saved.path)
    except ParserError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    save_parsed_text(paths, saved.source_id, parsed.text)
    return UploadResponse(
        source_id=saved.source_id,
        filename=saved.filename,
        status="parsed",
        text_chars=len(parsed.text),
    )
