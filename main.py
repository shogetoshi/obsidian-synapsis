"""
Obsidian Synapsis - ローカルからリクエストを受けてファイルとして保存するWebサーバー
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

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
    git_pushed: bool = False
    git_error: str | None = None


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
    git_pushed: bool = False
    git_error: str | None = None


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
    if not CONFIG_FILE.exists():
        raise RuntimeError(f"モード設定ファイルが見つかりません: {CONFIG_FILE}")

    try:
        config_data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        modes_config = ModesConfig(**config_data)
        print(f"モード設定を読み込みました: {len(modes_config.modes)}個のモード")
        return modes_config
    except Exception as e:
        raise RuntimeError(f"モード設定の読み込みに失敗: {e}") from e


def get_mode_by_id(mode_id: str) -> ModeConfig | None:
    """モードIDからモード設定を取得"""
    if modes_config is None:
        return None
    return next((m for m in modes_config.modes if m.id == mode_id), None)


def build_prompt_from_template(template: str, content: str) -> str:
    """プロンプトテンプレートにコンテンツを埋め込む"""
    return template.format(content=content)


async def git_commit_and_push(repo_dir: Path) -> tuple[bool, str | None]:
    """
    Git commit & push を実行

    Args:
        repo_dir: リポジトリのルートディレクトリ

    Returns:
        (成功フラグ, エラーメッセージ or None)
    """
    try:
        # JST現在時刻を取得
        jst = ZoneInfo("Asia/Tokyo")
        now = datetime.now(jst)
        commit_message = f"Synapsis: {now.strftime('%Y-%m-%d %H:%M:%S')}"

        # git add . を実行
        add_process = await asyncio.create_subprocess_exec(
            "git", "add", ".",
            cwd=str(repo_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await add_process.communicate()

        if add_process.returncode != 0:
            return False, "git add failed"

        # git commit を実行
        commit_process = await asyncio.create_subprocess_exec(
            "git", "commit", "-m", commit_message,
            cwd=str(repo_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await commit_process.communicate()

        # commitがない場合(nothing to commit)は成功とみなす
        if commit_process.returncode != 0:
            stderr_text = stderr.decode("utf-8")
            if "nothing to commit" in stderr_text:
                return True, None
            return False, f"git commit failed: {stderr_text}"

        # git push --force を実行
        push_process = await asyncio.create_subprocess_exec(
            "git", "push", "--force",
            cwd=str(repo_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await push_process.communicate()

        if push_process.returncode != 0:
            stderr_text = stderr.decode("utf-8")
            return False, f"git push failed: {stderr_text}"

        return True, None

    except Exception as e:
        return False, f"git operation error: {str(e)}"


def get_repo_root() -> Path:
    """
    main.pyの親ディレクトリをリポジトリルートとして返す

    Returns:
        リポジトリのルートディレクトリ
    """
    return Path(__file__).parent


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
    if modes_config is None:
        raise HTTPException(status_code=500, detail="モード設定が読み込まれていません")

    return GetModesResponse(
        modes=modes_config.modes,
        default_mode=modes_config.default_mode,
    )


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
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            background: #1e1e1e;
            color: #e0e0e0;
            height: 100vh;
            overflow: hidden;
        }
        .container {
            display: flex;
            height: 100vh;
        }

        /* 左ペイン: タブナビゲーション */
        .sidebar {
            width: 250px;
            background: #252525;
            border-right: 1px solid #444;
            padding: 20px 0;
            overflow-y: auto;
        }
        .sidebar h2 {
            color: #7c3aed;
            padding: 0 20px 20px;
            font-size: 24px;
        }
        .mode-tab {
            padding: 16px 20px;
            cursor: pointer;
            transition: all 0.2s;
            border-left: 3px solid transparent;
        }
        .mode-tab:hover {
            background: #2d2d2d;
        }
        .mode-tab.active {
            background: #2d2d2d;
            border-left-color: #7c3aed;
        }
        .mode-tab-name {
            font-size: 16px;
            font-weight: 500;
            margin-bottom: 4px;
        }
        .mode-tab-desc {
            font-size: 13px;
            color: #999;
        }

        /* 右ペイン: メインコンテンツ */
        .main-content {
            flex: 1;
            padding: 40px;
            overflow-y: auto;
        }
        .mode-title {
            color: #7c3aed;
            font-size: 28px;
            margin-bottom: 8px;
        }
        .mode-description {
            color: #999;
            margin-bottom: 24px;
            font-size: 14px;
        }
        textarea {
            width: 100%;
            height: 300px;
            padding: 16px;
            font-size: 16px;
            border: 1px solid #444;
            border-radius: 8px;
            background: #2d2d2d;
            color: #e0e0e0;
            resize: vertical;
            font-family: inherit;
        }
        .button-group {
            margin-top: 16px;
            display: flex;
            gap: 12px;
        }
        button {
            padding: 12px 32px;
            font-size: 16px;
            background: #7c3aed;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.2s;
        }
        button:hover { background: #6d28d9; }
        button:disabled { background: #666; cursor: not-allowed; }
        #askAIBtn { background: #10b981; }
        #askAIBtn:hover { background: #059669; }

        #message {
            margin-top: 16px;
            padding: 12px;
            border-radius: 8px;
            display: none;
        }
        .success { background: #065f46; display: block !important; }
        .error { background: #991b1b; display: block !important; }

        #aiResponse {
            margin-top: 24px;
            padding: 20px;
            background: #2d2d2d;
            border-radius: 8px;
            display: none;
        }
        #aiResponse h3 {
            color: #10b981;
            margin-top: 0;
            margin-bottom: 16px;
        }
        #aiResponseContent {
            white-space: pre-wrap;
            line-height: 1.6;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- 左ペイン: モード選択 -->
        <div class="sidebar">
            <h2>Synapsis</h2>
            <div id="modeTabs"></div>
        </div>

        <!-- 右ペイン: メインコンテンツ -->
        <div class="main-content">
            <h1 class="mode-title" id="modeTitle">読み込み中...</h1>
            <p class="mode-description" id="modeDescription"></p>

            <textarea id="content" placeholder="内容を入力..."></textarea>

            <div class="button-group">
                <button id="saveBtn" onclick="saveContent()">保存のみ</button>
                <button id="askAIBtn" onclick="askAI()">AIに質問</button>
            </div>

            <div id="message"></div>

            <div id="aiResponse">
                <h3>AI回答</h3>
                <div id="aiResponseContent"></div>
            </div>
        </div>
    </div>

    <script>
        let currentMode = null;
        let modesData = null;

        // ページ読み込み時にモード一覧を取得
        async function loadModes() {
            try {
                const res = await fetch('/modes');
                const data = await res.json();
                modesData = data;

                // タブを生成
                const tabsContainer = document.getElementById('modeTabs');
                data.modes.forEach(mode => {
                    const tab = document.createElement('div');
                    tab.className = 'mode-tab';
                    tab.onclick = () => selectMode(mode.id);
                    tab.innerHTML = `
                        <div class="mode-tab-name">${mode.name}</div>
                        <div class="mode-tab-desc">${mode.description}</div>
                    `;
                    tab.dataset.modeId = mode.id;
                    tabsContainer.appendChild(tab);
                });

                // デフォルトモードを選択
                selectMode(data.default_mode);
            } catch (e) {
                showMessage('モード読み込みエラー: ' + e.message, 'error');
            }
        }

        // モードを選択
        function selectMode(modeId) {
            const mode = modesData.modes.find(m => m.id === modeId);
            if (!mode) return;

            currentMode = mode;

            // タブのアクティブ状態を更新
            document.querySelectorAll('.mode-tab').forEach(tab => {
                tab.classList.toggle('active', tab.dataset.modeId === modeId);
            });

            // タイトルと説明を更新
            document.getElementById('modeTitle').textContent = mode.name;
            document.getElementById('modeDescription').textContent = mode.description;

            // AI回答を非表示
            document.getElementById('aiResponse').style.display = 'none';
            document.getElementById('message').style.display = 'none';
        }

        // 保存のみ
        async function saveContent() {
            const content = document.getElementById('content').value;
            const btn = document.getElementById('saveBtn');

            if (!content.trim()) {
                showMessage('内容を入力してください', 'error');
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
                    showMessage(data.message, 'success');
                    document.getElementById('content').value = '';
                } else {
                    showMessage(data.detail || '保存に失敗しました', 'error');
                }
            } catch (e) {
                showMessage('エラー: ' + e.message, 'error');
            } finally {
                btn.disabled = false;
                btn.textContent = '保存のみ';
            }
        }

        // AIに質問
        async function askAI() {
            const content = document.getElementById('content').value;
            const btn = document.getElementById('askAIBtn');
            const responseDiv = document.getElementById('aiResponse');
            const responseContent = document.getElementById('aiResponseContent');

            if (!content.trim()) {
                showMessage('内容を入力してください', 'error');
                return;
            }

            if (!currentMode) {
                showMessage('モードが選択されていません', 'error');
                return;
            }

            btn.disabled = true;
            btn.textContent = 'AI処理中...';
            responseDiv.style.display = 'none';

            try {
                const res = await fetch('/ask-ai', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        content,
                        mode_id: currentMode.id
                    })
                });
                const data = await res.json();

                if (res.ok) {
                    showMessage(data.message, 'success');
                    responseContent.textContent = data.ai_response;
                    responseDiv.style.display = 'block';
                } else {
                    showMessage(data.detail || 'AI処理に失敗しました', 'error');
                }
            } catch (e) {
                showMessage('エラー: ' + e.message, 'error');
            } finally {
                btn.disabled = false;
                btn.textContent = 'AIに質問';
            }
        }

        function showMessage(text, type) {
            const msg = document.getElementById('message');
            msg.textContent = text;
            msg.className = type;
        }

        // ページ読み込み時にモードを読み込む
        loadModes();
    </script>
</body>
</html>
"""


