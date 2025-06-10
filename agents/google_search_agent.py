from langchain_community.utilities import GoogleSearchAPIWrapper
from typing import List, Dict
import os

class GoogleSearchAgent:
    """Google検索を実行するAgent"""
    
    def __init__(self, google_api_key: str, google_cse_id: str):
        self.search = GoogleSearchAPIWrapper(
            google_api_key=google_api_key,
            google_cse_id=google_cse_id
        )
    
    def _print_thinking(self, message: str, indent: int = 1):
        """思考プロセスを表示"""
        prefix = "  " * indent + "🧠 "
        print(f"{prefix}{message}")
    
    def _print_search_step(self, step: str, details: str = None):
        """検索ステップを表示"""
        print(f"  🔍 {step}")
        if details:
            print(f"     └─ {details}")
    
    def _print_search_result(self, result: Dict, index: int):
        """個別の検索結果を詳細表示"""
        print(f"    📄 検索結果 [{index}]")
        print(f"    ┌─ タイトル: {result.get('title', 'タイトルなし')}")
        
        # スニペットを改行で整理して表示
        snippet = result.get('snippet', 'スニペットなし')
        if len(snippet) > 100:
            # 長いスニペットは適切に改行
            lines = []
            words = snippet.split()
            current_line = ""
            for word in words:
                if len(current_line + " " + word) > 80:
                    if current_line:
                        lines.append(current_line)
                        current_line = word
                    else:
                        lines.append(word)
                else:
                    current_line = current_line + " " + word if current_line else word
            if current_line:
                lines.append(current_line)
            
            print(f"    ├─ 概要:")
            for i, line in enumerate(lines[:3]):  # 最大3行まで表示
                print(f"    │   {line.strip()}")
            if len(lines) > 3:
                print(f"    │   ... (残り{len(lines) - 3}行)")
        else:
            print(f"    ├─ 概要: {snippet}")
        
        # URLを表示
        url = result.get('link', 'URLなし')
        if len(url) > 60:
            print(f"    └─ URL: {url[:57]}...")
        else:
            print(f"    └─ URL: {url}")
        print()  # 空行で区切り
    
    def _print_search_summary(self, keyword: str, results: List[Dict]):
        """検索結果のサマリーを表示"""
        if not results:
            return
        
        print(f"  📊 キーワード「{keyword}」の検索サマリー")
        print(f"     ├─ 取得件数: {len(results)}件")
        
        # タイトルに含まれるキーワードを分析
        restaurant_count = 0
        location_count = 0
        activity_count = 0
        
        for result in results:
            title = result.get('title', '').lower()
            snippet = result.get('snippet', '').lower()
            text = title + " " + snippet
            
            if any(word in text for word in ['レストラン', 'restaurant', '食事', 'グルメ', 'カフェ', 'cafe', 'パスタ', 'イタリアン']):
                restaurant_count += 1
            elif any(word in text for word in ['スポット', '観光', 'デート', '公園', 'museum', 'park', 'アクティビティ']):
                activity_count += 1
            else:
                location_count += 1
        
        print(f"     ├─ レストラン関連: {restaurant_count}件")
        print(f"     ├─ アクティビティ関連: {activity_count}件")
        print(f"     └─ その他の場所: {location_count}件")
        print()
    
    async def search_information(self, search_keywords: List[str]) -> Dict:
        """
        複数のキーワードで検索を実行
        """
        self._print_thinking("Web検索の準備を開始...")
        self._print_search_step("検索対象", f"{len(search_keywords)}個のキーワード")
        
        for i, keyword in enumerate(search_keywords):
            print(f"       [{i+1}] \"{keyword}\"")
        
        results = {}
        successful_searches = 0
        failed_searches = 0
        total_results_count = 0
        
        self._print_thinking("各キーワードで順次検索を実行中...")
        
        for i, keyword in enumerate(search_keywords):
            print(f"\n{'='*60}")
            self._print_search_step(f"検索実行 [{i+1}/{len(search_keywords)}]", f"キーワード: \"{keyword}\"")
            print(f"{'='*60}")
            
            try:
                self._print_thinking(f"Google Search APIにリクエスト送信中...", 2)
                search_results = self.search.results(keyword, num_results=5)
                
                if search_results and isinstance(search_results, list) and len(search_results) > 0:
                    results[keyword] = search_results
                    result_count = len(search_results)
                    total_results_count += result_count
                    self._print_search_step("検索成功", f"{result_count}件の結果を取得")
                    successful_searches += 1
                    
                    # 検索結果の詳細表示
                    print(f"\n  🔍 検索結果詳細:")
                    for j, result in enumerate(search_results, 1):
                        self._print_search_result(result, j)
                    
                    # 検索結果のサマリー表示
                    self._print_search_summary(keyword, search_results)
                    
                elif search_results and isinstance(search_results, list):
                    results[keyword] = {"message": "検索結果が見つかりませんでした"}
                    self._print_search_step("検索完了", "結果なし")
                    print(f"  ℹ️  キーワード「{keyword}」では有効な結果が見つかりませんでした\n")
                else:
                    results[keyword] = {"message": "検索結果の形式が不正です"}
                    self._print_search_step("検索警告", "結果の形式が予期しない形式です")
                    print(f"  ⚠️  キーワード「{keyword}」の検索結果が不正な形式です\n")
                    
            except Exception as e:
                error_message = str(e)
                results[keyword] = {"error": error_message}
                self._print_search_step("検索エラー", error_message[:50] + "..." if len(error_message) > 50 else error_message)
                failed_searches += 1
                
                # エラーの詳細表示
                print(f"  ❌ エラー詳細:")
                print(f"     キーワード: \"{keyword}\"")
                print(f"     エラー内容: {error_message}")
                if "quota" in error_message.lower():
                    print(f"     💡 対処法: Google Search APIの使用量制限に達している可能性があります")
                elif "key" in error_message.lower():
                    print(f"     💡 対処法: APIキーの設定を確認してください")
                print()
        
        # 全体の検索結果サマリーを表示
        print(f"\n{'🎯'*20} 検索完了サマリー {'🎯'*20}")
        self._print_thinking("✅ Web検索が完了しました")
        self._print_search_step("全体サマリー", 
            f"成功: {successful_searches}件, 失敗: {failed_searches}件, 総取得結果: {total_results_count}件")
        
        if successful_searches > 0:
            self._print_search_step("取得情報", f"合計{total_results_count}件の具体的な店舗・場所情報を取得")
            self._print_search_step("活用方針", "これらの検索結果を基に具体的なプランを作成します")
            
            # 成功したキーワードのリスト表示
            successful_keywords = [k for k, v in results.items() 
                                 if isinstance(v, list) and len(v) > 0]
            if successful_keywords:
                print(f"  ✅ 成功したキーワード:")
                for keyword in successful_keywords:
                    result_count = len(results[keyword]) if isinstance(results[keyword], list) else 0
                    print(f"     • \"{keyword}\" ({result_count}件)")
        else:
            self._print_search_step("代替対応", "一般的な知識ベースで提案を作成します")
            self._print_search_step("推奨対処", "Google Search APIの設定やネットワーク接続を確認してください")
            
            # 失敗したキーワードのリスト表示
            failed_keywords = [k for k, v in results.items() 
                             if isinstance(v, dict) and 'error' in v]
            if failed_keywords:
                print(f"  ❌ 失敗したキーワード:")
                for keyword in failed_keywords:
                    error = results[keyword].get('error', '不明なエラー')
                    print(f"     • \"{keyword}\" - {error[:30]}...")
        
        print(f"{'🎯'*60}")
        
        return results