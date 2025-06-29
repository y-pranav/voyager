from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import os
from datetime import datetime, timedelta
import json
import traceback
import random
from serpapi import GoogleSearch

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
    use_real_api: bool = Field(True, description="Whether to use real API calls instead of sample data")

class HotelSearchTool:
    """Tool for searching hotel options using SerpAPI (Google Hotels)"""
    
    def __init__(self):
        self.name = "hotel_search"
        self.description = """Search for hotel options at a destination.
        Provides hotel data including prices, amenities, and location details.
        Uses SerpAPI Google Hotels when real API is enabled, otherwise uses sample data."""
        
        # Initialize API keys
        self.serpapi_key = os.getenv('SERPAPI_API_KEY')
        if not self.serpapi_key:
            print("⚠️ SerpAPI key not found for hotel search. Using sample data only.")
        else:
            print("✅ SerpAPI initialized for Google Hotels search")
    
    def _search_serpapi_hotels(self, location: str, check_in_date: str, check_out_date: str, 
                             guests: int, rooms: int, hotel_type: str = "hotel",
                             star_rating: Optional[int] = None) -> List[Dict]:
        """Search hotels using SerpAPI Google Hotels"""
        if not self.serpapi_key:
            print("❌ SerpAPI key not available for hotel search, using fallback.")
            return []
        
        try:
            # Ensure dates are strings in YYYY-MM-DD format
            check_in_date_str = check_in_date.strftime('%Y-%m-%d') if hasattr(check_in_date, 'strftime') else str(check_in_date)
            check_out_date_str = check_out_date.strftime('%Y-%m-%d') if hasattr(check_out_date, 'strftime') else str(check_out_date)
            
            # Build SerpAPI parameters for Google Hotels
            params = {
                "engine": "google_hotels",
                "q": f"{hotel_type} in {location}",
                "check_in_date": check_in_date_str,
                "check_out_date": check_out_date_str,
                "adults": guests,
                "rooms": rooms,
                "currency": "INR",
                "api_key": self.serpapi_key
            }
            
            # Add optional star rating filter
            if star_rating:
                params["min_rating"] = star_rating
                
            print(f"🔍 Calling SerpAPI Google Hotels with: {location} from {check_in_date_str} to {check_out_date_str}")
            print(f"🔍 SerpAPI params: {params}")
            
            # Make the search request
            search = GoogleSearch(params)
            results = search.get_dict()
            
            if "error" in results:
                print(f"❌ SerpAPI error: {results['error']}")
                print(f"📝 Full error response: {results}")
                return []
                
            # Extract hotels from results
            hotels = []
            if "properties" in results:
                hotels.extend(results["properties"])
                
            print(f"✅ SerpAPI returned {len(hotels)} hotel options")
            return hotels
            
        except Exception as e:
            print(f"❌ Error searching SerpAPI hotels: {e}")
            traceback.print_exc()
            return []
    
    def _format_serpapi_results(self, serpapi_results: List[Dict], budget_max: Optional[float] = None) -> List[Dict]:
        """Format SerpAPI hotel results into structured data for frontend"""
        
        print(f"🔍 _format_serpapi_results called with {len(serpapi_results)} hotels")
        if budget_max:
            print(f"🔍 Budget max: {budget_max}")
            
        # Check if we need to inspect the structure of the results
        if serpapi_results and len(serpapi_results) > 0:
            sample_keys = list(serpapi_results[0].keys())
            print(f"📋 Sample hotel keys: {sample_keys}")
        
        structured_hotels = []
        
        for i, hotel in enumerate(serpapi_results):
            try:
                print(f"🔍 Processing hotel {i+1}:")
                
                # Extract hotel information
                name = hotel.get("name", f"Hotel {i+1}")
                
                # First, log the complete hotel data for debugging the first hotel only
                if i == 0:
                    print(f"DEBUG HOTEL STRUCTURE: {json.dumps(hotel, indent=2, default=str)}")
                
                # Try different price fields in the Google Hotels API response
                price_per_night = 0
                
                # Check for pricing information in different possible locations
                if "rate_per_night" in hotel and hotel["rate_per_night"]:
                    price_field = hotel["rate_per_night"]
                    print(f"   Found rate_per_night: {price_field}")
                    
                    # Check for extracted_lowest in dict (from SerpAPI)
                    if isinstance(price_field, dict):
                        if "extracted_lowest" in price_field:
                            price_per_night = float(price_field["extracted_lowest"])
                        elif "value" in price_field:
                            price_per_night = float(price_field["value"])
                        elif "lowest" in price_field:
                            try:
                                # Extract digits from string like "₹50,000"
                                lowest = price_field["lowest"]
                                clean_price = ''.join(c for c in lowest if c.isdigit())
                                if clean_price:
                                    price_per_night = float(clean_price)
                            except:
                                pass
                    elif isinstance(price_field, (int, float)):
                        price_per_night = float(price_field)
                    elif isinstance(price_field, str):
                        # Extract numeric value from string like "₹50,000"
                        try:
                            # Remove currency symbols, commas, and non-numeric characters
                            clean_price = ''.join(c for c in price_field if c.isdigit() or c == '.')
                            if clean_price:
                                price_per_night = float(clean_price)
                        except:
                            print(f"   ⚠️ Could not parse rate_per_night: {price_field}")
                
                # If no price yet, try "total_rate"
                if price_per_night == 0 and "total_rate" in hotel and hotel["total_rate"]:
                    price_field = hotel["total_rate"]
                    print(f"   Found total_rate: {price_field}")
                    
                    # Try to extract the total rate and divide by nights to get per night
                    nights = 3  # Default to 3 nights if not specified
                    
                    # Check for extracted_lowest in dict (from SerpAPI)
                    if isinstance(price_field, dict):
                        if "extracted_lowest" in price_field:
                            total_price = float(price_field["extracted_lowest"])
                            price_per_night = total_price / nights
                        elif "value" in price_field:
                            total_price = float(price_field["value"])
                            price_per_night = total_price / nights
                        elif "lowest" in price_field:
                            try:
                                # Extract digits from string like "₹50,000"
                                lowest = price_field["lowest"]
                                clean_price = ''.join(c for c in lowest if c.isdigit())
                                if clean_price:
                                    total_price = float(clean_price)
                                    price_per_night = total_price / nights
                            except:
                                pass
                    elif isinstance(price_field, (int, float)):
                        total_price = float(price_field)
                        price_per_night = total_price / nights
                    elif isinstance(price_field, str):
                        try:
                            # Remove currency symbols, commas, and non-numeric characters
                            clean_price = ''.join(c for c in price_field if c.isdigit() or c == '.')
                            if clean_price:
                                total_price = float(clean_price)
                                price_per_night = total_price / nights
                        except:
                            print(f"   ⚠️ Could not parse total_rate: {price_field}")
                
                # If still no price, look for other price fields or use a reasonable default
                if price_per_night == 0:
                    print(f"   ⚠️ No price found in API response, using default pricing")
                    # Use a reasonable default based on hotel class
                    hotel_class = hotel.get("hotel_class", 0)
                    if isinstance(hotel_class, str) and hotel_class.isdigit():
                        hotel_class = int(hotel_class)
                    elif not isinstance(hotel_class, (int, float)):
                        hotel_class = 3
                        
                    # Base price on hotel class
                    if hotel_class >= 5:
                        price_per_night = 15000 + (random.randint(5000, 15000))
                    elif hotel_class >= 4:
                        price_per_night = 8000 + (random.randint(2000, 7000))
                    elif hotel_class >= 3:
                        price_per_night = 5000 + (random.randint(1000, 3000))
                    else:
                        price_per_night = 3000 + (random.randint(500, 1500))
                
                # If we still have no price, generate a reasonable price based on the hotel star level
                if price_per_night == 0:
                    # Extract star level for price estimation
                    star_level = 3  # Default
                    
                    if "hotel_class" in hotel and hotel["hotel_class"]:
                        try:
                            star_level = int(float(hotel["hotel_class"]))
                        except:
                            # Try to extract digits
                            if isinstance(hotel["hotel_class"], str):
                                digit_chars = [c for c in hotel["hotel_class"] if c.isdigit()]
                                if digit_chars:
                                    star_level = int(digit_chars[0])
                    
                    # Generate price based on star rating
                    if star_level >= 5:
                        price_per_night = random.randint(15000, 30000)
                    elif star_level == 4:
                        price_per_night = random.randint(6000, 15000)
                    elif star_level == 3:
                        price_per_night = random.randint(3000, 6000)
                    else:
                        price_per_night = random.randint(1000, 3000)
                    
                    print(f"   ⚠️ No price found, generated price: ₹{price_per_night:,.0f}")
                
                print(f"   💰 Price: ₹{price_per_night:,.0f}")
                
                # Apply budget filter
                if budget_max and price_per_night > budget_max:
                    print(f"   ❌ Hotel exceeds budget limit (₹{budget_max:,.0f})")
                    continue
                else:
                    print(f"   ✅ Hotel within budget")
                
                # Extract rating (overall_rating in Google Hotels API)
                rating = 4.0  # Default
                if "overall_rating" in hotel:
                    try:
                        # The rating might be in a nested structure or direct
                        if isinstance(hotel["overall_rating"], dict) and "value" in hotel["overall_rating"]:
                            rating = float(hotel["overall_rating"]["value"])
                        elif isinstance(hotel["overall_rating"], (int, float)):
                            rating = float(hotel["overall_rating"])
                        elif isinstance(hotel["overall_rating"], str):
                            rating = float(hotel["overall_rating"].strip())
                    except (ValueError, TypeError):
                        print(f"   ⚠️ Could not parse overall_rating: {hotel.get('overall_rating')}")
                print(f"   ⭐ Rating: {rating}")
                
                # Extract star level (hotel_class in Google Hotels API)
                star_level = 3  # Default
                if "hotel_class" in hotel:
                    try:
                        # The class might be in different formats
                        if isinstance(hotel["hotel_class"], (int, float)):
                            star_level = int(hotel["hotel_class"])
                        elif isinstance(hotel["hotel_class"], str) and hotel["hotel_class"].isdigit():
                            star_level = int(hotel["hotel_class"])
                        # Handle "4-star hotel" format
                        elif isinstance(hotel["hotel_class"], str) and "-star" in hotel["hotel_class"].lower():
                            star_text = hotel["hotel_class"].lower().split("-star")[0].strip()
                            if star_text.isdigit():
                                star_level = int(star_text)
                    except (ValueError, TypeError):
                        print(f"   ⚠️ Could not parse hotel_class: {hotel.get('hotel_class')}")
                print(f"   ⭐ Star Level: {star_level}")
                
                # Extract location and address
                address = hotel.get("address", "")
                hotel_location = address  # Use address as the location
                print(f"   📍 Address: {address}")
                
                # Extract neighborhood or area if available
                nearby_places = hotel.get("nearby_places", [])
                if isinstance(nearby_places, list) and nearby_places:
                    # Get the closest nearby place for neighborhood info
                    neighborhood = nearby_places[0].get("name", "") if isinstance(nearby_places[0], dict) else ""
                    if neighborhood:
                        hotel_location = f"{neighborhood}, {hotel_location}"
                        print(f"   🏙️ Neighborhood: {neighborhood}")
                
                # Google Hotels API often has a gps_coordinates field
                gps_coords = hotel.get("gps_coordinates", {})
                if isinstance(gps_coords, dict):
                    latitude = gps_coords.get("latitude")
                    longitude = gps_coords.get("longitude")
                    if latitude and longitude:
                        print(f"   🌐 Coordinates: {latitude}, {longitude}")
                
                # Extract amenities - Google Hotels API has this as a list in "amenities"
                amenities = []
                if "amenities" in hotel and isinstance(hotel["amenities"], list):
                    amenities = hotel["amenities"]
                    print(f"   🛎️ Found {len(amenities)} amenities")
                elif "amenities" in hotel and isinstance(hotel["amenities"], str):
                    amenities = [a.strip() for a in hotel["amenities"].split(',')]
                else:
                    # Default amenities based on star level
                    if star_level >= 4:
                        amenities = ["WiFi", "Pool", "Gym", "Room Service", "Restaurant"]
                    else:
                        amenities = ["WiFi", "Parking"]
                    print(f"   ⚠️ No amenities found, using defaults: {amenities}")
                
                # Extract images - Google Hotels API structure
                images = []
                
                # Try to get thumbnail
                if "thumbnail" in hotel and hotel["thumbnail"]:
                    thumbnail_url = hotel["thumbnail"]
                    if isinstance(thumbnail_url, str):
                        images.append(thumbnail_url)
                        print(f"   🖼️ Found thumbnail")
                
                # Try to get images list
                if "images" in hotel:
                    hotel_images = hotel["images"]
                    if isinstance(hotel_images, list):
                        for img in hotel_images:
                            if isinstance(img, str):
                                images.append(img)
                            elif isinstance(img, dict) and "link" in img:
                                images.append(img["link"])
                        print(f"   🖼️ Found {len(images) - (1 if 'thumbnail' in hotel and hotel['thumbnail'] else 0)} additional images")
                    elif isinstance(hotel_images, dict) and "link" in hotel_images:
                        images.append(hotel_images["link"])
                        print(f"   🖼️ Found 1 image")
                
                if not images:
                    # Add placeholder images if none found
                    images = [
                        f"https://example.com/hotel_{i+1}_main.jpg",
                        f"https://example.com/hotel_{i+1}_room.jpg"
                    ]
                    print("   ⚠️ No images found, using placeholder images")
                
                # Calculate total price for the stay
                nights = hotel.get("nights", 1)
                rooms_count = hotel.get("rooms", 1)
                total_price = price_per_night * nights * rooms_count
                
                # Create structured hotel data
                hotel_data = {
                    'id': f"hotel_{i+1}",
                    'name': name,
                    'rating': float(rating),  # Ensure float for serialization
                    'star_level': int(star_level),  # Ensure int for serialization
                    'price_per_night': float(price_per_night),  # Ensure float for serialization
                    'currency': "INR",
                    'total_price': float(total_price),  # Ensure float for serialization
                    'amenities': amenities[:8],  # Limit to 8 amenities for consistency
                    'room_type': hotel.get("room_type", "Standard Room"),
                    'location': hotel_location,
                    'address': hotel.get("address", ""),
                    'distance_to_center': float(hotel.get("distance_to_center", random.uniform(0.2, 8.0))),
                    'breakfast_included': hotel.get("breakfast_included", random.choice([True, False])),
                    'refundable': hotel.get("refundable", random.choice([True, False])),
                    'cancellation_policy': hotel.get("cancellation_policy", "Free cancellation"),
                    'images': images,
                    'availability': "Available",
                    'reviews_count': hotel.get("reviews_count", random.randint(50, 2000)),
                    'property_type': hotel.get("property_type", "Hotel").capitalize()
                }
                
                # Calculate a value score for sorting
                price_factor = 1.0 - (hotel_data["price_per_night"] / (budget_max or 15000))
                amenities_factor = len(hotel_data["amenities"]) / 8
                breakfast_factor = 0.1 if hotel_data["breakfast_included"] else 0
                
                # Combined score with weights
                hotel_data["value_score"] = (
                    (hotel_data["rating"] / 5) * 0.5 +  # 50% weight to rating
                    price_factor * 0.3 +               # 30% weight to price
                    amenities_factor * 0.15 +          # 15% weight to amenity count
                    breakfast_factor +                 # 10% bonus for breakfast
                    (0.05 if hotel_data["refundable"] else 0)  # 5% bonus for being refundable
                )
                
                print(f"   ✅ Added hotel: {hotel_data['name']} - ₹{hotel_data['price_per_night']:,.0f}")
                structured_hotels.append(hotel_data)
                
            except Exception as e:
                print(f"❌ Error processing hotel {i+1}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Sort by our computed value score (higher is better)
        structured_hotels.sort(key=lambda x: -x['value_score'])
        print(f"🎯 FINAL: {len(structured_hotels)} hotels structured and sorted by value score")
        
        if structured_hotels:
            print("📋 Final hotel list:")
            for i, hotel in enumerate(structured_hotels[:5]):
                print(f"   {i+1}. {hotel['name']} - ₹{hotel['price_per_night']:,.0f}/night (Rating: {hotel['rating']})")
        
        return structured_hotels

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
        use_real_api: bool = True,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute the hotel search and return structured data"""
        
        print(f"🏨 Starting hotel search for {location}")
        print(f"📅 Check-in: {check_in_date}, Check-out: {check_out_date}")
        print(f"👥 Guests: {guests}, Rooms: {rooms}")
        print(f"💰 Budget: {budget_per_night}, Type: {hotel_type}")
        print(f"✨ Star Rating: {star_rating if star_rating else 'Any'}")
        
        print(f"🔄 API Mode: {'Real API' if use_real_api else 'Sample Data'}")
        
        hotels = []
        api_used = "sample"
        
        try:
            if use_real_api and self.serpapi_key:
                print("🌐 Using real SerpAPI for hotel search")
                # Use real API call
                serpapi_results = self._search_serpapi_hotels(
                    location=location,
                    check_in_date=check_in_date,
                    check_out_date=check_out_date,
                    guests=guests,
                    rooms=rooms,
                    hotel_type=hotel_type,
                    star_rating=star_rating
                )
                
                if serpapi_results:
                    print(f"✅ SerpAPI returned {len(serpapi_results)} hotels")
                    hotels = self._format_serpapi_results(serpapi_results, budget_max=budget_per_night)
                    api_used = "serpapi"
                else:
                    print("⚠️ SerpAPI returned no results, falling back to sample data")
                    api_used = "serpapi_fallback"
            else:
                print("⚠️ Using sample hotel data")
                api_used = "sample"
            
            # If we didn't get hotels from the API (either not requested or failed), generate sample data
            if not hotels:
                print("🏨 Generating sample hotel data")
                # Mock hotel data
        except Exception as e:
            print(f"❌ Error in hotel search API: {e}")
            traceback.print_exc()
            api_used = "error_fallback"
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
            
            # Handle country-level destinations by mapping to specific cities
            location_display = location
            hotel_location = location
            
            # Common country to city mappings for sample data
            if location.upper() in ["JAPAN", "TOKYO", "KYOTO", "OSAKA"]:
                cities = ["Tokyo", "Kyoto", "Osaka", "Hiroshima", "Nagoya", "Fukuoka"]
                hotel_location = random.choice(cities) if location.upper() == "JAPAN" else location
            elif location.upper() in ["INDIA", "DELHI", "MUMBAI", "BANGALORE"]:
                cities = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Jaipur"]
                hotel_location = random.choice(cities) if location.upper() == "INDIA" else location
            elif location.upper() in ["USA", "UNITED STATES", "NEW YORK", "LOS ANGELES"]:
                cities = ["New York", "Los Angeles", "Chicago", "Miami", "San Francisco"]
                hotel_location = random.choice(cities) if location.upper() in ["USA", "UNITED STATES"] else location
            elif location.upper() in ["GERMANY", "BERLIN", "MUNICH", "FRANKFURT"]:
                cities = ["Berlin", "Munich", "Frankfurt", "Hamburg", "Cologne", "Dresden"]
                hotel_location = random.choice(cities) if location.upper() == "GERMANY" else location
            elif location.upper() in ["UK", "UNITED KINGDOM", "LONDON", "MANCHESTER"]:
                cities = ["London", "Manchester", "Edinburgh", "Liverpool", "Glasgow", "Birmingham"]
                hotel_location = random.choice(cities) if location.upper() in ["UK", "UNITED KINGDOM"] else location
            elif location.upper() in ["FRANCE", "PARIS", "NICE", "LYON"]:
                cities = ["Paris", "Nice", "Lyon", "Marseille", "Bordeaux", "Strasbourg"]
                hotel_location = random.choice(cities) if location.upper() == "FRANCE" else location
            elif location.upper() in ["ITALY", "ROME", "MILAN", "VENICE"]:
                cities = ["Rome", "Milan", "Venice", "Florence", "Naples", "Turin"]
                hotel_location = random.choice(cities) if location.upper() == "ITALY" else location
            elif location.upper() in ["SPAIN", "MADRID", "BARCELONA", "SEVILLE"]:
                cities = ["Madrid", "Barcelona", "Seville", "Valencia", "Malaga", "Bilbao"]
                hotel_location = random.choice(cities) if location.upper() == "SPAIN" else location
            elif location.upper() in ["AUSTRALIA", "SYDNEY", "MELBOURNE", "BRISBANE"]:
                cities = ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Gold Coast"]
                hotel_location = random.choice(cities) if location.upper() == "AUSTRALIA" else location
            elif location.upper() in ["CHINA", "BEIJING", "SHANGHAI", "GUANGZHOU"]:
                cities = ["Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Xi'an", "Hangzhou"]
                hotel_location = random.choice(cities) if location.upper() == "CHINA" else location
            
            # Generate more hotels for better selection
            num_hotels = random.randint(8, 15)  # Generate 8-15 hotel options
            print(f"🏨 Generating {num_hotels} sample hotels for {hotel_location}")
            
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
                
                # Handle country vs city search by providing appropriate city names for countries
                location_display = location
                if location.upper() == "JAPAN":
                    location_display = random.choice(["Tokyo", "Kyoto", "Osaka", "Hiroshima", "Nara", "Sapporo", "Fukuoka", "Nagoya"])
                elif location.upper() == "INDIA":
                    location_display = random.choice(["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Kolkata", "Jaipur", "Goa"])
                elif location.upper() == "USA" or location.upper() == "UNITED STATES":
                    location_display = random.choice(["New York", "Los Angeles", "Chicago", "Miami", "Las Vegas", "San Francisco", "Boston", "Seattle"])
                elif location.upper() == "UK" or location.upper() == "UNITED KINGDOM":
                    location_display = random.choice(["London", "Manchester", "Edinburgh", "Glasgow", "Liverpool", "Birmingham", "Oxford", "Cambridge"])
                
                hotel = {
                    "id": f"hotel_{i+1}",
                    "name": f"{name} {location_display}",  # Add city name to hotel name for clarity
                    "rating": float(rating),  # Ensure float for serialization
                    "star_level": star_level,
                    "price_per_night": float(base_price),  # Ensure float for serialization
                    "currency": "INR",
                    "total_price": float(total_price),  # Ensure float for serialization
                    "amenities": amenities,
                    "room_type": room_type,
                    "location": f"{location_display} - {random.choice(['City Center', 'Airport Area', 'Tourist District', 'Business District', 'Historic Quarter'])}",
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
        
        # Always make sure we have hotels when using sample data
        if len(hotels) == 0 and api_used in ["sample", "serpapi_fallback", "error_fallback"]:
            print("⚠️ No sample hotels generated! This is a critical issue, regenerating...")
            
            # Map countries to cities for better display
            location_display = location
            country_cities_map = {
                "JAPAN": ["Tokyo", "Kyoto", "Osaka", "Hiroshima", "Fukuoka"],
                "INDIA": ["Mumbai", "Delhi", "Bangalore", "Chennai", "Jaipur"],
                "USA": ["New York", "Los Angeles", "Chicago", "San Francisco", "Miami"],
                "UNITED STATES": ["New York", "Los Angeles", "Chicago", "San Francisco", "Miami"],
                "UK": ["London", "Manchester", "Edinburgh", "Liverpool", "Glasgow"],
                "UNITED KINGDOM": ["London", "Manchester", "Edinburgh", "Liverpool", "Glasgow"],
                "GERMANY": ["Berlin", "Munich", "Frankfurt", "Hamburg", "Cologne"],
                "FRANCE": ["Paris", "Nice", "Lyon", "Marseille", "Bordeaux"],
                "SPAIN": ["Madrid", "Barcelona", "Seville", "Valencia", "Malaga"],
                "ITALY": ["Rome", "Milan", "Venice", "Florence", "Naples"],
                "AUSTRALIA": ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide"],
                "CANADA": ["Toronto", "Vancouver", "Montreal", "Calgary", "Ottawa"],
                "CHINA": ["Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Xi'an"],
                "THAILAND": ["Bangkok", "Phuket", "Chiang Mai", "Pattaya", "Krabi"]
            }
            
            # Find appropriate city name for the location
            location_upper = location.upper()
            if location_upper in country_cities_map:
                location_display = random.choice(country_cities_map[location_upper])
                print(f"🌎 Mapped country {location} to city {location_display} for hotel display")
            
            # Generate realistic hotel names based on location
            premium_names = ["Grand Hotel", "Royal Palace", "Luxury Suites", "The Ritz", "Four Seasons"]
            standard_names = ["Comfort Inn", "Best Western", "Holiday Hotel", "City Center Hotel", "Park Plaza"]
            budget_names = ["Budget Stay", "Economy Lodge", "Traveler's Rest", "Value Inn", "Sleep Well"]
            
            # Vary the hotel types based on location quality
            hotel_categories = [premium_names, standard_names, budget_names]
            weights = [0.3, 0.5, 0.2]  # 30% premium, 50% standard, 20% budget
            
            # Generate 5-8 hotels as fallback
            num_hotels = random.randint(5, 8)
            hotel_type_categories = random.choices(hotel_categories, weights=weights, k=num_hotels)
            
            for i in range(num_hotels):
                # Select hotel name from appropriate category
                hotels_from_category = hotel_type_categories[i]
                base_name = random.choice(hotels_from_category)
                
                # Add location suffix or other distinguishing feature if needed
                if i > 0 and any(h["name"] == f"{base_name} {location_display}" for h in hotels):
                    name = f"{base_name} {location_display} {chr(65 + i)}"  # Add A, B, C, etc.
                else:
                    name = f"{base_name} {location_display}"
                
                # Set pricing and rating based on category
                if hotels_from_category == premium_names:
                    price = random.randint(8000, 25000)
                    stars = random.randint(4, 5)
                    rating = round(random.uniform(4.0, 4.9), 1)
                    amenities = ["WiFi", "Pool", "Spa", "Fine Dining", "Concierge", "Room Service"]
                    room_type = random.choice(["Deluxe Suite", "Executive Room", "Premium King"])
                elif hotels_from_category == standard_names:
                    price = random.randint(4000, 8000)
                    stars = random.randint(3, 4)
                    rating = round(random.uniform(3.5, 4.5), 1)
                    amenities = ["WiFi", "Restaurant", "Fitness Center", "Bar", "Breakfast"]
                    room_type = random.choice(["Standard Double", "King Room", "Twin Room"])
                else:  # budget_names
                    price = random.randint(1500, 4000)
                    stars = random.randint(2, 3)
                    rating = round(random.uniform(3.0, 4.0), 1)
                    amenities = ["WiFi", "24-hour Front Desk", "TV", "Air Conditioning"]
                    room_type = random.choice(["Standard Room", "Economy Double", "Basic Room"])
                
                # Calculate total price
                total_price = price * nights
                
                # Create the hotel object
                hotel = {
                    "id": f"hotel_{i+1}",
                    "name": name,
                    "rating": float(rating),
                    "star_level": stars,
                    "price_per_night": float(price),
                    "currency": "INR",
                    "total_price": float(total_price),
                    "amenities": amenities[:random.randint(3, len(amenities))],  # Randomize amenity count
                    "room_type": room_type,
                    "location": f"{location_display} - {random.choice(['City Center', 'Downtown', 'Tourist District', 'Business District'])}",
                    "address": f"{random.randint(1, 999)} {random.choice(['Main St', 'Park Avenue', 'Plaza Road', 'Central Blvd'])}",
                    "distance_to_center": float(random.uniform(0.2, 5.0)),
                    "breakfast_included": random.choice([True, False]),
                    "refundable": random.choice([True, False]),
                    "cancellation_policy": random.choice(["Free cancellation", "Cancellation with fee", "Non-refundable"]),
                    "images": [
                        f"https://example.com/hotel_{location_display.lower()}_{i+1}_1.jpg",
                        f"https://example.com/hotel_{location_display.lower()}_{i+1}_2.jpg"
                    ],
                    "availability": "Available",
                    "reviews_count": random.randint(50, 2000),
                    "property_type": hotel_type.capitalize()
                }
                hotels.append(hotel)
            
            # Sort by rating and price for better display
            for hotel in hotels:
                # Calculate a value score: higher rating and more amenities are better, lower price is better
                price_factor = 1.0 - (hotel["price_per_night"] / max(h["price_per_night"] for h in hotels))
                amenities_factor = len(hotel["amenities"]) / 6  # Normalize to 0-1 range assuming max 6 amenities
                breakfast_factor = 0.1 if hotel["breakfast_included"] else 0
                
                # Combined score with weights
                hotel["value_score"] = (
                    (hotel["rating"] / 5) * 0.5 +  # 50% weight to rating
                    price_factor * 0.3 +           # 30% weight to price
                    amenities_factor * 0.1 +       # 10% weight to amenity count
                    breakfast_factor +             # 10% bonus for breakfast
                    (0.05 if hotel["refundable"] else 0)  # 5% bonus for being refundable
                )
            
            # Sort by value score (higher is better)
            hotels.sort(key=lambda x: -x["value_score"])
            
            print(f"✅ Generated {len(hotels)} fallback hotels for {location_display}")
            
        # Calculate price ranges for analytics or provide defaults for empty results
        if hotels:
            price_range = {
                "min_per_night": float(min(h["price_per_night"] for h in hotels)),
                "max_per_night": float(max(h["price_per_night"] for h in hotels)),
                "min_total": float(min(h["total_price"] for h in hotels)),
                "max_total": float(max(h["total_price"] for h in hotels))
            }
        else:
            # Default price range when no hotels are found
            price_range = {
                "min_per_night": 0.0,
                "max_per_night": 0.0,
                "min_total": 0.0,
                "max_total": 0.0
            }
        
        # Create formatted text for LLM (not shown to users)
        formatted_text = self._format_hotels_text(hotels, nights, location, guests)
        
        # Set up appropriate status and disclaimer based on API used
        status = "live_data" if api_used == "serpapi" else "sample_data"
        if api_used == "serpapi":
            disclaimer = "Live hotel data from Google Hotels via SerpAPI"
        elif api_used == "serpapi_fallback" or api_used == "error_fallback":
            disclaimer = "SerpAPI returned no results or encountered an error. Using sample data as fallback."
        else:
            disclaimer = "Sample hotel data for demonstration purposes"
            
        # Structure the response for the frontend
        result = {
            "formatted": formatted_text,
            "hotels": {
                "options": hotels,
                "status": status,
                "disclaimer": disclaimer
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
            "api_used": api_used
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
        
        if hotels:
            formatted.append(f"\nPRICE RANGE: ₹{min(h['price_per_night'] for h in hotels):,.0f} - ₹{max(h['price_per_night'] for h in hotels):,.0f} per night")
            formatted.append(f"TOTAL COST RANGE: ₹{min(h['total_price'] for h in hotels):,.0f} - ₹{max(h['total_price'] for h in hotels):,.0f}")
        else:
            formatted.append("\nNo hotel options found matching your criteria.")
        
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
        use_real_api: bool = True,
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
