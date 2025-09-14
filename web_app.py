
# web_app.py
import time
import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
from matplotlib_venn import venn2
from pathlib import Path
from dotenv import load_dotenv
import os

from agents.portfolio_orchestrator import PortfolioOrchestrator
from tools.edgar import EdgarTool

# --- Load environment variables ---
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Agentic Stock Picker", layout="wide")
st.title("📈 Agentic Fund Manager")

# --- Run Portfolio Analysis Button ---
st.sidebar.markdown("### Portfolio Picks")
run_button = st.sidebar.button("Run Analysis")

if run_button:
    st.info("Running portfolio analysis...")

    orchestrator = PortfolioOrchestrator()
    results = orchestrator.run([])  # Market scanner determines best tickers

    portfolio_results = results["portfolio_results"]
    market_scan = results.get("aggregated_ui", {})

    # --- Portfolio Table ---
    st.subheader("Portfolio Results")
    table_data = []
    for stock in portfolio_results:
        row = {
            "Ticker": stock["ticker"],
            "Price": stock["data"].get("price"),
            "Optimal Timing": stock["timing"].get("optimal_timing"),
            "Confidence": stock["timing"].get("confidence"),
            "Bullish Trend": stock["signals"].get("bullish_trend"),
            "Risk Flags": ", ".join(stock.get("risk_flags", []))
        }
        table_data.append(row)
    st.dataframe(pd.DataFrame(table_data), height=400)

    # # --- Market Scanner Venn Diagram ---
    # st.subheader("Market Scanner Analysis")
    # universe = set(market_scan.get("stock_universe", []))
    # selected = set(market_scan.get("selected_stocks", []))
    # fig, ax = plt.subplots(figsize=(6, 4))
    # venn2([universe, selected], set_labels=("Universe", "Selected"))
    # st.pyplot(fig)

    # --- Collapsible Price History ---
    st.subheader("Price History (Recommended Stocks)")
    for stock in portfolio_results:
        rec = stock.get("recommendation", {})
        if rec.get("buy_recommendation"):
            with st.expander(f"{stock['ticker']} Price History"):
                price_history = stock["data"].get("price_history", [])
                if price_history:
                    df_prices = pd.DataFrame(price_history)
                    date_col = [c for c in df_prices.columns if "Date" in c][0]
                    close_col = [c for c in df_prices.columns if c.startswith("Close")][0]
                    df_prices[date_col] = pd.to_datetime(df_prices[date_col])
                    fig = px.line(df_prices, x=date_col, y=close_col,
                                  title=f"{stock['ticker']} Price History")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"No price history available for {stock['ticker']}")

    # --- 13F Filings Viewer ---
    st.subheader("13F Filings (Parsed)")
    edgar = EdgarTool(user_agent="MyStockApp/0.1 (email@example.com)")
    for stock in portfolio_results:
        filings_dir = Path("downloads/edgar") / stock["ticker"]
        if filings_dir.exists() and any(filings_dir.iterdir()):
            latest_file = max(filings_dir.iterdir(), key=lambda f: f.stat().st_mtime)
            holdings = edgar.parse_13f_file(latest_file)
            if holdings:
                st.markdown(f"**{stock['ticker']} Holdings:**")
                df = pd.DataFrame(holdings)
                st.dataframe(df, height=400)
            else:
                st.info(f"No holdings found in the 13F filing for {stock['ticker']}")
        else:
            st.info(f"No filings found for {stock['ticker']}")

    # --- Chain of Thought / Data Flow ---
    # st.subheader("🧠 Agent Chain of Thought / Data Flow")
    # for stock in portfolio_results:
    #     with st.expander(f"{stock['ticker']}"):
    #         st.markdown("**Data Agent:**")
    #         data = stock["data"]
    #         st.write({
    #             "Price": data.get("price"),
    #             "Market Cap": data.get("fundamentals", {}).get("market_cap"),
    #             "Sector": data.get("fundamentals", {}).get("sector"),
    #             "Country": data.get("fundamentals", {}).get("country"),
    #             "13F Available": bool(data.get("13f_filings", []))
    #         })
    #
    #         st.markdown("**Signals Agent:**")
    #         signals = stock.get("signals", {})
    #         bullish = signals.get("bullish_trend")
    #         st.markdown(f"**Bullish Trend:** {'✅' if bullish else '❌'}")
    #         st.write({
    #             "Volume Spike": signals.get("volume_spike"),
    #             "PE Signal": signals.get("pe_signal"),
    #             "Short-term Trend": signals.get("short_term_trend")
    #         })
    #
    #         st.markdown("**Timing Agent:**")
    #         timing = stock.get("timing", {})
    #         confidence = timing.get("confidence")
    #         st.markdown(f"**Optimal Timing:** {timing.get('optimal_timing')} (Confidence: {confidence})")
    #
    #         st.markdown("**Recommendation Agent:**")
    #         rec = stock.get("recommendation", {})
    #         st.markdown(f"**Buy Recommendation:** {rec.get('buy_recommendation')}")
    #         st.markdown(f"**Rationale:** {rec.get('rationale')}")
    #
    #         st.markdown("**Risk Flags:**")
    #         flags = stock.get("risk_flags", [])
    #         if flags:
    #             st.markdown(", ".join([f"⚠️ {f}" for f in flags]))
    #         else:
    #             st.markdown("None")

    # --- Portfolio Summary & Allocation ---
    # st.subheader("📊 Portfolio Summary & Capital Allocation ($100 budget)")
    #
    # buy_stocks = [s for s in portfolio_results if s.get("recommendation", {}).get("buy_recommendation")]
    #
    # if buy_stocks:
    #     summary_input = []
    #     for stock in buy_stocks:
    #         summary_input.append({
    #             "ticker": stock["ticker"],
    #             "price": stock["data"].get("price"),
    #             "sector": stock["data"].get("fundamentals", {}).get("sector"),
    #             "market_cap": stock["data"].get("fundamentals", {}).get("market_cap"),
    #             "signals": stock.get("signals", {}),
    #             "rationale": stock.get("recommendation", {}).get("rationale")
    #         })
    #
    #     # Use LLM to get suggested allocation
    #     from agents.recommendation_agent import RecommendationAgent
    #
    #     rec_agent = RecommendationAgent()
    #     summary_text, allocations = rec_agent.summarize_and_allocate(summary_input, total_budget=100)
    #
    #     st.markdown("**Reasoning & Summary:**")
    #     st.markdown(summary_text)
    #
    #     # --- Display allocations ---
    #     st.markdown("**Suggested Allocation:**")
    #     df_alloc = pd.DataFrame(allocations)
    #     st.dataframe(df_alloc)
    #
    #     # --- Pie chart ---
    #     import plotly.express as px
    #
    #     fig = px.pie(df_alloc, names="Ticker", values="Allocation($)", title="Suggested Capital Allocation")
    #     st.plotly_chart(fig, use_container_width=True)
    #
    # else:
    #     st.info("No stocks selected for purchase in this analysis.")

    st.subheader("📊 Portfolio Summary & Capital Allocation ($100 budget)")

    # Filter only buy-recommended stocks
    buy_stocks = [s for s in portfolio_results if s.get("recommendation", {}).get("buy_recommendation")]

    if buy_stocks:
        summary_input = []
        for stock in buy_stocks:
            summary_input.append({
                "ticker": stock["ticker"],
                "price": stock["data"].get("price"),
                "sector": stock["data"].get("fundamentals", {}).get("sector"),
                "market_cap": stock["data"].get("fundamentals", {}).get("market_cap"),
                "signals": stock.get("signals", {}),
                "rationale": stock.get("recommendation", {}).get("rationale")
            })

        from agents.recommendation_agent import RecommendationAgent

        rec_agent = RecommendationAgent()

        # Get summary and allocations (total budget = 100)
        summary_text, allocations = rec_agent.summarize_and_allocate(summary_input, total_budget=100)

        st.markdown("**Reasoning & Summary:**")
        st.markdown(summary_text)

        if allocations:
            # --- Display allocations table ---
            st.markdown("**Suggested Allocation:**")
            df_alloc = pd.DataFrame(allocations)
            st.dataframe(df_alloc)

            # --- Display allocation pie chart ---
            import plotly.express as px

            fig = px.pie(df_alloc, names="Ticker", values="Allocation($)", title="Suggested Capital Allocation")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No allocations returned. Check recommendation agent outputs.")

    else:
        st.info("No stocks selected for purchase in this analysis.")

    # --- Agent Data Flow Animation ---

    st.subheader("🧠 Agent Chain-of-Thought / Data Flow")

    for stock in portfolio_results:
        with st.expander(f"{stock['ticker']} - Agent Data Flow"):
            # --- Data Agent ---
            with st.spinner("DataAgent processing..."):
                data = stock.get("data", {})
                st.markdown("**Data Agent:**")
                st.write({
                    "Price": data.get("price"),
                    "Market Cap": data.get("fundamentals", {}).get("market_cap"),
                    "Sector": data.get("fundamentals", {}).get("sector"),
                    "Country": data.get("fundamentals", {}).get("country"),
                    "13F Available": bool(data.get("13f_filings", []))
                })
                time.sleep(0.5)  # optional visual delay

            # --- Signals Agent ---
            with st.spinner("SignalsAgent evaluating signals..."):
                signals = stock.get("signals", {})
                st.markdown("**Signals Agent:**")
                st.write({
                    "Bullish Trend": "✅" if signals.get("bullish_trend") else "❌",
                    "Volume Spike": signals.get("volume_spike"),
                    "PE Signal": signals.get("pe_signal"),
                    "Short-term Trend": signals.get("short_term_trend")
                })
                time.sleep(0.5)

            # --- Timing Agent ---
            with st.spinner("TimingAgent calculating optimal time..."):
                timing = stock.get("timing", {})
                st.markdown("**Timing Agent:**")
                st.write({
                    "Optimal Timing": timing.get("optimal_timing"),
                    "Confidence": timing.get("confidence")
                })
                time.sleep(0.5)

            # --- Recommendation Agent ---
            with st.spinner("RecommendationAgent generating recommendation..."):
                rec = stock.get("recommendation", {})
                st.markdown("**Recommendation Agent:**")
                st.write({
                    "Buy Recommendation": rec.get("buy_recommendation"),
                    "Suggested Amount ($)": rec.get("suggested_amount"),
                    "Rationale": rec.get("rationale")
                })
                time.sleep(0.5)

            # --- Risk Flags ---
            st.markdown("**Risk Flags:**")
            flags = stock.get("risk_flags", [])
            if flags:
                st.markdown(", ".join([f"⚠️ {f}" for f in flags]))
            else:
                st.markdown("None")





