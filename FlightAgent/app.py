from typing import Dict, List
from pydantic import BaseModel, Field
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from firecrawl import FirecrawlApp
import streamlit as st
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Updated Data Schema for Flight Information
class FlightData(BaseModel):
    """Schema for flight details including price"""
    airline: str = Field(description="Airline Name")
    flight_number: str = Field(description="Flight Number")
    departure_time: str = Field(description="Departure Time")
    arrival_time: str = Field(description="Arrival Time")
    duration: str = Field(description="Total Duration of the flight")
    stops: int = Field(description="Number of stops (0 = direct flight)")
    price: str = Field(description="Ticket price in the local currency")

class FlightsResponse(BaseModel):
    """Schema for multiple flights response"""
    flights: List[FlightData] = Field(description="List of available flights")

class FlightBookingAgent:
    """Agent responsible for finding and recommending flights"""
    
    SKYSCANNER_URL_TEMPLATE = "https://www.skyscanner.co.in/transport/flights/{origin}/{destination}/{date}/?adultsv2={adults}&cabinclass={cabin_class}"

    def __init__(self, firecrawl_api_key: str, openai_api_key: str, model_id: str = "gpt-3.5-turbo"):
        self.agent = Agent(
            model=OpenAIChat(id=model_id, api_key=openai_api_key),
            markdown=True,
            description="I am a flight booking expert helping users find and analyze flights."
        )
        self.firecrawl = FirecrawlApp(api_key=firecrawl_api_key)

    def _format_date(self, date_str: str) -> str:
        """Converts date from YYYY-MM-DD to Skyscanner format DDMMYY"""
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d%m%y")

    def _fetch_flight_data(self, url: str, prompt: str, schema: Dict) -> Dict:
        """Helper method to fetch flight details from Firecrawl API"""
        try:
            response = self.firecrawl.extract(urls=[url], params={'prompt': prompt, 'schema': schema})
            if response.get('success'):
                return response.get('data', {})
            logger.error(f"Firecrawl API failed: {response}")
        except Exception as e:
            logger.exception(f"Error fetching flight data: {e}")
        return {}

    def search_flights(self, origin: str, destination: str, departure_date: str, adults: int, cabin_class: str) -> str:
        """Finds and analyzes available flights"""
        formatted_date = self._format_date(departure_date)

        flight_url = self.SKYSCANNER_URL_TEMPLATE.format(
            origin=origin.lower(),
            destination=destination.lower(),
            date=formatted_date,
            adults=adults,
            cabin_class=cabin_class.lower()
        )

        prompt = f"""
        Extract flight details from {origin} to {destination} on {departure_date}.

        **Requirements:**
        - Only flights on {departure_date}
        - Include airline name, flight number, departure/arrival times, duration, stops, and ticket price.
        """

        data = self._fetch_flight_data(flight_url, prompt, FlightsResponse.model_json_schema())
        flights = data.get('flights', [])

        if not flights:
            return f"No flights found. [Check Skyscanner]({flight_url})"

        analysis = self.agent.run(f"""
        ✈️ **Best Flights from {origin.upper()} to {destination.upper()}**
        {flights}

        💰 **Price Comparison**
        - Compare flights based on ticket price, travel time, and layovers.

        🔥 **Best Value Picks**
        - Highlight 3 best flights based on cost, convenience, and airline service.

        🎯 **Booking Recommendations**
        - When to book for the best price?
        - Which airline offers the best experience?

        **🔗 Check all flights here:** [Skyscanner Link]({flight_url})
        """)

        return analysis.content

def create_flight_agent():
    """Creates and initializes the FlightBookingAgent with API keys from session state"""
    if 'flight_agent' not in st.session_state:
        st.session_state.flight_agent = FlightBookingAgent(
            firecrawl_api_key=st.session_state.get("firecrawl_key", ""),
            openai_api_key=st.session_state.get("openai_key", ""),
            model_id=st.session_state.get("model_id", "gpt-3.5-turbo")
        )

def main():
    st.set_page_config(page_title="✈️ AI Flight Booking Agent", page_icon="✈️", layout="wide")

    with st.sidebar:
        st.title("🔑 API Configuration")
        
        st.subheader("🤖 Model Selection")
        model_id = st.selectbox("Choose OpenAI Model", options=["o3-mini", "gpt-4o", "gpt-3.5-turbo"])
        st.session_state.model_id = model_id
        
        st.subheader("🔐 API Keys")
        firecrawl_key = st.text_input("Firecrawl API Key", type="password")
        openai_key = st.text_input("OpenAI API Key", type="password")
        
        if firecrawl_key and openai_key:
            st.session_state.firecrawl_key = firecrawl_key
            st.session_state.openai_key = openai_key
            create_flight_agent()

    st.title("✈️ AI Flight Booking Agent")
    st.info("Find the best flights based on travel time, airline, and price.")

    col1, col2 = st.columns(2)
    
    with col1:
        origin = st.text_input("Origin (IATA Code)", value="LKO", help="Enter IATA code of departure airport")
        destination = st.text_input("Destination (IATA Code)", value="DEL", help="Enter IATA code of arrival airport")

    with col2:
        departure_date = st.date_input("Depart", value=datetime(2025, 3, 25))

    col3, col4 = st.columns(2)
    
    with col3:
        adults = st.number_input("Adults", min_value=1, max_value=10, value=1, step=1)
    
    with col4:
        cabin_class = st.selectbox("Cabin Class", ["economy", "premium_economy", "business", "first"])

    if st.button("🔍 Search Flights", use_container_width=True):
        if 'flight_agent' not in st.session_state:
            st.error("⚠️ Please enter your API keys in the sidebar first!")
            return
            
        if not origin or not destination:
            st.error("⚠️ Please enter both origin and destination (IATA codes)!")
            return
            
        try:
            with st.spinner("🔍 Searching for flights..."):
                flight_results = st.session_state.flight_agent.search_flights(
                    origin=origin,
                    destination=destination,
                    departure_date=str(departure_date),
                    adults=adults,
                    cabin_class=cabin_class
                )
                
                st.success("✅ Flight search completed!")
                st.subheader("✈️ Flight Recommendations")
                st.markdown(flight_results)
                
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")

if __name__ == "__main__":
    main()
