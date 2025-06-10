from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from typing import Dict
import json

class ThinkingAgent:
    """思考・推論を行うAgent"""
    
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.4,
            openai_api_key=openai_api_key
        )
    
    def _get_thinking_function(self):
        """思考・戦略立案用のfunction定義"""
        return {
            "name": "think_and_plan",
            "description": "意図理解結果から具体的な検索戦略と提案方針を立案する",
            "parameters": {
                "type": "object",
                "properties": {
                    "search_keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Google検索で使用する具体的なキーワード（5-7個）。地域+業種+予算+評価の組み合わせを重視"
                    },
                    "search_priority": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "検索結果から重視すべき要素（店舗名、住所、営業時間、予算、評価、アクセス方法など）"
                    },
                    "proposal_direction": {
                        "type": "string",
                        "description": "提案の方向性とトーン（検索で見つかった実店舗を活用した具体的なプラン）"
                    },
                    "constraints": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "考慮すべき制約条件（予算、地域、時間、アクセス方法など）"
                    },
                    "search_utilization_strategy": {
                        "type": "string",
                        "description": "検索結果をどのように実際のプランに組み込むかの戦略"
                    },
                    "target_audience_considerations": {
                        "type": "object",
                        "properties": {
                            "relationship_stage": {"type": "string", "description": "関係性の段階に応じた配慮"},
                            "preferences_alignment": {"type": "string", "description": "両者の好みの調整方針"},
                            "budget_sensitivity": {"type": "string", "description": "予算に対する配慮"}
                        },
                        "description": "対象カップルに対する配慮事項"
                    },
                    "expected_outcomes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "期待される成果や提案の効果"
                    },
                    "fallback_strategies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "検索結果が不十分な場合の代替戦略"
                    }
                },
                "required": ["search_keywords", "search_priority", "proposal_direction", "constraints", "search_utilization_strategy", "target_audience_considerations", "expected_outcomes", "fallback_strategies"]
            }
        }
    
    def _print_thinking(self, message: str, indent: int = 1):
        """思考プロセスを表示"""
        prefix = "  " * indent + "🧠 "
        print(f"{prefix}{message}")
    
    def _print_strategy_step(self, step: str, details: str = None):
        """戦略立案ステップを表示"""
        print(f"  🎲 {step}")
        if details:
            print(f"     └─ {details}")
    
    async def think_and_plan(self, intent_result: Dict) -> Dict:
        """
        意図理解結果から、具体的な検索戦略と提案方針を考える
        """
        self._print_thinking("意図理解結果の分析を開始...")
        
        # 意図理解結果の主要項目をチェック
        if 'support_type' in intent_result:
            support_type = intent_result['support_type']
            self._print_strategy_step("サポート種別確認", support_type)
        
        if 'budget_range' in intent_result:
            budget = intent_result['budget_range']
            if isinstance(budget, dict) and 'budget_description' in budget:
                self._print_strategy_step("予算制約確認", budget['budget_description'])
        
        if 'location_constraints' in intent_result:
            locations = intent_result['location_constraints']
            if isinstance(locations, list) and locations:
                self._print_strategy_step("地域制約確認", f"{len(locations)}箇所の候補地域")
        
        self._print_thinking("具体的店舗情報取得のための検索戦略を立案中...")
        self._print_strategy_step("戦略要素", "店舗名取得、営業時間確認、予算適合性、アクセス情報")
        
        self._print_thinking("実店舗発見に最適化された検索キーワードを考案中...")
        self._print_strategy_step("キーワード要件", "地域+業種+予算+評価を組み合わせた具体的検索")
        
        system_prompt = """
        あなたはカップルのデートプランを考える思考エージェントです。
        意図理解の結果から、Google検索で具体的な店舗・場所情報を取得するための戦略を立案してください。

        【重要な方針】
        1. 検索結果から実際の店舗名、住所、営業時間が取得できるキーワードを生成
        2. 一般的な情報ではなく、具体的な店舗・施設情報を取得することを最優先
        3. 地域名 + 業種 + 予算感 + 評価キーワードの組み合わせを重視
        4. 検索結果を活用した実現可能なプランを前提とした戦略立案

        提供されたfunction schemaに従って、構造化された戦略を立案してください。
        検索キーワードは実際の店舗情報が取得できる具体的なものを5-7個提案してください。
        """
        
        self._print_thinking("GPT-4による具体的検索戦略立案を実行中...")
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"意図理解結果:\n{json.dumps(intent_result, ensure_ascii=False, indent=2)}")
        ]
        
        self._print_thinking("GPT-4にfunction callingリクエスト送信中...")
        
        try:
            response = await self.llm.ainvoke(
                messages,
                functions=[self._get_thinking_function()],
                function_call={"name": "think_and_plan"}
            )
            
            self._print_thinking("GPT-4からレスポンス受信完了")
            
            # Function callの結果を取得
            if hasattr(response, 'additional_kwargs') and 'function_call' in response.additional_kwargs:
                function_call = response.additional_kwargs['function_call']
                if function_call['name'] == 'think_and_plan':
                    thinking_result = json.loads(function_call['arguments'])
                    
                    self._print_thinking("✅ 具体的検索戦略立案が正常に完了しました")
                    
                    # 主要な思考結果を表示
                    if 'search_keywords' in thinking_result:
                        keywords = thinking_result['search_keywords']
                        if isinstance(keywords, list):
                            self._print_strategy_step("具体的検索キーワード", f"{len(keywords)}個のキーワードを生成")
                            for i, keyword in enumerate(keywords):
                                print(f"       [{i+1}] \"{keyword}\"")
                                # キーワードの具体性をチェック
                                if any(word in keyword for word in ['おすすめ', '人気', '評価', '口コミ']):
                                    print(f"           └─ 評価情報取得キーワード")
                                if any(word in keyword for word in ['円', '予算', '安い', '高級']):
                                    print(f"           └─ 予算情報取得キーワード")
                    
                    if 'proposal_direction' in thinking_result:
                        direction = thinking_result['proposal_direction']
                        self._print_strategy_step("提案方針", direction)
                    
                    if 'search_utilization_strategy' in thinking_result:
                        strategy = thinking_result['search_utilization_strategy']
                        self._print_strategy_step("検索活用戦略", strategy)
                    
                    if 'constraints' in thinking_result:
                        constraints = thinking_result['constraints']
                        if isinstance(constraints, list) and constraints:
                            self._print_strategy_step("制約条件", f"{len(constraints)}項目の制約を考慮")
                            for i, constraint in enumerate(constraints[:3]):
                                print(f"       [{i+1}] {constraint}")
                    
                    if 'search_priority' in thinking_result:
                        priority = thinking_result['search_priority']
                        if isinstance(priority, list) and priority:
                            self._print_strategy_step("検索優先度", f"{len(priority)}項目の重視要素")
                            for i, item in enumerate(priority[:3]):
                                print(f"       [{i+1}] {item}")
                    
                    # 検索戦略の有効性をチェック
                    if 'search_keywords' in thinking_result:
                        keywords = thinking_result['search_keywords']
                        if isinstance(keywords, list) and len(keywords) >= 3:
                            self._print_strategy_step("戦略評価", f"✅ {len(keywords)}個の具体的キーワードで店舗情報取得準備完了")
                        else:
                            self._print_strategy_step("戦略評価", "⚠️ キーワード数が不足している可能性")
                    
                    return thinking_result
                else:
                    raise ValueError("予期しないfunction callが返されました")
            else:
                raise ValueError("Function callの結果が見つかりません")
                
        except Exception as e:
            self._print_thinking("❌ Function calling思考プロセスに失敗しました")
            self._print_strategy_step("エラー詳細", str(e))
            return {"error": "思考プロセスの解析に失敗しました", "error_details": str(e)}