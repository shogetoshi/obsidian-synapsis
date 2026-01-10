"""
Obsidian Synapsis - ローカルからリクエストを受けてファイルとして保存するWebサーバー
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from config import Config
from controllers import health_controller, mode_controller, save_controller, ai_controller

# 設定の初期化と検証
Config.validate()

# FastAPIアプリケーション
app = FastAPI(
    title="Obsidian Synapsis",
    description="ローカルからリクエストを受けてファイルとして保存",
)

# 静的ファイルのマウント
app.mount("/static", StaticFiles(directory=str(Config.STATIC_DIR)), name="static")

# テンプレートエンジンの設定
templates = Jinja2Templates(directory=str(Config.TEMPLATE_DIR))

# ルーターの登録
app.include_router(health_controller.router)
app.include_router(mode_controller.router)
app.include_router(save_controller.router)
app.include_router(ai_controller.router)


@app.on_event("startup")
async def startup_event() -> None:
    """起動時にdataディレクトリとモード別ディレクトリを作成"""
    Config.DATA_DIR.mkdir(exist_ok=True)

    # 各モードの保存ディレクトリを作成
    config = Config.load_modes_config()
    for mode_data in config["modes"]:
        mode_dir = Config.DATA_DIR / mode_data["save_dir"]
        mode_dir.mkdir(exist_ok=True)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Webページを表示"""
    return templates.TemplateResponse("index.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
