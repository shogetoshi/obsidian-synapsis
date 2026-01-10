"""レスポンスモデル定義"""
from pydantic import BaseModel


class SaveResponse(BaseModel):
    """ファイル保存レスポンスのスキーマ"""
    success: bool
    filepath: str
    message: str
    git_pushed: bool = False
    git_error: str | None = None


class AskAIResponse(BaseModel):
    """AI問い合わせレスポンスのスキーマ"""
    success: bool
    ai_response: str
    filepath: str
    message: str
    git_pushed: bool = False
    git_error: str | None = None


class ModeConfig(BaseModel):
    """モード設定のスキーマ"""
    id: str
    name: str
    prompt_template: str
    save_dir: str
    description: str


class GetModesResponse(BaseModel):
    """モード一覧取得レスポンスのスキーマ"""
    modes: list[ModeConfig]
    default_mode: str
