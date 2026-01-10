"""アプリケーション設定"""
import json
import os
from pathlib import Path
from models.responses import ModeConfig


class Config:
    """アプリケーション設定クラス"""

    # ディレクトリパス
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"
    CONFIG_FILE = BASE_DIR / "modes_config.json"
    TEMPLATE_DIR = BASE_DIR / "templates"
    STATIC_DIR = BASE_DIR / "static"

    # OpenAI設定
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = "gpt-4o"

    # モード設定 (遅延ロード)
    _modes_config: dict | None = None

    @classmethod
    def load_modes_config(cls) -> dict:
        """モード設定ファイルを読み込む"""
        if cls._modes_config is not None:
            return cls._modes_config

        if not cls.CONFIG_FILE.exists():
            raise RuntimeError(f"モード設定ファイルが見つかりません: {cls.CONFIG_FILE}")

        try:
            config_data = json.loads(cls.CONFIG_FILE.read_text(encoding="utf-8"))
            cls._modes_config = config_data
            print(f"モード設定を読み込みました: {len(config_data['modes'])}個のモード")
            return config_data
        except Exception as e:
            raise RuntimeError(f"モード設定の読み込みに失敗: {e}") from e

    @classmethod
    def get_mode_by_id(cls, mode_id: str) -> ModeConfig | None:
        """モードIDからモード設定を取得"""
        config = cls.load_modes_config()
        for mode_data in config["modes"]:
            if mode_data["id"] == mode_id:
                return ModeConfig(**mode_data)
        return None

    @classmethod
    def validate(cls) -> None:
        """設定の妥当性をチェック"""
        if not cls.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY環境変数が設定されていません")
        cls.load_modes_config()
