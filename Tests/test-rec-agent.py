from agents.data_agent import DataAgent
from agents.recommendation_agent import RecommendationAgent
import json
import os
from dotenv import load_dotenv

# Load API keys from .env
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError("OPENAI_API_KEY not found in .env file")
os.environ["OPENAI_API_KEY"] = openai_api_key

def test_recommendation_agent():
    ticker = "AAPL"
    data_agent = DataAgent()
    rec_agent = RecommendationAgent(model="gpt-4o-mini", budget=100)

    # Fetch structured data for one stock
    data_output = data_agent.fetch_data(ticker)
    print(f"\nDataAgent output for {ticker}:")
    print(json.dumps(data_output, indent=2, default=str))

    # Generate recommendation
    recommendation = rec_agent.generate_recommendation(data_output)
    print(f"\nRecommendationAgent output for {ticker}:")
    print(json.dumps(recommendation, indent=2, default=str))

if __name__ == "__main__":
    test_recommendation_agent()
