"""
Obsidian Synapsis - ローカルからリクエストを受けてファイルとして保存するWebサーバー
"""

import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from openai import OpenAI
from pydantic import BaseModel

# 環境変数の読み込み
load_dotenv()

# OpenAIクライアントの初期化
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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


class AskAIRequest(BaseModel):
    """AI問い合わせリクエストのスキーマ"""

    content: str
    filename: str | None = None


class AskAIResponse(BaseModel):
    """AI問い合わせレスポンスのスキーマ"""

    success: bool
    ai_response: str
    filepath: str
    message: str


@app.on_event("startup")
async def startup_event() -> None:
    """起動時にdataディレクトリを作成し、環境変数を確認"""
    DATA_DIR.mkdir(exist_ok=True)

    # OpenAI APIキーの存在確認
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY環境変数が設定されていません")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """ヘルスチェックエンドポイント"""
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    """Webページを表示"""
    return """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Obsidian Synapsis</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #1e1e1e;
            color: #e0e0e0;
        }
        h1 { color: #7c3aed; }
        textarea {
            width: 100%;
            height: 300px;
            padding: 12px;
            font-size: 16px;
            border: 1px solid #444;
            border-radius: 8px;
            background: #2d2d2d;
            color: #e0e0e0;
            resize: vertical;
        }
        button {
            margin-top: 16px;
            padding: 12px 32px;
            font-size: 16px;
            background: #7c3aed;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
        }
        button:hover { background: #6d28d9; }
        button:disabled { background: #666; cursor: not-allowed; }
        #message {
            margin-top: 16px;
            padding: 12px;
            border-radius: 8px;
            display: none;
        }
        .success { background: #065f46; display: block !important; }
        .error { background: #991b1b; display: block !important; }
    </style>
</head>
<body>
    <h1>Obsidian Synapsis</h1>
    <textarea id="content" placeholder="保存する内容を入力..."></textarea>
    <br>
    <button id="saveBtn" onclick="saveContent()">保存</button>
    <div id="message"></div>

    <script>
        async function saveContent() {
            const content = document.getElementById('content').value;
            const btn = document.getElementById('saveBtn');
            const msg = document.getElementById('message');

            if (!content.trim()) {
                msg.textContent = '内容を入力してください';
                msg.className = 'error';
                return;
            }

            btn.disabled = true;
            btn.textContent = '保存中...';

            try {
                const res = await fetch('/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content })
                });
                const data = await res.json();

                if (res.ok) {
                    msg.textContent = data.message;
                    msg.className = 'success';
                    document.getElementById('content').value = '';
                } else {
                    msg.textContent = data.detail || '保存に失敗しました';
                    msg.className = 'error';
                }
            } catch (e) {
                msg.textContent = 'エラー: ' + e.message;
                msg.className = 'error';
            } finally {
                btn.disabled = false;
                btn.textContent = '保存';
            }
        }
    </script>
</body>
</html>
"""


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


@app.post("/ask-ai", response_model=AskAIResponse)
async def ask_ai(request: AskAIRequest) -> AskAIResponse:
    """
    ユーザーの質問をAIに送信し、回答をファイルとして保存

    - content: ユーザーの質問
    - filename: ファイル名（省略時は日時ベースで自動生成）
    """
    try:
        # OpenAI APIを呼び出し
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": request.content}],
            temperature=0.7,
        )

        ai_response = response.choices[0].message.content

        # ファイル名の決定
        if request.filename:
            filename = request.filename
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ai_{timestamp}.md"

        # パストラバーサル対策
        safe_filename = Path(filename).name
        if not safe_filename:
            raise HTTPException(status_code=400, detail="無効なファイル名です")

        filepath = DATA_DIR / safe_filename

        # 質問と回答をMarkdown形式で保存
        content_to_save = f"# 質問\n\n{request.content}\n\n# AI回答\n\n{ai_response}\n"
        filepath.write_text(content_to_save, encoding="utf-8")

        return AskAIResponse(
            success=True,
            ai_response=ai_response,
            filepath=str(filepath),
            message=f"AI回答を保存しました: {safe_filename}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"AI処理中にエラーが発生しました: {e!s}"
        ) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
