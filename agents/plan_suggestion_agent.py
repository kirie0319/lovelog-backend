from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from typing import Dict
import json

class PlanSuggestionAgent:
    """最終的な予定提案を行うAgent"""
    
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-4.1",
            temperature=0.6,
            openai_api_key=openai_api_key
        )
    
    async def suggest_plans(self, thinking_result: Dict, search_results: Dict) -> Dict:
        """
        思考結果と検索結果から、具体的な予定を提案
        """
        system_prompt = """
        あなたはカップル向けの最高のデートプランナーです。
        思考結果と検索結果を基に、魅力的で実現可能な予定を3つ提案してください。
        
        各提案には以下を含めてください：
        1. プランのタイトル
        2. 詳細な内容とスケジュール
        3. 予算の目安
        4. おすすめポイント
        5. 注意事項や準備すべきこと
        
        カップルが楽しめるよう、温かみのあるトーンで提案してください。
        結果をJSON形式で返してください。
        """
        
        context = f"""
        思考結果:
        {json.dumps(thinking_result, ensure_ascii=False, indent=2)}
        
        検索結果:
        {json.dumps(search_results, ensure_ascii=False, indent=2)}
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {"error": "提案の解析に失敗しました", "raw_response": response.content}