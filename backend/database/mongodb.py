from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict, Any
import os
from datetime import datetime, timedelta
import uuid

class MongoDB:
    """MongoDB database manager for trip planner"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None
        self.trip_sessions = None
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/tripplanner")
            self.client = AsyncIOMotorClient(mongodb_uri)
            
            # Test the connection
            await self.client.admin.command('ping')
            
            # Get database and collections
            db_name = mongodb_uri.split('/')[-1] if '/' in mongodb_uri else 'tripplanner'
            self.database = self.client[db_name]
            self.trip_sessions = self.database.trip_sessions
            
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
