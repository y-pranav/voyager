from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import asyncio
from typing import Dict, Any
import os
from dotenv import load_dotenv

from models.trip_request import (
    TripRequest, TripResponse, SaveTripRequest, ShareTripRequest, 
    TripActionResponse, SavedTrip, SharedTrip
)
from agents.trip_planner_agent import TripPlannerAgent
from database.mongodb import MongoDB
from utils.logger import setup_logger
from utils.pdf_generator import TripPDFGenerator

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
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "https://voyager-9wc.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize components
logger = setup_logger()
db = MongoDB()
trip_agent = TripPlannerAgent()
pdf_generator = TripPDFGenerator()

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

# === TRIP ACTION ENDPOINTS ===

@app.post("/api/save-trip", response_model=TripActionResponse)
async def save_trip(request: SaveTripRequest) -> TripActionResponse:
    """Save a trip to user's saved trips"""
    try:
        # Validate session exists and is completed
        session = await db.get_trip_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.get("status") != "completed":
            raise HTTPException(status_code=400, detail="Trip is not completed yet")
        
        if not session.get("itinerary"):
            raise HTTPException(status_code=400, detail="No itinerary found for this session")
        
        # Save the trip
        saved_trip_id = await db.save_trip(
            session_id=request.session_id,
            title=request.title,
            tags=request.tags,
            notes=request.notes
        )
        
        if not saved_trip_id:
            raise HTTPException(status_code=500, detail="Failed to save trip")
        
        logger.info(f"Trip saved successfully: {saved_trip_id}")
        
        return TripActionResponse(
            success=True,
            message="Trip saved successfully!",
            data={"saved_trip_id": saved_trip_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving trip: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save trip: {str(e)}")

@app.post("/api/share-trip", response_model=TripActionResponse)
async def share_trip(request: ShareTripRequest) -> TripActionResponse:
    """Create a shareable link for a trip"""
    try:
        # Validate session exists and is completed
        session = await db.get_trip_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.get("status") != "completed":
            raise HTTPException(status_code=400, detail="Trip is not completed yet")
        
        if not session.get("itinerary"):
            raise HTTPException(status_code=400, detail="No itinerary found for this session")
        
        # Create shared trip
        share_id = await db.create_shared_trip(
            session_id=request.session_id,
            title=request.title,
            expires_in_days=request.expires_in_days
        )
        
        if not share_id:
            raise HTTPException(status_code=500, detail="Failed to create shareable link")
        
        # Generate shareable URL
        base_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        share_url = f"{base_url}/shared/{share_id}"
        
        logger.info(f"Trip shared successfully: {share_id}")
        
        return TripActionResponse(
            success=True,
            message="Shareable link created successfully!",
            data={
                "share_id": share_id,
                "share_url": share_url,
                "expires_in_days": request.expires_in_days
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sharing trip: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to share trip: {str(e)}")

@app.get("/api/download-pdf/{session_id}")
async def download_trip_pdf(session_id: str):
    """Download trip itinerary as PDF"""
    try:
        # Validate session exists and is completed
        session = await db.get_trip_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if session.get("status") != "completed":
            raise HTTPException(status_code=400, detail="Trip is not completed yet")
        
        itinerary = session.get("itinerary")
        if not itinerary:
            raise HTTPException(status_code=400, detail="No itinerary found for this session")
        
        # Generate PDF
        pdf_buffer = pdf_generator.generate_pdf(itinerary)
        
        # Create filename
        destination = itinerary.get("destination", "trip").replace(" ", "_").lower()
        filename = f"trip_itinerary_{destination}_{session_id[:8]}.pdf"
        
        logger.info(f"PDF generated successfully for session: {session_id}")
        
        # Return PDF as streaming response
        return StreamingResponse(
            iter([pdf_buffer.read()]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/pdf"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")

@app.get("/api/shared/{share_id}")
async def get_shared_trip(share_id: str):
    """Get shared trip by share ID"""
    try:
        shared_trip = await db.get_shared_trip(share_id)
        if not shared_trip:
            raise HTTPException(status_code=404, detail="Shared trip not found or expired")
        
        # Sanitize the response for JSON serialization
        sanitized_trip = sanitize_for_json(shared_trip)
        
        logger.info(f"Shared trip accessed: {share_id}")
        
        return sanitized_trip
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting shared trip: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get shared trip: {str(e)}")

@app.get("/api/saved-trips")
async def get_saved_trips(limit: int = 20, skip: int = 0):
    """Get saved trips with pagination"""
    try:
        saved_trips = await db.get_saved_trips(limit=limit, skip=skip)
        
        # Sanitize the response for JSON serialization
        sanitized_trips = sanitize_for_json(saved_trips)
        
        return {
            "trips": sanitized_trips,
            "total": len(sanitized_trips),
            "limit": limit,
            "skip": skip
        }
        
    except Exception as e:
        logger.error(f"Error getting saved trips: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get saved trips: {str(e)}")

@app.get("/api/saved-trips/{trip_id}")
async def get_saved_trip(trip_id: str):
    """Get a specific saved trip"""
    try:
        saved_trip = await db.get_saved_trip(trip_id)
        if not saved_trip:
            raise HTTPException(status_code=404, detail="Saved trip not found")
        
        # Sanitize the response for JSON serialization
        sanitized_trip = sanitize_for_json(saved_trip)
        
        return sanitized_trip
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting saved trip: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get saved trip: {str(e)}")

@app.delete("/api/saved-trips/{trip_id}")
async def delete_saved_trip(trip_id: str):
    """Delete a saved trip"""
    try:
        success = await db.delete_saved_trip(trip_id)
        if not success:
            raise HTTPException(status_code=404, detail="Saved trip not found")
        
        logger.info(f"Saved trip deleted: {trip_id}")
        
        return TripActionResponse(
            success=True,
            message="Trip deleted successfully!"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting saved trip: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete saved trip: {str(e)}")

# === END TRIP ACTION ENDPOINTS ===

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
