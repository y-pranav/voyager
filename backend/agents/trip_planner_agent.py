from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Dict, Any, List
import asyncio
import json
import os
import re
import random

from models.trip_request import TripRequest
from agents.tools.flight_search import FlightSearchTool
from agents.tools.hotel_search import HotelSearchTool
from agents.tools.attraction_search import AttractionSearchTool
from agents.tools.restaurant_search import RestaurantSearchTool
from agents.tools.weather_info import WeatherInfoTool
from agents.tools.currency_converter import CurrencyConverterTool
from utils.logger import setup_logger

logger = setup_logger()

class TripPlannerAgent:
    """
    Main trip planning agent using Google Gemini
    
    This agent coordinates the entire trip planning process:
    1. Goal interpretation
    2. Task breakdown
    3. Tool execution
    4. Itinerary generation    """
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.1,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        
        # Initialize tools
        self.tools = {
            "flight_search": FlightSearchTool(),
            "hotel_search": HotelSearchTool(),
            "attraction_search": AttractionSearchTool(),
            "restaurant_search": RestaurantSearchTool(),
            "weather_info": WeatherInfoTool(),
            "currency_converter": CurrencyConverterTool()
        }
        
        # Conversation history
        self.conversation_history = []
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the agent"""
        return """You are an expert AI trip planner agent. Your role is to create comprehensive, personalized travel itineraries.

## Your Process:
1. **Goal Interpretation**: Understand the user's travel goals, budget, and preferences
2. **Task Breakdown**: Break down the trip into subtasks (flights, hotels, attractions, etc.)
3. **Information Gathering**: Use available tools to search for flights, hotels, attractions, etc.
4. **Decision Making**: Make informed decisions based on budget constraints and preferences
5. **Itinerary Generation**: Create a detailed day-by-day itinerary

## Available Tools:
- flight_search: Search for flights between destinations
- hotel_search: Find accommodation options
- attraction_search: Discover tourist attractions and activities
- restaurant_search: Find dining options
- weather_info: Get weather information for planning
- currency_converter: Convert currencies for budget planning

## Guidelines:
- Always consider the user's budget constraints
- Provide realistic time estimates for activities
- Include transportation between locations
- Suggest backup options when possible
- Be specific with times, locations, and costs
- Create a balanced itinerary with variety

## Tool Usage Format:
When you need to use a tool, format your request as:
TOOL_CALL: tool_name
PARAMETERS: {"param1": "value1", "param2": "value2"}

## Output Format:
Generate a structured JSON itinerary with:
- Daily schedules with timings
- Cost breakdown
- Transportation details
- Accommodation information
- Restaurant recommendations
- Activity details with descriptions

