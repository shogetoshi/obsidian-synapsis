"""
Obsidian Synapsis - ローカルからリクエストを受けてファイルとして保存するWebサーバー
"""

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Obsidian Synapsis",
    description="ローカルからリクエストを受けてファイルとして保存",
)

DATA_DIR = Path(__file__).parent / "data"


class SaveRequest(BaseModel):
    """ファイル保存リクエストのスキーマ"""

    filename: str | None = None
    content: str


class SaveResponse(BaseModel):
    """ファイル保存レスポンスのスキーマ"""

    success: bool
    filepath: str
    message: str


@app.on_event("startup")
async def startup_event() -> None:
    """起動時にdataディレクトリを作成"""
    DATA_DIR.mkdir(exist_ok=True)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """ヘルスチェックエンドポイント"""
    return {"status": "ok"}


@app.post("/save", response_model=SaveResponse)
async def save_file(request: SaveRequest) -> SaveResponse:
    """
    リクエスト内容をファイルとして保存

    - filename: ファイル名（省略時は日時ベースで自動生成）
    - content: 保存する内容
    """
    # ファイル名の決定
    if request.filename:
        filename = request.filename
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}.md"

    # パストラバーサル対策
    safe_filename = Path(filename).name
    if not safe_filename:
        raise HTTPException(status_code=400, detail="無効なファイル名です")

    filepath = DATA_DIR / safe_filename

    try:
        filepath.write_text(request.content, encoding="utf-8")
    except OSError as e:
        raise HTTPException(status_code=500, detail=f"ファイル保存に失敗: {e}") from e

    return SaveResponse(
        success=True,
        filepath=str(filepath),
        message=f"ファイルを保存しました: {safe_filename}",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
