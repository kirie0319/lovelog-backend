from .conversation_analyzer import ConversationAnalyzer
from .intent_understanding import IntentUnderstandingAgent
from .thinking_agent import ThinkingAgent
from .google_search_agent import GoogleSearchAgent
from .plan_suggestion_agent import PlanSuggestionAgent
from typing import List, Dict
import asyncio
import json
import logging
import time
from datetime import datetime

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIOrchestrator:
    """全てのAgentを統括するオーケストレーター"""
    
    def __init__(self, openai_api_key: str, google_api_key: str = None, google_cse_id: str = None, debug_mode: bool = True):
        self.debug_mode = debug_mode
        self.conversation_analyzer = ConversationAnalyzer(openai_api_key)
        self.intent_agent = IntentUnderstandingAgent(openai_api_key)
        self.thinking_agent = ThinkingAgent(openai_api_key)
        self.plan_agent = PlanSuggestionAgent(openai_api_key)
        
        # Google Search Agentは必須
        if google_api_key and google_cse_id:
            self.search_agent = GoogleSearchAgent(google_api_key, google_cse_id)
        else:
            self.search_agent = None
            print("⚠️  警告: Google Search APIが設定されていません")
            print("   具体的な店舗情報を含むプランを作成するには、Google Search APIの設定が必要です")
    
    def _print_thinking_header(self, step: str, agent_name: str):
        """思考プロセスのヘッダーを表示"""
        print("\n" + "="*80)
        print(f"🤖 {agent_name} - {step}")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
    
    def _print_thinking_process(self, title: str, content: str, indent: int = 0):
        """思考プロセスの詳細を表示"""
        prefix = "  " * indent + "💭 "
        print(f"{prefix}{title}")
        if content:
            lines = content.split('\n')
            for line in lines:
                if line.strip():
                    print(f"{'  ' * (indent + 1)}└─ {line.strip()}")
    
    def _print_input_data(self, title: str, data: Dict, max_items: int = 3):
        """入力データを整理して表示"""
        print(f"\n📥 {title}")
        print("-" * 40)
        
        if isinstance(data, list):
            print(f"   データ数: {len(data)}件")
            for i, item in enumerate(data[:max_items]):
                if isinstance(item, dict):
                    if 'content' in item and 'sender' in item:
                        sender = item['sender'].get('display_name', 'Unknown')
                        content = item['content'][:50] + "..." if len(item['content']) > 50 else item['content']
                        print(f"   [{i+1}] {sender}: {content}")
                    else:
                        print(f"   [{i+1}] {str(item)[:80]}...")
                else:
                    print(f"   [{i+1}] {str(item)[:80]}...")
            if len(data) > max_items:
                print(f"   ... および他{len(data) - max_items}件")
        elif isinstance(data, dict):
            for key, value in list(data.items())[:max_items]:
                if isinstance(value, (str, int, float, bool)):
                    print(f"   {key}: {value}")
                elif isinstance(value, list):
                    print(f"   {key}: [{len(value)}件のリスト]")
                else:
                    print(f"   {key}: {type(value).__name__}")
            if len(data) > max_items:
                print(f"   ... および他{len(data) - max_items}項目")
        else:
            print(f"   {str(data)[:100]}...")
    
    def _print_output_data(self, title: str, data: Dict):
        """出力データを整理して表示"""
        print(f"\n📤 {title}")
        print("-" * 40)
        
        if isinstance(data, dict):
            # エラーがある場合は最初に表示
            if 'error' in data:
                print(f"   ❌ エラー: {data['error']}")
                return
            
            # 検索結果の場合は詳細表示
            if title == "出力: 検索結果" and any(isinstance(v, list) for v in data.values()):
                self._print_detailed_search_results(data)
                return
            
            # 重要な項目を優先表示
            priority_keys = ['topics', 'support_type', 'search_keywords', 'suggestions', 'plans']
            displayed_keys = set()
            
            for key in priority_keys:
                if key in data:
                    value = data[key]
                    if isinstance(value, list):
                        print(f"   ✅ {key}: {len(value)}件")
                        for i, item in enumerate(value[:2]):
                            print(f"      [{i+1}] {str(item)[:60]}...")
                        if len(value) > 2:
                            print(f"      ... および他{len(value) - 2}件")
                    elif isinstance(value, str):
                        print(f"   ✅ {key}: {value[:80]}...")
                    else:
                        print(f"   ✅ {key}: {type(value).__name__}")
                    displayed_keys.add(key)
            
            # その他の項目
            other_keys = [k for k in data.keys() if k not in displayed_keys and not k.startswith('_')]
            if other_keys:
                print(f"   📋 その他: {', '.join(other_keys[:3])}{'...' if len(other_keys) > 3 else ''}")
        else:
            print(f"   {str(data)[:100]}...")
    
    def _print_detailed_search_results(self, search_results: Dict):
        """検索結果の詳細表示"""
        total_results = 0
        successful_keywords = []
        
        print(f"   🔍 Google検索結果詳細:")
        
        for keyword, results in search_results.items():
            if isinstance(results, list) and len(results) > 0:
                total_results += len(results)
                successful_keywords.append(keyword)
                print(f"\n   📋 キーワード: \"{keyword}\"")
                print(f"   ├─ 取得件数: {len(results)}件")
                
                # 最初の2件を詳細表示
                for i, result in enumerate(results[:2], 1):
                    if isinstance(result, dict):
                        title = result.get('title', 'タイトルなし')
                        snippet = result.get('snippet', 'スニペットなし')
                        url = result.get('link', 'URLなし')
                        
                        print(f"   ├─ [{i}] {title[:50]}{'...' if len(title) > 50 else ''}")
                        print(f"   │    概要: {snippet[:80]}{'...' if len(snippet) > 80 else ''}")
                        print(f"   │    URL: {url[:50]}{'...' if len(url) > 50 else ''}")
                
                if len(results) > 2:
                    print(f"   └─ ... および他{len(results) - 2}件の結果")
            
            elif isinstance(results, dict):
                if 'error' in results:
                    print(f"\n   ❌ キーワード: \"{keyword}\" - エラー: {results['error'][:50]}...")
                else:
                    print(f"\n   ⚠️  キーワード: \"{keyword}\" - {results.get('message', '結果なし')}")
        
        # サマリー表示
        print(f"\n   📊 検索結果サマリー:")
        print(f"   ├─ 成功したキーワード: {len(successful_keywords)}個")
        print(f"   ├─ 総取得結果数: {total_results}件")
        print(f"   └─ プラン作成に活用: ✅ 可能" if total_results > 0 else "   └─ プラン作成に活用: ❌ 不可能")
        
        if successful_keywords:
            print(f"\n   ✅ 活用予定のキーワード:")
            for keyword in successful_keywords:
                result_count = len(search_results[keyword])
                print(f"      • \"{keyword}\" ({result_count}件)")
        
        print()  # 空行を追加
    
    def _print_thinking_step(self, step_name: str, description: str):
        """思考ステップを表示"""
        print(f"\n🔄 {step_name}")
        print(f"   {description}")
    
    def _print_completion(self, agent_name: str, duration: float, success: bool):
        """完了状況を表示"""
        status = "✅ 完了" if success else "❌ 失敗"
        print(f"\n{status} {agent_name} - 処理時間: {duration:.2f}秒")
        print("-" * 80)
    
    async def process_ai_request(self, messages: List[Dict]) -> Dict:
        """
        AIボタンが押された時のメイン処理
        """
        print("\n" + "🚀" * 20 + " AI思考プロセス開始 " + "🚀" * 20)
        print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"入力メッセージ数: {len(messages)}件")
        print("🚀" * 60)
        
        debug_info = {}
        overall_start_time = time.time()
        
        try:
            # Step 1: 会話分析
            self._print_thinking_header("STEP 1", "ConversationAnalyzer (会話分析エージェント)")
            self._print_input_data("入力: 会話履歴", messages)
            
            step_start_time = time.time()
            self._print_thinking_step("分析開始", "カップルの会話パターンと重要な情報を抽出中...")
            
            analysis_result = await self.conversation_analyzer.analyze_conversation(messages)
            
            step_duration = time.time() - step_start_time
            debug_info["step1_analysis"] = analysis_result
            
            self._print_output_data("出力: 分析結果", analysis_result)
            self._print_completion("ConversationAnalyzer", step_duration, 'error' not in analysis_result)
            
            # Step 2: 意図理解
            self._print_thinking_header("STEP 2", "IntentUnderstandingAgent (意図理解エージェント)")
            self._print_input_data("入力: 会話分析結果", analysis_result)
            
            step_start_time = time.time()
            self._print_thinking_step("意図分析開始", "カップルが求めているサポートの種類を判断中...")
            
            intent_result = await self.intent_agent.understand_intent(analysis_result)
            
            step_duration = time.time() - step_start_time
            debug_info["step2_intent"] = intent_result
            
            self._print_output_data("出力: 意図理解結果", intent_result)
            self._print_completion("IntentUnderstandingAgent", step_duration, 'error' not in intent_result)
            
            # Step 3: 思考・計画
            self._print_thinking_header("STEP 3", "ThinkingAgent (思考エージェント)")
            self._print_input_data("入力: 意図理解結果", intent_result)
            
            step_start_time = time.time()
            self._print_thinking_step("戦略立案開始", "最適な検索戦略と提案方針を考案中...")
            
            thinking_result = await self.thinking_agent.think_and_plan(intent_result)
            
            step_duration = time.time() - step_start_time
            debug_info["step3_thinking"] = thinking_result
            
            self._print_output_data("出力: 思考結果", thinking_result)
            self._print_completion("ThinkingAgent", step_duration, 'error' not in thinking_result)
            
            # Step 4: Google検索（必須）
            search_results = {}
            if not self.search_agent:
                # Google Search APIが設定されていない場合はエラー
                error_message = "Google Search APIが設定されていません。具体的な店舗情報を含むプランを作成するには、GOOGLE_API_KEYとGOOGLE_CSE_IDの設定が必要です。"
                print("\n" + "💥" * 20 + " 設定エラー " + "💥" * 20)
                print(f"❌ {error_message}")
                print("💥" * 60)
                
                return {
                    "success": False,
                    "error": "google_search_not_configured",
                    "message": error_message,
                    "debug_info": debug_info,
                    "processing_time": time.time() - overall_start_time
                }
            
            if not thinking_result.get('search_keywords'):
                # 検索キーワードが生成されていない場合
                error_message = "検索キーワードが生成されませんでした。会話内容から具体的な検索対象を特定できません。"
                print("\n" + "💥" * 20 + " キーワード生成エラー " + "💥" * 20)
                print(f"❌ {error_message}")
                print("💥" * 60)
                
                return {
                    "success": False,
                    "error": "no_search_keywords",
                    "message": error_message,
                    "debug_info": debug_info,
                    "processing_time": time.time() - overall_start_time
                }
            
            self._print_thinking_header("STEP 4", "GoogleSearchAgent (検索エージェント) - 必須")
            self._print_input_data("入力: 検索キーワード", thinking_result.get('search_keywords', []))
            
            step_start_time = time.time()
            self._print_thinking_step("情報検索開始", "具体的な店舗・場所情報をWeb検索中...")
            
            search_results = await self.search_agent.search_information(
                thinking_result['search_keywords']
            )
            
            step_duration = time.time() - step_start_time
            debug_info["step4_search"] = search_results
            
            # 検索結果の有効性をチェック
            valid_results = 0
            for keyword, result in search_results.items():
                if isinstance(result, list) and len(result) > 0:
                    valid_results += 1
                elif isinstance(result, dict) and 'error' not in result and result.get('message') != "検索結果が見つかりませんでした":
                    valid_results += 1
            
            if valid_results == 0:
                error_message = "有効な検索結果が取得できませんでした。ネットワーク接続やAPI設定を確認してください。"
                print(f"\n❌ 検索結果エラー: {error_message}")
                
                return {
                    "success": False,
                    "error": "no_valid_search_results",
                    "message": error_message,
                    "search_results": search_results,
                    "debug_info": debug_info,
                    "processing_time": time.time() - overall_start_time
                }
            
            self._print_output_data("出力: 検索結果", search_results)
            self._print_completion("GoogleSearchAgent", step_duration, True)
            
            # Step 5: 最終提案（検索結果必須）
            self._print_thinking_header("STEP 5", "PlanSuggestionAgent (プラン提案エージェント)")
            self._print_input_data("入力: 思考結果", thinking_result)
            self._print_input_data("入力: 検索結果", search_results)
            
            step_start_time = time.time()
            self._print_thinking_step("提案生成開始", "検索結果を基にした具体的なプランを作成中...")
            
            final_suggestions = await self.plan_agent.suggest_plans(thinking_result, search_results)
            
            step_duration = time.time() - step_start_time
            debug_info["step5_suggestions"] = final_suggestions
            
            self._print_output_data("出力: 最終提案", final_suggestions)
            self._print_completion("PlanSuggestionAgent", step_duration, 'error' not in final_suggestions)
            
            # 全体の完了
            overall_duration = time.time() - overall_start_time
            print("\n" + "🎉" * 20 + " AI思考プロセス完了 " + "🎉" * 20)
            print(f"総処理時間: {overall_duration:.2f}秒")
            print(f"完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"🔍 検索結果活用: {valid_results}件のキーワードで有効な結果を取得")
            print("🎉" * 60)
            
            result = {
                "success": True,
                "analysis": analysis_result,
                "intent": intent_result,
                "thinking": thinking_result,
                "search_results": search_results,
                "suggestions": final_suggestions,
                "message": "検索結果を基にした具体的な提案を作成しました！",
                "processing_time": overall_duration,
                "search_stats": {
                    "total_keywords": len(thinking_result.get('search_keywords', [])),
                    "successful_searches": valid_results,
                    "search_required": True
                }
            }
            
            # デバッグモードの場合、詳細情報を含める
            if self.debug_mode:
                result["debug_info"] = debug_info
                result["processing_steps"] = [
                    "会話分析完了",
                    "意図理解完了", 
                    "思考・計画完了",
                    f"検索処理完了 ({valid_results}件成功)",
                    "最終提案完了"
                ]
            
            return result
            
        except Exception as e:
            overall_duration = time.time() - overall_start_time
            
            print("\n" + "💥" * 20 + " エラー発生 " + "💥" * 20)
            print(f"❌ エラー内容: {str(e)}")
            print(f"⏱️ エラー発生時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"⏱️ 処理時間: {overall_duration:.2f}秒")
            
            error_info = {
                "error": str(e),
                "debug_info": debug_info,
                "message": "申し訳ございません。AIの処理中にエラーが発生しました。",
                "processing_time": overall_duration
            }
            
            if self.debug_mode:
                import traceback
                error_traceback = traceback.format_exc()
                error_info["traceback"] = error_traceback
                print(f"📋 詳細なエラー情報:")
                print(error_traceback)
            
            print("💥" * 60)
            
            return {
                "success": False,
                **error_info
            }