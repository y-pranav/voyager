from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
from typing import Dict, Any
import os
from dotenv import load_dotenv

from models.trip_request import TripRequest, TripResponse
from agents.trip_planner_agent import TripPlannerAgent
from database.mongodb import MongoDB
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="AI Trip Planner API",
    description="Agentic AI trip planner that creates personalized itineraries",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
logger = setup_logger()
db = MongoDB()
trip_agent = TripPlannerAgent()

@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup"""
    try:
        await db.connect()
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        # Continue without database for development

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown"""
    await db.close()
    logger.info("Application shutdown complete")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "AI Trip Planner API is running", "status": "healthy"}

@app.post("/api/plan-trip", response_model=TripResponse)
async def plan_trip(request: TripRequest) -> TripResponse:
    """
    Main endpoint to process trip planning requests
    
    This endpoint:
    1. Receives user trip requirements
    2. Triggers the LangChain agent
    3. Returns the generated itinerary
    """
    
    try:
        logger.info(f"Received trip planning request: {request.destination}")
        
        # Store request in database for tracking
        session_id = await db.create_trip_session(request.model_dump())
        
        # Trigger the LangChain agent
        itinerary = await trip_agent.plan_trip(
            session_id=session_id,
            request=request
        )
        
        # Ensure JSON serialization by sanitizing the itinerary
        import json
        try:
            # Test if itinerary is JSON serializable
            json.dumps(itinerary)
        except TypeError as e:
            logger.error(f"JSON serialization error in itinerary: {str(e)}")
            # Create a sanitized copy
            sanitized = sanitize_for_json(itinerary)
            logger.info(f"Itinerary sanitized for JSON serialization")
            itinerary = sanitized
        
        # Store the result and mark as completed
        await db.update_trip_session(session_id, {
            "itinerary": itinerary,
            "status": "completed"
        })
        
        response = TripResponse(
            session_id=session_id,
            status="completed",
            itinerary=itinerary,
            total_cost=itinerary.get("total_cost", 0)
        )
        
        logger.info(f"Trip planning completed for session: {session_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error planning trip: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Trip planning failed: {str(e)}")

@app.get("/api/trip-status/{session_id}")
async def get_trip_status(session_id: str):
    """Get the status of a trip planning session"""
    try:
        session = await db.get_trip_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        response = {
            "session_id": session_id,
            "status": session.get("status", "processing"),
            "progress": session.get("progress", {}),
            "created_at": session.get("created_at")
        }
        
        # If the session is completed, include the itinerary and cost
        if session.get("status") == "completed" and session.get("itinerary"):
            response["itinerary"] = session.get("itinerary")
            response["total_cost"] = session.get("itinerary", {}).get("total_cost", 0)
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trip status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get trip status")

@app.get("/api/debug-session/{session_id}")
async def debug_session(session_id: str):
    """Debug endpoint to see raw session data"""
    try:
        session = await db.get_trip_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        return {
            "session_id": session_id,
            "status": session.get("status"),
            "has_itinerary": "itinerary" in session and session["itinerary"] is not None,
            "itinerary_keys": list(session.get("itinerary", {}).keys()) if session.get("itinerary") else [],
            "created_at": session.get("created_at"),
            "updated_at": session.get("updated_at")
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/agent-tools")
async def get_available_tools():
    """Get list of available agent tools for debugging"""
    return {
        "tools": [
            "flight_search",
            "hotel_search", 
            "attraction_search",
            "restaurant_search",
            "weather_info",
            "currency_converter"
        ]
    }

def sanitize_for_json(obj):
    """
    Recursively sanitize an object to ensure it's JSON serializable.
    Converts datetime objects to strings and handles other non-serializable types.
    """
    from datetime import date, datetime
    
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, (int, float, bool, str, type(None))):
        return obj
    else:
        # For any other types, convert to string
        return str(obj)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
