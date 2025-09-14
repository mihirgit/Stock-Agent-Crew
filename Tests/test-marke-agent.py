# test_market_scanner.py
from agents.market_scanner_agent import MarketScannerAgent

scanner = MarketScannerAgent()
results = scanner.scan_universe(limit=20)

print("\n=== Top 10 Picks ===")
for stock in results[:10]:
    print(f"{stock['ticker']} | Score: {stock['score']} | "
          f"Price: {stock['price']} | Sector: {stock['sector']} | Flags: {stock['risk_flags']}")
