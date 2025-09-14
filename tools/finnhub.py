# tools/finnhub_tool.py
import os
from dotenv import load_dotenv
import finnhub
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict

class FinnhubTool:
    """
    A wrapper around the Finnhub API for stock data and fundamentals.
    Free-tier friendly (excludes premium-only sentiment).
    Requires FINNHUB_API_KEY in `.env`.
    """

    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("FINNHUB_API_KEY")
        if not self.api_key:
            raise ValueError("Missing FINNHUB_API_KEY. Please set it in your .env file.")
        self.client = finnhub.Client(api_key=self.api_key)

    def get_quote(self, symbol: str) -> Dict:
        """
        Get real-time quote for a stock.
        """
        return self.client.quote(symbol)

    def get_company_profile(self, symbol: str) -> Optional[Dict]:
        """
        Get basic company profile (name, industry, market cap).
        """
        return self.client.company_profile2(symbol=symbol)

    def get_financials(self, symbol: str) -> Optional[Dict]:
        """
        Get latest financials.
        """
        return self.client.financials_reported(symbol=symbol, freq="annual")

    def get_news(self, symbol: str, num_articles: int = 5) -> pd.DataFrame:
        """
        Get latest company news (free plan: last 30 days only).
        Returns DataFrame with headline, datetime, source, url.
        """
        today = datetime.now().date()
        thirty_days_ago = today - timedelta(days=30)

        news = self.client.company_news(
            symbol,
            _from=thirty_days_ago.isoformat(),
            to=today.isoformat()
        )
        if not news:
            return pd.DataFrame()
        df = pd.DataFrame(news)
        if "datetime" in df.columns:
            df["datetime"] = pd.to_datetime(df["datetime"], unit="s")
        return df[["datetime", "headline", "source", "url"]].head(num_articles)

    def get_sentiment(self, symbol: str) -> Dict:
        """
        Placeholder for sentiment (premium only).
        """
        return {"error": "News sentiment API is not available on free plan"}