@app.post("/save", response_model=SaveResponse)
async def save_file(request: SaveRequest) -> SaveResponse:
    """
    リクエスト内容をファイルとして保存し、git commit & push

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

    # Git commit & push を実行
    repo_root = get_repo_root()
    git_success, git_error = await git_commit_and_push(repo_root)

    return SaveResponse(
        success=True,
        filepath=str(filepath),
        message=f"ファイルを保存しました: {safe_filename}",
        git_pushed=git_success,
        git_error=git_error,
    )


@app.post("/ask-ai", response_model=AskAIResponse)
async def ask_ai(request: AskAIRequest) -> AskAIResponse:
    """
    ユーザーの質問をAIに送信し、回答をモード別ディレクトリに保存

    - content: ユーザーの質問/入力
    - mode_id: 使用するモードのID
    - filename: ファイル名（省略時は日時ベースで自動生成）
    """
    if modes_config is None:
        raise HTTPException(status_code=500, detail="モード設定が読み込まれていません")

    # モードの検証
    mode = get_mode_by_id(request.mode_id)
    if mode is None:
        raise HTTPException(
            status_code=400,
            detail=f"無効なモードID: {request.mode_id}"
        )

    try:
        # プロンプトテンプレートを適用
        prompt = build_prompt_from_template(mode.prompt_template, request.content)

        # OpenAI APIを呼び出し
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        ai_response = response.choices[0].message.content

        # ファイル名の決定
        if request.filename:
            filename = request.filename
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{mode.id}_{timestamp}.md"

        # パストラバーサル対策
        safe_filename = Path(filename).name
        if not safe_filename:
            raise HTTPException(status_code=400, detail="無効なファイル名です")

        # モード別ディレクトリに保存
        mode_dir = DATA_DIR / mode.save_dir
        filepath = mode_dir / safe_filename

        # 質問と回答をMarkdown形式で保存
        content_to_save = (
            f"# {mode.name}\n\n"
            f"## 入力\n\n{request.content}\n\n"
            f"## AI回答\n\n{ai_response}\n"
        )
        filepath.write_text(content_to_save, encoding="utf-8")

        return AskAIResponse(
            success=True,
            ai_response=ai_response,
            filepath=str(filepath),
            message=f"AI回答を保存しました: {mode.name} / {safe_filename}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"AI処理中にエラーが発生しました: {e!s}"
        ) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
