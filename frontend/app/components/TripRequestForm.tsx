'use client'

import { useState } from 'react'
import { Calendar, Users, MapPin, DollarSign, Heart, Plane, Sparkles } from 'lucide-react'

interface TripRequest {
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

interface TripRequestFormProps {
  onSubmit: (request: TripRequest) => void
}

const INTERESTS_OPTIONS = [
  'Culture & History',
  'Adventure & Sports',
  'Nature & Wildlife',
  'Food & Cuisine',
  'Art & Museums',
  'Beach & Relaxation',
  'Shopping',
  'Nightlife',
  'Photography',
  'Spiritual & Religious'
]

const ACCOMMODATION_TYPES = [
  { value: 'hotel', label: 'Hotel' },
  { value: 'resort', label: 'Resort' },
  { value: 'hostel', label: 'Hostel' },
  { value: 'apartment', label: 'Apartment' },
  { value: 'guesthouse', label: 'Guesthouse' }
]

const TRANSPORT_MODES = [
  { value: 'flight', label: 'Flight' },
  { value: 'train', label: 'Train' },
  { value: 'bus', label: 'Bus' },
  { value: 'car', label: 'Car' }
]

export default function TripRequestForm({ onSubmit }: TripRequestFormProps) {
  const [formData, setFormData] = useState<TripRequest>({
    destination: '',
    source: '',
    budget: 50000,
    duration_days: 5,
    start_date: '',
    travelers: 2,
    interests: [],
    accommodation_type: 'hotel',
    transport_mode: 'flight',
    special_requirements: '',
    use_real_api: true
  })

  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleInterestToggle = (interest: string) => {
    setFormData(prev => ({
      ...prev,
      interests: prev.interests.includes(interest)
        ? prev.interests.filter(i => i !== interest)
        : [...prev.interests, interest]
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.destination.trim()) {
      alert('Please enter a destination')
      return
    }

    if (!formData.source.trim()) {
      alert('Please enter your departure city/airport')
      return
    }

    if (formData.interests.length === 0) {
      alert('Please select at least one interest')
      return
    }

    setIsSubmitting(true)
    
    try {
      await onSubmit(formData)
    } catch (error) {
      console.error('Error submitting form:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Destination & Basic Info */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
            <MapPin className="h-5 w-5 text-primary-600 mr-2" />
            Destination & Basic Details
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="form-label">
                Where are you traveling from? *
              </label>
              <input
                type="text"
                className="input-field"
                placeholder="e.g., Delhi, BLR, HYD, Mumbai"
                value={formData.source}
                onChange={(e) => setFormData(prev => ({ ...prev, source: e.target.value }))}
                required
              />
            </div>

            <div>
              <label className="form-label">
                Where do you want to go? *
              </label>
              <input
                type="text"
                className="input-field"
                placeholder="e.g., Japan, Goa, Paris"
                value={formData.destination}
                onChange={(e) => setFormData(prev => ({ ...prev, destination: e.target.value }))}
                required
              />
            </div>

            <div>
              <label className="form-label">
                <Calendar className="h-4 w-4 inline mr-1" />
                Start Date (Optional)
              </label>
              <input
                type="date"
                className="input-field"
                value={formData.start_date}
                onChange={(e) => setFormData(prev => ({ ...prev, start_date: e.target.value }))}
              />
            </div>

            <div>
              <label className="form-label">
                Duration (Days) *
              </label>
              <input
                type="number"
                className="input-field"
                min="1"
                max="30"
                value={formData.duration_days}
                onChange={(e) => setFormData(prev => ({ ...prev, duration_days: parseInt(e.target.value) }))}
                required
              />
            </div>

            <div>
              <label className="form-label">
                <Users className="h-4 w-4 inline mr-1" />
                Number of Travelers *
              </label>
              <input
                type="number"
                className="input-field"
                min="1"
                max="10"
                value={formData.travelers}
                onChange={(e) => setFormData(prev => ({ ...prev, travelers: parseInt(e.target.value) }))}
                required
              />
            </div>
          </div>
        </div>

        {/* Budget */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
            <DollarSign className="h-5 w-5 text-primary-600 mr-2" />
            Budget
          </h3>
          
          <div>
            <label className="form-label">
              Total Budget (INR) *
            </label>
            <div className="space-y-4">
              <input
                type="range"
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                min="10000"
                max="500000"
                step="5000"
                value={formData.budget}
                onChange={(e) => setFormData(prev => ({ ...prev, budget: parseInt(e.target.value) }))}
              />
              <div className="flex justify-between text-sm text-gray-600">
                <span>₹10,000</span>
                <span className="font-semibold text-primary-600">₹{formData.budget.toLocaleString()}</span>
                <span>₹5,00,000</span>
              </div>
              <input
                type="number"
                className="input-field"
                min="10000"
                max="500000"
                step="1000"
                value={formData.budget}
                onChange={(e) => setFormData(prev => ({ ...prev, budget: parseInt(e.target.value) }))}
                required
              />
            </div>
          </div>
        </div>

        {/* Interests */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
            <Heart className="h-5 w-5 text-primary-600 mr-2" />
            What are you interested in? *
          </h3>
          
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {INTERESTS_OPTIONS.map((interest) => (
              <button
                key={interest}
                type="button"
                onClick={() => handleInterestToggle(interest)}
                className={`p-3 rounded-lg border text-sm font-medium transition-all duration-200 ${
                  formData.interests.includes(interest)
                    ? 'bg-primary-600 text-white border-primary-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:border-primary-300'
                }`}
              >
                {interest}
              </button>
            ))}
          </div>
          
          {formData.interests.length > 0 && (
            <div className="mt-4 p-3 bg-primary-50 rounded-lg">
              <p className="text-sm text-primary-800">
                Selected: {formData.interests.join(', ')}
              </p>
            </div>
          )}
        </div>

        {/* Preferences */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
            <Plane className="h-5 w-5 text-primary-600 mr-2" />
            Travel Preferences
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="form-label">
                Accommodation Type
              </label>
              <select
                className="input-field"
                value={formData.accommodation_type}
                onChange={(e) => setFormData(prev => ({ ...prev, accommodation_type: e.target.value }))}
              >
                {ACCOMMODATION_TYPES.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="form-label">
                Preferred Transport
              </label>
              <select
                className="input-field"
                value={formData.transport_mode}
                onChange={(e) => setFormData(prev => ({ ...prev, transport_mode: e.target.value }))}
              >
                {TRANSPORT_MODES.map(mode => (
                  <option key={mode.value} value={mode.value}>
                    {mode.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="mt-6">
            <label className="form-label">
              Special Requirements (Optional)
            </label>
            <textarea
              className="input-field"
              rows={3}
              placeholder="Any dietary restrictions, accessibility needs, or special requests..."
              value={formData.special_requirements}
              onChange={(e) => setFormData(prev => ({ ...prev, special_requirements: e.target.value }))}
            />
          </div>
        </div>

        {/* API Options */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-6 flex items-center">
            <Sparkles className="h-5 w-5 text-primary-600 mr-2" />
            Advanced Options
          </h3>
          
          <div className="flex items-center space-x-3">
            <input
              type="checkbox"
              id="use_real_api"
              className="h-5 w-5 text-primary-600 border-gray-300 rounded"
              checked={formData.use_real_api}
              onChange={(e) => setFormData(prev => ({ ...prev, use_real_api: e.target.checked }))}
            />
            <label htmlFor="use_real_api" className="font-medium text-gray-700 cursor-pointer">
              Use real API data for flights and hotels
            </label>
          </div>
          <p className="mt-2 text-sm text-gray-500">
            When checked, the system will use real-time data from SerpAPI for flights and hotels. 
            Unchecking will use sample data which is faster but less accurate.
          </p>
        </div>

        {/* Submit Button */}
        <div className="text-center">
          <button
            type="submit"
            disabled={isSubmitting || !formData.destination.trim() || formData.interests.length === 0}
            className="btn-primary px-8 py-4 text-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white inline-block mr-2"></div>
                Creating Your Trip...
              </>
            ) : (
              <>
                <Plane className="h-5 w-5 inline-block mr-2" />
                Plan My Trip with AI
              </>
            )}
          </button>
          
          <p className="mt-4 text-sm text-gray-600">
            Our AI agent will analyze your preferences and create a personalized itinerary
          </p>
        </div>
      </form>
    </div>
  )
}
