"""リクエストモデル定義"""
from pydantic import BaseModel


class SaveRequest(BaseModel):
    """ファイル保存リクエストのスキーマ"""
    filename: str | None = None
    content: str


class AskAIRequest(BaseModel):
    """AI問い合わせリクエストのスキーマ"""
    content: str
    mode_id: str = "general"
    filename: str | None = None
