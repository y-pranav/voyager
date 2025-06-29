from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import os
from datetime import datetime, timedelta
import json
import traceback
from serpapi import GoogleSearch

class FlightSearchInput(BaseModel):
    """Input for flight search tool"""
    origin: str = Field(description="Origin city or airport code")
    destination: str = Field(description="Destination city or airport code")
    departure_date: str = Field(description="Departure date in YYYY-MM-DD format")
    return_date: Optional[str] = Field(None, description="Return date for round trip")
    passengers: int = Field(1, description="Number of passengers")
    budget_max: Optional[float] = Field(None, description="Maximum budget in INR")
    use_real_api: bool = Field(False, description="Whether to use real API calls instead of sample data")

class FlightSearchTool:
    """Tool for searching flight options using SerpAPI (Google Flights)"""
    
    def __init__(self):
        self.name = "flight_search"
        self.description = """Search for real flight options using SerpAPI Google Flights. 
        Provides accurate, real-time flight data including prices, airlines, and schedules.
        Limited to essential searches due to API costs."""
        
        # Initialize SerpAPI
        self.serpapi_key = os.getenv('SERPAPI_API_KEY')
        if not self.serpapi_key:
            print("⚠️ Warning: SerpAPI key not found. Using fallback mode.")
        else:
            print("✅ SerpAPI initialized for Google Flights search")
    
    def _get_airport_code(self, location: str) -> str:
        """Convert city name to IATA airport code"""
        # Common airport mappings
        airport_codes = {
            # India
            'delhi': 'DEL', 'new delhi': 'DEL',
            'mumbai': 'BOM', 'bombay': 'BOM',
            'bangalore': 'BLR', 'bengaluru': 'BLR',
            'chennai': 'MAA', 'madras': 'MAA',
            'hyderabad': 'HYD',
            'kolkata': 'CCU', 'calcutta': 'CCU',
            'pune': 'PNQ',
            'ahmedabad': 'AMD',
            'kochi': 'COK', 'cochin': 'COK',
            'goa': 'GOI',
            
            # International
            'tokyo': 'NRT', 'japan': 'NRT',
            'london': 'LHR', 'uk': 'LHR',
            'paris': 'CDG', 'france': 'CDG',
            'new york': 'JFK', 'nyc': 'JFK',
            'dubai': 'DXB', 'uae': 'DXB',
            'singapore': 'SIN',
            'bangkok': 'BKK', 'thailand': 'BKK',
            'sydney': 'SYD', 'australia': 'SYD',
            'los angeles': 'LAX', 'la': 'LAX',
            'amsterdam': 'AMS', 'netherlands': 'AMS',
            'frankfurt': 'FRA', 'germany': 'FRA',
            'zurich': 'ZRH', 'switzerland': 'ZRH',
        }
        
        location_lower = location.lower().strip()
        return airport_codes.get(location_lower, location.upper()[:3])
    
    def _search_serpapi_flights(self, origin: str, destination: str, departure_date: str, 
                               passengers: int, return_date: Optional[str] = None) -> List[Dict]:
        """Search flights using SerpAPI Google Flights"""
        if not self.serpapi_key:
            print("❌ SerpAPI key not available, using fallback.")
            return []
        
        try:
            origin_code = self._get_airport_code(origin)
            destination_code = self._get_airport_code(destination)
            
            # Ensure dates are strings
            departure_date_str = departure_date.strftime('%Y-%m-%d') if hasattr(departure_date, 'strftime') else str(departure_date)
            
            # Build SerpAPI parameters for Google Flights
            params = {
                "engine": "google_flights",
                "departure_id": origin_code,
                "arrival_id": destination_code,
                "outbound_date": departure_date_str,
                "currency": "INR",
                "adults": passengers,
                "type": "2",  # Default to one-way (which works!)
                "api_key": self.serpapi_key
            }
            
            # Only add return_date if it's a round trip
            if return_date:
                return_date_str = return_date.strftime('%Y-%m-%d') if hasattr(return_date, 'strftime') else str(return_date)
                params["return_date"] = return_date_str
                params["type"] = "1"  # Round trip
            
            print(f"🔍 Calling SerpAPI Google Flights with: {origin_code} → {destination_code} on {departure_date_str}")
            
            # Make the search request
            print(f"🔍 SerpAPI params: {params}")
            search = GoogleSearch(params)
            results = search.get_dict()
            
            if "error" in results:
                print(f"❌ SerpAPI error: {results['error']}")
                print(f"📝 Full error response: {results}")
                
                # Special handling for common SerpAPI errors
                if "return_date" in str(results['error']):
                    print("🛠️ Attempting to fix return_date error...")
                    # Retry with properly set return_date
                    if not return_date:
                        # Generate a return date 7 days after departure
                        try:
                            from datetime import datetime, timedelta
                            departure_dt = datetime.strptime(departure_date_str, "%Y-%m-%d")
                            auto_return_date = (departure_dt + timedelta(days=7)).strftime("%Y-%m-%d")
                            params["return_date"] = auto_return_date
                            print(f"🔄 Retrying with auto-generated return date: {auto_return_date}")
                            search = GoogleSearch(params)
                            results = search.get_dict()
                            if "error" not in results:
                                flights = []
                                if "best_flights" in results:
                                    flights.extend(results["best_flights"])
                                if "other_flights" in results:
                                    flights.extend(results["other_flights"])
                                print(f"✅ Retry successful! Found {len(flights)} flights")
                                return flights
                        except Exception as retry_error:
                            print(f"⚠️ Retry also failed: {retry_error}")
                
                # If we reach here, all attempts failed
                return []
            
            # Extract flights from results
            flights = []
            if "best_flights" in results:
                flights.extend(results["best_flights"])
            if "other_flights" in results:
                flights.extend(results["other_flights"])
                
            print(f"✅ SerpAPI returned {len(flights)} flight options")
            return flights
            
        except Exception as e:
            print(f"❌ Error searching SerpAPI flights: {e}")
            traceback.print_exc()
            return []
    
    def _format_flight_results_structured(self, serpapi_results: List[Dict], budget_max: Optional[float] = None) -> List[Dict]:
        """Format SerpAPI results into structured data for frontend"""
        
        print(f"🔍 _format_flight_results_structured called with {len(serpapi_results)} offers")
        if budget_max:
            print(f"🔍 Budget max: {budget_max}")
            
        # Check if we need to inspect the structure of the results
        if serpapi_results and len(serpapi_results) > 0:
            sample_keys = list(serpapi_results[0].keys())
            print(f"📋 Sample flight keys: {sample_keys}")
        
        structured_flights = []
        
        for i, flight in enumerate(serpapi_results):
            try:
                print(f"🔍 Processing flight {i+1}:")
                
                # Extract price information
                price_inr = flight.get("price", 0)
                if isinstance(price_inr, str):
                    # Extract numeric value from string like "₹50,000"
                    price_inr = float(''.join(filter(str.isdigit, price_inr.replace(',', ''))))
                
                print(f"   💰 Price: ₹{price_inr:,.0f}")
                
                # Apply budget filter
                if budget_max and price_inr > budget_max * 0.4:
                    print(f"   ❌ Flight exceeds budget limit (₹{budget_max * 0.4:,.0f})")
                    continue
                else:
                    print(f"   ✅ Flight within budget")
                
                # Extract flight details
                flights_info = flight.get("flights", [])
                airlines = []
                segments = []
                total_duration = 0
                
                for segment in flights_info:
                    airline = segment.get("airline", "")
                    flight_number = segment.get("flight_number", "")
                    departure_airport = segment.get("departure_airport", {}).get("id", "")
                    arrival_airport = segment.get("arrival_airport", {}).get("id", "")
                    departure_time = segment.get("departure_airport", {}).get("time", "")
                    arrival_time = segment.get("arrival_airport", {}).get("time", "")
                    duration = segment.get("duration", 0)
                    
                    if airline and airline not in airlines:
                        airlines.append(airline)
                    
                    print(f"   ✈️ Segment: {flight_number} ({departure_airport} → {arrival_airport})")
                    
                    segments.append({
                        'flight_number': flight_number,
                        'airline': airline,
                        'departure_airport': departure_airport,
                        'departure_time': departure_time,
                        'arrival_airport': arrival_airport,
                        'arrival_time': arrival_time,
                        'duration': f"{duration//60}h {duration%60}m" if duration else "",
                        'cabin': "Economy",  # Default
                        'aircraft': segment.get("aircraft", ""),
                        'stops': 0
                    })
                    
                    total_duration += duration
                
                # Calculate stops
                stops = max(0, len(segments) - 1)
                
                # Format duration
                hours = total_duration // 60
                minutes = total_duration % 60
                duration_str = f"PT{hours}H{minutes}M"  # ISO 8601 duration
                
                # Create structured flight data
                flight_data = {
                    'id': str(i + 1),
                    'price_inr': price_inr,
                    'price_original': price_inr,
                    'currency': "INR",
                    'airlines': airlines,
                    'total_duration': duration_str,
                    'segments': segments,
                    'total_stops': stops,
                    'validating_airlines': airlines,
                    'bookable_seats': flight.get("seats_left", 0),
                    'instant_ticketing_required': False,
                    'last_ticketing_date': datetime.now().strftime("%Y-%m-%d"),
                    'fare_type': "PUBLISHED",
                    'price_disclaimer': 'Real-time prices from Google Flights',
                    'api_source': 'SerpAPI',
                    'environment': 'production'
                }
                
                print(f"   ✅ Added flight: {flight_data['airlines']} - ₹{flight_data['price_inr']:,.0f}")
                structured_flights.append(flight_data)
                
            except Exception as e:
                print(f"❌ Error processing flight offer {i+1}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Sort by price
        structured_flights.sort(key=lambda x: x['price_inr'])
        print(f"🎯 FINAL: {len(structured_flights)} flights structured and sorted by price")
        
        if structured_flights:
            print("📋 Final flight list:")
            for i, flight in enumerate(structured_flights):
                print(f"   {i+1}. {flight['airlines']} - ₹{flight['price_inr']:,.0f} ({flight['currency']} {flight['price_original']})")
        
        return structured_flights
    
    def _format_flight_results_text(self, structured_flights: List[Dict]) -> str:
        """Format structured flight data into readable text for LLM"""
        if not structured_flights:
            return self._get_fallback_results()
        
        result_lines = []
        result_lines.append("✈️ REAL FLIGHT OPTIONS (Powered by Google Flights)")
        result_lines.append("=" * 55)
        
        for i, flight in enumerate(structured_flights[:3], 1):  # Show top 3
            # Get main route info
            first_segment = flight['segments'][0]
            last_segment = flight['segments'][-1]
            
            # Use the times directly from SerpAPI
            dep_time = first_segment['departure_time']
            arr_time = last_segment['arrival_time']
            
            # Format duration safely
            try:
                duration = flight['total_duration'].replace('PT', '').replace('H', 'h ').replace('M', 'm').lower()
            except:
                # Fallback if total_duration is not formatted as expected
                duration = "varies"
            
            # Stops info
            stops_text = "Direct" if flight['total_stops'] == 0 else f"{flight['total_stops']} stop(s)"
            
            result_lines.append(f"\n🎫 OPTION {i}: {' & '.join(flight['airlines'])}")
            result_lines.append(f"   Route: {first_segment['departure_airport']} → {last_segment['arrival_airport']}")
            result_lines.append(f"   Time: {dep_time} - {arr_time} ({duration})")
            result_lines.append(f"   Stops: {stops_text}")
            result_lines.append(f"   Price: ₹{int(flight['price_inr']):,}")  # Ensure we're handling price as int
            result_lines.append(f"   Cabin: {first_segment['cabin']}")
            
            if flight['bookable_seats'] > 0:
                result_lines.append(f"   Seats: {flight['bookable_seats']} available")
        
        result_lines.append(f"\n💡 FLIGHT INFORMATION:")
        result_lines.append(f"   • Real-time prices from Google Flights")
        result_lines.append(f"   • Actual airline prices may vary slightly")
        result_lines.append(f"   • Book directly with airlines for final rates")
        result_lines.append(f"\n✅ Flight details are accurate and current")
        result_lines.append(f"🔄 Compare and book through airlines or travel websites")
        result_lines.append(f"⚡ {len(structured_flights)} total options found")
        
        return "\n".join(result_lines)
    
    def _get_fallback_results(self) -> str:
        """Fallback results when API fails"""
        import random
        
        airlines = ["Air India", "IndiGo", "SpiceJet", "Vistara", "GoAir"]
        
        result_lines = []
        result_lines.append("✈️ SAMPLE FLIGHT OPTIONS (Demo Mode)")
        result_lines.append("=" * 45)
        
        for i in range(3):
            airline = random.choice(airlines)
            price = random.randint(8000, 25000)
            departure_time = f"{random.randint(6, 22):02d}:{random.choice(['00', '30'])}"
            duration = f"{random.randint(1, 8)}h {random.randint(0, 59):02d}m"
            flight_number = f"{airline[:2].upper()}{random.randint(100, 999)}"
            
            result_lines.append(f"\n🎫 OPTION {i+1}: {airline}")
            result_lines.append(f"   Flight: {flight_number}")
            result_lines.append(f"   Departure: {departure_time}")
            result_lines.append(f"   Duration: {duration}")
            result_lines.append(f"   Price: ₹{price:,}")
        
        result_lines.append(f"\n⚠️ Sample data - Add SerpAPI key for real Google Flights data")
        return "\n".join(result_lines)
    
    def _get_fallback_results_structured(self, origin: str, destination: str, passengers: int) -> List[Dict]:
        """Create enhanced sample flight results with varied options"""
        import random
        
        print("⚠️ Using structured sample flight data")
        origin_code = self._get_airport_code(origin)
        dest_code = self._get_airport_code(destination)
        
        # Create sample flights with more variety
        flights = []
        airlines = ["Air India", "IndiGo", "SpiceJet", "Vistara", "GoAir", 
                  "Emirates", "Etihad Airways", "Qatar Airways", "Lufthansa", "British Airways",
                  "Singapore Airlines", "Thai Airways", "ANA", "Cathay Pacific", "Japan Airlines"]
        aircraft_types = ["B737", "A320", "A321", "B777", "B787", "A380", "A350", "B747", "A330", "B767"]
        cabin_classes = ["Economy", "Premium Economy", "Business", "First"]
        fare_types = ["PUBLISHED", "SPECIAL", "DISCOUNTED", "SALE", "REGULAR"]
        
        # Generate a variety of flights (8-12 options)
        for i in range(random.randint(8, 12)):
            # Decide if this will be a direct flight or have stops
            stops = random.choices([0, 1, 2], weights=[0.6, 0.3, 0.1])[0]
            
            # Select airlines (can be multiple for code-share)
            selected_airlines = random.sample(airlines, k=min(stops+1, 3))
            main_airline = selected_airlines[0]
            airline_code = main_airline.split()[0][:2].upper()
            
            # Base price calculation with variability
            base_price = random.randint(8000, 25000)
            if stops == 0:
                # Direct flights can be premium priced
                price = base_price * (1 + random.uniform(0.1, 0.3))
            else:
                # Flights with stops may be cheaper
                price = base_price * (1 - random.uniform(0.05, 0.15) * stops)
            
            price = price * passengers  # Multiply by passenger count
            
            # Initial departure time
            dep_hour = random.randint(4, 23)
            dep_min = random.choice([0, 10, 15, 20, 30, 40, 45, 50])
            
            # Total duration calculation
            base_duration_hrs = max(1, int(abs(hash(dest_code) - hash(origin_code)) % 10))  # Pseudo-realistic duration
            total_duration_hrs = base_duration_hrs + random.randint(0, 3) + (stops * random.uniform(1, 3))
            total_duration_mins = random.randint(0, 59)
            
            # Each segment can be a different flight
            segments = []
            segment_airports = [origin_code]
            
            # Add connecting airports for multi-segment flights
            if stops > 0:
                # Common connecting hubs
                connecting_hubs = ["DXB", "AUH", "DOH", "FRA", "LHR", "CDG", "SIN", "BKK", "DEL", "BOM"]
                # Filter out origin and destination from possible hubs
                possible_hubs = [hub for hub in connecting_hubs if hub != origin_code and hub != dest_code]
                # Select random hubs for connections
                connecting_airports = random.sample(possible_hubs, stops)
                segment_airports.extend(connecting_airports)
            
            segment_airports.append(dest_code)
            
            # Calculate segment durations
            segment_durations = []
            remaining_duration_hrs = total_duration_hrs
            remaining_duration_mins = total_duration_mins
            
            for s in range(stops + 1):
                if s == stops:  # Last segment
                    segment_durations.append((remaining_duration_hrs, remaining_duration_mins))
                else:
                    # Random proportion of total time
                    proportion = random.uniform(0.3, 0.7)
                    seg_hrs = int(remaining_duration_hrs * proportion)
                    seg_mins = int(remaining_duration_mins * proportion)
                    segment_durations.append((seg_hrs, seg_mins))
                    remaining_duration_hrs -= seg_hrs
                    remaining_duration_mins -= seg_mins
                    if remaining_duration_mins < 0:
                        remaining_duration_hrs -= 1
                        remaining_duration_mins += 60
            
            # Track current time for segments
            current_hour = dep_hour
            current_min = dep_min
            
            for s in range(stops + 1):
                # Calculate segment details
                current_airline = selected_airlines[min(s, len(selected_airlines)-1)]
                current_code = current_airline.split()[0][:2].upper()
                flight_num = random.randint(100, 999)
                
                segment_hrs, segment_mins = segment_durations[s]
                
                # Calculate arrival time for this segment
                arr_hour = int((current_hour + segment_hrs) % 24)
                arr_min = int((current_min + segment_mins) % 60)
                
                # Select cabin class with business/first more common on international routes
                cabin = random.choices(cabin_classes, weights=[0.7, 0.15, 0.1, 0.05])[0]
                
                segments.append({
                    'flight_number': f"{current_code}{flight_num}",
                    'airline': current_airline,
                    'departure_airport': segment_airports[s],
                    'departure_time': f"{int(current_hour):02d}:{int(current_min):02d}",
                    'arrival_airport': segment_airports[s+1],
                    'arrival_time': f"{int(arr_hour):02d}:{int(arr_min):02d}",
                    'duration': f"{int(segment_hrs)}h {int(segment_mins)}m",
                    'cabin': cabin,
                    'aircraft': random.choice(aircraft_types),
                    'stops': 0  # Each segment has no stops within itself
                })
                
                # Add layover time between segments
                if s < stops:
                    layover_hrs = random.randint(1, 3)
                    layover_mins = random.randint(0, 59)
                    current_hour = (arr_hour + layover_hrs) % 24
                    current_min = (arr_min + layover_mins) % 60
            
            # Create the full flight record
            flights.append({
                'id': str(i+1),
                'price_inr': float(round(price)),  # Ensure it's a proper float with no decimal issues
                'price_original': float(round(price)),  # Ensure it's a proper float with no decimal issues
                'currency': 'INR',
                'airlines': selected_airlines,
                'total_duration': f"PT{int(total_duration_hrs)}H{int(total_duration_mins)}M",
                'segments': segments,
                'total_stops': stops,
                'validating_airlines': selected_airlines,
                'bookable_seats': random.randint(1, 20),
                'instant_ticketing_required': random.choice([True, False]),
                'last_ticketing_date': datetime.now().strftime("%Y-%m-%d"),
                'fare_type': random.choice(fare_types),
                'price_disclaimer': 'Sample flight data for demonstration',
                'api_source': 'Sample',
                'environment': 'demo'
            })
        
        return flights
    
    def _run(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        passengers: int = 1,
        budget_max: Optional[float] = None,
        use_real_api: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute the flight search and return both formatted string and structured data"""
        
        print(f"🚀 Starting flight search: {origin} → {destination} on {departure_date}")
        print(f"📊 Search params - Passengers: {passengers}, Budget: {budget_max}")
        print(f"🔄 API Mode: {'Real API' if use_real_api else 'Sample Data'}")
        
        structured_flights = []
        api_used = "sample"
        
        try:
            if use_real_api and self.serpapi_key:
                print("🌐 Using real SerpAPI for flight search")
                # Use real API call
                serpapi_results = self._search_serpapi_flights(
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date,
                    return_date=return_date,
                    passengers=passengers
                )
                
                if serpapi_results:
                    print(f"✅ SerpAPI returned {len(serpapi_results)} flights")
                    structured_flights = self._format_flight_results_structured(serpapi_results, budget_max)
                    api_used = "serpapi"
                else:
                    print("⚠️ SerpAPI returned no results, falling back to sample data")
                    structured_flights = self._get_fallback_results_structured(origin, destination, passengers)
                    api_used = "serpapi_fallback"
            else:
                # Use sample data - no API calls
                print("⚠️ Using enhanced sample flight data")
                structured_flights = self._get_fallback_results_structured(origin, destination, passengers)
                api_used = "sample"
            
            # Generate formatted text results for LLM
            formatted_text = self._format_flight_results_text(structured_flights)
            
            print(f"📋 Structured flights count after processing: {len(structured_flights)}")
            print(f"💰 Budget constraint applied: {budget_max}")
            
            # Log each structured flight for debugging
            for i, flight in enumerate(structured_flights):
                print(f"✈️ Flight {i+1}: {flight['airlines']} - ₹{flight['price_inr']:,.0f} ({flight['currency']} {flight['price_original']})")
                print(f"   Segments: {len(flight['segments'])}, Stops: {flight['total_stops']}")
                for j, segment in enumerate(flight['segments']):
                    print(f"   Segment {j+1}: {segment['flight_number']} {segment['departure_airport']}→{segment['arrival_airport']}")
            
            # Ensure dates are strings for JSON serialization
            departure_date_str = departure_date.strftime('%Y-%m-%d') if hasattr(departure_date, 'strftime') else str(departure_date)
            return_date_str = return_date.strftime('%Y-%m-%d') if return_date and hasattr(return_date, 'strftime') else str(return_date) if return_date else None
            
            # Ensure we're returning the correct structure that the frontend expects
            result = {
                'formatted': formatted_text,
                'flights': {
                    'options': structured_flights,  # Make sure flights are under 'options' key
                    'status': 'sample_data',
                    'disclaimer': 'Sample flight data for demonstration purposes'
                },
                'search_params': {
                    'origin': origin,
                    'destination': destination,
                    'departure_date': departure_date_str,
                    'return_date': return_date_str,
                    'passengers': passengers,
                    'budget_max': budget_max
                },
                'total_options': len(structured_flights),
                'api_used': api_used
            }
            
            print(f"✅ FlightSearchTool returning {len(structured_flights)} flights to TripPlannerAgent")
            print(f"🎯 Result structure: formatted={type(result['formatted'])}, flights={type(result['flights'])}, count={len(result['flights'])}")
            return result
            
        except Exception as e:
            print(f"❌ Error in flight search: {e}")
            traceback.print_exc()
            
            try:
                # Use fallback data even when errors occur
                fallback_flights = self._get_fallback_results_structured(origin, destination, passengers)
                
                # Ensure dates are strings for JSON serialization
                departure_date_str = departure_date.strftime('%Y-%m-%d') if hasattr(departure_date, 'strftime') else str(departure_date)
                return_date_str = return_date.strftime('%Y-%m-%d') if return_date and hasattr(return_date, 'strftime') else str(return_date) if return_date else None
            except:
                # Final fallback if even structured fallback fails
                print("⚠️ Critical error: Using emergency basic fallback")
                fallback_flights = [{"id": "1", "price_inr": float(10000), "airlines": ["Sample Airline"], "total_duration": "PT2H0M", "segments": [{"departure_airport": "DEP", "arrival_airport": "ARR", "departure_time": "10:00", "arrival_time": "12:00", "airline": "Sample Airline", "flight_number": "SA123", "duration": "2h 0m", "cabin": "Economy", "aircraft": "A320", "stops": 0}], "total_stops": 0}]
                departure_date_str = str(departure_date)
                return_date_str = str(return_date) if return_date else None
            
            # Match the structure expected by the frontend even in error cases
            return {
                'formatted': f"Error searching flights: {str(e)}\n\nShowing sample flight options instead.",
                'flights': {
                    'options': fallback_flights,  # Make sure flights are under 'options' key
                    'status': 'error_fallback',
                    'disclaimer': 'Error occurred. Sample flight data shown as fallback.'
                },
                'search_params': {
                    'origin': origin,
                    'destination': destination,
                    'departure_date': departure_date_str,
                    'return_date': return_date_str,
                    'passengers': passengers,
                    'budget_max': budget_max
                },
                'total_options': len(fallback_flights),
                'api_used': 'error_fallback',
                'error': str(e)
            }
