from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from typing import List, Dict
import json

class ConversationAnalyzer:
    """会話履歴を分析するAgent"""
    
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-4.1",
            temperature=0.3,
            openai_api_key=openai_api_key
        )
    
    async def analyze_conversation(self, messages: List[Dict]) -> Dict:
        """
        会話履歴を分析して、重要な情報を抽出
        """
        # メッセージを文字列に変換
        conversation_text = self._format_messages(messages)
        
        system_prompt = """
        あなたはカップルの会話を分析する専門家です。
        以下の会話履歴から、以下の情報を抽出してください：
        
        1. 話題の種類（デート、旅行、食事、日常など）
        2. 具体的な場所や時間の言及
        3. 興味や好みの表現
        4. 計画や提案に関する発言
        5. 感情的なトーン
        
        結果をJSON形式で返してください。
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"会話履歴:\n{conversation_text}")
        ]
        
        response = await self.llm.ainvoke(messages)
        
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {"error": "分析結果の解析に失敗しました", "raw_response": response.content}
    
    def _format_messages(self, messages: List[Dict]) -> str:
        """メッセージリストを読みやすい形式に変換"""
        formatted = []
        for msg in messages:
            sender_name = msg.get('sender', {}).get('display_name', 'Unknown')
            content = msg.get('content', '')
            timestamp = msg.get('created_at', '')
            formatted.append(f"[{timestamp}] {sender_name}: {content}")
        
        return "\n".join(formatted)