from tools.edgar import EdgarTool

edgar = EdgarTool(user_agent="MyStockApp/0.1 (email@example.com)")
ticker = "BRK-B"

latest_13f = edgar.get_latest_13f(ticker)
if latest_13f:
    txt_path = edgar.download_filing(latest_13f)
    print("Downloaded TXT filing path:", txt_path)
