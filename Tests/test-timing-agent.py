from agents.data_agent import DataAgent
from agents.signal_agent import SignalAgent
from agents.timing_agent import TimingAgent
import json

data_agent = DataAgent()
signal_agent = SignalAgent()
timing_agent = TimingAgent()

data_output = data_agent.fetch_data("AAPL")
signals = signal_agent.generate_signals(data_output)
timing = timing_agent.generate_timing(data_output, signals)

print(json.dumps(timing, indent=2, default=str))
