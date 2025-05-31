from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from typing import Dict
import json

class ThinkingAgent:
    """思考・推論を行うAgent"""
    
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-4.1",
            temperature=0.4,
            openai_api_key=openai_api_key
        )
    
    async def think_and_plan(self, intent_result: Dict) -> Dict:
        """
        意図理解結果から、具体的な検索戦略と提案方針を考える
        """
        system_prompt = """
        あなたはカップルのデートプランを考える思考エージェントです。
        意図理解の結果から、以下を決定してください：
        
        1. Google検索で調べるべきキーワード（複数）
        2. 検索結果から重視すべき要素
        3. 提案の方向性とトーン
        4. 考慮すべき制約条件
        
        検索キーワードは具体的で効果的なものを3-5個提案してください。
        結果をJSON形式で返してください。
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"意図理解結果:\n{json.dumps(intent_result, ensure_ascii=False, indent=2)}")
        ]
        
        response = await self.llm.ainvoke(messages)
        
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {"error": "思考プロセスの解析に失敗しました", "raw_response": response.content}