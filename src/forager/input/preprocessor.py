from typing import Dict, Any, List

class URLPreprocessor:
    """Preprocess the URL"""
    
    @staticmethod
    def clean_url_reply(url: str) -> str:
        """
        clean the reply mark in the URL
        
        Args:
            url (str): the original URL
            
        Returns:
            str: the processed URL
        """
        if '#reply' in url:
            return url.split('#reply')[0]
        return url
        
    @staticmethod
    def process_article(article: Dict[str, Any]) -> Dict[str, Any]:
        """
        process the URL in the article dictionary
        
        Args:
            article (Dict[str, Any]): the dictionary containing the article information
            
        Returns:
            Dict[str, Any]: the processed article dictionary
        """
        if "link" in article:
            article["link"] = URLPreprocessor.clean_url_reply(article["link"])
        return article
    
    @staticmethod
    def process_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        process multiple articles
        
        Args:
            articles (List[Dict[str, Any]]): the article list
            
        Returns:
            List[Dict[str, Any]]: the processed article list
        """
        return [URLPreprocessor.process_article(article) for article in articles]