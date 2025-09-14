from agents.portfolio_orchestrator import PortfolioOrchestrator
import json

orchestrator = PortfolioOrchestrator()
tickers = ["AAPL", "MSFT", "BRK-B", "TSLA", "GOOGL"]

results = orchestrator.run(tickers)
print(json.dumps(results, indent=2, default=str))
