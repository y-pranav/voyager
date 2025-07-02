'use client'

import { useState } from 'react'
import TripRequestForm from './components/TripRequestForm'
import ProgressTracker from './components/ProgressTracker'
import ItineraryDisplay from './components/ItineraryDisplay'
import { Plane, MapPin, Sparkles, Heart } from 'lucide-react'

export interface TripRequest {
  destination: string
  source: string
  budget: number
  duration_days: number
  start_date?: string
  travelers: number
  interests: string[]
  accommodation_type: string
  transport_mode: string
  special_requirements?: string
  use_real_api: boolean
}

export interface TripItinerary {
  destination: string
  total_days: number
  total_cost: number
  currency: string
  daily_itinerary: any[]
  flights: any
  accommodation_summary: any
  cost_breakdown: any
  recommendations: string[]
}

export default function Home() {
  const [currentStep, setCurrentStep] = useState<'form' | 'planning' | 'results'>('form')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [itinerary, setItinerary] = useState<TripItinerary | null>(null)
  const [progress, setProgress] = useState({ percentage: 0, currentStep: '', details: '' })

  const handleTripSubmit = async (tripRequest: TripRequest) => {
    try {
      setCurrentStep('planning')
      
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      
      // Submit trip request
      const response = await fetch(`${API_URL}/api/plan-trip`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(tripRequest),
      })

      if (!response.ok) {
        throw new Error('Failed to submit trip request')
      }

      const result = await response.json()
      setSessionId(result.session_id)
      
      // Poll for progress updates
      pollProgress(result.session_id)
      
    } catch (error) {
      console.error('Error submitting trip request:', error)
      alert('Failed to submit trip request. Please try again.')
      setCurrentStep('form')
    }
  }

  const pollProgress = async (sessionId: string) => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    let attempts = 0
    const maxAttempts = 60 // 5 minutes with 5-second intervals

    const poll = async () => {
      try {
        if (attempts >= maxAttempts) {
          throw new Error('Timeout: Trip planning took too long')
        }

        const response = await fetch(`${API_URL}/api/trip-status/${sessionId}`)
        if (!response.ok) {
          throw new Error('Failed to get trip status')
        }

        const status = await response.json()
        
        // Update progress
        setProgress({
          percentage: status.progress?.percentage || 0,
          currentStep: status.progress?.current_step || 'Processing...',
          details: status.progress?.details || ''
        })

        if (status.status === 'completed') {
          // Use the itinerary from the status response
          if (status.itinerary) {
            setItinerary(status.itinerary)
            setCurrentStep('results')
          } else {
            throw new Error('Trip completed but no itinerary found')
          }
          return
        } else if (status.status === 'failed') {
          throw new Error(status.error_message || 'Trip planning failed')
        }

        // Continue polling
        attempts++
        setTimeout(poll, 5000) // Poll every 5 seconds
        
      } catch (error) {
        console.error('Error polling progress:', error)
        alert('Error during trip planning. Please try again.')
        setCurrentStep('form')
      }
    }

    poll()
  }

  const resetForm = () => {
    setCurrentStep('form')
    setSessionId(null)
    setItinerary(null)
    setProgress({ percentage: 0, currentStep: '', details: '' })
  }

  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-2 rounded-lg">
                <Sparkles className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  AI Trip Planner
                </h1>
                <p className="text-sm text-gray-600">Intelligent travel planning with AI agents</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <a 
                href="/saved-trips"
                className="text-gray-600 hover:text-blue-600 font-medium transition-colors flex items-center"
              >
                <Heart className="h-4 w-4 mr-1" />
                Saved Trips
              </a>
              
              {currentStep !== 'form' && (
                <button
                  onClick={resetForm}
                  className="btn-secondary flex items-center space-x-2"
                >
                  <MapPin className="h-4 w-4" />
                  <span>Plan New Trip</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentStep === 'form' && (
          <div className="animate-fade-in">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Plan Your Perfect Trip
              </h2>
              <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                Tell us your travel goals and our AI agent will create a personalized itinerary 
                with flights, hotels, activities, and dining recommendations.
              </p>
            </div>
            <TripRequestForm onSubmit={handleTripSubmit} />
          </div>
        )}

        {currentStep === 'planning' && (
          <div className="animate-fade-in">
            <ProgressTracker 
              progress={progress.percentage}
              currentStep={progress.currentStep}
              details={progress.details}
            />
          </div>
        )}

        {currentStep === 'results' && itinerary && (
          <div className="animate-fade-in">
            <ItineraryDisplay itinerary={itinerary} sessionId={sessionId} />
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="bg-white border-t mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-600">
            <p>© 2024 AI Trip Planner. Powered by advanced AI agents and LangChain.</p>
          </div>
        </div>
      </footer>
    </main>
  )
}
