from .conversation_analyzer import ConversationAnalyzer
from .intent_understanding import IntentUnderstandingAgent
from .thinking_agent import ThinkingAgent
from .google_search_agent import GoogleSearchAgent
from .plan_suggestion_agent import PlanSuggestionAgent
from typing import List, Dict
import asyncio

class AIOrchestrator:
    """全てのAgentを統括するオーケストレーター"""
    
    def __init__(self, openai_api_key: str, google_api_key: str = None, google_cse_id: str = None):
        self.conversation_analyzer = ConversationAnalyzer(openai_api_key)
        self.intent_agent = IntentUnderstandingAgent(openai_api_key)
        self.thinking_agent = ThinkingAgent(openai_api_key)
        self.plan_agent = PlanSuggestionAgent(openai_api_key)
        
        # Google Search Agentは後で実装（API設定が必要）
        if google_api_key and google_cse_id:
            self.search_agent = GoogleSearchAgent(google_api_key, google_cse_id)
        else:
            self.search_agent = None
    
    async def process_ai_request(self, messages: List[Dict]) -> Dict:
        """
        AIボタンが押された時のメイン処理
        """
        try:
            # Step 1: 会話分析
            print("🔍 会話を分析中...")
            analysis_result = await self.conversation_analyzer.analyze_conversation(messages)
            
            # Step 2: 意図理解
            print("🧠 意図を理解中...")
            intent_result = await self.intent_agent.understand_intent(analysis_result)
            
            # Step 3: 思考・計画
            print("💭 最適なプランを考え中...")
            thinking_result = await self.thinking_agent.think_and_plan(intent_result)
            
            # Step 4: Google検索（オプション）
            search_results = {}
            if self.search_agent and thinking_result.get('search_keywords'):
                print("🔎 関連情報を検索中...")
                search_results = await self.search_agent.search_information(
                    thinking_result['search_keywords']
                )
            
            # Step 5: 最終提案
            print("✨ 素敵な提案を作成中...")
            final_suggestions = await self.plan_agent.suggest_plans(thinking_result, search_results)
            
            return {
                "success": True,
                "analysis": analysis_result,
                "intent": intent_result,
                "thinking": thinking_result,
                "search_results": search_results,
                "suggestions": final_suggestions,
                "message": "AIが素敵な提案を考えました！"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "申し訳ございません。AIの処理中にエラーが発生しました。"
            }