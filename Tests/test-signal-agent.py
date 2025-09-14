from agents.data_agent import DataAgent
from agents.signal_agent import SignalAgent
import json

def test_signal_agent():
    ticker = "AAPL"
    data_agent = DataAgent()
    signal_agent = SignalAgent()

    # Fetch structured data for one stock
    data_output = data_agent.fetch_data(ticker)
    print(f"\nDataAgent output for {ticker}:")
    # print(json.dumps(data_output, indent=2, default=str))

    # Generate signals
    signals = signal_agent.generate_signals(data_output)
    print(f"\nSignalAgent output for {ticker}:")
    print(json.dumps(signals, indent=2, default=str))

if __name__ == "__main__":
    test_signal_agent()
