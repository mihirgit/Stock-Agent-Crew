from agents.data_agent import DataAgent
import json

def test_data_agent():
    data_agent = DataAgent()
    tickers = ["AAPL", "MSFT", "BRK-B"]

    for ticker in tickers:
        print(f"\n--- Fetching data for {ticker} ---")
        data = data_agent.fetch_data(ticker)
        # Pretty-print structured data
        print(json.dumps(data, indent=2, default=str))

if __name__ == "__main__":
    test_data_agent()
