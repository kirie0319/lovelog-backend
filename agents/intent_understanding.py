from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from typing import Dict
import json

class IntentUnderstandingAgent:
    """ユーザーの意図を理解するAgent"""
    
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.2,
            openai_api_key=openai_api_key
        )
    
    def _get_intent_function(self):
        """意図理解用のfunction定義"""
        return {
            "name": "understand_intent",
            "description": "カップルの会話分析結果から意図を理解し、求めているサポートを特定する",
            "parameters": {
                "type": "object",
                "properties": {
                    "support_type": {
                        "type": "string",
                        "enum": ["date_plan", "travel_plan", "restaurant_suggestion", "event_activity", "other"],
                        "description": "求められているサポートの種類"
                    },
                    "support_type_details": {
                        "type": "string",
                        "description": "サポート種別の詳細説明"
                    },
                    "budget_range": {
                        "type": "object",
                        "properties": {
                            "min_budget": {"type": "integer", "description": "最小予算（円）"},
                            "max_budget": {"type": "integer", "description": "最大予算（円）"},
                            "budget_description": {"type": "string", "description": "予算に関する詳細説明"}
                        },
                        "description": "予算の範囲"
                    },
                    "time_preferences": {
                        "type": "object",
                        "properties": {
                            "preferred_dates": {"type": "array", "items": {"type": "string"}, "description": "希望する日時"},
                            "time_constraints": {"type": "array", "items": {"type": "string"}, "description": "時間的な制約"},
                            "duration": {"type": "string", "description": "希望する所要時間"}
                        },
                        "description": "時間に関する希望"
                    },
                    "location_constraints": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "場所の制約や希望エリア"
                    },
                    "preferences": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "category": {"type": "string", "description": "好みのカテゴリ"},
                                "preference": {"type": "string", "description": "具体的な好み"},
                                "priority": {"type": "string", "enum": ["high", "medium", "low"], "description": "優先度"}
                            },
                            "required": ["category", "preference", "priority"]
                        },
                        "description": "特別な要望や好み"
                    },
                    "constraints": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "制限事項や避けたいこと"
                    },
                    "urgency_level": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "緊急度レベル"
                    },
                    "relationship_context": {
                        "type": "object",
                        "properties": {
                            "occasion": {"type": "string", "description": "特別な機会や理由"},
                            "relationship_stage": {"type": "string", "description": "関係性の段階"},
                            "special_considerations": {"type": "array", "items": {"type": "string"}, "description": "特別な配慮事項"}
                        },
                        "description": "関係性のコンテキスト"
                    }
                },
                "required": ["support_type", "support_type_details", "budget_range", "time_preferences", "location_constraints", "preferences", "constraints", "urgency_level", "relationship_context"]
            }
        }
    
    def _print_thinking(self, message: str, indent: int = 1):
        """思考プロセスを表示"""
        prefix = "  " * indent + "🧠 "
        print(f"{prefix}{message}")
    
    def _print_intent_step(self, step: str, details: str = None):
        """意図理解ステップを表示"""
        print(f"  🎯 {step}")
        if details:
            print(f"     └─ {details}")
    
    async def understand_intent(self, analysis_result: Dict) -> Dict:
        """
        会話分析結果から、カップルが求めているものを理解
        """
        self._print_thinking("会話分析結果の解釈を開始...")
        
        # 分析結果の主要項目をチェック
        if 'topics' in analysis_result:
            topics = analysis_result['topics']
            if isinstance(topics, list):
                self._print_intent_step("話題分析", f"{len(topics)}個の話題を検出")
                for i, topic in enumerate(topics[:3]):
                    print(f"       [{i+1}] {topic}")
        
        if 'metadata' in analysis_result:
            metadata = analysis_result['metadata']
            speakers_count = len(metadata.get('speakers', {}))
            self._print_intent_step("参加者情報", f"{speakers_count}名の話者を確認")
        
        self._print_thinking("サポート種別の判定を開始...")
        self._print_intent_step("判定項目", "デートプラン、旅行、レストラン、イベント、その他")
        
        system_prompt = """
        あなたはカップルの意図を理解する専門家です。
        会話分析結果から、カップルが以下のどのようなサポートを求めているかを判断してください：
        
        1. デートプランの提案 (date_plan)
        2. 旅行計画のサポート (travel_plan)
        3. レストラン・食事の提案 (restaurant_suggestion)
        4. イベント・アクティビティの提案 (event_activity)
        5. その他 (other)
        
        会話の内容を詳細に分析し、提供されたfunction schemaに従って構造化された情報を抽出してください。
        特に以下の点に注意してください：
        - 予算の範囲（明示的または暗示的）
        - 希望する時期・時間
        - 場所の制約
        - 特別な要望や制限
        - 関係性のコンテキスト
        """
        
        self._print_thinking("GPT-4による意図分析を実行中...")
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"会話分析結果:\n{json.dumps(analysis_result, ensure_ascii=False, indent=2)}")
        ]
        
        self._print_thinking("GPT-4にfunction callingリクエスト送信中...")
        
        try:
            response = await self.llm.ainvoke(
                messages,
                functions=[self._get_intent_function()],
                function_call={"name": "understand_intent"}
            )
            
            self._print_thinking("GPT-4からレスポンス受信完了")
            
            # Function callの結果を取得
            if hasattr(response, 'additional_kwargs') and 'function_call' in response.additional_kwargs:
                function_call = response.additional_kwargs['function_call']
                if function_call['name'] == 'understand_intent':
                    intent_result = json.loads(function_call['arguments'])
                    
                    self._print_thinking("✅ 意図理解が正常に完了しました")
                    
                    # 主要な意図理解結果を表示
                    if 'support_type' in intent_result:
                        support_type = intent_result['support_type']
                        self._print_intent_step("サポート種別", support_type)
                    
                    if 'budget_range' in intent_result:
                        budget = intent_result['budget_range']
                        if isinstance(budget, dict) and 'budget_description' in budget:
                            self._print_intent_step("予算範囲", budget['budget_description'])
                    
                    if 'location_constraints' in intent_result:
                        locations = intent_result['location_constraints']
                        if isinstance(locations, list) and locations:
                            self._print_intent_step("場所制約", f"{len(locations)}箇所の候補地域")
                            for i, location in enumerate(locations[:3]):
                                print(f"       [{i+1}] {location}")
                    
                    if 'preferences' in intent_result:
                        preferences = intent_result['preferences']
                        if isinstance(preferences, list) and preferences:
                            self._print_intent_step("好み・要望", f"{len(preferences)}項目の好みを特定")
                            for i, pref in enumerate(preferences[:3]):
                                if isinstance(pref, dict) and 'preference' in pref:
                                    print(f"       [{i+1}] {pref['preference']}")
                    
                    return intent_result
                else:
                    raise ValueError("予期しないfunction callが返されました")
            else:
                raise ValueError("Function callの結果が見つかりません")
                
        except Exception as e:
            self._print_thinking("❌ Function calling意図理解に失敗しました")
            self._print_intent_step("エラー詳細", str(e))
            return {"error": "意図理解の解析に失敗しました", "error_details": str(e)}