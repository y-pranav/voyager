from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Dict, Any, List
import asyncio
import json
import os
import re

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
    4. Itinerary generation
    """
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
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
            # Flight search
            flight_tool = self.tools["flight_search"]
            print(f"🛫 CALLING FLIGHT SEARCH TOOL...")
            flight_result = flight_tool._run(
                origin="India",  # This would be determined from user location
                destination=request.destination,
                departure_date=request.start_date or "2024-01-15",
                passengers=request.travelers,
                budget_max=request.budget
            )
            print(f"📨 RECEIVED FROM FLIGHT TOOL:")
            print(f"   - Type: {type(flight_result)}")
            print(f"   - Keys: {list(flight_result.keys()) if isinstance(flight_result, dict) else 'Not a dict'}")
            
            if isinstance(flight_result, dict):
                if 'flights' in flight_result:
                    print(f"   - flights count: {len(flight_result['flights'])}")
                    if flight_result['flights']:
                        print(f"   - First flight sample: {flight_result['flights'][0] if flight_result['flights'] else 'None'}")
                else:
                    print(f"   - ❌ No 'flights' key in result!")
            
            # Store both formatted string and structured data
            tool_results["flights"] = {
                "formatted": flight_result["formatted"],
                "options": flight_result["flights"]  # Store as "options" to match frontend interface
            }
            print(f"🗂️ STORED IN TOOL_RESULTS['flights']:")
            print(f"   - formatted: {len(flight_result.get('formatted', '')) if flight_result.get('formatted') else 0} chars")
            print(f"   - options: {len(flight_result.get('flights', [])) if flight_result.get('flights') else 0} items")
            
            # Hotel search
            hotel_tool = self.tools["hotel_search"]
            hotel_result = hotel_tool._run(
                location=request.destination,
                check_in_date=request.start_date or "2024-01-15",
                check_out_date="2024-01-20",  # Calculate based on duration
                guests=request.travelers,
                hotel_type=request.accommodation_type
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
            # Extract the final itinerary from agent result
            final_response = agent_result.get("final_itinerary", "")
            tool_results = agent_result.get("tool_results", {})
            
            # Try to parse JSON from the response
            try:
                # Look for JSON in the response
                json_match = re.search(r'\{.*\}', final_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    structured_data = json.loads(json_str)
                else:
                    structured_data = self._create_fallback_structure(final_response, request)
            except:
                # If JSON parsing fails, create structure from text
                structured_data = self._create_fallback_structure(final_response, request)
            
            # Get flight data from tool results
            flight_data = tool_results.get("flights", {})
            print(f"🏗️ STRUCTURING ITINERARY - Flight data:")
            print(f"   - flight_data type: {type(flight_data)}")
            print(f"   - flight_data keys: {list(flight_data.keys()) if isinstance(flight_data, dict) else 'Not a dict'}")
            
            if isinstance(flight_data, dict):
                options = flight_data.get("options", [])
                print(f"   - options count: {len(options)}")
                if options:
                    print(f"   - First option sample: {options[0] if options else 'None'}")
                else:
                    print(f"   - ❌ No options in flight_data!")
            
            flight_structured = {
                "formatted": flight_data.get("formatted", ""),
                "options": flight_data.get("options", [])  # Include structured flight options
            }
            print(f"📦 FINAL flight_structured:")
            print(f"   - formatted: {len(flight_structured['formatted'])} chars")
            print(f"   - options: {len(flight_structured['options'])} items")
            
            # Ensure required fields are present
            itinerary = {
                "destination": request.destination,
                "total_days": request.duration_days,
                "total_cost": structured_data.get("total_cost", request.budget * 0.8),
                "currency": "INR",
                "daily_itinerary": structured_data.get("daily_itinerary", []),
                "flights": flight_structured,  # Use structured flight data
                "accommodation_summary": structured_data.get("accommodation_summary", {}),
                "cost_breakdown": structured_data.get("cost_breakdown", {}),
                "recommendations": structured_data.get("recommendations", []),
                "tool_results": {
                    k: v for k, v in tool_results.items() if k != "flights"  # Avoid duplicate flight data
                }
            }
            
            print(f"🚀 FINAL ITINERARY BEING SENT TO FRONTEND:")
            print(f"   - destination: {itinerary['destination']}")
            print(f"   - flights type: {type(itinerary['flights'])}")
            print(f"   - flights keys: {list(itinerary['flights'].keys()) if isinstance(itinerary['flights'], dict) else 'Not a dict'}")
            if isinstance(itinerary['flights'], dict) and 'options' in itinerary['flights']:
                print(f"   - flights.options count: {len(itinerary['flights']['options'])}")
                if itinerary['flights']['options']:
                    for i, opt in enumerate(itinerary['flights']['options'][:2]):
                        print(f"     Option {i+1}: {opt.get('airlines', [])} - ₹{opt.get('price_inr', 0):,.0f}")
            
            return itinerary
            
        except Exception as e:
            logger.error(f"Error structuring itinerary: {str(e)}")
            # Return a basic structure if everything fails
            return self._create_emergency_fallback(request)

    def _create_fallback_structure(self, output: str, request: TripRequest) -> Dict[str, Any]:
        """Create a basic structure when JSON parsing fails"""
        return {
            "destination": request.destination,
            "total_days": request.duration_days,
            "total_cost": request.budget * 0.8,  # Conservative estimate
            "daily_itinerary": [
                {
                    "day": i + 1,
                    "date": f"Day {i + 1}",
                    "activities": [{"name": f"Explore {request.destination}", "time": "10:00 AM"}],
                    "meals": [{"name": "Local Restaurant", "time": "12:00 PM"}],
                    "estimated_cost": request.budget / request.duration_days
                }
                for i in range(request.duration_days)
            ],
            "flights": {"status": "found", "cost": request.budget * 0.3},
            "accommodation_summary": {"type": request.accommodation_type, "cost": request.budget * 0.4},
            "cost_breakdown": {
                "flights": request.budget * 0.3,
                "accommodation": request.budget * 0.4,
                "activities": request.budget * 0.2,
                "meals": request.budget * 0.1
            },
            "recommendations": ["Book flights early", "Try local cuisine"],
            "raw_output": output
        }
    
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
