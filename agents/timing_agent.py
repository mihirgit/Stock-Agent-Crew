import datetime

class TimingAgent:
    """
    Estimates the optimal timing to buy a stock using historical price trends
    and enhanced signals. Returns web UI-ready output including confidence score.
    """

    def __init__(self):
        pass

    def generate_timing(self, data_agent_output: dict, signals: dict = None) -> dict:
        ticker = data_agent_output.get("ticker")
        data_snapshot = data_agent_output.get("data", {})
        signals = signals or {}

        timing_output = {
            "ticker": ticker,
            "generated_time": datetime.datetime.utcnow().isoformat(),
            "optimal_timing": None,
            "confidence": 0.0,  # new field
            "reasoning": "",
            "data_snapshot": data_snapshot,
            "signals": signals.get("signals", {})
        }

        try:
            price_history = data_snapshot.get("price_history", [])
            if not price_history:
                timing_output["reasoning"] = "No price history available for timing analysis."
                return timing_output

            close_key = f"Close_{ticker}"
            closes = [p.get(close_key) for p in price_history if p.get(close_key) is not None]

            if not closes:
                timing_output["reasoning"] = f"No valid {close_key} in price history."
                return timing_output

            latest_price = closes[-1]
            avg_10 = sum(closes[-10:]) / min(len(closes), 10)
            avg_50 = sum(closes[-50:]) / min(len(closes), 50)

            reasoning_parts = []
            confidence = 0.0

            # --- Use signals if available ---
            bullish = signals.get("signals", {}).get("bullish_trend")
            short_term = signals.get("signals", {}).get("short_term_trend")
            volume_spike = signals.get("signals", {}).get("volume_spike")
            pe_signal = signals.get("signals", {}).get("pe_signal")

            # Bullish trend
            if bullish:
                confidence += 0.4
                reasoning_parts.append("Bullish trend confirmed.")
            else:
                reasoning_parts.append("Not bullish.")

            # Short-term trend
            if short_term == "upward":
                confidence += 0.2
                reasoning_parts.append("Short-term trend upward.")
            elif short_term == "neutral":
                confidence += 0.1
                reasoning_parts.append("Short-term trend neutral.")
            else:
                reasoning_parts.append("Short-term trend downward.")

            # Volume spike
            if volume_spike is False:
                confidence += 0.2
                reasoning_parts.append("No volume spike detected.")
            else:
                reasoning_parts.append("Volume spike detected; caution.")

            # PE ratio signal
            if pe_signal:
                confidence += 0.2
                reasoning_parts.append("PE ratio favorable.")
            elif pe_signal is False:
                reasoning_parts.append("PE ratio unfavorable.")

            # Decision logic based on confidence
            if confidence >= 0.7:
                timing_output["optimal_timing"] = "Buy now"
            elif confidence >= 0.4:
                timing_output["optimal_timing"] = "Consider buying soon"
            else:
                timing_output["optimal_timing"] = "Wait"

            timing_output["confidence"] = round(confidence, 2)
            timing_output["reasoning"] = " ".join(reasoning_parts)

        except Exception as e:
            timing_output["reasoning"] = f"Timing analysis failed: {str(e)}"
            timing_output["optimal_timing"] = None
            timing_output["confidence"] = 0.0

        return timing_output
