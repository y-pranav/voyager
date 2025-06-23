from langchain.tools import BaseTool
from typing import Optional, Type, Dict, Any, List
from pydantic import BaseModel, Field
import random

class RestaurantSearchInput(BaseModel):
    """Input for restaurant search tool"""
    location: str = Field(description="City or area to search for restaurants")
    cuisine_type: Optional[str] = Field("local", description="Type of cuisine (local, international, vegetarian, etc.)")
    budget_per_meal: Optional[float] = Field(None, description="Maximum budget per meal in INR")
    meal_type: str = Field("dinner", description="Type of meal (breakfast, lunch, dinner, snacks)")

class RestaurantSearchTool(BaseTool):
    """Tool for searching restaurants and dining options"""
    
    name = "restaurant_search"
    description = """Search for restaurants and dining options in a specific location.
    Use this tool to find restaurants that match cuisine preferences and budget.
    Returns restaurant details including cuisine, prices, and ratings."""
    args_schema: Type[BaseModel] = RestaurantSearchInput
    
    def _run(
        self,
        location: str,
        cuisine_type: str = "local",
        budget_per_meal: Optional[float] = None,
        meal_type: str = "dinner",
        **kwargs: Any,
    ) -> str:
        """Execute the restaurant search"""
        
        # Mock restaurant data - replace with real API calls
        restaurants_db = {
            "local": [
                {"name": "Traditional Spice Kitchen", "cuisine": "Local Traditional", "price_range": "₹₹"},
                {"name": "Heritage Restaurant", "cuisine": "Regional Specialties", "price_range": "₹₹₹"},
                {"name": "Street Food Corner", "cuisine": "Local Street Food", "price_range": "₹"},
                {"name": "Authentic Local Diner", "cuisine": "Home-style Cooking", "price_range": "₹₹"}
            ],
            "international": [
                {"name": "Italian Bistro", "cuisine": "Italian", "price_range": "₹₹₹"},
                {"name": "Asian Fusion", "cuisine": "Pan-Asian", "price_range": "₹₹₹"},
                {"name": "Mediterranean Grill", "cuisine": "Mediterranean", "price_range": "₹₹"},
                {"name": "Continental Cafe", "cuisine": "Continental", "price_range": "₹₹"}
            ],
            "vegetarian": [
                {"name": "Pure Veg Paradise", "cuisine": "Vegetarian", "price_range": "₹₹"},
                {"name": "Green Garden Restaurant", "cuisine": "Vegan & Vegetarian", "price_range": "₹₹"},
                {"name": "Satvik Dining", "cuisine": "Traditional Vegetarian", "price_range": "₹"},
                {"name": "Organic Farm Kitchen", "cuisine": "Organic Vegetarian", "price_range": "₹₹₹"}
            ]
        }
        
        # Get restaurants based on cuisine type
        cuisine_lower = cuisine_type.lower()
        if cuisine_lower in restaurants_db:
            selected_restaurants = restaurants_db[cuisine_lower].copy()
        else:
            selected_restaurants = restaurants_db["local"].copy()
        
        # Add random additional restaurants from other categories
        all_restaurants = []
        for restaurants in restaurants_db.values():
            all_restaurants.extend(restaurants)
        
        # Add 2 more random restaurants
        additional = random.sample([r for r in all_restaurants if r not in selected_restaurants], 2)
        selected_restaurants.extend(additional)
        
        # Add detailed information
        for restaurant in selected_restaurants:
            # Determine price based on price range and meal type
            base_prices = {"₹": 300, "₹₹": 800, "₹₹₹": 1500}
            base_price = base_prices[restaurant["price_range"]]
            
            # Adjust for meal type
            meal_multipliers = {"breakfast": 0.6, "lunch": 0.8, "dinner": 1.0, "snacks": 0.4}
            actual_price = int(base_price * meal_multipliers.get(meal_type, 1.0))
            
            # Apply budget filter if provided
            if budget_per_meal and actual_price > budget_per_meal:
                actual_price = int(budget_per_meal * 0.9)
            
            restaurant.update({
                "average_price": actual_price,
                "rating": round(random.uniform(3.5, 4.8), 1),
                "location": f"{location} - {random.choice(['City Center', 'Food Street', 'Mall Area', 'Old Town'])}",
                "specialties": self._get_specialties(restaurant["cuisine"]),
                "ambiance": random.choice(["Casual", "Fine Dining", "Family-friendly", "Romantic", "Traditional"]),
                "service": random.choice(["Table Service", "Quick Service", "Buffet", "Self Service"]),
                "distance": f"{random.uniform(0.5, 3.0):.1f} km from center",
                "opening_hours": "11:00 AM - 11:00 PM",
                "reservation_required": random.choice([True, False])
            })
        
        # Sort by rating and price
        selected_restaurants.sort(key=lambda x: (-x["rating"], x["average_price"]))
        
        return f"""Restaurant Search Results for {location}:

DINING OPTIONS ({meal_type.title()}, {cuisine_type} cuisine):
{self._format_restaurants(selected_restaurants)}

PRICE RANGE: ₹{min(r['average_price'] for r in selected_restaurants):,} - ₹{max(r['average_price'] for r in selected_restaurants):,} per person

TOP RECOMMENDATIONS:
{self._get_top_restaurant_recommendations(selected_restaurants)}

DINING TIPS:
• Make reservations for popular restaurants
• Try local specialties for authentic experience
• Check opening hours before visiting
• Consider location when planning your itinerary
"""

    def _get_specialties(self, cuisine: str) -> List[str]:
        """Get typical specialties for a cuisine type"""
        specialties_map = {
            "Local Traditional": ["Curry", "Rice Dishes", "Traditional Bread"],
            "Regional Specialties": ["Regional Curry", "Local Sweets", "Signature Dishes"],
            "Local Street Food": ["Chaat", "Kebabs", "Local Snacks"],
            "Italian": ["Pasta", "Pizza", "Risotto"],
            "Pan-Asian": ["Noodles", "Stir-fry", "Sushi"],
            "Mediterranean": ["Grilled Items", "Salads", "Seafood"],
            "Vegetarian": ["Dal", "Vegetable Curry", "Paneer Dishes"]
        }
        return specialties_map.get(cuisine, ["Special Dishes", "Chef's Recommendations"])

    def _format_restaurants(self, restaurants: List[Dict[str, Any]]) -> str:
        """Format restaurant list for display"""
        formatted = []
        for i, restaurant in enumerate(restaurants, 1):
            specialties_str = ", ".join(restaurant["specialties"][:2])
            reservation_text = " (Reservation Required)" if restaurant["reservation_required"] else ""
            
            formatted.append(
                f"{i}. {restaurant['name']} ({restaurant['rating']}★)\n"
                f"   Cuisine: {restaurant['cuisine']} | Price: ₹{restaurant['average_price']} per person\n"
                f"   Specialties: {specialties_str}\n"
                f"   Ambiance: {restaurant['ambiance']} | Service: {restaurant['service']}\n"
                f"   Location: {restaurant['location']} ({restaurant['distance']}){reservation_text}\n"
            )
        return "\n".join(formatted)
    
    def _get_top_restaurant_recommendations(self, restaurants: List[Dict[str, Any]]) -> str:
        """Get top 3 restaurant recommendations"""
        top_3 = restaurants[:3]
        recommendations = []
        for i, restaurant in enumerate(top_3, 1):
            recommendations.append(
                f"{i}. {restaurant['name']} - {restaurant['cuisine']} (₹{restaurant['average_price']}, {restaurant['rating']}★)"
            )
        return "\n".join(recommendations)

    async def _arun(
        self,
        location: str,
        cuisine_type: str = "local",
        budget_per_meal: Optional[float] = None,
        meal_type: str = "dinner",
        **kwargs: Any,
    ) -> str:
        """Async version of the restaurant search"""
        return self._run(location, cuisine_type, budget_per_meal, meal_type, **kwargs)
