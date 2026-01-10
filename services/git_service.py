"""Git操作サービス"""
import asyncio
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


class GitService:
    """Git操作を管理するサービスクラス"""

    @staticmethod
    async def commit_and_push(repo_dir: Path) -> tuple[bool, str | None]:
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
