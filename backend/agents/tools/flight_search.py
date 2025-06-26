from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import os
from datetime import datetime, timedelta
from amadeus import Client, ResponseError
import json

class FlightSearchInput(BaseModel):
    """Input for flight search tool"""
    origin: str = Field(description="Origin city or airport code")
    destination: str = Field(description="Destination city or airport code")
    departure_date: str = Field(description="Departure date in YYYY-MM-DD format")
    return_date: Optional[str] = Field(None, description="Return date for round trip")
    passengers: int = Field(1, description="Number of passengers")
    budget_max: Optional[float] = Field(None, description="Maximum budget in INR")

class FlightSearchTool:
    """Tool for searching flight options using Amadeus API"""
    
    def __init__(self):
        self.name = "flight_search"
        self.description = """Search for real flight options between cities using Amadeus API. 
        Use this tool to find flights that match the user's budget and travel dates.
        Returns flight details including airlines, prices, schedules, and booking information."""
        
        # Initialize Amadeus client
        api_key = os.getenv('AMADEUS_API_KEY')
        api_secret = os.getenv('AMADEUS_API_SECRET')
        environment = os.getenv('AMADEUS_ENVIRONMENT', 'test')  # 'test' or 'production'
        
        if not api_key or not api_secret:
            print("⚠️ Warning: Amadeus API credentials not found. Using fallback mode.")
            self.amadeus = None
        else:
            try:
                self.amadeus = Client(
                    client_id=api_key,
                    client_secret=api_secret,
                    hostname='production' if environment == 'production' else 'test'
                )
                print(f"✅ Amadeus API client initialized successfully ({environment} environment)")
                print(f"ℹ️ Note: {environment.title()} environment may have different pricing than live booking sites")
            except Exception as e:
                print(f"❌ Failed to initialize Amadeus client: {e}")
                self.amadeus = None
    
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
            'zurich': 'ZUR', 'switzerland': 'ZUR',
        }
        
        location_lower = location.lower().strip()
        return airport_codes.get(location_lower, location.upper()[:3])
    
    def _search_amadeus_flights(self, origin: str, destination: str, departure_date: str, 
                               passengers: int, return_date: Optional[str] = None) -> List[Dict]:
        """Search flights using Amadeus API"""
        if not self.amadeus:
            print("Amadeus client not initialized, using fallback.")
            return []
        
        try:
            origin_code = self._get_airport_code(origin)
            destination_code = self._get_airport_code(destination)
            
            # Ensure dates are strings
            if hasattr(departure_date, 'strftime'):
                departure_date = departure_date.strftime('%Y-%m-%d')
            
            if return_date and hasattr(return_date, 'strftime'):
                return_date = return_date.strftime('%Y-%m-%d')
            
            # Build search parameters
            search_params = {
                'originLocationCode': origin_code,
                'destinationLocationCode': destination_code,
                'departureDate': departure_date,
                'adults': passengers,
                'max': 5  # Limit to 5 results
            }
            
            if return_date:
                search_params['returnDate'] = return_date
            
            print(f"🔍 Calling Amadeus API with: {search_params}")
            response = self.amadeus.shopping.flight_offers_search.get(**search_params)
            print(f"✅ Amadeus response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Amadeus API error: {response.status_code}")
                return []
            
            print(f"📊 Found {len(response.data)} flight offers")
            return response.data
            
        except ResponseError as error:
            print(f"❌ Amadeus API ResponseError: {error}")
            return []
        except Exception as e:
            print(f"❌ Error searching Amadeus flights: {e}")
            return []
    
    def _format_flight_results_structured(self, amadeus_data: List[Dict], budget_max: Optional[float] = None) -> List[Dict]:
        """Format Amadeus flight data into a structured list of dicts for API/frontend use"""
        print(f"🔍 _format_flight_results_structured called with {len(amadeus_data) if amadeus_data else 0} offers")
        print(f"🔍 Budget max: {budget_max}")
        
        if not amadeus_data:
            print("❌ No amadeus_data provided to _format_flight_results_structured")
            return []
        
        structured_flights = []
        
        for i, offer in enumerate(amadeus_data):
            print(f"🔍 Processing offer {i+1}:")
            try:
                # Extract price information
                price = float(offer['price']['total'])
                currency = offer['price']['currency']
                print(f"   💰 Price: {currency} {price}")
                
                # Convert to INR (simplified conversion rates)
                if currency == 'USD':
                    price_inr = price * 83
                elif currency == 'EUR':
                    price_inr = price * 90
                elif currency == 'GBP':
                    price_inr = price * 105
                else:
                    price_inr = price
                
                print(f"   💰 Price in INR: ₹{price_inr:,.0f}")
                
                # Check budget constraint
                if budget_max and price_inr > budget_max * 0.4:
                    print(f"   ❌ Flight excluded: Price ₹{price_inr:,.0f} exceeds budget limit ₹{budget_max * 0.4:,.0f}")
                    continue
                else:
                    print(f"   ✅ Flight within budget")
                
                # Extract segments information
                segments = []
                all_airlines = set()
                
                for segment in offer['itineraries'][0]['segments']:
                    airline = segment['carrierCode']
                    all_airlines.add(airline)
                    print(f"   ✈️ Segment: {segment['carrierCode']}{segment['number']} ({segment['departure']['iataCode']} → {segment['arrival']['iataCode']})")
                    
                    # Get cabin information if available
                    cabin = 'ECONOMY'  # Default
                    if 'travelerPricings' in offer:
                        for pricing in offer['travelerPricings']:
                            for fare_detail in pricing.get('fareDetailsBySegment', []):
                                if fare_detail['segmentId'] == segment['id']:
                                    cabin = fare_detail.get('cabin', 'ECONOMY')
                                    break
                    
                    segments.append({
                        'flight_number': f"{segment['carrierCode']}{segment['number']}",
                        'airline': segment['carrierCode'],
                        'departure_airport': segment['departure']['iataCode'],
                        'departure_time': segment['departure']['at'],
                        'arrival_airport': segment['arrival']['iataCode'],
                        'arrival_time': segment['arrival']['at'],
                        'duration': segment.get('duration', ''),
                        'cabin': cabin,
                        'aircraft': segment.get('aircraft', {}).get('code', ''),
                        'stops': 0 if len(offer['itineraries'][0]['segments']) == 1 else len(offer['itineraries'][0]['segments']) - 1
                    })
                
                # Create structured flight data
                flight_data = {
                    'id': offer.get('id', ''),
                    'price_inr': round(price_inr, 2),
                    'price_original': price,
                    'currency': currency,
                    'airlines': list(all_airlines),
                    'total_duration': offer['itineraries'][0]['duration'],
                    'segments': segments,
                    'total_stops': len(segments) - 1,
                    'validating_airlines': offer.get('validatingAirlineCodes', []),
                    'bookable_seats': offer.get('numberOfBookableSeats', 0),
                    'instant_ticketing_required': offer.get('instantTicketingRequired', False),
                    'last_ticketing_date': offer.get('lastTicketingDate', ''),
                    'fare_type': offer.get('pricingOptions', {}).get('fareType', ['PUBLISHED'])[0] if offer.get('pricingOptions', {}).get('fareType') else 'PUBLISHED',
                    'price_disclaimer': 'API pricing may differ from booking sites',
                    'api_source': 'Amadeus',
                    'environment': os.getenv('AMADEUS_ENVIRONMENT', 'test')
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
        result_lines.append("✈️ REAL FLIGHT OPTIONS (Powered by Amadeus)")
        result_lines.append("=" * 55)
        
        for i, flight in enumerate(structured_flights[:3], 1):  # Show top 3
            # Get main route info
            first_segment = flight['segments'][0]
            last_segment = flight['segments'][-1]
            
            # Format times
            dep_time = datetime.fromisoformat(first_segment['departure_time'].replace('Z', '+00:00')).strftime('%H:%M')
            arr_time = datetime.fromisoformat(last_segment['arrival_time'].replace('Z', '+00:00')).strftime('%H:%M')
            
            # Format duration
            duration = flight['total_duration'].replace('PT', '').replace('H', 'h ').replace('M', 'm').lower()
            
            # Stops info
            stops_text = "Direct" if flight['total_stops'] == 0 else f"{flight['total_stops']} stop(s)"
            
            result_lines.append(f"\n🎫 OPTION {i}: {' & '.join(flight['airlines'])}")
            result_lines.append(f"   Route: {first_segment['departure_airport']} → {last_segment['arrival_airport']}")
            result_lines.append(f"   Time: {dep_time} - {arr_time} ({duration})")
            result_lines.append(f"   Stops: {stops_text}")
            result_lines.append(f"   Price: ₹{flight['price_inr']:,.0f} ({flight['currency']} {flight['price_original']})")
            result_lines.append(f"   Cabin: {flight['segments'][0]['cabin']}")
            
            if flight['bookable_seats'] > 0:
                result_lines.append(f"   Seats: {flight['bookable_seats']} available")
        
        result_lines.append(f"\n⚠️ IMPORTANT PRICING DISCLAIMER:")
        result_lines.append(f"   • Amadeus API prices may differ from booking sites")
        result_lines.append(f"   • Actual prices can vary based on booking time, availability")
        result_lines.append(f"   • These are reference prices for planning purposes")
        result_lines.append(f"   • Always verify final price when booking")
        result_lines.append(f"\n💡 Flight details (times, routes) are accurate from Amadeus")
        result_lines.append(f"🔄 Book through travel agencies or airline websites")
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
        
        result_lines.append(f"\n⚠️ Sample data - Connect Amadeus API for real flights")
        return "\n".join(result_lines)
    
    def _run(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        passengers: int = 1,
        budget_max: Optional[float] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute the flight search using Amadeus API and return both formatted string and structured data"""
        
        print(f"🚀 Starting flight search: {origin} → {destination} on {departure_date}")
        print(f"📊 Search params - Passengers: {passengers}, Budget: {budget_max}")
        
        try:
            # Search flights using Amadeus API
            amadeus_results = self._search_amadeus_flights(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                passengers=passengers,
                return_date=return_date
            )
            
            print(f"🔍 Raw Amadeus results count: {len(amadeus_results)}")
            
            # Format structured data for frontend
            structured_flights = self._format_flight_results_structured(amadeus_results, budget_max)
            
            print(f"📋 Structured flights count after processing: {len(structured_flights)}")
            print(f"💰 Budget constraint applied: {budget_max}")
            
            # Log each structured flight for debugging
            for i, flight in enumerate(structured_flights):
                print(f"✈️ Flight {i+1}: {flight['airlines']} - ₹{flight['price_inr']:,.0f} ({flight['currency']} {flight['price_original']})")
                print(f"   Segments: {len(flight['segments'])}, Stops: {flight['total_stops']}")
                for j, segment in enumerate(flight['segments']):
                    print(f"   Segment {j+1}: {segment['flight_number']} {segment['departure_airport']}→{segment['arrival_airport']}")
            
            # Format text for LLM
            formatted_text = self._format_flight_results_text(structured_flights)
            
            # Ensure dates are strings for JSON serialization
            departure_date_str = departure_date.strftime('%Y-%m-%d') if hasattr(departure_date, 'strftime') else str(departure_date)
            return_date_str = return_date.strftime('%Y-%m-%d') if return_date and hasattr(return_date, 'strftime') else str(return_date) if return_date else None
            
            result = {
                'formatted': formatted_text,
                'flights': structured_flights,
                'search_params': {
                    'origin': origin,
                    'destination': destination,
                    'departure_date': departure_date_str,
                    'return_date': return_date_str,
                    'passengers': passengers,
                    'budget_max': budget_max
                },
                'total_options': len(structured_flights),
                'api_used': 'amadeus' if self.amadeus else 'fallback'
            }
            
            print(f"✅ FlightSearchTool returning {len(structured_flights)} flights to TripPlannerAgent")
            print(f"🎯 Result structure: formatted={type(result['formatted'])}, flights={type(result['flights'])}, count={len(result['flights'])}")
            return result
            
        except Exception as e:
            print(f"❌ Error in flight search: {e}")
            
            # Ensure dates are strings for JSON serialization
            departure_date_str = departure_date.strftime('%Y-%m-%d') if hasattr(departure_date, 'strftime') else str(departure_date)
            return_date_str = return_date.strftime('%Y-%m-%d') if return_date and hasattr(return_date, 'strftime') else str(return_date) if return_date else None
            
            return {
                'formatted': self._get_fallback_results(),
                'flights': [],
                'search_params': {
                    'origin': origin,
                    'destination': destination,
                    'departure_date': departure_date_str,
                    'return_date': return_date_str,
                    'passengers': passengers,
                    'budget_max': budget_max
                },
                'total_options': 0,
                'api_used': 'fallback',
                'error': str(e)
            }
