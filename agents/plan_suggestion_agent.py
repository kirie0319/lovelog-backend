from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from typing import Dict
import json

class PlanSuggestionAgent:
    """最終的な予定提案を行うAgent"""
    
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.6,
            openai_api_key=openai_api_key
        )
    
    def _get_suggestion_function(self):
        """プラン提案用のfunction定義"""
        return {
            "name": "suggest_plans",
            "description": "検索結果を基に具体的で実現可能なデートプランを3つ提案する",
            "parameters": {
                "type": "object",
                "properties": {
                    "plans": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string", "description": "プランのタイトル（具体的な店舗名を含む）"},
                                "description": {"type": "string", "description": "プランの概要説明"},
                                "schedule": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "time": {"type": "string", "description": "時間帯"},
                                            "activity": {"type": "string", "description": "活動内容"},
                                            "location": {"type": "string", "description": "場所（実際の店舗名・住所を含む）"},
                                            "estimated_cost": {"type": "string", "description": "予想費用"},
                                            "notes": {"type": "string", "description": "注意事項やおすすめポイント"}
                                        },
                                        "required": ["time", "activity", "location"]
                                    },
                                    "description": "詳細なスケジュール"
                                },
                                "total_budget": {
                                    "type": "object",
                                    "properties": {
                                        "min_cost": {"type": "integer", "description": "最小予算（円）"},
                                        "max_cost": {"type": "integer", "description": "最大予算（円）"},
                                        "cost_breakdown": {"type": "string", "description": "費用の内訳"}
                                    },
                                    "description": "総予算の目安"
                                },
                                "highlights": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "このプランのおすすめポイント"
                                },
                                "access_info": {
                                    "type": "string",
                                    "description": "アクセス方法や交通手段"
                                },
                                "considerations": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "注意事項や事前準備"
                                },
                                "search_sources": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "使用した検索情報の出典"
                                }
                            },
                            "required": ["title", "description", "schedule", "total_budget", "highlights", "access_info", "considerations", "search_sources"]
                        },
                        "minItems": 3,
                        "maxItems": 3,
                        "description": "3つの具体的なデートプラン"
                    },
                    "overall_recommendations": {
                        "type": "string",
                        "description": "全体的な推奨事項やアドバイス"
                    },
                    "alternative_options": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "代替案や追加のアイデア"
                    },
                    "seasonal_considerations": {
                        "type": "string",
                        "description": "季節や天候に関する配慮"
                    }
                },
                "required": ["plans", "overall_recommendations", "alternative_options", "seasonal_considerations"]
            }
        }
    
    def _print_thinking(self, message: str, indent: int = 1):
        """思考プロセスを表示"""
        prefix = "  " * indent + "🧠 "
        print(f"{prefix}{message}")
    
    def _print_creation_step(self, step: str, details: str = None):
        """プラン作成ステップを表示"""
        print(f"  ✨ {step}")
        if details:
            print(f"     └─ {details}")
    
    def _analyze_search_results(self, search_results: Dict) -> Dict:
        """検索結果を分析して有用な情報を抽出"""
        self._print_thinking("検索結果の詳細分析を開始...")
        
        extracted_info = {
            "restaurants": [],
            "activities": [],
            "locations": [],
            "total_results": 0
        }
        
        for keyword, results in search_results.items():
            if isinstance(results, list):
                self._print_creation_step(f"キーワード分析", f"\"{keyword}\" - {len(results)}件の結果")
                extracted_info["total_results"] += len(results)
                
                for result in results:
                    if isinstance(result, dict):
                        title = result.get('title', '')
                        snippet = result.get('snippet', '')
                        
                        # レストラン情報の抽出
                        if any(word in title.lower() or word in snippet.lower() 
                               for word in ['レストラン', 'restaurant', 'カフェ', 'cafe', '食事', 'グルメ', 'イタリアン', 'フレンチ', '和食', '中華']):
                            extracted_info["restaurants"].append({
                                "name": title,
                                "description": snippet,
                                "keyword": keyword
                            })
                        
                        # アクティビティ情報の抽出
                        elif any(word in title.lower() or word in snippet.lower() 
                                for word in ['映画', 'cinema', '美術館', 'museum', '公園', 'park', 'デート', 'date', 'アクティビティ']):
                            extracted_info["activities"].append({
                                "name": title,
                                "description": snippet,
                                "keyword": keyword
                            })
                        
                        # その他の場所情報
                        else:
                            extracted_info["locations"].append({
                                "name": title,
                                "description": snippet,
                                "keyword": keyword
                            })
            elif isinstance(results, dict) and 'error' in results:
                self._print_creation_step(f"検索エラー", f"\"{keyword}\" - {results['error']}")
        
        self._print_creation_step("抽出結果", 
            f"レストラン: {len(extracted_info['restaurants'])}件, "
            f"アクティビティ: {len(extracted_info['activities'])}件, "
            f"その他: {len(extracted_info['locations'])}件")
        
        return extracted_info
    
    async def suggest_plans(self, thinking_result: Dict, search_results: Dict) -> Dict:
        """
        思考結果と検索結果を基に、具体的なプランを提案
        """
        self._print_thinking("検索結果を基にした具体的プラン作成を開始...")
        
        # 検索結果を分析
        extracted_info = self._analyze_search_results(search_results)
        
        self._print_thinking("検索結果を基にした実現可能なプランを作成中...")
        self._print_creation_step("提案トーン", "具体的で実行しやすく、魅力的な内容")
        
        system_prompt = f"""
        あなたはカップル向けの最高のデートプランナーです。
        以下の実際の検索結果を必ず活用して、具体的で実現可能な予定を3つ提案してください。

        【重要な指示】
        1. 検索結果に含まれる実際の店舗名、場所名を必ず使用してください
        2. 各プランには具体的な店舗名、住所（分かる範囲で）、営業時間（推定可）を含めてください
        3. 検索結果の情報を基に、実際に存在する場所でのプランを作成してください
        4. 一般的な提案ではなく、検索で見つかった具体的な情報を活用してください

        【検索結果サマリー】
        - レストラン情報: {len(extracted_info['restaurants'])}件
        - アクティビティ情報: {len(extracted_info['activities'])}件
        - その他の場所情報: {len(extracted_info['locations'])}件
        - 総検索結果数: {extracted_info['total_results']}件

        提供されたfunction schemaに従って、構造化された3つのプランを提案してください。
        カップルが実際に行動できるよう、具体的で実用的な提案をしてください。
        """
        
        # 検索結果を整理して含める
        context = f"""
        思考結果:
        {json.dumps(thinking_result, ensure_ascii=False, indent=2)}
        
        検索結果（詳細）:
        {json.dumps(search_results, ensure_ascii=False, indent=2)}
        
        抽出された情報:
        {json.dumps(extracted_info, ensure_ascii=False, indent=2)}
        """
        
        self._print_thinking("GPT-4による具体的プラン生成を実行中...")
        self._print_creation_step("生成方針", "検索結果の実店舗情報を必ず活用")
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=context)
        ]
        
        self._print_thinking("GPT-4にfunction callingリクエスト送信中...")
        
        try:
            response = await self.llm.ainvoke(
                messages,
                functions=[self._get_suggestion_function()],
                function_call={"name": "suggest_plans"}
            )
            
            self._print_thinking("GPT-4からレスポンス受信完了")
            
            # Function callの結果を取得
            if hasattr(response, 'additional_kwargs') and 'function_call' in response.additional_kwargs:
                function_call = response.additional_kwargs['function_call']
                if function_call['name'] == 'suggest_plans':
                    plan_result = json.loads(function_call['arguments'])
                    
                    self._print_thinking("✅ 具体的プラン提案が正常に完了しました")
                    
                    # 検索結果活用状況を追加
                    plan_result["search_utilization"] = {
                        "total_search_results": extracted_info["total_results"],
                        "restaurants_found": len(extracted_info["restaurants"]),
                        "activities_found": len(extracted_info["activities"]),
                        "locations_found": len(extracted_info["locations"]),
                        "search_keywords_used": thinking_result.get('search_keywords', [])
                    }
                    
                    # 主要なプラン結果を表示
                    if 'plans' in plan_result:
                        plans = plan_result['plans']
                        if isinstance(plans, list):
                            self._print_creation_step("生成されたプラン", f"{len(plans)}個の具体的な提案を作成")
                            for i, plan in enumerate(plans):
                                if isinstance(plan, dict) and 'title' in plan:
                                    print(f"       [{i+1}] {plan['title']}")
                                    # 具体的な店舗名が含まれているかチェック
                                    if 'schedule' in plan:
                                        self._print_creation_step(f"プラン{i+1}詳細", "実店舗情報を含む具体的なスケジュール")
                                else:
                                    print(f"       [{i+1}] プラン{i+1}")
                    
                    # 予算情報の表示
                    if 'plans' in plan_result and isinstance(plan_result['plans'], list):
                        for i, plan in enumerate(plan_result['plans']):
                            if isinstance(plan, dict) and 'total_budget' in plan:
                                budget = plan['total_budget']
                                if isinstance(budget, dict) and 'cost_breakdown' in budget:
                                    self._print_creation_step(f"プラン{i+1}予算", budget['cost_breakdown'])
                    
                    # 検索結果活用状況の表示
                    self._print_creation_step("検索活用状況", 
                        f"検索結果{extracted_info['total_results']}件から具体的な店舗・場所情報を抽出")
                    
                    return plan_result
                else:
                    raise ValueError("予期しないfunction callが返されました")
            else:
                raise ValueError("Function callの結果が見つかりません")
                
        except Exception as e:
            self._print_thinking("❌ Function callingプラン提案に失敗しました")
            self._print_creation_step("エラー詳細", str(e))
            return {"error": "提案の解析に失敗しました", "error_details": str(e)}