"""AI処理コントローラ"""
from fastapi import APIRouter, Depends
from pathlib import Path
from config import Config
from models.requests import AskAIRequest
from models.responses import AskAIResponse
from services.ai_service import AIService
from services.file_service import FileService
from services.git_service import GitService
from services.mode_service import ModeService

router = APIRouter()


def get_ai_service() -> AIService:
    """AIServiceの依存性注入"""
    return AIService(
        api_key=Config.OPENAI_API_KEY,
        model=Config.OPENAI_MODEL
    )


@router.post("/ask-ai", response_model=AskAIResponse)
async def ask_ai(
    request: AskAIRequest,
    ai_service: AIService = Depends(get_ai_service)
) -> AskAIResponse:
    """
    ユーザーの質問をAIに送信し、回答をモード別ディレクトリに保存し、git commit & push

    - content: ユーザーの質問/入力
    - mode_id: 使用するモードのID
    - filename: ファイル名(省略時は日時ベースで自動生成)
    """
    # モードの検証と取得
    mode = ModeService.get_mode_by_id(request.mode_id)

    # プロンプト構築
    prompt = ai_service.build_prompt_from_template(
        mode.prompt_template,
        request.content
    )

    # AI呼び出し
    ai_response = ai_service.ask(prompt)

    # ファイル名の決定
    if request.filename:
        filename = FileService.sanitize_filename(request.filename)
    else:
        filename = FileService.generate_filename(prefix=mode.id)

    # 保存先パスの決定
    mode_dir = Config.DATA_DIR / mode.save_dir
    filepath = mode_dir / filename

    # 質問と回答をMarkdown形式で構築
    content_to_save = FileService.build_ai_response_content(
        mode.name,
        request.content,
        ai_response
    )

    # ファイル保存
    FileService.save_text_file(filepath, content_to_save)

    # Git commit & push を実行
    git_success, git_error = await GitService.commit_and_push(Config.DATA_DIR)

    return AskAIResponse(
        success=True,
        ai_response=ai_response,
        filepath=str(filepath),
        message=f"AI回答を保存しました: {mode.name} / {filename}",
        git_pushed=git_success,
        git_error=git_error,
    )
