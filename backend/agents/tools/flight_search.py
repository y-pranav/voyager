from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import random
from datetime import datetime, timedelta

class FlightSearchInput(BaseModel):
    """Input for flight search tool"""
    origin: str = Field(description="Origin city or airport code")
    destination: str = Field(description="Destination city or airport code")
    departure_date: str = Field(description="Departure date in YYYY-MM-DD format")
    return_date: Optional[str] = Field(None, description="Return date for round trip")
    passengers: int = Field(1, description="Number of passengers")
    budget_max: Optional[float] = Field(None, description="Maximum budget in INR")

class FlightSearchTool:
    """Tool for searching flight options"""
    
    def __init__(self):
        self.name = "flight_search"
        self.description = """Search for flight options between cities. 
        Use this tool to find flights that match the user's budget and travel dates.
        Returns flight details including airlines, prices, and schedules."""
    
    def _run(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        passengers: int = 1,
        budget_max: Optional[float] = None,
        **kwargs: Any,
    ) -> str:
        """Execute the flight search"""
        
        # Mock flight data - replace with real API calls
        airlines = ["Air India", "IndiGo", "SpiceJet", "Vistara", "GoAir"]
        
        # Generate mock flight options
        flights = []
        for i in range(3):  # Return 3 options
            airline = random.choice(airlines)
            base_price = random.randint(8000, 25000) * passengers
            
            # Apply budget filter if provided
            if budget_max and base_price > budget_max * 0.4:  # Assume flights take 40% of budget
                base_price = int(budget_max * 0.35)  # Adjust to fit budget
            
            departure_time = f"{random.randint(6, 22):02d}:{random.choice(['00', '30'])}"
            duration = f"{random.randint(1, 8)}h {random.randint(0, 59):02d}m"
            
            flight = {
                "airline": airline,
                "flight_number": f"{airline[:2].upper()}{random.randint(100, 999)}",
                "departure_time": departure_time,
                "arrival_time": f"{(int(departure_time[:2]) + random.randint(2, 6)) % 24:02d}:{departure_time[3:]}",
                "duration": duration,
                "price": base_price,
                "currency": "INR",
                "stops": random.choice([0, 1]),
                "availability": "Available"
            }
            flights.append(flight)
        
        # Sort by price
        flights.sort(key=lambda x: x["price"])
        
        # Create return flights if round trip
        return_flights = []
        if return_date:
            for flight in flights:
                return_flight = flight.copy()
                return_flight["departure_time"] = f"{random.randint(6, 22):02d}:{random.choice(['00', '30'])}"
                return_flight["price"] = flight["price"] // 2  # Return flight cost
                return_flights.append(return_flight)
        
        result = {
            "search_query": {
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date,
                "return_date": return_date,
                "passengers": passengers
            },
            "outbound_flights": flights,
            "return_flights": return_flights,
            "total_cost_range": {
                "min": min(f["price"] for f in flights) + (min(rf["price"] for rf in return_flights) if return_flights else 0),
                "max": max(f["price"] for f in flights) + (max(rf["price"] for rf in return_flights) if return_flights else 0)
            },
            "recommendations": [
                f"Book {flights[0]['airline']} for best price",
                "Consider flexible dates for better rates",
                "Early morning flights are usually cheaper"
            ]
        }
        
        return f"""Flight Search Results for {origin} to {destination}:

OUTBOUND FLIGHTS ({departure_date}):
{self._format_flights(flights)}

{f"RETURN FLIGHTS ({return_date}):" if return_flights else ""}
{self._format_flights(return_flights) if return_flights else ""}

TOTAL COST RANGE: ₹{result['total_cost_range']['min']:,} - ₹{result['total_cost_range']['max']:,}

RECOMMENDATIONS:
{chr(10).join(f"• {rec}" for rec in result['recommendations'])}

BEST OPTION: {flights[0]['airline']} {flights[0]['flight_number']} - ₹{flights[0]['price']:,}
"""

    def _format_flights(self, flights: List[Dict[str, Any]]) -> str:
        """Format flight list for display"""
        if not flights:
            return ""
        
        formatted = []
        for flight in flights:
            stops_text = "Direct" if flight["stops"] == 0 else f"{flight['stops']} stop"
            formatted.append(
                f"• {flight['airline']} {flight['flight_number']}: "
                f"{flight['departure_time']} - {flight['arrival_time']} "
                f"({flight['duration']}, {stops_text}) - ₹{flight['price']:,}"            )
        return "\n".join(formatted)
