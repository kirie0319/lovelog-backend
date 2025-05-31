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
    
    async def search_information(self, search_keywords: List[str]) -> Dict:
        """
        複数のキーワードで検索を実行
        """
        results = {}
        
        for keyword in search_keywords:
            try:
                search_results = self.search.results(keyword, num_results=5)
                results[keyword] = search_results
            except Exception as e:
                results[keyword] = {"error": str(e)}
        
        return results