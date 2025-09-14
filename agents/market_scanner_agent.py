# import datetime
# from typing import List, Dict
# from statistics import stdev
# from agents.data_agent import DataAgent
# from agents.signal_agent import SignalAgent
#
# class MarketScannerAgent:
#     """
#     Scans a universe of stocks, filters safe investments, generates
#     rich metrics, and web UI-ready output with risk flags for visualization.
#     """
#
#     def __init__(self):
#         self.data_agent = DataAgent()
#         self.signal_agent = SignalAgent()
#
#     def scan_universe(self, tickers: List[str]) -> Dict:
#         """
#         Scan the stock universe and filter stocks for recommendation.
#         Returns:
#             - stock_universe: list of all tickers scanned
#             - selected_stocks: list of tickers passing guardrails
#             - details: full stock info (price, sector, risk flags, signals, etc.)
#         """
#         results = []
#         selected_stocks = []
#
#         for ticker in tickers:
#             stock_info = {
#                 "ticker": ticker,
#                 "generated_time": datetime.datetime.utcnow().isoformat(),
#                 "price": None,
#                 "market_cap": None,
#                 "sector": None,
#                 "country": None,
#                 "signals": {},
#                 "risk_flags": [],
#                 "volatility": None,
#                 "latest_volume": None,
#                 "pe_ratio": None
#             }
#
#             try:
#                 # Fetch structured data
#                 data_output = self.data_agent.fetch_data(ticker)
#                 stock_data = data_output.get("data", {})
#
#                 stock_info["price"] = stock_data.get("price")
#                 stock_info["market_cap"] = stock_data.get("fundamentals", {}).get("market_cap")
#                 stock_info["sector"] = stock_data.get("fundamentals", {}).get("sector")
#                 stock_info["country"] = stock_data.get("fundamentals", {}).get("country")
#                 stock_info["pe_ratio"] = stock_data.get("fundamentals", {}).get("pe_ratio")
#
#                 # Guardrails
#                 if stock_info["price"] is None or stock_info["price"] < 5:
#                     stock_info["risk_flags"].append("Price too low (possible penny stock)")
#
#                 if not stock_info["sector"]:
#                     stock_info["risk_flags"].append("Sector unknown")
#
#                 if not stock_data.get("price_history"):
#                     stock_info["risk_flags"].append("Insufficient price history")
#
#                 # Generate signals
#                 signals = self.signal_agent.generate_signals(data_output)
#                 stock_info["signals"] = signals.get("signals", {})
#
#                 # --- Risk flags based on metrics ---
#                 price_history = stock_data.get("price_history", [])
#                 close_key = f"Close_{ticker}"
#                 volume_key = f"Volume_{ticker}"
#
#                 closes = [p.get(close_key) for p in price_history if p.get(close_key) is not None]
#                 volumes = [p.get(volume_key) for p in price_history if p.get(volume_key) is not None]
#
#                 # Volatility
#                 if len(closes) >= 20:
#                     vol = stdev(closes[-20:])
#                     stock_info["volatility"] = vol
#                     if vol / closes[-1] > 0.05:  # more than 5% daily SD
#                         stock_info["risk_flags"].append("High recent volatility")
#
#                 # Volume spike
#                 if len(volumes) >= 20:
#                     avg_vol = sum(volumes[-20:]) / 20
#                     stock_info["latest_volume"] = volumes[-1]
#                     if volumes[-1] > 2 * avg_vol:
#                         stock_info["risk_flags"].append("Sudden volume spike")
#
#                 # Extreme PE ratio
#                 pe = stock_info.get("pe_ratio")
#                 if pe is not None and (pe < 5 or pe > 50):
#                     stock_info["risk_flags"].append("Extreme PE ratio")
#
#                 # --- Select stocks passing guardrails ---
#                 if not stock_info["risk_flags"]:
#                     selected_stocks.append({"ticker": ticker, **stock_info})
#
#             except Exception as e:
#                 stock_info["risk_flags"].append(f"Data fetch failed: {str(e)}")
#
#             results.append(stock_info)
#
#         # Prepare return dict for UI
#         return {
#             "stock_universe": [s["ticker"] for s in results],
#             "selected_stocks": [s["ticker"] for s in selected_stocks],
#             "details": results
#         }
#
#     def aggregate_for_ui(self, scanned_stocks: List[Dict]) -> Dict:
#         sector_distribution = {}
#         country_distribution = {}
#         bullish_stocks = []
#
#         for stock in scanned_stocks:
#             sector = stock.get("sector", "Unknown")
#             sector_distribution[sector] = sector_distribution.get(sector, 0) + 1
#
#             country = stock.get("country", "Unknown")
#             country_distribution[country] = country_distribution.get(country, 0) + 1
#
#             if stock.get("signals", {}).get("bullish_trend"):
#                 bullish_stocks.append({
#                     "ticker": stock["ticker"],
#                     "price": stock["price"],
#                     "sector": sector,
#                     "country": country,
#                     "volatility": stock.get("volatility"),
#                     "pe_ratio": stock.get("pe_ratio")
#                 })
#
#         aggregated = {
#             "sector_distribution": sector_distribution,
#             "country_distribution": country_distribution,
#             "most_bullish_stocks": bullish_stocks,
#             "scanned_stocks": scanned_stocks
#         }
#
#         return aggregated


