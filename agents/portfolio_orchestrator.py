# from typing import List, Dict
# from agents.market_scanner_agent import MarketScannerAgent
# from agents.data_agent import DataAgent
# from agents.signal_agent import SignalAgent
# from agents.timing_agent import TimingAgent
# from agents.recommendation_agent import RecommendationAgent
#
# class PortfolioOrchestrator:
#     """
#     Orchestrates the stock portfolio workflow:
#     Market scanning → Data collection → Signal generation → Timing → Recommendation
#     """
#
#     def __init__(self):
#         self.scanner = MarketScannerAgent()
#         self.data_agent = DataAgent()
#         self.signal_agent = SignalAgent()
#         self.timing_agent = TimingAgent()
#         self.recommendation_agent = RecommendationAgent()
#
#     def run(self, tickers: List[str]) -> Dict:
#         """
#         Runs the full workflow for a list of tickers.
#         Returns a web UI-ready aggregated report.
#         """
#         # --- Step 1: Scan universe ---
#         scanned_stocks = self.scanner.scan_universe(tickers)
#
#         # --- Step 2: Process each stock for signals, timing, recommendations ---
#         portfolio_results = []
#
#         for stock in scanned_stocks:
#             ticker = stock["ticker"]
#             data_output = self.data_agent.fetch_data(ticker)
#             signals = self.signal_agent.generate_signals(data_output)
#             timing = self.timing_agent.generate_timing(data_output, signals)
#             recommendation = self.recommendation_agent.generate_recommendation(
#                 data_output, signals, timing
#             )
#
#             portfolio_results.append({
#                 "ticker": ticker,
#                 "data": data_output["data"],
#                 "signals": signals.get("signals", {}),
#                 "timing": timing,
#                 "recommendation": recommendation,
#                 "risk_flags": stock.get("risk_flags", []),
#             })
#
#         # --- Step 3: Aggregate for UI ---
#         aggregated_ui = self.scanner.aggregate_for_ui(scanned_stocks)
#
#         orchestrator_output = {
#             "portfolio_results": portfolio_results,
#             "aggregated_ui": aggregated_ui
#         }
#
#         return orchestrator_output


from typing import Dict
from agents.market_scanner_agent import MarketScannerAgent
from agents.data_agent import DataAgent
from agents.signal_agent import SignalAgent
from agents.timing_agent import TimingAgent
from agents.recommendation_agent import RecommendationAgent
from tools.edgar import EdgarTool


class PortfolioOrchestrator:
    """
    Orchestrates the stock portfolio workflow:
    Market scanning → Data collection → Signal generation → Timing → Recommendation → Filings
    """

    def __init__(self):
        self.scanner = MarketScannerAgent()
        self.data_agent = DataAgent()
        self.signal_agent = SignalAgent()
        self.timing_agent = TimingAgent()
        self.recommendation_agent = RecommendationAgent()
        self.edgar = EdgarTool(user_agent="MyStockApp/0.1 (email@example.com)")

    def run(self, limit: int = 20) -> Dict:
        """
        Runs the full workflow for top-ranked stocks from the market scanner.
        Returns a web UI-ready aggregated report.
        """
        # --- Step 1: Scan & rank ---
        scanned_stocks = self.scanner.scan_universe(limit=limit)

        portfolio_results = []
        for stock in scanned_stocks:
            ticker = stock["ticker"]

            # --- Step 2: Data ---
            data_output = self.data_agent.fetch_data(ticker)

            # --- Step 3: Signals ---
            signals = self.signal_agent.generate_signals(data_output)

            # --- Step 4: Timing ---
            timing = self.timing_agent.generate_timing(data_output, signals)

            # --- Step 5: Recommendation ---
            recommendation = self.recommendation_agent.generate_recommendation(
                data_output,
                signals, timing,

            )

            # --- Step 6: 13F Filings ---
            try:
                latest_13f = self.edgar.get_latest_13f(ticker)
                holdings = []
                if latest_13f:
                    holdings = self.edgar.parse_13f_file(latest_13f)
            except Exception:
                holdings = []

            portfolio_results.append({
                "ticker": ticker,
                "data": data_output["data"],
                "signals": signals.get("signals", {}),
                "timing": timing,
                "recommendation": recommendation,
                "risk_flags": stock.get("risk_flags", []),
                "score": stock.get("score"),
                "13f_holdings": holdings,
            })

        orchestrator_output = {
            "portfolio_results": portfolio_results,
            "aggregated_ui": {
                "stock_universe": [s["ticker"] for s in scanned_stocks],
                "selected_stocks": [s["ticker"] for s in portfolio_results],
            },
        }

        return orchestrator_output

