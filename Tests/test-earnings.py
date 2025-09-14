from tools.earnings import EarningsTool

tool = EarningsTool()
symbol = "AAPL"

print("Next Earnings Date:", tool.get_next_earnings_date(symbol))
history = tool.get_earnings_history(symbol)
print("Earnings History:\n", history.head() if history is not None else "No data")