import yfinance as yf
import random
import statistics

class MarketScannerAgent:
    """
    Market Scanner Agent:
    - Builds a stock universe (default: S&P 500 tickers via yfinance Tickers API).
    - Analyzes each stock's fundamentals, signals, and risk flags.
    - Produces a ranked list of stocks with composite 'score'.
    """

    def __init__(self):
        self.default_universe = self._load_sp500_tickers()

    # def _load_sp500_tickers(self):
    #     """Load S&P 500 tickers from Wikipedia (via yfinance fallback)."""
    #     # try:
    #     #     import pandas as pd
    #     #     sp500 = pd.read_html(
    #     #         "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    #     #     )[0]
    #     #     return sp500["Symbol"].tolist()
    #     # except Exception:
    #     #     # Fallback small universe if Wikipedia fails
    #     #     return ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "BRK-B", "META"]
    def _load_sp500_tickers(self) -> list:
        """
        Load S&P 500 tickers from Wikipedia.
        If that fails, fallback to yfinance S&P 500 download.
        Ensures a broad universe instead of tech-only default.
        """
        import pandas as pd
        import yfinance as yf

        try:
            sp500 = pd.read_html(
                "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            )[0]
            tickers = sp500["Symbol"].tolist()
            return tickers
        except Exception:
            # Fallback using yfinance (broader S&P 500)
            try:
                sp500_tickers = yf.Tickers("^GSPC").tickers
                if sp500_tickers:
                    return [t.ticker for t in sp500_tickers]
            except Exception:
                pass

        # Ultimate fallback: larger diversified sample
        return [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "BRK-B", "META",
            "JNJ", "V", "PG", "NVDA", "JPM", "UNH", "HD", "DIS", "MA", "PYPL", "KO", "PEP",
            "XOM", "CVX", "CSCO", "ORCL", "MRK", "ABBV", "T", "VZ", "WMT", "MCD"
        ]

    def _analyze_ticker(self, ticker: str):
        """Analyze single ticker and compute score."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            price = info.get("currentPrice") or info.get("previousClose")
            sector = info.get("sector", "Unknown")
            country = info.get("country", "Unknown")
            pe_ratio = info.get("trailingPE")

            # --- Simple signals (placeholder for ML/quant signals)
            momentum = random.choice(["strong_up", "sideways", "weak_down"])
            volume = info.get("volume") or random.randint(1e6, 5e6)
            volatility = random.uniform(1.0, 5.0)

            # --- Risk flags
            risk_flags = []
            if pe_ratio and pe_ratio > 40:
                risk_flags.append("High P/E")
            if volatility > 4:
                risk_flags.append("High volatility")

            # --- Composite scoring (0–100)
            score = 50
            if momentum == "strong_up":
                score += 20
            if pe_ratio and 10 <= pe_ratio <= 25:
                score += 15
            if not risk_flags:
                score += 10
            score -= len(risk_flags) * 5
            score = max(0, min(100, score))

            return {
                "ticker": ticker,
                "price": price,
                "sector": sector,
                "country": country,
                "pe_ratio": pe_ratio,
                "signals": {"momentum": momentum},
                "volatility": round(volatility, 2),
                "latest_volume": volume,
                "risk_flags": risk_flags,
                "score": score,
            }
        except Exception as e:
            return {"ticker": ticker, "error": str(e)}

    def scan_universe(self, tickers=None, limit=50):
        """
        Scan tickers and rank them.
        - If tickers=None, scans default S&P 500 universe.
        - limit: number of stocks to scan (default 50 for speed).
        """
        tickers = tickers or self.default_universe
        tickers = tickers[:limit] if limit else tickers

        results = []
        for t in tickers:
            result = self._analyze_ticker(t)
            if "error" not in result:
                results.append(result)

        # Sort by score
        results_sorted = sorted(results, key=lambda x: x.get("score", 0), reverse=True)
        return results_sorted
