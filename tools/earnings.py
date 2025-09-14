# tools/earnings_tool.py
import yfinance as yf
import pandas as pd
from typing import Optional

class EarningsTool:
    """
    Fetch earnings history and upcoming earnings dates for a stock.
    Uses yfinance for free access.
    """

    def __init__(self):
        pass

    def get_earnings_history(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Returns historical earnings (quarterly or annual)
        Columns: 'Revenue', 'Earnings', 'EPS', 'Date'
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = getattr(ticker, 'earnings_history', None)
            if hist is None:
                return None
            df = pd.DataFrame(hist)
            return df
        except Exception as e:
            print(f"[EarningsTool] Failed to fetch earnings for {symbol}: {e}")
            return None

    def get_next_earnings_date(self, symbol: str) -> Optional[str]:
        try:
            ticker = yf.Ticker(symbol)
            cal = ticker.calendar

            # calendar may be dict, DataFrame, or already datetime/date
            date = None
            if isinstance(cal, dict):
                val = cal.get("Earnings Date")
                if isinstance(val, (list, tuple)):
                    date = val[0]
                else:
                    date = val
            elif isinstance(cal, pd.DataFrame):
                if 'Earnings Date' in cal.index:
                    date = cal.loc['Earnings Date'][0]
            # finally, just return str()
            return str(date) if date is not None else None
        except Exception:
            return None

