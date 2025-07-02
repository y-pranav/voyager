from pydantic import BaseModel, Field, field_serializer
from typing import Optional, List, Dict, Any
from datetime import datetime, date

class TripRequest(BaseModel):
    """Trip planning request model"""
    destination: str = Field(..., description="Primary destination for the trip")
    source: str = Field(..., description="Source location (departure city/airport) for the trip")
    budget: float = Field(..., description="Budget in INR")
    duration_days: int = Field(..., description="Number of days for the trip")
    start_date: Optional[date] = Field(None, description="Preferred start date")
    travelers: int = Field(1, description="Number of travelers")
    interests: Optional[List[str]] = Field(default=[], description="User interests (culture, adventure, food, etc.)")
    accommodation_type: Optional[str] = Field("hotel", description="Preferred accommodation type")
    transport_mode: Optional[str] = Field("flight", description="Preferred transport mode")
    special_requirements: Optional[str] = Field(None, description="Any special requirements or notes")
    use_real_api: bool = Field(False, description="Whether to use real API for flight and hotel searches")

    @field_serializer('start_date')
    def serialize_start_date(self, start_date: Optional[date]) -> Optional[str]:
        if start_date:
            return start_date.isoformat()
        return None

class DayItinerary(BaseModel):
    """Single day itinerary model"""
    day: int
    date: str
    activities: List[Dict[str, Any]]
    accommodation: Dict[str, Any]
    meals: List[Dict[str, Any]]
    transport: List[Dict[str, Any]]
    estimated_cost: float

class TripItinerary(BaseModel):
    """Complete trip itinerary model"""
    destination: str
    total_days: int
    total_cost: float
    currency: str = "INR"
    daily_itinerary: List[DayItinerary]
    flights: Dict[str, Any]
    accommodation_summary: Dict[str, Any]
    cost_breakdown: Dict[str, float]
    recommendations: List[str]

class TripResponse(BaseModel):
    """Trip planning response model"""
    session_id: str
    status: str = Field(..., description="Status: processing, completed, failed")
    itinerary: Optional[Dict[str, Any]] = None
    total_cost: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    
    @field_serializer('created_at')
    def serialize_created_at(self, created_at: datetime) -> str:
        return created_at.isoformat()

class AgentProgress(BaseModel):
    """Agent execution progress model"""
    current_step: str
    completed_steps: List[str]
    total_steps: int
    percentage: float
    details: Optional[str] = None

class SavedTrip(BaseModel):
    """Saved trip model"""
    id: str
    session_id: str
    title: str
    destination: str
    total_days: int
    total_cost: float
    currency: str = "INR"
    itinerary: Dict[str, Any]
    saved_at: datetime = Field(default_factory=datetime.now)
    tags: Optional[List[str]] = Field(default=[])
    notes: Optional[str] = None

class SharedTrip(BaseModel):
    """Shared trip model"""
    share_id: str
    session_id: str
    title: str
    destination: str
    itinerary: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    view_count: int = 0
    is_public: bool = True

class TripActionResponse(BaseModel):
    """Response for trip actions (save, share, etc.)"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class SaveTripRequest(BaseModel):
    """Request to save a trip"""
    session_id: str
    title: Optional[str] = None
    tags: Optional[List[str]] = Field(default=[])
    notes: Optional[str] = None

class ShareTripRequest(BaseModel):
    """Request to share a trip"""
    session_id: str
    title: Optional[str] = None
    expires_in_days: Optional[int] = 30  # Default 30 days expiry
