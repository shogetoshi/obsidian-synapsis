"""
Obsidian Synapsis - ローカルからリクエストを受けてファイルとして保存するWebサーバー
"""

import json
import os
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from openai import OpenAI
from pydantic import BaseModel

# OpenAIクライアントの初期化
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 設定ファイルのパス
CONFIG_FILE = Path(__file__).parent / "modes_config.json"

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
    mode_id: str = "general"  # モードIDを追加
    filename: str | None = None


class AskAIResponse(BaseModel):
    """AI問い合わせレスポンスのスキーマ"""

    success: bool
    ai_response: str
    filepath: str
    message: str


class ModeConfig(BaseModel):
    """モード設定のスキーマ"""

    id: str
    name: str
    prompt_template: str
    save_dir: str
    description: str


class ModesConfig(BaseModel):
    """モード設定全体のスキーマ"""

    modes: list[ModeConfig]
    default_mode: str


class GetModesResponse(BaseModel):
    """モード一覧取得レスポンスのスキーマ"""

    modes: list[ModeConfig]
    default_mode: str


# モード設定をグローバル変数として保持
modes_config: ModesConfig | None = None


@app.on_event("startup")
async def startup_event() -> None:
    """起動時にdataディレクトリを作成し、環境変数とモード設定を確認"""
    global modes_config

    DATA_DIR.mkdir(exist_ok=True)

    # OpenAI APIキーの存在確認
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY環境変数が設定されていません")

    # モード設定の読み込み
    modes_config = load_modes_config()

    # 各モードの保存ディレクトリを作成
    for mode in modes_config.modes:
        mode_dir = DATA_DIR / mode.save_dir
        mode_dir.mkdir(exist_ok=True)


def load_modes_config() -> ModesConfig:
    """モード設定ファイルを読み込む"""
    # TODO: 実装
    raise NotImplementedError("load_modes_config is not implemented")


def get_mode_by_id(mode_id: str) -> ModeConfig:
    """モードIDからモード設定を取得"""
    # TODO: 実装
    raise NotImplementedError("get_mode_by_id is not implemented")


def build_prompt_from_template(template: str, content: str) -> str:
    """プロンプトテンプレートにコンテンツを埋め込む"""
    # TODO: 実装
    raise NotImplementedError("build_prompt_from_template is not implemented")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """ヘルスチェックエンドポイント"""
    return {"status": "ok"}


@app.get("/modes", response_model=GetModesResponse)
async def get_modes() -> GetModesResponse:
    """
    利用可能なモード一覧を取得

    Returns:
        モード一覧とデフォルトモード
    """
    # TODO: 実装
    raise NotImplementedError("get_modes is not implemented")


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
        #askAIBtn:hover { background: #059669; }
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
    <button id="askAIBtn" onclick="askAI()" style="background: #10b981; margin-left: 8px;">AIに質問</button>
    <div id="message"></div>
    <div id="aiResponse" style="margin-top: 20px; padding: 16px; background: #2d2d2d; border-radius: 8px; display: none;">
        <h3 style="color: #10b981; margin-top: 0;">AI回答</h3>
        <div id="aiResponseContent" style="white-space: pre-wrap;"></div>
    </div>

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

        async function askAI() {
            const content = document.getElementById('content').value;
            const btn = document.getElementById('askAIBtn');
            const msg = document.getElementById('message');
            const responseDiv = document.getElementById('aiResponse');
            const responseContent = document.getElementById('aiResponseContent');

            if (!content.trim()) {
                msg.textContent = '質問を入力してください';
                msg.className = 'error';
                return;
            }

            btn.disabled = true;
            btn.textContent = 'AI処理中...';
            responseDiv.style.display = 'none';

            try {
                const res = await fetch('/ask-ai', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ content })
                });
                const data = await res.json();

                if (res.ok) {
                    msg.textContent = data.message;
                    msg.className = 'success';
                    responseContent.textContent = data.ai_response;
                    responseDiv.style.display = 'block';
                } else {
                    msg.textContent = data.detail || 'AI処理に失敗しました';
                    msg.className = 'error';
                }
            } catch (e) {
                msg.textContent = 'エラー: ' + e.message;
                msg.className = 'error';
            } finally {
                btn.disabled = false;
                btn.textContent = 'AIに質問';
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
    ユーザーの質問をAIに送信し、回答をモード別ディレクトリに保存

    - content: ユーザーの質問/入力
    - mode_id: 使用するモードのID
    - filename: ファイル名（省略時は日時ベースで自動生成）
    """
    # TODO: mode_idを使用したモード取得とプロンプトテンプレート適用
    # mode = get_mode_by_id(request.mode_id)
    # prompt = build_prompt_from_template(mode.prompt_template, request.content)
    # save_dir = DATA_DIR / mode.save_dir

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
