"""モード管理コントローラ"""
from fastapi import APIRouter
from models.responses import GetModesResponse
from services.mode_service import ModeService

router = APIRouter()


@router.get("/modes", response_model=GetModesResponse)
async def get_modes() -> GetModesResponse:
    """
    利用可能なモード一覧を取得

    Returns:
        モード一覧とデフォルトモード
    """
    return ModeService.get_modes()
