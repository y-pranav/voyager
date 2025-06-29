from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import os
from datetime import datetime, timedelta
import json
import traceback
import random

class HotelSearchInput(BaseModel):
    """Input for hotel search tool"""
    location: str = Field(description="City or location to search for hotels")
    check_in_date: str = Field(description="Check-in date in YYYY-MM-DD format")
    check_out_date: str = Field(description="Check-out date in YYYY-MM-DD format")
    guests: int = Field(1, description="Number of guests")
    rooms: int = Field(1, description="Number of rooms")
    budget_max: Optional[float] = Field(None, description="Maximum budget per night in INR")
    star_rating: Optional[int] = Field(None, description="Minimum star rating (1-5)")
    hotel_type: str = Field("hotel", description="Type of accommodation (hotel, hostel, resort, etc.)")
    use_real_api: bool = Field(False, description="Whether to use real API calls instead of sample data")

class HotelSearchTool:
    """Tool for searching hotel options using sample data for now"""
    
    def __init__(self):
        self.name = "hotel_search"
        self.description = """Search for hotel options at a destination.
        Provides hotel data including prices, amenities, and location details.
        Currently uses sample data."""
        
        # Initialize API keys (not used with sample data)
        self.api_key = os.getenv('HOTEL_API_KEY')
        if not self.api_key:
            print("⚠️ Hotel API key not found. Using sample data only.")
        else:
            print("✅ Hotel API initialized")
    
    def _run(
        self,
        location: str,
        check_in_date: str,
        check_out_date: str,
        guests: int = 1,
        rooms: int = 1,
        budget_per_night: Optional[float] = None,
        hotel_type: str = "hotel",
        star_rating: Optional[int] = None,
        use_real_api: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute the hotel search and return structured data"""
        
        print(f"🏨 Starting hotel search for {location}")
        print(f"📅 Check-in: {check_in_date}, Check-out: {check_out_date}")
        print(f"👥 Guests: {guests}, Rooms: {rooms}")
        print(f"💰 Budget: {budget_per_night}, Type: {hotel_type}")
        print(f"✨ Star Rating: {star_rating if star_rating else 'Any'}")
        
        # Mock hotel data - replace with real API calls if use_real_api is True
        hotel_names = [
            "Grand Palace Hotel", "City View Inn", "Comfort Stay", 
            "Luxury Resort & Spa", "Budget Traveler Lodge", "Heritage Hotel",
            "Modern Suites", "Boutique Hotel", "Business Center Hotel",
            "Royal Gardens Resort", "Seaside Getaway", "Urban Retreat",
            "Family Inn & Suites", "Executive Quarters", "Landmark Hotel",
            "Sunset Resort", "Metro Lodging", "Plaza Premium"
        ]
        
        amenities_options = [
            ["WiFi", "Pool", "Gym", "Spa", "Restaurant", "Room Service", "Concierge", "Terrace"],
            ["WiFi", "Breakfast", "Parking", "Room Service", "Bar", "Laundry", "Airport Shuttle"],
            ["WiFi", "Pool", "Restaurant", "Concierge", "Beach Access", "Kids Club", "Tennis Court"],
            ["WiFi", "Breakfast", "Gym", "Business Center", "Conference Room", "Parking"],
            ["WiFi", "Parking", "Pet Friendly", "Restaurant", "Non-smoking Rooms"],
            ["WiFi", "Room Service", "Laundry", "24-hour Front Desk", "Security"],
            ["WiFi", "Pool", "Spa", "Fitness Center", "Rooftop Bar", "Restaurant", "Lounge"],
            ["WiFi", "Restaurant", "Bar", "Meeting Rooms", "Parking", "Express Check-in/out"]
        ]
        
        room_types = [
            "Standard Room", "Deluxe Room", "Superior Room", "Executive Room",
            "Junior Suite", "Suite", "Family Room", "Studio", "Twin Room",
            "Single Room", "Double Room", "King Room", "Queen Room"
        ]
        
        hotels = []
        num_hotels = random.randint(8, 15)  # Generate 8-15 hotel options
        
        # Ensure we don't have duplicate hotel names
        used_names = set()
        
        for i in range(num_hotels):
            # Ensure unique hotel names
            available_names = [name for name in hotel_names if name not in used_names]
            if not available_names:  # If we've used all names, add a suffix
                name = f"{random.choice(hotel_names)} {chr(65 + i)}"
            else:
                name = random.choice(available_names)
                used_names.add(name)
            
            # Generate price based on hotel type and star rating
            if hotel_type == "hostel":
                base_price = random.randint(800, 2500)
                star_level = random.randint(1, 3)
            elif hotel_type == "resort":
                base_price = random.randint(8000, 20000)
                star_level = random.randint(3, 5)
            else:  # hotel
                base_price = random.randint(2500, 12000)
                star_level = random.randint(2, 5)
            
            # Apply star rating filter if provided
            if star_rating and star_level < star_rating:
                star_level = star_rating
                # Adjust price based on star rating
                base_price = base_price * (1 + (star_rating - 3) * 0.2)
            
            # Apply budget filter if provided
            if budget_per_night and base_price > budget_per_night:
                base_price = int(budget_per_night * 0.9)
            
            # Generate rating with more variation but weighted toward good reviews
            if star_level >= 4:
                rating = round(random.uniform(3.8, 4.9), 1)
            elif star_level == 3:
                rating = round(random.uniform(3.0, 4.5), 1)
            else:
                rating = round(random.uniform(2.5, 4.0), 1)
            
            amenities = random.choice(amenities_options)
            room_type = random.choice(room_types)
            
            # Generate some image URLs (these would be placeholders for real APIs)
            images = [
                f"https://example.com/hotel_{i+1}_main.jpg",
                f"https://example.com/hotel_{i+1}_room.jpg",
                f"https://example.com/hotel_{i+1}_exterior.jpg"
            ]
            
            # Calculate total price based on days and rooms
            from datetime import date
            try:
                # Handle various date input formats
                if isinstance(check_in_date, str):
                    check_in_dt = datetime.strptime(check_in_date, "%Y-%m-%d")
                elif isinstance(check_in_date, datetime):
                    check_in_dt = check_in_date
                elif isinstance(check_in_date, date):
                    # Convert date to datetime
                    check_in_dt = datetime.combine(check_in_date, datetime.min.time())
                else:
                    print(f"⚠️ Unexpected check_in_date type: {type(check_in_date)}")
                    check_in_dt = datetime.now()  # Fallback
                    
                if isinstance(check_out_date, str):
                    check_out_dt = datetime.strptime(check_out_date, "%Y-%m-%d")
                elif isinstance(check_out_date, datetime):
                    check_out_dt = check_out_date
                elif isinstance(check_out_date, date):
                    # Convert date to datetime
                    check_out_dt = datetime.combine(check_out_date, datetime.min.time())
                else:
                    print(f"⚠️ Unexpected check_out_date type: {type(check_out_date)}")
                    # Default to 3 nights if we can't parse checkout date
                    check_out_dt = check_in_dt + timedelta(days=3)
                
                nights = max(1, (check_out_dt - check_in_dt).days)  # Ensure at least 1 night
                print(f"✅ Calculated {nights} nights stay")
            except Exception as e:
                print(f"⚠️ Date parsing error in hotel option generation: {str(e)}")
                nights = 3  # Reasonable default
            
            total_price = base_price * nights * rooms
            
            hotel = {
                "id": f"hotel_{i+1}",
                "name": name,
                "rating": float(rating),  # Ensure float for serialization
                "star_level": star_level,
                "price_per_night": float(base_price),  # Ensure float for serialization
                "currency": "INR",
                "total_price": float(total_price),  # Ensure float for serialization
                "amenities": amenities,
                "room_type": room_type,
                "location": f"{location} - {random.choice(['City Center', 'Airport Area', 'Tourist District', 'Business District', 'Historic Quarter'])}",
                "address": f"{random.randint(1, 999)} {random.choice(['Main St', 'Park Ave', 'Beach Road', 'Market Lane', 'Tourism Road'])}",
                "distance_to_center": float(random.uniform(0.2, 8.0)),  # in km
                "breakfast_included": random.choice([True, False]),
                "refundable": random.choice([True, False]),
                "cancellation_policy": random.choice(["Free cancellation", "Non-refundable", "Cancellation with fee", "24-hour cancellation"]),
                "images": images,
                "availability": "Available",
                "reviews_count": random.randint(50, 2000),
                "property_type": hotel_type.capitalize()
            }
            hotels.append(hotel)
        
        # Custom sorting for more realistic "best value" ranking
        # Combine rating, price, and amenities count in a weighted score
        for hotel in hotels:
            # Calculate a value score: higher rating and more amenities are better, lower price is better
            price_factor = 1.0 - (hotel["price_per_night"] / max(h["price_per_night"] for h in hotels))
            amenities_factor = len(hotel["amenities"]) / 8  # Normalize to 0-1 range assuming max 8 amenities
            breakfast_factor = 0.1 if hotel["breakfast_included"] else 0
            
            # Combined score with weights (rating has most weight, then price, then amenities)
            hotel["value_score"] = (
                (hotel["rating"] / 5) * 0.5 +  # 50% weight to rating (normalized to 0-1)
                price_factor * 0.3 +           # 30% weight to price (inversed, lower is better)
                amenities_factor * 0.15 +      # 15% weight to amenity count
                breakfast_factor +             # 10% bonus for breakfast
                (0.05 if hotel["refundable"] else 0)  # 5% bonus for being refundable
            )
        
        # Sort by our computed value score (higher is better)
        hotels.sort(key=lambda x: -x["value_score"])
        
        # Calculate total costs
        # Calculate nights and ensure all dates are strings for JSON serialization
        from datetime import date
        
        # Handle check-in date
        if isinstance(check_in_date, str):
            check_in_date_str = check_in_date
            try:
                check_in = datetime.strptime(check_in_date, "%Y-%m-%d")
            except:
                check_in = datetime.now()
        elif isinstance(check_in_date, datetime):
            check_in = check_in_date
            check_in_date_str = check_in.strftime("%Y-%m-%d")
        elif isinstance(check_in_date, date):
            check_in = datetime.combine(check_in_date, datetime.min.time())
            check_in_date_str = check_in_date.strftime("%Y-%m-%d")
        else:
            print(f"⚠️ Unsupported check_in_date type: {type(check_in_date)}")
            check_in = datetime.now()
            check_in_date_str = check_in.strftime("%Y-%m-%d")
        
        # Handle check-out date
        if isinstance(check_out_date, str):
            check_out_date_str = check_out_date
            try:
                check_out = datetime.strptime(check_out_date, "%Y-%m-%d")
            except:
                check_out = check_in + timedelta(days=3)
        elif isinstance(check_out_date, datetime):
            check_out = check_out_date
            check_out_date_str = check_out.strftime("%Y-%m-%d")
        elif isinstance(check_out_date, date):
            check_out = datetime.combine(check_out_date, datetime.min.time())
            check_out_date_str = check_out_date.strftime("%Y-%m-%d")
        else:
            print(f"⚠️ Unsupported check_out_date type: {type(check_out_date)}")
            check_out = check_in + timedelta(days=3)
            check_out_date_str = check_out.strftime("%Y-%m-%d")
        
        # Calculate nights
        try:
            nights = max(1, (check_out - check_in).days)
            print(f"✅ Calculated {nights} nights from {check_in_date_str} to {check_out_date_str}")
        except Exception as e:
            print(f"⚠️ Error calculating nights: {str(e)}")
            nights = 3  # Default to 3 nights
            
        # Calculate price ranges for analytics
        price_range = {
            "min_per_night": float(min(h["price_per_night"] for h in hotels)),
            "max_per_night": float(max(h["price_per_night"] for h in hotels)),
            "min_total": float(min(h["total_price"] for h in hotels)),
            "max_total": float(max(h["total_price"] for h in hotels))
        }
        
        # Create formatted text for LLM (not shown to users)
        formatted_text = self._format_hotels_text(hotels, nights, location, guests)
        
        # Structure the response for the frontend
        result = {
            "formatted": formatted_text,
            "hotels": {
                "options": hotels,
                "status": "sample_data",
                "disclaimer": "Sample hotel data for demonstration purposes"
            },
            "search_params": {
                "location": location,
                "check_in_date": check_in_date_str,  # Use string version
                "check_out_date": check_out_date_str,  # Use string version
                "guests": int(guests),  # Ensure integers
                "rooms": int(rooms),  # Ensure integers
                "nights": int(nights),  # Ensure integers 
                "budget_max": float(budget_per_night) if budget_per_night else None,
                "hotel_type": hotel_type,
                "star_rating": int(star_rating) if star_rating else None
            },
            "price_range": price_range,
            "total_options": len(hotels),
            "best_value": hotels[0]["id"] if hotels else None,
            "api_used": "sample"
        }
        
        print(f"✅ HotelSearchTool returning {len(hotels)} hotels")
        return result

    def _format_hotels_text(self, hotels: List[Dict[str, Any]], nights: int, location: str, guests: int) -> str:
        """Format hotel list for display in text form (for LLM consumption)"""
        formatted = []
        formatted.append(f"Hotel Search Results for {location}:")
        formatted.append(f"ACCOMMODATION OPTIONS ({nights} nights, {guests} guests):\n")
        
        for hotel in hotels:
            amenities_str = ", ".join(hotel["amenities"][:3])  # Show first 3 amenities
            breakfast = " + Breakfast" if hotel["breakfast_included"] else ""
            
            formatted.append(
                f"• {hotel['name']} ({hotel['rating']}★, {hotel['star_level']}-star): "
                f"₹{hotel['price_per_night']:,.0f}/night (Total: ₹{hotel['total_price']:,.0f})\n"
                f"  {hotel['room_type']} | Location: {hotel['location']} ({hotel['distance_to_center']:.1f} km from center)\n"
                f"  Amenities: {amenities_str}{breakfast}\n"
                f"  {hotel['cancellation_policy']} | Reviews: {hotel['reviews_count']}\n"
            )
            
        formatted.append(f"\nPRICE RANGE: ₹{min(h['price_per_night'] for h in hotels):,.0f} - ₹{max(h['price_per_night'] for h in hotels):,.0f} per night")
        formatted.append(f"TOTAL COST RANGE: ₹{min(h['total_price'] for h in hotels):,.0f} - ₹{max(h['total_price'] for h in hotels):,.0f}")
        
        if hotels:
            formatted.append(f"\nBEST VALUE: {hotels[0]['name']} - ₹{hotels[0]['price_per_night']:,.0f}/night (Rating: {hotels[0]['rating']})")
            
        formatted.append(f"\nRECOMMENDATIONS:")
        formatted.append(f"• Book early for better rates")
        formatted.append(f"• Check cancellation policies")
        formatted.append(f"• Consider location vs price trade-offs")
        if hotels:
            formatted.append(f"• {hotels[0]['name']} offers best value for money")
        
        return "\n".join(formatted)

    async def _arun(
        self,
        location: str,
        check_in_date: str,
        check_out_date: str,
        guests: int = 1,
        rooms: int = 1,
        budget_per_night: Optional[float] = None,
        hotel_type: str = "hotel",
        star_rating: Optional[int] = None,
        use_real_api: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Async version of the hotel search"""
        return self._run(
            location=location, 
            check_in_date=check_in_date, 
            check_out_date=check_out_date, 
            guests=guests,
            rooms=rooms,
            budget_per_night=budget_per_night, 
            hotel_type=hotel_type,
            star_rating=star_rating,
            use_real_api=use_real_api,
            **kwargs
        )
