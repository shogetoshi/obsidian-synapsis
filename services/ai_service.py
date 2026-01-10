"""AI処理サービス"""
from openai import OpenAI
from fastapi import HTTPException


class AIService:
    """AI処理を管理するサービスクラス"""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """
        Args:
            api_key: OpenAI APIキー
            model: 使用するモデル名
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def build_prompt_from_template(self, template: str, content: str) -> str:
        """
        プロンプトテンプレートにコンテンツを埋め込む

        Args:
            template: プロンプトテンプレート
            content: ユーザー入力

        Returns:
            構築されたプロンプト
        """
        return template.format(content=content)

    def ask(self, prompt: str, temperature: float = 0.7) -> str:
        """
        AIに質問して回答を取得

        Args:
            prompt: プロンプト
            temperature: 温度パラメータ

        Returns:
            AI回答

        Raises:
            HTTPException: API呼び出し失敗時
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"AI処理中にエラーが発生しました: {e!s}"
            ) from e
