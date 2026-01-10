"""ファイル保存コントローラ"""
from fastapi import APIRouter
from pathlib import Path
from config import Config
from models.requests import SaveRequest
from models.responses import SaveResponse
from services.file_service import FileService
from services.git_service import GitService

router = APIRouter()


@router.post("/save", response_model=SaveResponse)
async def save_file(request: SaveRequest) -> SaveResponse:
    """
    リクエスト内容をファイルとして保存し、git commit & push

    - filename: ファイル名(省略時は日時ベースで自動生成)
    - content: 保存する内容
    """
    # ファイル名の決定
    if request.filename:
        filename = FileService.sanitize_filename(request.filename)
    else:
        filename = FileService.generate_filename()

    filepath = Config.DATA_DIR / filename

    # ファイル保存
    FileService.save_text_file(filepath, request.content)

    # Git commit & push を実行
    git_success, git_error = await GitService.commit_and_push(Config.DATA_DIR)

    return SaveResponse(
        success=True,
        filepath=str(filepath),
        message=f"ファイルを保存しました: {filename}",
        git_pushed=git_success,
        git_error=git_error,
    )
