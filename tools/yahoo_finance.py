# tools/yahoo_finance_tool.py
import yfinance as yf
import pandas as pd
from typing import Optional, Dict

class YahooFinanceTool:
    """
    A wrapper around the yfinance library for fetching stock data
    without API keys.
    """

    def __init__(self):
        pass  # no config needed

    def get_price_history(self, symbol: str, period: str = "6mo", interval: str = "1d") -> list:
        import yfinance as yf

        try:
            df = yf.download(symbol, period=period, interval=interval, progress=False)
            if df.empty:
                print(f"[YahooFinanceTool] No data found for {symbol}")
                return []

            # Flatten MultiIndex columns if present
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ["_".join(col).strip() for col in df.columns.values]

            # Rename standard columns
            df.rename(
                columns={
                    "Open": "open",
                    "High": "high",
                    "Low": "low",
                    "Close": "close",
                    "Adj Close": "adj_close",
                    "Volume": "volume",
                },
                inplace=True,
            )

            df = df.reset_index()
            price_history = df.to_dict(orient="records")
            return price_history

        except Exception as e:
            print(f"[YahooFinanceTool] Failed to fetch price history for {symbol}: {e}")
            return []

    def get_fundamentals(self, symbol: str) -> Optional[Dict]:
        """
        Fetch basic fundamentals & company info.
        Returns: dict with PE ratio, market cap, etc.
        """
        ticker = yf.Ticker(symbol)
        info = ticker.info
        if not info or "shortName" not in info:
            return None
        fundamentals = {
            "name": info.get("shortName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap": info.get("marketCap"),
            "trailing_pe": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "eps": info.get("trailingEps"),
            "dividend_yield": info.get("dividendYield"),
            "beta": info.get("beta"),
        }
        return fundamentals

    def get_recommendations(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Fetch analyst recommendations for a ticker.
        Returns: DataFrame with date, rating, firm, etc.
        """
        ticker = yf.Ticker(symbol)
        recs = ticker.recommendations
        if recs is None or recs.empty:
            return None
        return recs.tail(10)  # last 10 recommendations

    def get_current_price(self, ticker: str):
        try:
            return yf.Ticker(ticker).info.get("currentPrice", None)
        except:
            return None

    def get_summary(self, ticker: str):
        try:
            return yf.Ticker(ticker).info
        except:
            return {}
