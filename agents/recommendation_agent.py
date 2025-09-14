import openai
from openai import OpenAI
from typing import Optional, Dict, List
import json, os
from json.decoder import JSONDecodeError
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class RecommendationAgent:
    """
    Generates buy recommendations based on structured data from DataAgent.
    Fully web UI-ready and robust to LLM errors.
    """

    def __init__(self, model="gpt-4o-mini", budget=100):
        self.model = model
        self.budget = budget
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    @staticmethod
    def safe_parse_json(llm_output: str):
        """
        Safely parse JSON returned by LLM. If parsing fails, try to extract
        content between first and last braces, else return None.
        """
        try:
            return json.loads(llm_output)
        except JSONDecodeError:
            start = llm_output.find("{")
            end = llm_output.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(llm_output[start:end + 1])
                except JSONDecodeError:
                    pass
            return None

    def generate_recommendation(
        self,
        data_agent_output: dict,
        signals: Optional[dict] = None,
        timing: Optional[dict] = None
    ) -> dict:
        """
        Single-stock recommendation
        """
        ticker = data_agent_output.get("ticker")
        data_snapshot = data_agent_output.get("data", {})

        prompt = f"""
        You are a highly analytical stock portfolio assistant.
        Give **long-term buy recommendations only** for a user
        who wants to invest up to ${self.budget} in total.

        Consider this structured data for {ticker}:
        {json.dumps(data_snapshot, default=str)}

        Also consider signals and timing factors if provided.
        Respond **ONLY in JSON format** with fields:
        - buy_recommendation: true or false
        - suggested_amount: numeric allocation
        - rationale: short paragraph explaining reasoning
        - optimal_timing: string if relevant, else null
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful and accurate financial assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )

            llm_output = response.choices[0].message.content.strip()
            recommendation = self.safe_parse_json(llm_output)

            if recommendation is None:
                raise ValueError("LLM returned invalid JSON")

            # Attach metadata
            recommendation["ticker"] = ticker
            recommendation["data_snapshot"] = data_snapshot
            recommendation["signals"] = signals or {}
            recommendation["timing_factors"] = timing or {}
            recommendation["llm_raw_response"] = llm_output

        except Exception as e:
            recommendation = {
                "ticker": ticker,
                "buy_recommendation": False,
                "suggested_amount": 0.0,
                "rationale": f"Fallback: LLM returned invalid JSON or error: {str(e)}",
                "optimal_timing": None,
                "data_snapshot": data_snapshot,
                "signals": signals or {},
                "timing_factors": timing or {},
                "llm_raw_response": llm_output if 'llm_output' in locals() else ""
            }

        return recommendation

    def generate_portfolio_recommendations(self, stocks_data: List[dict]) -> List[dict]:
        """
        Multi-stock recommendation with sector diversification.
        Normalizes suggested amounts to match self.budget.
        """
        recommendations = []

        # Step 1: Generate individual recommendations
        for stock_data in stocks_data:
            rec = self.generate_recommendation(
                stock_data,
                signals=stock_data.get("signals"),
                timing=stock_data.get("timing")
            )
            recommendations.append(rec)

        # Step 2: Normalize suggested_amount to budget
        buy_recs = [r for r in recommendations if r.get("buy_recommendation")]
        total_alloc = sum(r.get("suggested_amount", 0.0) for r in buy_recs)

        if total_alloc > 0:
            scale = self.budget / total_alloc
            for r in buy_recs:
                r["suggested_amount"] = round(r.get("suggested_amount", 0.0) * scale, 2)
        else:
            # Fallback: equal allocation
            n = len(buy_recs)
            if n > 0:
                equal_alloc = round(self.budget / n, 2)
                for r in buy_recs:
                    r["suggested_amount"] = equal_alloc

        # Step 3: Optional sector diversification enforcement
        sector_alloc = {}
        for r in buy_recs:
            sector = r["data_snapshot"].get("fundamentals", {}).get("sector", "Other")
            sector_alloc.setdefault(sector, 0.0)
            sector_alloc[sector] += r["suggested_amount"]

        # Scale down any sector >50% of budget
        for r in buy_recs:
            sector = r["data_snapshot"].get("fundamentals", {}).get("sector", "Other")
            if sector_alloc[sector] > self.budget * 0.5:
                over = sector_alloc[sector] - self.budget * 0.5
                peers = [x for x in buy_recs if x["data_snapshot"].get("fundamentals", {}).get("sector") == sector]
                for peer in peers:
                    peer["suggested_amount"] -= round(over / len(peers), 2)

        return recommendations

    def summarize_and_allocate(self, buy_stocks: list, total_budget: float = 100):
        """
        Summarize buy recommendations and suggest capital allocation for total budget.
        Ensures total allocations sum to total_budget, with optional sector diversification.

        Args:
            buy_stocks (list): List of buy-recommended stock dicts (from generate_recommendation).
            total_budget (float): Total capital to allocate across stocks.

        Returns:
            summary_text (str): Human-readable reasoning summary.
            allocations (list[dict]): Each dict: {'Ticker', 'Weight (%)', 'Allocation($)'}
        """
        if not buy_stocks:
            return "No buy-recommended stocks available.", []

        # Step 1: Use LLM to summarize reasoning and suggested weights (as percentages)
        from openai import OpenAI
        import json, os

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        prompt = f"""
        You are a financial AI assistant.
        Given the following buy-recommended stocks, provide:
        1. A concise reasoning summary for the selections.
        2. Suggested allocation percentages for each stock (sum to 100%).

        Ensure sector diversification. Avoid allocating more than 40% to any single sector.

        Stock data:
        {buy_stocks}

        Output format: JSON with 'summary' (text) and 'allocations' (list of {{ticker, weight_percent}}).
        """

        try:
            resp = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=400
            )

            content = resp.choices[0].message.content.strip()

            # Safe parsing of JSON
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # Attempt to extract JSON between first and last braces
                start = content.find("{")
                end = content.rfind("}")
                if start != -1 and end != -1:
                    result = json.loads(content[start:end + 1])
                else:
                    raise ValueError("LLM returned invalid JSON")

            summary_text = result.get("summary", "")
            allocations_raw = result.get("allocations", [])

            # Step 2: Convert percentages to actual $ allocations
            allocations = []
            for a in allocations_raw:
                ticker = a.get("ticker")
                weight = a.get("weight_percent", 0)
                alloc_amount = round(total_budget * weight / 100, 2)
                allocations.append({
                    "Ticker": ticker,
                    "Weight (%)": weight,
                    "Allocation($)": alloc_amount
                })

            # Step 3: Ensure sum matches total_budget (adjust last stock if rounding caused drift)
            total_alloc = sum(a["Allocation($)"] for a in allocations)
            drift = round(total_budget - total_alloc, 2)
            if allocations and drift != 0:
                allocations[-1]["Allocation($)"] += drift

        except Exception as e:
            # Fallback if LLM fails
            summary_text = f"Fallback: LLM error or invalid output: {str(e)}"
            equal_alloc = round(total_budget / len(buy_stocks), 2) if buy_stocks else 0
            allocations = [{"Ticker": s["ticker"], "Weight (%)": round(100 / len(buy_stocks), 2),
                            "Allocation($)": equal_alloc} for s in buy_stocks]

        return summary_text, allocations

    # def summarize_and_allocate(self, buy_stocks: list, total_budget: float = 100):
    #     """
    #     Summarize buy recommendations and suggest capital allocation.
    #     Returns:
    #         summary_text (str)
    #         allocations (list of dicts with Ticker, Weight (%), Allocation($))
    #     """
    #     prompt = f"""
    #     You are a financial AI assistant.
    #     Given the following buy-recommended stocks, provide:
    #     1. A concise reasoning summary for the selections.
    #     2. Suggested allocation percentages for each stock (sum to 100%).
    #
    #     Ensure sector diversification: no more than 40% in any single sector.
    #
    #     Stock data:
    #     {buy_stocks}
    #
    #     Respond ONLY in JSON with:
    #     {{
    #         "summary": "text summary",
    #         "allocations": [
    #             {{"ticker": "AAPL", "weight_percent": 25}},
    #             ...
    #         ]
    #     }}
    #     """
    #
    #     try:
    #         resp = self.client.chat.completions.create(
    #             model="gpt-4",
    #             messages=[{"role": "user", "content": prompt}],
    #             max_tokens=400
    #         )
    #
    #         content = resp.choices[0].message.content.strip()
    #         result = self.safe_parse_json(content)
    #
    #         # Fallback: equal allocation if LLM fails
    #         if result is None or not result.get("allocations"):
    #             n = len(buy_stocks)
    #             allocations_raw = [{"ticker": s["ticker"], "weight_percent": round(100/n, 2)} for s in buy_stocks]
    #             summary_text = "LLM failed or returned invalid JSON; allocating equally across selected stocks."
    #         else:
    #             allocations_raw = result.get("allocations", [])
    #             summary_text = result.get("summary", "")
    #
    #         allocations = []
    #         for a in allocations_raw:
    #             ticker = a["ticker"]
    #             weight = a["weight_percent"]
    #             alloc_amount = round(total_budget * weight / 100, 2)
    #             allocations.append({"Ticker": ticker, "Weight (%)": weight, "Allocation($)": alloc_amount})
    #
    #     except Exception as e:
    #         summary_text = f"Error generating summary/allocations: {str(e)}"
    #         allocations = [{"Ticker": s["ticker"], "Weight (%)": 0, "Allocation($)": 0} for s in buy_stocks]
    #
    #     return summary_text, allocations
