import datetime

class SignalAgent:
    """
    Generates stock signals (bullish trend, PE ratio, short-term trend, volume spike)
    based on price history and fundamentals.
    Web UI-ready output with robust handling of missing data.
    """

    def __init__(self):
        pass

    def generate_signals(self, data_agent_output: dict) -> dict:
        ticker = data_agent_output.get("ticker")
        data_snapshot = data_agent_output.get("data", {})

        signals_output = {
            "ticker": ticker,
            "generated_time": datetime.datetime.utcnow().isoformat(),
            "signals": {},
            "data_snapshot": data_snapshot
        }

        try:
            price_history = data_snapshot.get("price_history", [])
            price = data_snapshot.get("price")

            if not price_history:
                signals_output["signals"]["bullish_trend"] = None
                signals_output["signals"]["error"] = "No price history available."
                return signals_output

            # --- Extract ticker-suffixed keys ---
            close_key = f"Close_{ticker}"
            open_key = f"Open_{ticker}"
            high_key = f"High_{ticker}"
            low_key = f"Low_{ticker}"
            volume_key = f"Volume_{ticker}"

            closes = [float(p.get(close_key)) for p in price_history if p.get(close_key) is not None]
            opens = [float(p.get(open_key)) for p in price_history if p.get(open_key) is not None]
            highs = [float(p.get(high_key)) for p in price_history if p.get(high_key) is not None]
            lows = [float(p.get(low_key)) for p in price_history if p.get(low_key) is not None]
            volumes = [float(p.get(volume_key)) for p in price_history if p.get(volume_key) is not None]

            if not closes:
                signals_output["signals"]["bullish_trend"] = None
                signals_output["signals"]["error"] = f"No valid {close_key} in price history."
                return signals_output

            # Fallback price
            if price is None:
                price = closes[-1]

            # --- Bullish trend (price vs 50-day MA) ---
            avg_50 = sum(closes[-50:]) / min(len(closes), 50)
            signals_output["signals"]["bullish_trend"] = price > avg_50

            # --- Short-term trend (10-day vs 50-day MA) ---
            avg_10 = sum(closes[-10:]) / min(len(closes), 10)
            if avg_10 > avg_50:
                signals_output["signals"]["short_term_trend"] = "upward"
            elif avg_10 < avg_50:
                signals_output["signals"]["short_term_trend"] = "downward"
            else:
                signals_output["signals"]["short_term_trend"] = "neutral"

            # --- Volume spike detection (latest vs average of last 20 days) ---
            if volumes and len(volumes) >= 20:
                avg_vol = sum(volumes[-20:]) / 20
                signals_output["signals"]["volume_spike"] = volumes[-1] > 1.5 * avg_vol
            else:
                signals_output["signals"]["volume_spike"] = False

            # --- PE ratio signal ---
            fundamentals = data_snapshot.get("fundamentals", {})
            pe_ratio = fundamentals.get("pe_ratio")
            if pe_ratio is not None:
                signals_output["signals"]["pe_signal"] = pe_ratio < 30  # example threshold

        except Exception as e:
            signals_output["signals"]["error"] = f"Signal generation failed: {str(e)}"
            signals_output["signals"]["bullish_trend"] = None

        return signals_output
