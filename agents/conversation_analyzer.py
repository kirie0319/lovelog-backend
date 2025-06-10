from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from typing import List, Dict
import json
from datetime import datetime

class ConversationAnalyzer:
    """会話履歴を分析するAgent"""
    
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.3,
            openai_api_key=openai_api_key
        )
    
    def _get_analysis_function(self):
        """会話分析用のfunction定義"""
        return {
            "name": "analyze_conversation",
            "description": "カップルの会話を分析して構造化された結果を返す",
            "parameters": {
                "type": "object",
                "properties": {
                    "topics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "会話で言及された話題のリスト（デート、旅行、食事、日常、趣味、イベントなど）"
                    },
                    "locations_mentioned": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "具体的に言及された場所や地名のリスト"
                    },
                    "time_references": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "言及された時間や日時の表現のリスト"
                    },
                    "preferences": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "category": {"type": "string", "description": "好みのカテゴリ（料理、活動、場所など）"},
                                "preference": {"type": "string", "description": "具体的な好みの内容"},
                                "speaker": {"type": "string", "description": "発言した話者"}
                            },
                            "required": ["category", "preference", "speaker"]
                        },
                        "description": "表現された興味や好みのリスト"
                    },
                    "plans_or_proposals": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "proposal": {"type": "string", "description": "提案や計画の内容"},
                                "status": {"type": "string", "enum": ["proposed", "agreed", "rejected", "pending"], "description": "提案の状態"},
                                "speaker": {"type": "string", "description": "提案した話者"}
                            },
                            "required": ["proposal", "status", "speaker"]
                        },
                        "description": "計画や提案に関する発言のリスト"
                    },
                    "emotional_tone": {
                        "type": "object",
                        "properties": {
                            "overall_mood": {"type": "string", "description": "会話全体の雰囲気"},
                            "relationship_dynamic": {"type": "string", "description": "関係性の特徴"},
                            "enthusiasm_level": {"type": "string", "enum": ["low", "medium", "high"], "description": "積極性のレベル"}
                        },
                        "required": ["overall_mood", "relationship_dynamic", "enthusiasm_level"]
                    },
                    "speaker_characteristics": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "object",
                            "properties": {
                                "message_count": {"type": "integer", "description": "発言数"},
                                "communication_style": {"type": "string", "description": "コミュニケーションスタイル"},
                                "main_interests": {"type": "array", "items": {"type": "string"}, "description": "主な関心事"}
                            }
                        },
                        "description": "各話者の特徴"
                    },
                    "unresolved_topics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "未解決や決まっていない話題のリスト"
                    }
                },
                "required": ["topics", "locations_mentioned", "time_references", "preferences", "plans_or_proposals", "emotional_tone", "speaker_characteristics", "unresolved_topics"]
            }
        }
    
    def _print_thinking(self, message: str, indent: int = 1):
        """思考プロセスを表示"""
        prefix = "  " * indent + "🧠 "
        print(f"{prefix}{message}")
    
    def _print_analysis_step(self, step: str, details: str = None):
        """分析ステップを表示"""
        print(f"  🔍 {step}")
        if details:
            print(f"     └─ {details}")

    async def analyze_conversation(self, messages: List[Dict]) -> Dict:
        """
        会話履歴を分析して構造化された結果を返す
        """
        self._print_thinking("会話履歴の分析を開始...")
        
        if not messages:
            self._print_analysis_step("エラー", "分析対象の会話が見つかりません")
            return {"error": "会話履歴が空です"}
        
        # 最新の会話を優先（最大30件）
        recent_messages = messages[:30] if len(messages) > 30 else messages
        self._print_analysis_step("分析対象", f"{len(recent_messages)}件のメッセージを分析")
        
        # 話者情報を抽出
        speakers_info = {}
        for msg in recent_messages:
            if 'sender' in msg and isinstance(msg['sender'], dict):
                sender_id = msg['sender'].get('user_id', 'unknown')
                display_name = msg['sender'].get('display_name', f'User_{sender_id}')
                if sender_id not in speakers_info:
                    speakers_info[sender_id] = {
                        "display_name": display_name,
                        "message_count": 0
                    }
                speakers_info[sender_id]["message_count"] += 1
        
        self._print_analysis_step("話者情報", f"{len(speakers_info)}名の話者を検出")
        
        # 会話テキストを構築
        conversation_text = ""
        for msg in recent_messages:
            if 'sender' in msg and 'content' in msg:
                sender_name = msg['sender'].get('display_name', 'Unknown')
                content = msg['content']
                timestamp = msg.get('created_at', '')
                conversation_text += f"[{timestamp}] {sender_name}: {content}\n"
        
        system_prompt = f"""
        あなたはカップルの会話を分析する専門家です。
        以下の会話履歴から、提供されたfunction schemaに従って情報を抽出してください。
        
        【話者情報】
        {json.dumps(speakers_info, ensure_ascii=False, indent=2)}
        
        【会話統計】
        - 総メッセージ数: {len(recent_messages)}
        - 分析対象期間: {self._get_conversation_timespan(recent_messages)}
        - 各話者の発言数と比率
        
        会話の内容を詳細に分析し、構造化された形で情報を抽出してください。
        """
        
        messages_for_llm = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"会話履歴:\n{conversation_text}")
        ]
        
        self._print_thinking("GPT-4にfunction callingリクエスト送信中...")
        
        try:
            response = await self.llm.ainvoke(
                messages_for_llm,
                functions=[self._get_analysis_function()],
                function_call={"name": "analyze_conversation"}
            )
            
            self._print_thinking("GPT-4からレスポンス受信完了")
            
            # Function callの結果を取得
            if hasattr(response, 'additional_kwargs') and 'function_call' in response.additional_kwargs:
                function_call = response.additional_kwargs['function_call']
                if function_call['name'] == 'analyze_conversation':
                    analysis_result = json.loads(function_call['arguments'])
                    
                    # メタデータを追加
                    analysis_result["metadata"] = {
                        "total_messages_analyzed": len(recent_messages),
                        "total_messages_available": len(messages),
                        "speakers": speakers_info,
                        "analysis_timestamp": datetime.now().isoformat(),
                        "conversation_timespan": self._get_conversation_timespan(recent_messages)
                    }
                    
                    self._print_thinking("✅ 会話分析が正常に完了しました")
                    
                    # 主要な分析結果を表示
                    if 'topics' in analysis_result:
                        topics = analysis_result['topics']
                        if isinstance(topics, list):
                            self._print_analysis_step("検出された話題", f"{len(topics)}個のトピックを特定")
                            for i, topic in enumerate(topics[:3]):
                                print(f"       [{i+1}] {topic}")
                    
                    return analysis_result
                else:
                    raise ValueError("予期しないfunction callが返されました")
            else:
                raise ValueError("Function callの結果が見つかりません")
                
        except Exception as e:
            self._print_thinking("❌ Function calling分析に失敗しました")
            self._print_analysis_step("エラー詳細", str(e))
            return {
                "error": "分析結果の解析に失敗しました", 
                "error_details": str(e),
                "metadata": {
                    "total_messages_analyzed": len(recent_messages),
                    "total_messages_available": len(messages),
                    "speakers": speakers_info,
                    "analysis_timestamp": datetime.now().isoformat()
                }
            }

    def _get_conversation_timespan(self, messages: List[Dict]) -> str:
        """会話の時間範囲を取得"""
        if not messages:
            return "不明"
        
        timestamps = []
        for msg in messages:
            if 'created_at' in msg and msg['created_at']:
                timestamps.append(msg['created_at'])
        
        if not timestamps:
            return "不明"
        
        # 最新と最古のタイムスタンプを取得
        timestamps.sort()
        oldest = timestamps[0]
        newest = timestamps[-1]
        
        return f"{oldest} ～ {newest}"