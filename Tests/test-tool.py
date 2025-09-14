# from tools.yahoo_finance import YahooFinanceTool
#
# yahoo = YahooFinanceTool()
#
# # Get price history
# df = yahoo.get_price_history("AAPL", period="3mo", interval="1d")
# print(df.tail())
#
# # Get fundamentals
# funds = yahoo.get_fundamentals("AAPL")
# print(funds)
#
# # Get analyst recommendations
# recs = yahoo.get_recommendations("AAPL")
# print(recs)

from tools.finnhub import FinnhubTool

finnhub_tool = FinnhubTool()

print("Quote:", finnhub_tool.get_quote("AAPL"))
print("Profile:", finnhub_tool.get_company_profile("AAPL"))

# News works only for last 30 days
news_df = finnhub_tool.get_news("AAPL", num_articles=3)
print(news_df)

# Sentiment is premium only, so returns a stub
print(finnhub_tool.get_sentiment("AAPL"))

