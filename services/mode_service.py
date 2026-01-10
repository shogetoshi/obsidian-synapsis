"""モード管理サービス"""
from config import Config
from models.responses import ModeConfig, GetModesResponse
from fastapi import HTTPException


class ModeService:
    """モード管理を行うサービスクラス"""

    @staticmethod
    def get_modes() -> GetModesResponse:
        """
        利用可能なモード一覧を取得

        Returns:
            モード一覧とデフォルトモード
        """
        config = Config.load_modes_config()
        modes = [ModeConfig(**mode_data) for mode_data in config["modes"]]
        return GetModesResponse(
            modes=modes,
            default_mode=config["default_mode"]
        )

    @staticmethod
    def get_mode_by_id(mode_id: str) -> ModeConfig:
        """
        モードIDからモード設定を取得

        Args:
            mode_id: モードID

        Returns:
            モード設定

        Raises:
            HTTPException: 無効なモードIDの場合
        """
        mode = Config.get_mode_by_id(mode_id)
        if mode is None:
            raise HTTPException(
                status_code=400,
                detail=f"無効なモードID: {mode_id}"
            )
        return mode
