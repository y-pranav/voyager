from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict, Any, List
import os
from datetime import datetime, timedelta
import uuid

class MongoDB:
    """MongoDB database manager for trip planner"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None
        self.trip_sessions = None
        self.saved_trips = None
        self.shared_trips = None
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/tripplanner")
            self.client = AsyncIOMotorClient(mongodb_uri)
            
            # Test the connection
            await self.client.admin.command('ping')
            
            # Get database and collections - fix parsing to handle query parameters
            if '/' in mongodb_uri:
                db_part = mongodb_uri.split('/')[-1]
                # Remove query parameters (everything after ?)
                db_name = db_part.split('?')[0] if '?' in db_part else db_part
                # Use default if empty
                db_name = db_name if db_name else 'tripplanner'
            else:
                db_name = 'tripplanner'
                
            self.database = self.client[db_name]
            self.trip_sessions = self.database.trip_sessions
            self.saved_trips = self.database.saved_trips
            self.shared_trips = self.database.shared_trips
            
            # Create indexes
            await self._create_indexes()
            
            print("✅ Connected to MongoDB")
            
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            print("⚠️ Continuing without database - some features may not work")
            # Don't raise exception, continue without database for development
    
    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print("✅ MongoDB connection closed")
    
    async def _create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Index on session_id for fast lookups
            await self.trip_sessions.create_index("session_id", unique=True)
            
            # Index on created_at for cleanup operations
            await self.trip_sessions.create_index("created_at")
            
            # Compound index for user queries
            await self.trip_sessions.create_index([
                ("status", 1),
                ("created_at", -1)
            ])
            
            # Indexes for saved trips
            await self.saved_trips.create_index("session_id")
            await self.saved_trips.create_index("destination")
            await self.saved_trips.create_index("saved_at")
            
            # Indexes for shared trips
            await self.shared_trips.create_index("share_id", unique=True)
            await self.shared_trips.create_index("session_id")
            await self.shared_trips.create_index("expires_at")
            
            print("✅ Database indexes created")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not create indexes: {e}")
    
    async def create_trip_session(self, request_data: Dict[str, Any]) -> str:
        """Create a new trip planning session"""
        try:
            session_id = str(uuid.uuid4())
            
            session_document = {
                "session_id": session_id,
                "status": "processing",
                "request_data": request_data,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "progress": {
                    "current_step": "initializing",
                    "completed_steps": [],
                    "total_steps": 6,
                    "percentage": 0
                },
                "agent_logs": [],
                "itinerary": None,
                "error_message": None
            }
            
            result = await self.trip_sessions.insert_one(session_document)
            
            if result.inserted_id:
                print(f"✅ Created trip session: {session_id}")
                return session_id
            else:
                raise Exception("Failed to insert session document")
                
        except Exception as e:
            print(f"❌ Error creating trip session: {e}")
            raise
    
    async def get_trip_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get trip session by ID"""
        try:
            session = await self.trip_sessions.find_one({"session_id": session_id})
            return session
            
        except Exception as e:
            print(f"❌ Error getting trip session {session_id}: {e}")
            return None
    
    async def update_trip_session(self, session_id: str, update_data: Dict[str, Any]) -> bool:
        """Update trip session with new data"""
        try:
            update_data["updated_at"] = datetime.utcnow()
            
            # Add detailed logging for debugging
            if 'itinerary' in update_data:
                flight_status = update_data['itinerary'].get('flights', {}).get('status', 'unknown')
                hotel_status = update_data['itinerary'].get('hotels', {}).get('status', 'unknown')
                flight_count = len(update_data['itinerary'].get('flights', {}).get('options', []))
                hotel_count = len(update_data['itinerary'].get('hotels', {}).get('options', []))
                print(f"💾 Saving itinerary to DB - Flight status: {flight_status}, Hotel status: {hotel_status}")
                print(f"💾 Flight count: {flight_count}, Hotel count: {hotel_count}")
                
            result = await self.trip_sessions.update_one(
                {"session_id": session_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                print(f"✅ Updated trip session: {session_id}")
                return True
            else:
                print(f"⚠️ No changes made to session: {session_id}")
                return False
                
        except Exception as e:
            print(f"❌ Error updating trip session {session_id}: {e}")
            return False
    
    async def update_session_progress(self, session_id: str, step: str, percentage: float, details: str = None) -> bool:
        """Update session progress"""
        try:
            progress_update = {
                "progress.current_step": step,
                "progress.percentage": percentage,
                "updated_at": datetime.utcnow()
            }
            
            if details:
                progress_update["progress.details"] = details
            
            # Add step to completed steps if not already there
            session = await self.get_trip_session(session_id)
            if session and step not in session.get("progress", {}).get("completed_steps", []):
                await self.trip_sessions.update_one(
                    {"session_id": session_id},
                    {"$push": {"progress.completed_steps": step}}
                )
            
            result = await self.trip_sessions.update_one(
                {"session_id": session_id},
                {"$set": progress_update}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"❌ Error updating session progress {session_id}: {e}")
            return False
    
    async def add_agent_log(self, session_id: str, log_entry: Dict[str, Any]) -> bool:
        """Add agent execution log entry"""
        try:
            log_entry["timestamp"] = datetime.utcnow()
            
            result = await self.trip_sessions.update_one(
                {"session_id": session_id},
                {
                    "$push": {"agent_logs": log_entry},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"❌ Error adding agent log {session_id}: {e}")
            return False
    
    async def set_session_error(self, session_id: str, error_message: str) -> bool:
        """Set session status to error with message"""
        try:
            update_data = {
                "status": "failed",
                "error_message": error_message,
                "updated_at": datetime.utcnow()
            }
            
            result = await self.trip_sessions.update_one(
                {"session_id": session_id},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"❌ Error setting session error {session_id}: {e}")
            return False
    
    async def complete_session(self, session_id: str, itinerary: Dict[str, Any]) -> bool:
        """Mark session as completed with final itinerary"""
        try:
            update_data = {
                "status": "completed",
                "itinerary": itinerary,
                "progress.current_step": "completed",
                "progress.percentage": 100,
                "updated_at": datetime.utcnow()
            }
            
            result = await self.trip_sessions.update_one(
                {"session_id": session_id},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            print(f"❌ Error completing session {session_id}: {e}")
            return False
    
    async def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """Clean up sessions older than specified days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            result = await self.trip_sessions.delete_many({
                "created_at": {"$lt": cutoff_date}
            })
            
            deleted_count = result.deleted_count
            if deleted_count > 0:
                print(f"✅ Cleaned up {deleted_count} old sessions")
            
            return deleted_count
            
        except Exception as e:
            print(f"❌ Error cleaning up old sessions: {e}")
            return 0
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            total_sessions = await self.trip_sessions.count_documents({})
            
            # Count by status
            pipeline = [
                {"$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }}
            ]
            
            status_counts = {}
            async for result in self.trip_sessions.aggregate(pipeline):
                status_counts[result["_id"]] = result["count"]
            
            return {
                "total_sessions": total_sessions,
                "status_breakdown": status_counts,
                "last_updated": datetime.utcnow()
            }
            
        except Exception as e:
            print(f"❌ Error getting session stats: {e}")
            return {}

    # === SAVED TRIPS METHODS ===
    
    async def save_trip(self, session_id: str, title: str, tags: List[str] = None, notes: str = None) -> Optional[str]:
        """Save a trip to user's saved trips"""
        try:
            # Get the completed session
            session = await self.get_trip_session(session_id)
            if not session or session.get("status") != "completed":
                return None
            
            itinerary = session.get("itinerary")
            if not itinerary:
                return None
            
            # Generate unique ID for saved trip
            saved_trip_id = str(uuid.uuid4())
            
            # Create saved trip document
            saved_trip = {
                "id": saved_trip_id,
                "session_id": session_id,
                "title": title or f"Trip to {itinerary.get('destination', 'Unknown')}",
                "destination": itinerary.get("destination", "Unknown"),
                "total_days": itinerary.get("total_days", 0),
                "total_cost": itinerary.get("total_cost", 0),
                "currency": itinerary.get("currency", "INR"),
                "itinerary": itinerary,
                "saved_at": datetime.utcnow(),
                "tags": tags or [],
                "notes": notes
            }
            
            result = await self.saved_trips.insert_one(saved_trip)
            
            if result.inserted_id:
                print(f"✅ Saved trip: {saved_trip_id}")
                return saved_trip_id
            
            return None
            
        except Exception as e:
            print(f"❌ Error saving trip {session_id}: {e}")
            return None
    
    async def get_saved_trips(self, limit: int = 20, skip: int = 0) -> List[Dict[str, Any]]:
        """Get saved trips with pagination"""
        try:
            cursor = self.saved_trips.find({}).sort("saved_at", -1).skip(skip).limit(limit)
            trips = []
            async for trip in cursor:
                # Remove MongoDB _id field
                trip.pop("_id", None)
                trips.append(trip)
            
            return trips
            
        except Exception as e:
            print(f"❌ Error getting saved trips: {e}")
            return []
    
    async def get_saved_trip(self, trip_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific saved trip"""
        try:
            trip = await self.saved_trips.find_one({"id": trip_id})
            if trip:
                trip.pop("_id", None)
            return trip
            
        except Exception as e:
            print(f"❌ Error getting saved trip {trip_id}: {e}")
            return None
    
    async def delete_saved_trip(self, trip_id: str) -> bool:
        """Delete a saved trip"""
        try:
            result = await self.saved_trips.delete_one({"id": trip_id})
            return result.deleted_count > 0
            
        except Exception as e:
            print(f"❌ Error deleting saved trip {trip_id}: {e}")
            return False

    # === SHARED TRIPS METHODS ===
    
    async def create_shared_trip(self, session_id: str, title: str = None, expires_in_days: int = 30) -> Optional[str]:
        """Create a shareable trip link"""
        try:
            # Get the completed session
            session = await self.get_trip_session(session_id)
            if not session or session.get("status") != "completed":
                return None
            
            itinerary = session.get("itinerary")
            if not itinerary:
                return None
            
            # Generate unique share ID
            share_id = str(uuid.uuid4())
            
            # Calculate expiry date
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days) if expires_in_days else None
            
            # Create shared trip document
            shared_trip = {
                "share_id": share_id,
                "session_id": session_id,
                "title": title or f"Trip to {itinerary.get('destination', 'Unknown')}",
                "destination": itinerary.get("destination", "Unknown"),
                "itinerary": itinerary,
                "created_at": datetime.utcnow(),
                "expires_at": expires_at,
                "view_count": 0,
                "is_public": True
            }
            
            result = await self.shared_trips.insert_one(shared_trip)
            
            if result.inserted_id:
                print(f"✅ Created shared trip: {share_id}")
                return share_id
            
            return None
            
        except Exception as e:
            print(f"❌ Error creating shared trip {session_id}: {e}")
            return None
    
    async def get_shared_trip(self, share_id: str) -> Optional[Dict[str, Any]]:
        """Get shared trip by share ID"""
        try:
            # Check if not expired
            shared_trip = await self.shared_trips.find_one({
                "share_id": share_id,
                "$or": [
                    {"expires_at": None},
                    {"expires_at": {"$gt": datetime.utcnow()}}
                ]
            })
            
            if shared_trip:
                # Increment view count
                await self.shared_trips.update_one(
                    {"share_id": share_id},
                    {"$inc": {"view_count": 1}}
                )
                
                shared_trip.pop("_id", None)
                return shared_trip
            
            return None
            
        except Exception as e:
            print(f"❌ Error getting shared trip {share_id}: {e}")
            return None
    
    async def delete_shared_trip(self, share_id: str) -> bool:
        """Delete a shared trip"""
        try:
            result = await self.shared_trips.delete_one({"share_id": share_id})
            return result.deleted_count > 0
            
        except Exception as e:
            print(f"❌ Error deleting shared trip {share_id}: {e}")
            return False
    
    async def cleanup_expired_shares(self) -> int:
        """Clean up expired shared trips"""
        try:
            result = await self.shared_trips.delete_many({
                "expires_at": {"$lt": datetime.utcnow()}
            })
            
            deleted_count = result.deleted_count
            if deleted_count > 0:
                print(f"✅ Cleaned up {deleted_count} expired shared trips")
            
            return deleted_count
            
        except Exception as e:
            print(f"❌ Error cleaning up expired shares: {e}")
            return 0
