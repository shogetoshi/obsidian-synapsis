"""ファイル操作サービス"""
from datetime import datetime
from pathlib import Path
from fastapi import HTTPException


class FileService:
    """ファイル操作を管理するサービスクラス"""

    @staticmethod
    def generate_filename(prefix: str = "", extension: str = "md") -> str:
        """
        タイムスタンプベースのファイル名を生成

        Args:
            prefix: ファイル名のプレフィックス
            extension: 拡張子 (デフォルト: md)

        Returns:
            生成されたファイル名
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if prefix:
            return f"{prefix}_{timestamp}.{extension}"
        return f"{timestamp}.{extension}"

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        ファイル名をサニタイズ (パストラバーサル対策)

        Args:
            filename: サニタイズするファイル名

        Returns:
            安全なファイル名

        Raises:
            HTTPException: 無効なファイル名の場合
        """
        safe_filename = Path(filename).name
        if not safe_filename:
            raise HTTPException(status_code=400, detail="無効なファイル名です")
        return safe_filename

    @staticmethod
    def save_text_file(filepath: Path, content: str) -> None:
        """
        テキストファイルを保存

        Args:
            filepath: 保存先パス
            content: 保存する内容

        Raises:
            HTTPException: ファイル保存失敗時
        """
        try:
            filepath.write_text(content, encoding="utf-8")
        except OSError as e:
            raise HTTPException(
                status_code=500,
                detail=f"ファイル保存に失敗: {e}"
            ) from e

    @staticmethod
    def build_ai_response_content(
        mode_name: str,
        user_input: str,
        ai_response: str
    ) -> str:
        """
        AI回答をMarkdown形式で構築

        Args:
            mode_name: モード名
            user_input: ユーザー入力
            ai_response: AI回答

        Returns:
            Markdown形式の文字列
        """
        return (
            f"# {mode_name}\n\n"
            f"## 入力\n\n{user_input}\n\n"
            f"## AI回答\n\n{ai_response}\n"
        )
