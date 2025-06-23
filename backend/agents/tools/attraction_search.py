from langchain.tools import BaseTool
from typing import Optional, Type, Dict, Any, List
from pydantic import BaseModel, Field
import random

class AttractionSearchInput(BaseModel):
    """Input for attraction search tool"""
    location: str = Field(description="City or area to search for attractions")
    interests: Optional[List[str]] = Field(default=[], description="Types of attractions (culture, adventure, nature, food, etc.)")
    budget_per_activity: Optional[float] = Field(None, description="Maximum budget per activity in INR")
    duration_preference: Optional[str] = Field("half-day", description="Preferred duration (half-day, full-day, few-hours)")

class AttractionSearchTool(BaseTool):
    """Tool for searching tourist attractions and activities"""
    
    name = "attraction_search"
    description = """Search for tourist attractions and activities in a specific location.
    Use this tool to find attractions that match user interests and budget.
    Returns attraction details including descriptions, prices, and duration."""
    args_schema: Type[BaseModel] = AttractionSearchInput
    
    def _run(
        self,
        location: str,
        interests: Optional[List[str]] = None,
        budget_per_activity: Optional[float] = None,
        duration_preference: str = "half-day",
        **kwargs: Any,
    ) -> str:
        """Execute the attraction search"""
        
        if interests is None:
            interests = ["general"]
        
        # Mock attraction data - replace with real API calls
        attractions_db = {
            "culture": [
                {"name": "Historic Palace", "type": "Historical Site", "price": 500, "duration": "3 hours"},
                {"name": "Art Museum", "type": "Museum", "price": 300, "duration": "2 hours"},
                {"name": "Traditional Market", "type": "Cultural Experience", "price": 200, "duration": "2 hours"},
                {"name": "Heritage Walk", "type": "Guided Tour", "price": 800, "duration": "4 hours"}
            ],
            "adventure": [
                {"name": "River Rafting", "type": "Water Sports", "price": 2500, "duration": "6 hours"},
                {"name": "Trekking Trail", "type": "Nature Adventure", "price": 1200, "duration": "8 hours"},
                {"name": "Zip Lining", "type": "Adventure Sports", "price": 1500, "duration": "3 hours"},
                {"name": "Rock Climbing", "type": "Adventure Sports", "price": 2000, "duration": "5 hours"}
            ],
            "nature": [
                {"name": "Botanical Garden", "type": "Nature Park", "price": 150, "duration": "3 hours"},
                {"name": "Wildlife Safari", "type": "Nature Experience", "price": 3000, "duration": "6 hours"},
                {"name": "Scenic Viewpoint", "type": "Sightseeing", "price": 100, "duration": "2 hours"},
                {"name": "Lake Boating", "type": "Water Activity", "price": 400, "duration": "2 hours"}
            ],
            "food": [
                {"name": "Street Food Tour", "type": "Food Experience", "price": 800, "duration": "3 hours"},
                {"name": "Cooking Class", "type": "Cultural Activity", "price": 1500, "duration": "4 hours"},
                {"name": "Local Market Visit", "type": "Food Shopping", "price": 300, "duration": "2 hours"},
                {"name": "Fine Dining Experience", "type": "Restaurant", "price": 2500, "duration": "2 hours"}
            ],
            "general": [
                {"name": "City Tour", "type": "Sightseeing", "price": 1000, "duration": "6 hours"},
                {"name": "Local Temple", "type": "Religious Site", "price": 50, "duration": "1 hour"},
                {"name": "Shopping District", "type": "Shopping", "price": 500, "duration": "4 hours"},
                {"name": "Sunset Point", "type": "Scenic Spot", "price": 0, "duration": "2 hours"}
            ]
        }
        
        # Collect attractions based on interests
        selected_attractions = []
        for interest in interests:
            interest_lower = interest.lower()
            if interest_lower in attractions_db:
                selected_attractions.extend(attractions_db[interest_lower])
            else:
                selected_attractions.extend(attractions_db["general"])
        
        # Remove duplicates and limit to 6 attractions
        unique_attractions = []
        seen_names = set()
        for attraction in selected_attractions:
            if attraction["name"] not in seen_names:
                unique_attractions.append(attraction)
                seen_names.add(attraction["name"])
                if len(unique_attractions) >= 6:
                    break
        
        # Apply budget filter if provided
        if budget_per_activity:
            unique_attractions = [a for a in unique_attractions if a["price"] <= budget_per_activity]
        
        # Add location and rating info
        for attraction in unique_attractions:
            attraction.update({
                "location": f"{location} - {random.choice(['City Center', 'Old Town', 'Tourist District', 'Outskirts'])}",
                "rating": round(random.uniform(3.8, 4.9), 1),
                "description": f"A wonderful {attraction['type'].lower()} offering great {interest} experience",
                "best_time": random.choice(["Morning", "Afternoon", "Evening", "Anytime"]),
                "crowd_level": random.choice(["Low", "Moderate", "High"]),
                "accessibility": random.choice(["Easy", "Moderate", "Challenging"])
            })
        
        # Sort by rating and price
        unique_attractions.sort(key=lambda x: (-x["rating"], x["price"]))
        
        return f"""Attraction Search Results for {location}:

RECOMMENDED ACTIVITIES (Based on interests: {', '.join(interests)}):
{self._format_attractions(unique_attractions)}

BUDGET SUMMARY:
Total for all activities: ₹{sum(a['price'] for a in unique_attractions):,}
Average per activity: ₹{sum(a['price'] for a in unique_attractions) // len(unique_attractions) if unique_attractions else 0:,}

TOP RECOMMENDATIONS:
{self._get_top_recommendations(unique_attractions)}

PLANNING TIPS:
• Book adventure activities in advance
• Check weather conditions for outdoor activities
• Consider crowd levels when planning timing
• Some attractions offer combo tickets for savings
"""

    def _format_attractions(self, attractions: List[Dict[str, Any]]) -> str:
        """Format attraction list for display"""
        if not attractions:
            return "No attractions found matching your criteria."
        
        formatted = []
        for i, attraction in enumerate(attractions, 1):
            price_str = "Free" if attraction["price"] == 0 else f"₹{attraction['price']}"
            
            formatted.append(
                f"{i}. {attraction['name']} ({attraction['rating']}★)\n"
                f"   Type: {attraction['type']} | Duration: {attraction['duration']}\n"
                f"   Price: {price_str} | Best Time: {attraction['best_time']}\n"
                f"   Location: {attraction['location']}\n"
                f"   Crowd Level: {attraction['crowd_level']} | Accessibility: {attraction['accessibility']}\n"
            )
        return "\n".join(formatted)
    
    def _get_top_recommendations(self, attractions: List[Dict[str, Any]]) -> str:
        """Get top 3 recommendations"""
        if not attractions:
            return "No recommendations available."
        
        top_3 = attractions[:3]
        recommendations = []
        for i, attraction in enumerate(top_3, 1):
            price_str = "Free" if attraction["price"] == 0 else f"₹{attraction['price']}"
            recommendations.append(f"{i}. {attraction['name']} - {price_str} ({attraction['duration']})")
        
        return "\n".join(recommendations)

    async def _arun(
        self,
        location: str,
        interests: Optional[List[str]] = None,
        budget_per_activity: Optional[float] = None,
        duration_preference: str = "half-day",
        **kwargs: Any,
    ) -> str:
        """Async version of the attraction search"""
        return self._run(location, interests, budget_per_activity, duration_preference, **kwargs)
