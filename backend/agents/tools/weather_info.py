from langchain.tools import BaseTool
from typing import Optional, Type, Dict, Any
from pydantic import BaseModel, Field
import random
from datetime import datetime, timedelta

class WeatherInfoInput(BaseModel):
    """Input for weather information tool"""
    location: str = Field(description="City or location to get weather information for")
    date: Optional[str] = Field(None, description="Date for weather forecast in YYYY-MM-DD format")

class WeatherInfoTool(BaseTool):
    """Tool for getting weather information and forecasts"""
    
    name = "weather_info"
    description = """Get weather information and forecasts for a specific location and date.
    Use this tool to help plan activities based on weather conditions.
    Returns temperature, conditions, and recommendations for activities."""
    args_schema: Type[BaseModel] = WeatherInfoInput
    
    def _run(
        self,
        location: str,
        date: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Execute the weather information lookup"""
        
        # Mock weather data - replace with real weather API calls
        weather_conditions = [
            "Clear", "Partly Cloudy", "Cloudy", "Light Rain", 
            "Heavy Rain", "Thunderstorms", "Sunny", "Overcast"
        ]
        
        # Generate realistic weather based on location (simplified)
        if any(tropical in location.lower() for tropical in ["goa", "kerala", "mumbai", "chennai"]):
            # Tropical climate
            temp_range = (25, 35)
            humidity_range = (60, 85)
            likely_conditions = ["Sunny", "Partly Cloudy", "Light Rain", "Thunderstorms"]
        elif any(cold in location.lower() for cold in ["kashmir", "himachal", "uttarakhand", "ladakh"]):
            # Cold climate
            temp_range = (5, 20)
            humidity_range = (40, 70)
            likely_conditions = ["Clear", "Cloudy", "Light Rain", "Overcast"]
        else:
            # Moderate climate
            temp_range = (18, 30)
            humidity_range = (45, 75)
            likely_conditions = ["Clear", "Partly Cloudy", "Sunny", "Cloudy"]
        
        # Generate weather data
        current_weather = {
            "temperature": random.randint(*temp_range),
            "condition": random.choice(likely_conditions),
            "humidity": random.randint(*humidity_range),
            "wind_speed": random.randint(5, 25),
            "visibility": random.choice(["Excellent", "Good", "Fair", "Poor"]),
            "uv_index": random.randint(3, 10)
        }
        
        # Generate 5-day forecast if date is provided
        forecast = []
        if date:
            try:
                start_date = datetime.strptime(date, "%Y-%m-%d")
            except:
                start_date = datetime.now()
        else:
            start_date = datetime.now()
        
        for i in range(5):
            forecast_date = start_date + timedelta(days=i)
            day_weather = {
                "date": forecast_date.strftime("%Y-%m-%d"),
                "day": forecast_date.strftime("%A"),
                "high": random.randint(temp_range[0] + 2, temp_range[1] + 5),
                "low": random.randint(temp_range[0] - 2, temp_range[1] - 5),
                "condition": random.choice(likely_conditions),
                "rain_chance": random.randint(0, 80)
            }
            forecast.append(day_weather)
        
        # Generate activity recommendations
        recommendations = self._get_weather_recommendations(current_weather, forecast)
        
        return f"""Weather Information for {location}:

CURRENT CONDITIONS:
Temperature: {current_weather['temperature']}°C
Condition: {current_weather['condition']}
Humidity: {current_weather['humidity']}%
Wind Speed: {current_weather['wind_speed']} km/h
Visibility: {current_weather['visibility']}
UV Index: {current_weather['uv_index']}

5-DAY FORECAST:
{self._format_forecast(forecast)}

ACTIVITY RECOMMENDATIONS:
{chr(10).join(f"• {rec}" for rec in recommendations)}

WHAT TO PACK:
{self._get_packing_suggestions(current_weather, forecast)}
"""

    def _format_forecast(self, forecast: list) -> str:
        """Format weather forecast for display"""
        formatted = []
        for day in forecast:
            rain_text = f" ({day['rain_chance']}% rain)" if day['rain_chance'] > 30 else ""
            formatted.append(
                f"{day['day']} ({day['date']}): {day['high']}°/{day['low']}° - {day['condition']}{rain_text}"
            )
        return "\n".join(formatted)
    
    def _get_weather_recommendations(self, current: dict, forecast: list) -> list:
        """Generate activity recommendations based on weather"""
        recommendations = []
        
        # Current weather recommendations
        if current['condition'] in ['Sunny', 'Clear']:
            recommendations.extend([
                "Perfect weather for outdoor sightseeing",
                "Great time for photography and walking tours",
                "Consider visiting outdoor attractions"
            ])
        elif current['condition'] in ['Light Rain', 'Cloudy']:
            recommendations.extend([
                "Good weather for indoor attractions like museums",
                "Carry an umbrella for outdoor activities",
                "Consider covered markets or shopping areas"
            ])
        elif current['condition'] in ['Heavy Rain', 'Thunderstorms']:
            recommendations.extend([
                "Stay indoors - visit museums, galleries, or malls",
                "Perfect time for spa treatments or indoor dining",
                "Avoid outdoor activities and tours"
            ])
        
        # Temperature-based recommendations
        if current['temperature'] > 30:
            recommendations.append("Stay hydrated and seek shade during peak hours")
        elif current['temperature'] < 15:
            recommendations.append("Dress warmly and consider indoor activities")
        
        # UV index recommendations
        if current['uv_index'] > 7:
            recommendations.append("Use sunscreen and wear protective clothing")
        
        return recommendations[:5]  # Limit to 5 recommendations
    
    def _get_packing_suggestions(self, current: dict, forecast: list) -> str:
        """Generate packing suggestions based on weather"""
        suggestions = []
        
        # Temperature-based packing
        max_temp = max([day['high'] for day in forecast])
        min_temp = min([day['low'] for day in forecast])
        
        if max_temp > 30:
            suggestions.extend(["Light cotton clothes", "Sunglasses", "Hat/cap"])
        if min_temp < 15:
            suggestions.extend(["Warm jacket", "Long pants", "Closed shoes"])
        if any(day['rain_chance'] > 50 for day in forecast):
            suggestions.extend(["Umbrella", "Raincoat", "Waterproof shoes"])
        
        # General items
        suggestions.extend(["Sunscreen", "Comfortable walking shoes"])
        
        return ", ".join(suggestions[:6])  # Limit to 6 items

    async def _arun(
        self,
        location: str,
        date: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Async version of the weather information lookup"""
        return self._run(location, date, **kwargs)
