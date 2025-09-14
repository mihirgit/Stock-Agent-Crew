import yfinance as yf

class YahooFinanceTool:
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

if __name__ == "__main__":
    print(YahooFinanceTool().get_summary(ticker="AAPL"))