Remember: You're an autonomous agent - make decisions confidently based on the available information and tools."""

    async def plan_trip(self, session_id: str, request: TripRequest) -> Dict[str, Any]:
        """
        Main method to plan a trip using the agent
        
        Args:
            session_id: Unique session identifier
            request: Trip planning request
            
        Returns:
            Complete trip itinerary as a dictionary
        """
        try:
            logger.info(f"Starting trip planning for session {session_id}")
            
            # Create detailed planning prompt
            planning_prompt = self._create_planning_prompt(request)
            
            # Execute the agent step by step
            result = await self._execute_planning_process(planning_prompt, request)
            
            # Structure the result
            itinerary = self._structure_itinerary(result, request)
            
            logger.info(f"Trip planning completed for session {session_id}")
            return itinerary
            
        except Exception as e:
            logger.error(f"Error in trip planning: {str(e)}")
            raise

    def _create_planning_prompt(self, request: TripRequest) -> str:
        """Create a detailed planning prompt from the request"""
        interests_str = ", ".join(request.interests) if request.interests else "general sightseeing"
        
        prompt = f"""
Plan a comprehensive {request.duration_days}-day trip to {request.destination} with the following requirements:

**Budget**: ₹{request.budget:,.0f} INR total
**Travelers**: {request.travelers} person(s)
**Duration**: {request.duration_days} days
**Start Date**: {request.start_date or 'Flexible'}
**Interests**: {interests_str}
**Accommodation Type**: {request.accommodation_type}
**Transport Mode**: {request.transport_mode}
**Special Requirements**: {request.special_requirements or 'None'}

Please follow this process step by step:

1. First, search for flights to {request.destination} within budget
2. Then, find accommodation options that fit the budget and preferences  
3. Research attractions based on interests: {interests_str}
4. Find restaurants for dining experiences
5. Check weather for appropriate planning
6. Calculate costs and ensure everything fits within ₹{request.budget:,.0f}

Create a detailed day-by-day itinerary with:
- Specific timings for each activity
- Transportation between locations
- Meal recommendations
- Cost breakdown for each day
- Alternative options if something is unavailable

Make sure the total cost does not exceed the budget of ₹{request.budget:,.0f}.

Start by using the tools to gather information, then create the final itinerary.
"""
        return prompt

    async def _execute_planning_process(self, prompt: str, request: TripRequest) -> Dict[str, Any]:
        """Execute the planning process step by step"""
        
        # Start with the system prompt and user request
        full_prompt = self._create_system_prompt() + "\n\n" + prompt
        
        # Step 1: Get initial plan from Gemini
        response = await self._call_gemini(full_prompt)
        
        # Step 2: Execute any tool calls found in the response
        tool_results = await self._execute_tool_calls(response, request)
        
        # Step 3: Get final itinerary with tool results
        final_prompt = f"""
Based on the following tool results, create a detailed JSON itinerary:

{json.dumps(tool_results, indent=2)}

Create a comprehensive itinerary in JSON format with the structure:
{{
    "destination": "{request.destination}",
    "total_days": {request.duration_days},
    "total_cost": <calculated_total>,
    "currency": "INR",
    "daily_itinerary": [
        {{
            "day": 1,
            "date": "Day 1",
            "activities": [...],
            "meals": [...],
            "accommodation": {{}},
            "estimated_cost": <cost>
        }}
    ],
    "flights": {{}},
    "accommodation_summary": {{}},
    "cost_breakdown": {{}},
    "recommendations": []
}}

Make sure all costs fit within the budget of ₹{request.budget:,.0f}.
"""
        
        final_response = await self._call_gemini(final_prompt)
        
        return {
            "initial_response": response,
            "tool_results": tool_results,
            "final_itinerary": final_response
        }

    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini with the given prompt"""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.llm.invoke(prompt).content
            )
            return response
        except Exception as e:
            logger.error(f"Error calling Gemini: {str(e)}")
            return f"Error: {str(e)}"

    async def _execute_tool_calls(self, response: str, request: TripRequest) -> Dict[str, Any]:
        """Execute tool calls found in the response"""
        tool_results = {}
        
        # Execute each tool with appropriate parameters
        try:
            print(f"🔧 Executing tool calls for {request.destination}")
            print(f"🛠️ use_real_api setting: {request.use_real_api}")
            
            # Flight search
            flight_tool = self.tools["flight_search"]
            print(f"🛫 Calling flight search tool...")
            print(f"🌍 Using source: {request.source}, destination: {request.destination}")
            flight_result = flight_tool._run(
                origin=request.source,  # Use the source location from the request
                destination=request.destination,
                departure_date=request.start_date or "2025-06-28",
                passengers=request.travelers,
                budget_max=request.budget,
                use_real_api=request.use_real_api
            )
            
            print(f"📊 Flight tool returned: {type(flight_result)}")
            print(f"🔍 Flight result keys: {list(flight_result.keys()) if isinstance(flight_result, dict) else 'Not a dict'}")
            
            if isinstance(flight_result, dict):
                if 'flights' in flight_result and isinstance(flight_result['flights'], dict) and 'options' in flight_result['flights']:
                    # Already has the correct structure with flights.options
                    print(f"✈️ Found {len(flight_result['flights']['options'])} structured flights")
                    tool_results["flights"] = flight_result['flights']
                    print(f"🎯 Stored flights in tool_results with {len(flight_result['flights']['options'])} options")
                elif 'flights' in flight_result and isinstance(flight_result['flights'], list):
                    # Handle case where flights is a direct list of options
                    print(f"✈️ Found {len(flight_result['flights'])} structured flights")
                    tool_results["flights"] = {
                        "formatted": flight_result.get("formatted", ""),
                        "options": flight_result["flights"],  # This is what frontend expects
                        "status": "sample_data",
                        "disclaimer": "Sample flight data for demonstration purposes"
                    }
                    print(f"🎯 Stored flights in tool_results with {len(flight_result['flights'])} options")
                else:
                    print(f"⚠️ Unexpected flight result structure, trying to adapt")
                    tool_results["flights"] = {
                        "formatted": flight_result.get("formatted", ""),
                        "options": flight_result.get("flights", []),
                        "status": "adapted_data",
                        "disclaimer": "Sample flight data (adapted format)"
                    }
            else:
                print(f"❌ Unexpected flight result format: {flight_result}")
                tool_results["flights"] = {"formatted": str(flight_result), "options": []}
            
            # Hotel search
            hotel_tool = self.tools["hotel_search"]
            
            # Calculate proper check-in and check-out dates
            from datetime import datetime, timedelta, date
            
            # Handle the start date properly regardless of type (string or date)
            if isinstance(request.start_date, date):
                # It's already a date object
                start_date = request.start_date
                start_date_str = start_date.strftime("%Y-%m-%d")
            elif isinstance(request.start_date, str) and request.start_date:
                # It's a string, parse it
                try:
                    start_date = datetime.strptime(request.start_date, "%Y-%m-%d").date()
                    start_date_str = request.start_date
                except:
                    # Invalid string format, use default
                    start_date = datetime.now().date()
                    start_date_str = start_date.strftime("%Y-%m-%d")
            else:
                # No start date provided or invalid type, use default
                start_date = datetime.now().date()
                start_date_str = start_date.strftime("%Y-%m-%d")
                
            # Calculate checkout date
            try:
                # Calculate check-out date based on duration
                end_date = start_date + timedelta(days=request.duration_days)
                # Format to string
                check_out_date_str = end_date.strftime("%Y-%m-%d")
                print(f"✅ Calculated dates: {start_date_str} to {check_out_date_str}")
            except Exception as e:
                print(f"⚠️ Error calculating checkout date: {str(e)}")
                # Fallback to default dates if there's an issue
                end_date = start_date + timedelta(days=3)
                check_out_date_str = end_date.strftime("%Y-%m-%d")
            
            hotel_result = hotel_tool._run(
                location=request.destination,
                check_in_date=start_date_str,
                check_out_date=check_out_date_str,
                guests=request.travelers,
                hotel_type=request.accommodation_type,
                use_real_api=request.use_real_api
            )
            tool_results["hotels"] = hotel_result
            
            # Attraction search
            attraction_tool = self.tools["attraction_search"]
            attraction_result = attraction_tool._run(
                location=request.destination,
                interests=request.interests
            )
            tool_results["attractions"] = attraction_result
            
            # Restaurant search
            restaurant_tool = self.tools["restaurant_search"]
            restaurant_result = restaurant_tool._run(
                location=request.destination,
                cuisine_type="local"
            )
            tool_results["restaurants"] = restaurant_result
            
            # Weather info
            weather_tool = self.tools["weather_info"]
            weather_result = weather_tool._run(
                location=request.destination,
                date=request.start_date
            )
            tool_results["weather"] = weather_result
            
        except Exception as e:
            logger.error(f"Error executing tools: {str(e)}")
            tool_results["error"] = str(e)
        
        return tool_results

    def _structure_itinerary(self, agent_result: Dict[str, Any], request: TripRequest) -> Dict[str, Any]:
        """Structure the agent result into a proper itinerary format"""
        try:
            print(f"🏗️ Structuring itinerary for {request.destination}")
            
            # Extract the final itinerary from agent result
            final_response = agent_result.get("final_itinerary", "")
            tool_results = agent_result.get("tool_results", {})
            
            print(f"📋 Tool results keys: {list(tool_results.keys())}")
            
            # Get flight data from tool results
            flight_data = tool_results.get("flights", {})
            print(f"✈️ Flight data type: {type(flight_data)}")
            print(f"🔍 Flight data keys: {list(flight_data.keys()) if isinstance(flight_data, dict) else 'Not a dict'}")
            
            # Ensure flight data always has the expected structure for the frontend
            if isinstance(flight_data, dict) and "options" in flight_data and isinstance(flight_data["options"], list):
                # Already in correct format
                flight_structured = flight_data
                print(f"✅ Using structured flight data with {len(flight_data['options'])} options")
            elif isinstance(flight_data, dict) and 'flights' in flight_data:
                # Legacy format: flight_data.flights is the options array
                print(f"🔄 Converting flight data from legacy format...")
                flight_options = flight_data.get("flights", [])
                if isinstance(flight_options, list):
                    flight_structured = {
                        "formatted": flight_data.get("formatted", ""),
                        "options": flight_options,
                        "status": flight_data.get("status", "sample_data"),
                        "disclaimer": flight_data.get("disclaimer", "Sample flight data")
                    }
                else:
                    # Handle nested structure
                    flight_structured = {
                        "formatted": flight_data.get("formatted", ""),
                        "options": flight_options.get("options", []) if isinstance(flight_options, dict) else [],
                        "status": flight_options.get("status", "sample_data") if isinstance(flight_options, dict) else "sample_data",
                        "disclaimer": flight_options.get("disclaimer", "Sample flight data") if isinstance(flight_options, dict) else "Sample flight data"
                    }
                print(f"🔧 Converted to {len(flight_structured['options'])} options")
            elif isinstance(flight_data, list):
                # Direct array of flight options
                print(f"🔄 Converting flight data from direct list...")
                flight_structured = {
                    "options": flight_data,
                    "status": "sample_data",
                    "disclaimer": "Sample flight data for demonstration purposes"
                }
                print(f"🔧 Converted direct list to {len(flight_structured['options'])} options")
            else:
                # Emergency fallback
                print(f"⚠️ Using empty flight data structure")
                flight_structured = {
                    "options": [],
                    "status": "error",
                    "disclaimer": "No flight data available"
                }
                print(f"⚠️ No valid flight options found")
            
            # Try to parse JSON from the response
            try:
                # Look for JSON in the response
                json_match = re.search(r'\{.*\}', final_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    structured_data = json.loads(json_str)
                else:
                    structured_data = self._create_fallback_structure(final_response, request)
            except Exception as e:
                # If JSON parsing fails, create structure from text
                print(f"⚠️ Failed to parse JSON from Gemini response: {str(e)}")
                structured_data = self._create_fallback_structure(final_response, request)
            
            # Extract hotel data if available
            hotel_structured = None
            if "hotels" in tool_results:
                print(f"🔍 DEBUG hotel_result structure: {list(tool_results['hotels'].keys())}")
                
                if isinstance(tool_results["hotels"], dict) and "hotels" in tool_results["hotels"]:
                    # The hotel data is structured correctly with nested "hotels" key
                    hotel_structured = tool_results["hotels"]["hotels"]
                    print(f"✅ Using structured hotel data with {len(hotel_structured.get('options', []))} options")
                elif isinstance(tool_results["hotels"], dict):
                    # Direct structure without nested "hotels" key - create proper structure
                    if "options" in tool_results["hotels"]:
                        # Already has options directly
                        hotel_structured = {
                            "options": tool_results["hotels"]["options"],
                            "status": tool_results["hotels"].get("status", "sample_data"),
                            "disclaimer": tool_results["hotels"].get("disclaimer", "Hotel options for your stay")
                        }
                    else:
                        # Try to extract options from potential nested structure
                        options = []
                        if "hotels" in tool_results["hotels"]:
                            if isinstance(tool_results["hotels"]["hotels"], dict) and "options" in tool_results["hotels"]["hotels"]:
                                options = tool_results["hotels"]["hotels"]["options"]
                            elif isinstance(tool_results["hotels"]["hotels"], list):
                                options = tool_results["hotels"]["hotels"]
                        
                        hotel_structured = {
                            "options": options,
                            "status": tool_results["hotels"].get("status", "sample_data"),
                            "disclaimer": tool_results["hotels"].get("disclaimer", "Hotel options for your stay")
                        }
                    
                    print(f"🔄 Adapted hotel data structure with {len(hotel_structured['options'])} options")
            
            # Create emergency hotel data if needed as fallback
            if hotel_structured is None or not hotel_structured.get('options') or len(hotel_structured.get('options', [])) == 0:
                print("⚠️ No valid hotel data found, creating fallback hotel data")
                hotel_fallback = self._create_fallback_hotels(request)
                hotel_structured = {
                    "options": hotel_fallback,
                    "status": "sample_data",
                    "disclaimer": "Sample hotel data (fallback)"
                }
                print(f"✅ Created fallback hotel data with {len(hotel_structured['options'])} options")
                
            # Enhance the daily itinerary with more descriptive content
            daily_itinerary = structured_data.get("daily_itinerary", [])
            
            # If we have a valid daily itinerary from Gemini, enhance it with hotel info
            if daily_itinerary and isinstance(daily_itinerary, list):
                print(f"📆 Found {len(daily_itinerary)} days in Gemini-generated itinerary")
                # If we have hotel options, link them to the daily itinerary
                if hotel_structured and hotel_structured.get('options'):
                    # Use the first hotel option as the selected hotel for the itinerary
                    selected_hotel = hotel_structured['options'][0] if hotel_structured['options'] else None
                    
                    if selected_hotel:
                        # Add hotel details to each day's accommodation
                        for day in daily_itinerary:
                            if "accommodation" not in day or not day["accommodation"]:
                                day["accommodation"] = {
                                    "name": selected_hotel.get("name", "Selected Hotel"),
                                    "rating": selected_hotel.get("rating", 4.0),
                                    "price_per_night": selected_hotel.get("price_per_night", 0),
                                    "total_price": selected_hotel.get("total_price", 0),
                                    "address": selected_hotel.get("address", ""),
                                    "location": selected_hotel.get("location", ""),
                                    "amenities": selected_hotel.get("amenities", []),
                                    "hotel_id": selected_hotel.get("id", "hotel_1")
                                }
            else:
                # If no daily itinerary was generated by Gemini, create a more detailed fallback
                print("⚠️ No valid daily itinerary found, creating enhanced fallback itinerary")
                daily_itinerary = self._create_enhanced_daily_itinerary(request, hotel_structured)
                
            # Ensure required fields are present
            itinerary = {
                "destination": request.destination,
                "total_days": request.duration_days,
                "total_cost": structured_data.get("total_cost", request.budget * 0.8),
                "currency": "INR",
                "daily_itinerary": daily_itinerary,  # Use the enhanced daily itinerary
                "flights": flight_structured,  # Use properly structured flight data
                "hotels": hotel_structured,    # Add structured hotel data
                "accommodation_summary": structured_data.get("accommodation_summary", {}),
                "cost_breakdown": structured_data.get("cost_breakdown", {}),
                "recommendations": structured_data.get("recommendations", []),
                "tool_results": {k: v for k, v in tool_results.items() if k not in ["flights", "hotels"]}  # Avoid duplicates
            }
            
            print(f"🎯 Final itinerary flights: {len(itinerary['flights'].get('options', []))} options")
            print(f"📤 Sending to frontend - flights type: {type(itinerary['flights'])}")
            
            # Log final flight data being sent to frontend
            if itinerary['flights'].get('options'):
                for i, flight in enumerate(itinerary['flights']['options'][:3]):
                    print(f"📤 Frontend Flight {i+1}: {flight.get('airlines', [])} - ₹{flight.get('price_inr', 0):,.0f}")
                    
            # Log hotel data
            if itinerary.get('hotels') and itinerary['hotels'].get('options'):
                print(f"🏨 Final itinerary hotels: {len(itinerary['hotels'].get('options', []))} options")
                for i, hotel in enumerate(itinerary['hotels']['options'][:3]):
                    print(f"🏨 Frontend Hotel {i+1}: {hotel.get('name', '')} - ₹{hotel.get('price_per_night', 0):,.0f}/night")
            
            # Add debug info for frontend
            print("\n🔍 FINAL ITINERARY STRUCTURE:")
            print(f"- flights: {type(itinerary['flights'])} with {len(itinerary['flights'].get('options', []))} options")
            print(f"- Has flights.options? {'options' in itinerary['flights']}")
            print(f"- First flight airline: {itinerary['flights'].get('options', [{}])[0].get('airlines', []) if itinerary['flights'].get('options') else 'N/A'}")
            print(f"- Daily itinerary days: {len(itinerary['daily_itinerary'])}")
            
            # Ensure flights.options always exists
            if 'flights' in itinerary and not itinerary['flights'].get('options'):
                print("⚠️ Adding empty options array to flights")
                itinerary['flights']['options'] = []
            
            return itinerary
            
        except Exception as e:
            logger.error(f"Error structuring itinerary: {str(e)}")
            # Return a basic structure if everything fails
            return self._create_emergency_fallback(request)

    def _get_airport_code(self, location: str) -> str:
        """Convert city name to IATA airport code for fallback scenarios"""
        # Common airport mappings
        airport_codes = {
            # India
            'delhi': 'DEL', 'new delhi': 'DEL',
            'mumbai': 'BOM', 'bombay': 'BOM',
            'bangalore': 'BLR', 'bengaluru': 'BLR',
            'chennai': 'MAA', 'madras': 'MAA',
            'hyderabad': 'HYD',
            'kolkata': 'CCU', 'calcutta': 'CCU',
            'goa': 'GOI',
            
            # International
            'tokyo': 'NRT', 'japan': 'NRT',
            'london': 'LHR', 'uk': 'LHR',
            'paris': 'CDG', 'france': 'CDG',
            'new york': 'JFK', 'nyc': 'JFK',
            'dubai': 'DXB', 'uae': 'DXB',
            'singapore': 'SIN',
            'bangkok': 'BKK', 'thailand': 'BKK',
            'sydney': 'SYD', 'australia': 'SYD'
        }
        
        location_lower = location.lower().strip()
        return airport_codes.get(location_lower, location.upper()[:3])

    def _create_fallback_structure(self, output: str, request: TripRequest) -> Dict[str, Any]:
        """Create a basic structure when JSON parsing fails"""
        print("📄 Creating fallback structure for itinerary using enhanced daily itinerary")
        
        # Create hotel fallback data for the enhanced daily itinerary
        hotel_fallback = self._create_fallback_hotels(request)
        hotel_structured = {
            "options": hotel_fallback,
            "status": "sample_data",
            "disclaimer": "Sample hotel data (fallback)"
        }
        
        # Generate an enhanced daily itinerary using our new method
        daily_itinerary = self._create_enhanced_daily_itinerary(request, hotel_structured)
        
        # Create flight fallback
        flight_fallback = {
            "options": [{
                "id": "fallback1",
                "price_inr": float(request.budget * 0.25),
                "currency": "INR",
                "airlines": ["Sample Airline"],
                "total_duration": "PT2H0M",
                "segments": [{
                    "departure_airport": self._get_airport_code(request.source),
                    "arrival_airport": self._get_airport_code(request.destination),
                    "departure_time": "10:00",
                    "arrival_time": "12:00",
                    "airline": "Sample Airline",
                    "flight_number": "SA123",
                    "duration": "2h 0m",
                    "cabin": "Economy",
                    "aircraft": "A320",
                    "stops": 0
                }],
                "total_stops": 0
            }],
            "status": "fallback",
            "disclaimer": "Sample fallback flight data"
        }
        
        # Calculate costs from daily itinerary
        total_cost = sum(day.get("estimated_cost", 0) for day in daily_itinerary)
        
        # Create cost breakdown
        cost_breakdown = {
            "flights": request.budget * 0.3,
            "accommodation": request.budget * 0.4,
            "activities": request.budget * 0.15,
            "meals": request.budget * 0.15
        }
        
        # Summary of the accommodation
        accommodation_summary = {
            "type": request.accommodation_type,
            "total_cost": cost_breakdown["accommodation"],
            "nights": request.duration_days,
            "selected": hotel_structured["options"][0].get("name", "Hotel") if hotel_structured["options"] else "Hotel"
        }
        
        return {
            "destination": request.destination,
            "total_days": request.duration_days,
            "total_cost": total_cost,
            "currency": "INR",
            "daily_itinerary": daily_itinerary,
            "flights": flight_fallback,
            "accommodation_summary": accommodation_summary,
            "cost_breakdown": cost_breakdown,
            "recommendations": [
                "Book flights and accommodation early for better rates",
                f"Consider visiting {request.destination} during shoulder season for fewer crowds",
                "Try the local cuisine for an authentic experience",
                "Use public transportation to save on travel costs"
            ],
            "raw_output": output
        }
    
    def _create_fallback_hotels(self, request: TripRequest) -> List[Dict[str, Any]]:
        """Create fallback hotel options for when hotel search returns no results"""
        import random
        from datetime import datetime, timedelta
        
        # Map country names to cities for better display
        destination = request.destination
        if destination.upper() == "JAPAN":
            cities = ["Tokyo", "Kyoto", "Osaka", "Hiroshima"]
        elif destination.upper() == "INDIA":
            cities = ["Mumbai", "Delhi", "Bangalore", "Chennai"]
        elif destination.upper() in ["USA", "UNITED STATES"]:
            cities = ["New York", "Los Angeles", "Chicago", "Miami"]
        elif destination.upper() in ["UK", "UNITED KINGDOM"]:
            cities = ["London", "Manchester", "Edinburgh", "Liverpool"]
        elif destination.upper() == "AUSTRALIA":
            cities = ["Sydney", "Melbourne", "Brisbane", "Perth"]
        else:
            cities = [destination]  # Use the original destination
        
        hotel_types = {
            "budget": {
                "names": ["Budget Inn", "City Stay", "Traveler Lodge", "Value Hotel", "Economy Suites"],
                "stars": [2, 3],
                "price_range": [1500, 3000],
                "amenities": ["WiFi", "24-hour Front Desk", "Air Conditioning"]
            },
            "hotel": {
                "names": ["Grand Hotel", "Plaza Hotel", "City Center Hotel", "Comfort Hotel", "Downtown Inn"],
                "stars": [3, 4],
                "price_range": [3500, 8000],
                "amenities": ["WiFi", "Pool", "Restaurant", "Room Service", "Fitness Center"]
            },
            "luxury": {
                "names": ["Royal Palace", "Grand Luxury Resort", "Premium Suites", "Five Star Hotel", "Elite Residences"],
                "stars": [4, 5],
                "price_range": [9000, 20000],
                "amenities": ["WiFi", "Pool", "Spa", "Multiple Restaurants", "Fitness Center", "Concierge", "Room Service"]
            },
            "resort": {
                "names": ["Beach Resort", "Mountain Retreat", "Vacation Resort", "Paradise Getaway", "Sunrise Resort"],
                "stars": [4, 5],
                "price_range": [8000, 18000],
                "amenities": ["WiFi", "Pool", "Spa", "Beach Access", "Multiple Restaurants", "Activities"]
            }
        }
        
        # Choose the right hotel type based on request
        hotel_type = request.accommodation_type.lower() if request.accommodation_type else "hotel"
        if hotel_type not in hotel_types:
            hotel_type = "hotel"  # default
            
        # Create 5-8 hotel options
        num_hotels = random.randint(5, 8)
        hotels = []
        
        for i in range(num_hotels):
            city = random.choice(cities)
            hotel_config = hotel_types[hotel_type]
            
            star_level = random.choice(hotel_config["stars"])
            price_min, price_max = hotel_config["price_range"]
            price_per_night = random.randint(price_min, price_max)
            
            if star_level >= 4:
                rating = round(random.uniform(3.9, 4.9), 1)
            else:
                rating = round(random.uniform(3.0, 4.3), 1)
                
            # Calculate total price based on duration
            nights = request.duration_days if request.duration_days else 3
            total_price = price_per_night * nights
            
            # Create a unique name
            hotel_name = f"{random.choice(hotel_config['names'])} {city}"
            if i > 0 and any(h['name'] == hotel_name for h in hotels):
                hotel_name += f" {chr(65 + i)}"  # Add A, B, C, etc.
                
            hotel = {
                "id": f"hotel_{i+1}",
                "name": hotel_name,
                "rating": float(rating),
                "star_level": star_level,
                "price_per_night": float(price_per_night),
                "currency": "INR",
                "total_price": float(total_price),
                "amenities": hotel_config["amenities"][:3 + i % 3],  # Vary amenities slightly
                "room_type": random.choice(["Deluxe Room", "Standard Room", "Superior Room", "Suite"]),
                "location": f"{city} - {random.choice(['City Center', 'Downtown', 'Tourist District'])}",
                "address": f"{random.randint(1, 999)} {random.choice(['Main Street', 'Park Road', 'Tourism Avenue'])}",
                "distance_to_center": float(random.uniform(0.3, 5.0)),
                "breakfast_included": random.choice([True, False]),
                "refundable": random.choice([True, False]),
                "cancellation_policy": random.choice(["Free cancellation", "Non-refundable", "24-hour cancellation"]),
                "images": [
                    f"https://example.com/hotel_{i+1}_image1.jpg",
                    f"https://example.com/hotel_{i+1}_image2.jpg"
                ],
                "availability": "Available",
                "reviews_count": random.randint(50, 2000),
                "property_type": hotel_type.capitalize()
            }
            hotels.append(hotel)
        
        # Sort by a calculated value score (better rating and lower price is better)
        for hotel in hotels:
            price_factor = 1.0 - (hotel["price_per_night"] / max(h["price_per_night"] for h in hotels))
            hotel["value_score"] = (hotel["rating"] / 5) * 0.6 + price_factor * 0.4
            
        hotels.sort(key=lambda x: -x["value_score"])
        print(f"✅ Created {len(hotels)} fallback hotels (best: {hotels[0]['name']})")
        return hotels

    def _create_emergency_fallback(self, request: TripRequest) -> Dict[str, Any]:
        """Emergency fallback when everything fails"""
        return {
            "destination": request.destination,
            "total_days": request.duration_days,
            "total_cost": 0,
            "currency": "INR",
            "daily_itinerary": [],
            "flights": {},
            "accommodation_summary": {},
            "cost_breakdown": {},
            "recommendations": [],
            "error": "Failed to generate itinerary - please try again"
        }
    
    def _create_enhanced_daily_itinerary(self, request: TripRequest, hotel_structured: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create a more descriptive daily itinerary when Gemini doesn't provide enough detail"""
        from datetime import datetime, timedelta
        import random
        
        # Get top hotel if available
        selected_hotel = None
        if hotel_structured and hotel_structured.get('options') and len(hotel_structured['options']) > 0:
            selected_hotel = hotel_structured['options'][0]
            
        # Get attractions and restaurants from tool results if available
        attractions = []
        if "attractions" in self.tools:
            try:
                # Try to get some attraction data
                attraction_result = self.tools["attraction_search"]._run(
                    location=request.destination,
                    interests=request.interests
                )
                if isinstance(attraction_result, dict) and "attractions" in attraction_result:
                    attractions = attraction_result["attractions"]
            except Exception as e:
                print(f"⚠️ Error getting attractions for enhanced itinerary: {str(e)}")
                
        # If no attractions, create dummy ones
        if not attractions:
            attractions = [
                {
                    "name": f"{request.destination} Museum of Art",
                    "description": "A world-class museum featuring local and international art exhibitions.",
                    "rating": 4.7,
                    "estimated_duration": "2 hours",
                    "category": "Museum"
                },
                {
                    "name": f"{request.destination} Historical District",
                    "description": "Explore the historic streets and architecture of the old city center.",
                    "rating": 4.5,
                    "estimated_duration": "3 hours",
                    "category": "Sightseeing"
                },
                {
                    "name": f"{request.destination} Central Park",
                    "description": "A beautiful urban park perfect for relaxation and outdoor activities.",
                    "rating": 4.6,
                    "estimated_duration": "2 hours",
                    "category": "Nature"
                },
                {
                    "name": f"Local Market of {request.destination}",
                    "description": "Vibrant market where you can shop for local crafts and try regional delicacies.",
                    "rating": 4.4,
                    "estimated_duration": "2 hours",
                    "category": "Shopping"
                },
                {
                    "name": f"{request.destination} Cultural Center",
                    "description": "Experience local performances and cultural exhibits showcasing regional traditions.",
                    "rating": 4.3,
                    "estimated_duration": "2 hours",
                    "category": "Culture"
                }
            ]
            
            # Add special attractions based on interests
            for interest in request.interests:
                interest_lower = interest.lower()
                if "food" in interest_lower or "culinary" in interest_lower:
                    attractions.append({
                        "name": f"{request.destination} Food Tour",
                        "description": "Guided tour of the city's best food spots with tastings of local specialties.",
                        "rating": 4.8,
                        "estimated_duration": "3 hours",
                        "category": "Food"
                    })
                elif "adventure" in interest_lower or "hiking" in interest_lower:
                    attractions.append({
                        "name": f"Adventure Excursion near {request.destination}",
                        "description": "Exciting outdoor activities including hiking and local adventure experiences.",
                        "rating": 4.7,
                        "estimated_duration": "5 hours",
                        "category": "Adventure"
                    })
                elif "history" in interest_lower or "heritage" in interest_lower:
                    attractions.append({
                        "name": f"Historical Heritage Tour of {request.destination}",
                        "description": "Guided tour of the most important historical sites and monuments with expert commentary.",
                        "rating": 4.6,
                        "estimated_duration": "4 hours",
                        "category": "History"
                    })
                    
        # Create sample restaurants
        restaurants = [
            {
                "name": f"Authentic {request.destination} Restaurant",
                "cuisine": "Local",
                "price_range": "$$",
                "description": "Traditional dishes prepared with local ingredients and authentic recipes.",
                "rating": 4.7
            },
            {
                "name": "International Fusion Bistro",
                "cuisine": "Fusion",
                "price_range": "$$$",
                "description": "Creative fusion cuisine combining local flavors with international techniques.",
                "rating": 4.5
            },
            {
                "name": "Street Food Market",
                "cuisine": "Various",
                "price_range": "$",
                "description": "A variety of local street food vendors offering authentic quick bites.",
                "rating": 4.4
            },
            {
                "name": "Riverside Café",
                "cuisine": "Café",
                "price_range": "$$",
                "description": "Relaxed café with scenic views and a menu of light meals and beverages.",
                "rating": 4.3
            },
            {
                "name": "Gourmet Experience",
                "cuisine": "Fine Dining",
                "price_range": "$$$$",
                "description": "Upscale dining experience with innovative cuisine and elegant atmosphere.",
                "rating": 4.8
            }
        ]
        
        # Create daily itinerary
        daily_itinerary = []
        
        # Calculate daily budget (excluding flights)
        daily_budget = (request.budget * 0.6) / request.duration_days  # 60% of budget after flights
        
        for day in range(1, request.duration_days + 1):
            # Create a varied schedule based on day number
            if day == 1:
                # First day - arrival, check-in, light exploration
                activities = [
                    {
                        "name": f"Arrive in {request.destination}",
                        "description": f"Arrival and transfer to accommodation in {request.destination}.",
                        "time": "12:00",
                        "duration": "1 hour",
                        "cost": 1000,
                        "type": "transportation"
                    },
                    {
                        "name": f"Check-in at {selected_hotel.get('name', 'hotel') if selected_hotel else 'hotel'}",
                        "description": f"Check-in and refresh after your journey.",
                        "time": "14:00",
                        "duration": "1 hour",
                        "cost": 0,
                        "type": "accommodation"
                    },
                    {
                        "name": f"Orientation Walk in {request.destination}",
                        "description": f"Take a leisurely walk to get oriented with the neighborhood and surroundings.",
                        "time": "16:00",
                        "duration": "2 hours",
                        "cost": 0,
                        "type": "exploration"
                    }
                ]
                
                meals = [
                    {
                        "name": "Welcome Dinner",
                        "description": "Enjoy authentic local cuisine at a highly rated restaurant.",
                        "time": "19:00",
                        "restaurant": restaurants[0]["name"],
                        "cuisine": restaurants[0]["cuisine"],
                        "cost": 1500,
                        "type": "dinner"
                    }
                ]
            
            elif day == request.duration_days:
                # Last day - checkout, final sightseeing, departure
                activities = [
                    {
                        "name": "Morning Leisure",
                        "description": "Enjoy a relaxed morning in your hotel or nearby cafe.",
                        "time": "09:00",
                        "duration": "2 hours",
                        "cost": 500,
                        "type": "leisure"
                    },
                    {
                        "name": f"Check-out from {selected_hotel.get('name', 'hotel') if selected_hotel else 'hotel'}",
                        "description": "Check-out and store luggage if needed.",
                        "time": "11:00",
                        "duration": "1 hour",
                        "cost": 0,
                        "type": "accommodation"
                    },
                    {
                        "name": "Last-Minute Shopping",
                        "description": f"Purchase souvenirs and gifts from {request.destination}.",
                        "time": "12:30",
                        "duration": "2 hours",
                        "cost": 2000,
                        "type": "shopping"
                    },
                    {
                        "name": f"Departure from {request.destination}",
                        "description": "Transfer to airport/station and departure.",
                        "time": "17:00",
                        "duration": "2 hours",
                        "cost": 1000,
                        "type": "transportation"
                    }
                ]
                
                meals = [
                    {
                        "name": "Breakfast at Hotel",
                        "description": "Final breakfast at your accommodation.",
                        "time": "08:00",
                        "restaurant": f"{selected_hotel.get('name', 'hotel') if selected_hotel else 'hotel'} Restaurant",
                        "cuisine": "Breakfast",
                        "cost": 500,
                        "type": "breakfast"
                    },
                    {
                        "name": "Farewell Lunch",
                        "description": "A final taste of the local cuisine before departure.",
                        "time": "14:30",
                        "restaurant": restaurants[2]["name"],
                        "cuisine": restaurants[2]["cuisine"],
                        "cost": 1000,
                        "type": "lunch"
                    }
                ]
            
            else:
                # Middle days - full day activities based on interests
                # Select 2-3 attractions for the day
                day_attractions = random.sample(attractions, min(3, len(attractions)))
                
                activities = [
                    {
                        "name": day_attractions[0]["name"],
                        "description": day_attractions[0]["description"],
                        "time": "09:30",
                        "duration": day_attractions[0].get("estimated_duration", "2 hours"),
                        "cost": 1200,
                        "type": day_attractions[0].get("category", "sightseeing")
                    },
                    {
                        "name": day_attractions[1]["name"] if len(day_attractions) > 1 else "Local Exploration",
                        "description": day_attractions[1]["description"] if len(day_attractions) > 1 else "Explore the local neighborhood and discover hidden gems.",
                        "time": "14:00",
                        "duration": day_attractions[1].get("estimated_duration", "3 hours") if len(day_attractions) > 1 else "3 hours",
                        "cost": 800,
                        "type": day_attractions[1].get("category", "exploration") if len(day_attractions) > 1 else "exploration"
                    }
                ]
                
                # Add a third activity if available
                if len(day_attractions) > 2:
                    activities.append({
                        "name": day_attractions[2]["name"],
                        "description": day_attractions[2]["description"],
                        "time": "18:00",
                        "duration": day_attractions[2].get("estimated_duration", "2 hours"),
                        "cost": 1000,
                        "type": day_attractions[2].get("category", "entertainment")
                    })
                
                # Rotate restaurant options for variety
                lunch_index = (day % len(restaurants))
                dinner_index = ((day + 2) % len(restaurants))
                
                meals = [
                    {
                        "name": "Breakfast at Hotel",
                        "description": "Start your day with a nutritious breakfast.",
                        "time": "08:00",
                        "restaurant": f"{selected_hotel.get('name', 'hotel') if selected_hotel else 'hotel'} Restaurant",
                        "cuisine": "Breakfast",
                        "cost": 500,
                        "type": "breakfast"
                    },
                    {
                        "name": "Lunch",
                        "description": f"Lunch at {restaurants[lunch_index]['name']}.",
                        "time": "12:30",
                        "restaurant": restaurants[lunch_index]["name"],
                        "cuisine": restaurants[lunch_index]["cuisine"],
                        "cost": 800,
                        "type": "lunch"
                    },
                    {
                        "name": "Dinner",
                        "description": f"Dinner at {restaurants[dinner_index]['name']}.",
                        "time": "19:30",
                        "restaurant": restaurants[dinner_index]["name"],
                        "cuisine": restaurants[dinner_index]["cuisine"],
                        "cost": 1200,
                        "type": "dinner"
                    }
                ]
            
            # Calculate estimated cost for the day
            estimated_cost = sum(activity["cost"] for activity in activities) + sum(meal["cost"] for meal in meals)
            
            # Adjust if over budget
            if estimated_cost > daily_budget:
                # Scale down costs to fit daily budget
                scale_factor = daily_budget / estimated_cost
                for activity in activities:
                    activity["cost"] = round(activity["cost"] * scale_factor)
                for meal in meals:
                    meal["cost"] = round(meal["cost"] * scale_factor)
                estimated_cost = daily_budget
            
            # Create the daily itinerary item
            daily_item = {
                "day": day,
                "date": f"Day {day}",
                "activities": activities,
                "meals": meals,
                "estimated_cost": float(estimated_cost),
                "description": f"Day {day}: " + (
                    "Arrival and orientation" if day == 1 else
                    "Departure day" if day == request.duration_days else
                    f"Exploring {request.destination} - Day {day}"
                )
            }
            
            # Add accommodation details if available
            if selected_hotel:
                daily_item["accommodation"] = {
                    "name": selected_hotel.get("name", "Selected Hotel"),
                    "rating": selected_hotel.get("rating", 4.0),
                    "price_per_night": selected_hotel.get("price_per_night", 0),
                    "total_price": selected_hotel.get("total_price", 0),
                    "address": selected_hotel.get("address", ""),
                    "location": selected_hotel.get("location", ""),
                    "amenities": selected_hotel.get("amenities", []),
                    "hotel_id": selected_hotel.get("id", "hotel_1")
                }
            else:
                daily_item["accommodation"] = {
                    "name": f"{request.accommodation_type.capitalize()} in {request.destination}",
                    "rating": 4.0,
                    "price_per_night": daily_budget * 0.4,
                    "total_price": daily_budget * 0.4 * request.duration_days,
                    "address": f"{request.destination} City Center",
                    "location": f"{request.destination} - Central Area",
                    "amenities": ["WiFi", "Air Conditioning", "Breakfast Available"],
                    "hotel_id": "fallback_hotel"
                }
                
            daily_itinerary.append(daily_item)
        
        print(f"✅ Created enhanced daily itinerary with {len(daily_itinerary)} days")
        return daily_itinerary
