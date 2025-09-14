# from typing import Optional, Dict, Any
# import pandas as pd
# import yfinance as yf
# from tools.yahoo_finance import YahooFinanceTool
# from tools.finnhub import FinnhubTool
# from tools.earnings import EarningsTool
# from tools.edgar import EdgarTool
#
#
# class DataAgent:
#     """
#     Central agent to fetch stock data from multiple sources:
#     - Yahoo Finance
#     - Finnhub (quotes, news, sentiment)
#     - Earnings history & next earnings
#     - 13F filings (optional download)
#
#     All outputs are mapped into a standardized format for downstream agents.
#     Robust: handles missing methods, empty responses, and exceptions.
#     """
#
#     def __init__(self):
#         self.yahoo = YahooFinanceTool()
#         self.finnhub = FinnhubTool()
#         self.earnings = EarningsTool()
#         self.edgar = EdgarTool()
#
#     def fetch_data(
#         self,
#         ticker: str,
#         fetch_earnings: bool = False,
#         fetch_13f: bool = False
#     ) -> Dict[str, Any]:
#         """
#         Fetch all relevant data for a ticker in a standardized format.
#         Returns a dictionary with all results.
#         """
#
#         # --- Initialize standardized schema ---
#         data: Dict[str, Any] = {
#             "ticker": ticker,
#             "price": None,
#             "summary": {},
#             "quote": {},
#             "news": [],
#             "sentiment": {},
#             "earnings": {"history": [], "next_date": None},
#             "filings": {"latest_13f": None, "file_path": None}
#         }
#
#         # --- Yahoo Finance ---
#         try:
#             summary = self.yahoo.get_summary(ticker)
#             if summary:
#                 data["summary"] = summary
#                 data["price"] = float(summary.get("currentPrice", 0)) if "currentPrice" in summary else None
#         except Exception as e:
#             data["summary"]["error"] = f"Yahoo error: {str(e)}"
#             data["price"] = None
#
#         # --- Finnhub ---
#         try:
#             if hasattr(self.finnhub, "get_quote"):
#                 data["quote"] = self.finnhub.get_quote(ticker) or {}
#
#             # if hasattr(self.finnhub, "get_news"):
#             #     data["news"] = self.finnhub.get_news(ticker) or []
#                 # Yahoo news replacement
#             if hasattr(self.yahoo, "news"):
#                 # some YahooFinanceTool implementations may have `news()` method
#                 news_items = getattr(self.yahoo, "news")(ticker)
#                 data["news"] = news_items or []
#             else:
#                 # fallback: yfinance directly
#                 yf_ticker = yf.Ticker(ticker)
#                 yf_news = yf_ticker.news
#                 data["news"] = yf_news if yf_news else []
#
#             if hasattr(self.finnhub, "get_sentiment"):
#                 data["sentiment"] = self.finnhub.get_sentiment(ticker) or {}
#         except Exception as e:
#             data["sentiment"]["error"] = f"Finnhub/Yahoo News error: {str(e)}"
#             data["news"] = []
#
#         # --- Earnings ---
#         if fetch_earnings:
#             try:
#                 hist = self.earnings.get_earnings_history(ticker)
#                 if hist is not None and not hist.empty:
#                     data["earnings"]["history"] = hist.to_dict(orient="records")
#
#                 next_earn = self.earnings.get_next_earnings_date(ticker)
#                 if next_earn is not None:
#                     data["earnings"]["next_date"] = str(next_earn)
#             except Exception as e:
#                 data["earnings"]["error"] = f"Earnings error: {str(e)}"
#
#         # --- 13F Filings ---
#         if fetch_13f:
#             try:
#                 latest_13f = self.edgar.get_latest_13f(ticker)
#                 if latest_13f:
#                     file_path = self.edgar.download_filing(latest_13f)
#                     data["filings"]["latest_13f"] = latest_13f
#                     data["filings"]["file_path"] = file_path
#             except Exception as e:
#                 data["filings"]["error"] = f"EDGAR error: {str(e)}"
#
#         return data

