'use client'

import { useState, useEffect } from 'react'
import { MapPin, Calendar, DollarSign, Heart, Eye, Trash2, Share2 } from 'lucide-react'
import { ToastContainer, useToast } from '../components/Toast'

interface SavedTrip {
  id: string
  session_id: string
  title: string
  destination: string
  total_days: number
  total_cost: number
  currency: string
  saved_at: string
  tags: string[]
  notes: string | null
}

export default function SavedTripsPage() {
  const [savedTrips, setSavedTrips] = useState<SavedTrip[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Toast system
  const { toasts, removeToast, success, error: showError, info } = useToast()

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    fetchSavedTrips()
  }, [])

  const fetchSavedTrips = async () => {
    try {
      const response = await fetch(`${API_URL}/api/saved-trips`)
      
      if (!response.ok) {
        throw new Error('Failed to load saved trips')
      }
      
      const data = await response.json()
      setSavedTrips(data.trips || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteTrip = async (tripId: string) => {
    if (!confirm('Are you sure you want to delete this saved trip? This action cannot be undone.')) {
      return
    }

    try {
      const response = await fetch(`${API_URL}/api/saved-trips/${tripId}`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        throw new Error('Failed to delete trip')
      }

      // Remove from local state
      setSavedTrips(trips => trips.filter(trip => trip.id !== tripId))
      success('Trip Deleted', 'Trip deleted successfully!')
    } catch (err) {
      console.error('Error deleting trip:', err)
      showError('Delete Failed', 'Failed to delete trip')
    }
  }

  const formatCurrency = (amount: number) => {
    return `₹${amount.toLocaleString()}`
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white border-b shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center">
              <a href="/" className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                  <MapPin className="h-5 w-5 text-white" />
                </div>
                <span className="text-xl font-bold text-gray-900">AI Trip Planner</span>
              </a>
            </div>
          </div>
        </header>
        
        <div className="flex items-center justify-center py-24">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading your saved trips...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <a href="/" className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                  <MapPin className="h-5 w-5 text-white" />
                </div>
                <span className="text-xl font-bold text-gray-900">AI Trip Planner</span>
              </a>
            </div>
            
            <a 
              href="/"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <MapPin className="h-4 w-4 mr-2" />
              Plan New Trip
            </a>
          </div>
        </div>
      </header>

      {/* Page Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center">
            <Heart className="h-8 w-8 mr-3 text-red-500" />
            My Saved Trips
          </h1>
          <p className="text-lg text-gray-600">
            Your collection of AI-generated travel itineraries
          </p>
        </div>

        {error ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <MapPin className="h-8 w-8 text-red-600" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Trips</h2>
            <p className="text-gray-600 mb-6">{error}</p>
            <button 
              onClick={fetchSavedTrips}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Try Again
            </button>
          </div>
        ) : savedTrips.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Heart className="h-8 w-8 text-gray-400" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">No Saved Trips Yet</h2>
            <p className="text-gray-600 mb-6">
              Start planning your next adventure and save your favorite itineraries here.
            </p>
            <a 
              href="/"
              className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <MapPin className="h-5 w-5 mr-2" />
              Plan Your First Trip
            </a>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {savedTrips.map((trip) => (
              <div key={trip.id} className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow border">
                <div className="p-6">
                  {/* Trip Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
                        {trip.title}
                      </h3>
                      <div className="flex items-center text-gray-600 mb-2">
                        <MapPin className="h-4 w-4 mr-1" />
                        <span className="font-medium">{trip.destination}</span>
                      </div>
                    </div>
                  </div>

                  {/* Trip Details */}
                  <div className="space-y-2 mb-4">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center text-gray-600">
                        <Calendar className="h-4 w-4 mr-1" />
                        <span>{trip.total_days} days</span>
                      </div>
                      <div className="flex items-center text-green-600 font-semibold">
                        <DollarSign className="h-4 w-4 mr-1" />
                        <span>{formatCurrency(trip.total_cost)}</span>
                      </div>
                    </div>
                    
                    <div className="text-xs text-gray-500">
                      Saved {new Date(trip.saved_at).toLocaleDateString()}
                    </div>
                  </div>

                  {/* Tags */}
                  {trip.tags && trip.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-4">
                      {trip.tags.slice(0, 3).map((tag, index) => (
                        <span 
                          key={index}
                          className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                        >
                          {tag}
                        </span>
                      ))}
                      {trip.tags.length > 3 && (
                        <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                          +{trip.tags.length - 3} more
                        </span>
                      )}
                    </div>
                  )}

                  {/* Notes */}
                  {trip.notes && (
                    <div className="mb-4">
                      <p className="text-sm text-gray-600 line-clamp-2">
                        {trip.notes}
                      </p>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                    <a 
                      href={`/saved-trips/${trip.id}`}
                      className="inline-flex items-center text-blue-600 hover:text-blue-700 font-medium text-sm"
                    >
                      <Eye className="h-4 w-4 mr-1" />
                      View Details
                    </a>
                    
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => {
                          // TODO: Implement share saved trip
                          info('Coming Soon', 'Share functionality coming soon!')
                        }}
                        className="p-2 text-gray-600 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                        title="Share trip"
                      >
                        <Share2 className="h-4 w-4" />
                      </button>
                      
                      <button
                        onClick={() => handleDeleteTrip(trip.id)}
                        className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        title="Delete trip"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="bg-white border-t mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 text-center text-gray-600">
          <p>© 2024 AI Trip Planner. Powered by advanced AI agents and LangChain.</p>
        </div>
      </footer>

      {/* Toast notifications */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </div>
  )
}
