from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from typing import Dict
import json

class IntentUnderstandingAgent:
    """ユーザーの意図を理解するAgent"""
    
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-4.1",
            temperature=0.2,
            openai_api_key=openai_api_key
        )
    
    async def understand_intent(self, analysis_result: Dict) -> Dict:
        """
        会話分析結果から、カップルが求めているものを理解
        """
        system_prompt = """
        あなたはカップルの意図を理解する専門家です。
        会話分析結果から、カップルが以下のどのようなサポートを求めているかを判断してください：
        
        1. デートプランの提案
        2. 旅行計画のサポート
        3. レストラン・食事の提案
        4. イベント・アクティビティの提案
        5. その他
        
        また、以下の詳細情報も抽出してください：
        - 予算の範囲
        - 希望する時期・時間
        - 場所の制約
        - 特別な要望や制限
        
        結果をJSON形式で返してください。
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"会話分析結果:\n{json.dumps(analysis_result, ensure_ascii=False, indent=2)}")
        ]
        
        response = await self.llm.ainvoke(messages)
        
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {"error": "意図理解の解析に失敗しました", "raw_response": response.content}