import datetime
from tools.yahoo_finance import YahooFinanceTool
from tools.edgar import EdgarTool
from pathlib import Path

class DataAgent:
    """
    Fetches and structures all data for a given stock ticker.
    Fully compatible with web UI: includes timestamps, sources, and structured metadata.
    """

    def __init__(self):
        self.yahoo = YahooFinanceTool()
        self.edgar = EdgarTool(user_agent="MyStockApp/0.1 (email@example.com)")

    def download_latest_13f(self, ticker: str):
        """
        Download the latest 13F filing for the given ticker.
        Returns the file path if successful, else None.
        """
        try:
            latest_13f = self.edgar.get_latest_13f(ticker)
            if not latest_13f:
                print(f"No 13F filing found for {ticker}")
                return None

            # Ensure download directory exists
            filings_dir = Path("downloads/edgar") / ticker
            filings_dir.mkdir(parents=True, exist_ok=True)

            # Download the filing
            txt_path = self.edgar.download_filing(latest_13f)
            if txt_path:
                # Move/save to our downloads folder
                target_path = filings_dir / Path(txt_path).name
                Path(txt_path).rename(target_path)
                return target_path
            else:
                print(f"Failed to download 13F for {ticker}")
                return None

        except Exception as e:
            print(f"[EDGAR] Error downloading 13F for {ticker}: {e}")
            return None


    def fetch_data(self, ticker: str, fetch_earnings=True, fetch_13f=True) -> dict:
        result = {
            "ticker": ticker,
            "fetch_time": datetime.datetime.utcnow().isoformat(),
            "sources": [],
            "data": {}
        }

        # --- Yahoo Finance Summary ---
        try:
            summary = self.yahoo.get_summary(ticker)
            result["data"]["summary"] = summary
            result["data"]["price"] = self.yahoo.get_current_price(ticker)
            result["sources"].append("YahooFinance")
        except Exception as e:
            result["data"]["summary"] = None
            result["data"]["price"] = None
            result["sources"].append(f"YahooFinance_failed:{str(e)}")

        # --- Yahoo Recommendations ---
        try:
            recommendations = self.yahoo.get_recommendations(ticker)
            result["data"]["recommendations"] = recommendations
            result["sources"].append("YahooRecommendations")
        except Exception as e:
            result["data"]["recommendations"] = None
            result["sources"].append(f"YahooRecommendations_failed:{str(e)}")

        # --- Yahoo Fundamentals ---
        try:
            fundamentals = self.yahoo.get_fundamentals(ticker)
            result["data"]["fundamentals"] = fundamentals
            result["sources"].append("YahooFundamentals")
        except Exception as e:
            result["data"]["fundamentals"] = None
            result["sources"].append(f"YahooFundamentals_failed:{str(e)}")

        # --- Yahoo Price History ---
        if fetch_earnings:
            try:
                price_history = self.yahoo.get_price_history(ticker)
                result["data"]["price_history"] = price_history
                result["sources"].append("YahooPriceHistory")
            except Exception as e:
                result["data"]["price_history"] = None
                result["sources"].append(f"YahooPriceHistory_failed:{str(e)}")

        # --- Edgar 13F Filings ---
        if fetch_13f:
            try:
                cik = self.edgar.get_cik(ticker)
                latest_filing = self.edgar.get_latest_13f(cik)
                result["data"]["filings"] = latest_filing or {}
                result["sources"].append("EDGAR")

                # Optionally download filing
                if latest_filing and latest_filing.get("url"):
                    downloaded_file = self.edgar.download_filing(latest_filing["url"])
                    result["data"]["filings"]["downloaded_file"] = downloaded_file

            except Exception as e:
                result["data"]["filings"] = {}
                result["sources"].append(f"EDGAR_failed:{str(e)}")

        return result
