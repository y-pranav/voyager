from langchain.tools import BaseTool
from typing import Optional, Type, Dict, Any, List
from pydantic import BaseModel, Field
import random

class HotelSearchInput(BaseModel):
    """Input for hotel search tool"""
    location: str = Field(description="City or area to search for hotels")
    check_in_date: str = Field(description="Check-in date in YYYY-MM-DD format")
    check_out_date: str = Field(description="Check-out date in YYYY-MM-DD format")
    guests: int = Field(1, description="Number of guests")
    budget_per_night: Optional[float] = Field(None, description="Maximum budget per night in INR")
    hotel_type: str = Field("hotel", description="Type of accommodation (hotel, hostel, resort, etc.)")

class HotelSearchTool(BaseTool):
    """Tool for searching hotel accommodations"""
    
    name = "hotel_search"
    description = """Search for hotel accommodations in a specific location.
    Use this tool to find hotels that match budget and preference requirements.
    Returns hotel details including amenities, prices, and ratings."""
    args_schema: Type[BaseModel] = HotelSearchInput
    
    def _run(
        self,
        location: str,
        check_in_date: str,
        check_out_date: str,
        guests: int = 1,
        budget_per_night: Optional[float] = None,
        hotel_type: str = "hotel",
        **kwargs: Any,
    ) -> str:
        """Execute the hotel search"""
        
        # Mock hotel data - replace with real API calls
        hotel_names = [
            "Grand Palace Hotel", "City View Inn", "Comfort Stay", 
            "Luxury Resort & Spa", "Budget Traveler Lodge", "Heritage Hotel",
            "Modern Suites", "Boutique Hotel", "Business Center Hotel"
        ]
        
        amenities_options = [
            ["WiFi", "Pool", "Gym", "Spa", "Restaurant"],
            ["WiFi", "Breakfast", "Parking", "Room Service"],
            ["WiFi", "Pool", "Restaurant", "Concierge"],
            ["WiFi", "Breakfast", "Gym", "Business Center"],
            ["WiFi", "Parking", "Pet Friendly"],
        ]
        
        hotels = []
        for i in range(4):  # Return 4 hotel options
            name = random.choice(hotel_names)
            
            # Generate price based on hotel type and budget
            if hotel_type == "hostel":
                base_price = random.randint(800, 2500)
            elif hotel_type == "resort":
                base_price = random.randint(8000, 20000)
            else:  # hotel
                base_price = random.randint(2500, 12000)
            
            # Apply budget filter if provided
            if budget_per_night and base_price > budget_per_night:
                base_price = int(budget_per_night * 0.9)
            
            rating = round(random.uniform(3.5, 4.8), 1)
            amenities = random.choice(amenities_options)
            
            hotel = {
                "name": name,
                "rating": rating,
                "price_per_night": base_price,
                "currency": "INR",
                "amenities": amenities,
                "location": f"{location} - {random.choice(['City Center', 'Airport Area', 'Tourist District', 'Business District'])}",
                "distance_to_center": f"{random.uniform(0.5, 5.0):.1f} km",
                "breakfast_included": random.choice([True, False]),
                "cancellation": random.choice(["Free cancellation", "Non-refundable", "Partial refund"]),
                "availability": "Available"
            }
            hotels.append(hotel)
        
        # Sort by rating and price
        hotels.sort(key=lambda x: (-x["rating"], x["price_per_night"]))
        
        # Calculate total costs
        from datetime import datetime
        try:
            check_in = datetime.strptime(check_in_date, "%Y-%m-%d")
            check_out = datetime.strptime(check_out_date, "%Y-%m-%d")
            nights = (check_out - check_in).days
        except:
            nights = 1  # Fallback
        
        result = {
            "search_query": {
                "location": location,
                "check_in": check_in_date,
                "check_out": check_out_date,
                "guests": guests,
                "nights": nights
            },
            "hotels": hotels,
            "price_range": {
                "min_per_night": min(h["price_per_night"] for h in hotels),
                "max_per_night": max(h["price_per_night"] for h in hotels),
                "min_total": min(h["price_per_night"] for h in hotels) * nights,
                "max_total": max(h["price_per_night"] for h in hotels) * nights
            }
        }
        
        return f"""Hotel Search Results for {location}:

ACCOMMODATION OPTIONS ({nights} nights, {guests} guests):
{self._format_hotels(hotels, nights)}

PRICE RANGE: ₹{result['price_range']['min_per_night']:,} - ₹{result['price_range']['max_per_night']:,} per night
TOTAL COST RANGE: ₹{result['price_range']['min_total']:,} - ₹{result['price_range']['max_total']:,}

BEST VALUE: {hotels[0]['name']} - ₹{hotels[0]['price_per_night']:,}/night (Rating: {hotels[0]['rating']})

RECOMMENDATIONS:
• Book early for better rates
• Check cancellation policies
• Consider location vs price trade-offs
• {hotels[0]['name']} offers best value for money
"""

    def _format_hotels(self, hotels: List[Dict[str, Any]], nights: int) -> str:
        """Format hotel list for display"""
        formatted = []
        for hotel in hotels:
            total_cost = hotel["price_per_night"] * nights
            amenities_str = ", ".join(hotel["amenities"][:3])  # Show first 3 amenities
            breakfast = " + Breakfast" if hotel["breakfast_included"] else ""
            
            formatted.append(
                f"• {hotel['name']} ({hotel['rating']}★): "
                f"₹{hotel['price_per_night']:,}/night (Total: ₹{total_cost:,})\n"
                f"  Location: {hotel['location']}\n"
                f"  Amenities: {amenities_str}{breakfast}\n"
                f"  {hotel['cancellation']}\n"
            )
        return "\n".join(formatted)

    async def _arun(
        self,
        location: str,
        check_in_date: str,
        check_out_date: str,
        guests: int = 1,
        budget_per_night: Optional[float] = None,
        hotel_type: str = "hotel",
        **kwargs: Any,
    ) -> str:
        """Async version of the hotel search"""
        return self._run(location, check_in_date, check_out_date, guests, budget_per_night, hotel_type, **kwargs)
