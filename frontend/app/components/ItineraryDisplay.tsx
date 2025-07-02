'use client'

import { useState } from 'react'
import { 
  MapPin, Calendar, Users, DollarSign, Plane, Hotel, 
  Camera, Utensils, Clock, Star, ChevronDown, ChevronUp,
  Download, Share2, Heart
} from 'lucide-react'
import { ToastContainer, useToast } from './Toast'
import { Modal } from './Modal'

// Flight-related interfaces
interface FlightSegment {
  flight_number?: string
  airline?: string
  departure_airport?: string
  departure_time?: string
  arrival_airport?: string
  arrival_time?: string
  duration?: string
  cabin?: string
  aircraft?: string
  stops?: number
}

interface FlightOption {
  id: string
  price_inr: number
  airlines: string[]
  total_duration: string
  segments: FlightSegment[]
  total_stops: number
  bookable_seats?: number
  instant_ticketing_required?: boolean
  fare_type?: string
  [key: string]: any  // Allow other properties
}

interface FlightData {
  options: FlightOption[]
  status: string
  disclaimer: string
}

// Hotel-related interfaces
interface HotelOption {
  id: string
  name: string
  rating: number
  star_level: number
  price_per_night: number
  currency: string
  total_price: number
  amenities: string[]
  room_type: string
  location: string
  address: string
  distance_to_center: number
  breakfast_included: boolean
  refundable: boolean
  cancellation_policy: string
  images: string[]
  availability: string
  reviews_count: number
  property_type: string
  [key: string]: any  // Allow other properties
}

interface HotelData {
  options: HotelOption[]
  status: string
  disclaimer: string
}

interface TripItinerary {
  destination: string
  total_days: number
  total_cost: number
  currency: string
  daily_itinerary: DayItinerary[]
  flights: FlightData
  hotels?: HotelData
  accommodation_summary: any
  cost_breakdown: any
  recommendations: string[]
}

interface DayItinerary {
  day: number
  date: string
  activities: Activity[]
  accommodation: any
  meals: Meal[]
  transport: any[]
  estimated_cost: number
}

interface Activity {
  name: string
  time: string
  duration?: string
  description?: string
  cost?: number
  location?: string
}

interface Meal {
  name: string
  time: string
  cuisine?: string
  cost?: number
  location?: string
}

interface ItineraryDisplayProps {
  itinerary: TripItinerary
  sessionId?: string | null
}

export default function ItineraryDisplay({ itinerary, sessionId }: ItineraryDisplayProps) {
  const [expandedDays, setExpandedDays] = useState<number[]>([1])
  const [activeTab, setActiveTab] = useState<'itinerary' | 'summary' | 'costs'>('itinerary')
  const [showAllFlights, setShowAllFlights] = useState<boolean>(false)
  const [isLoading, setIsLoading] = useState<{[key: string]: boolean}>({})

  // Toast system
  const { toasts, removeToast, success, error, info, warning } = useToast()

  // Modal state
  const [modal, setModal] = useState<{
    isOpen: boolean;
    title: string;
    content: string;
    type: 'input' | 'confirm';
    inputValue?: string;
    onConfirm?: (value?: string) => void;
    onCancel?: () => void;
  }>({
    isOpen: false,
    title: '',
    content: '',
    type: 'confirm'
  })
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  // Toast helpers
  const showToast = (title: string, message?: string, type: 'success' | 'error' | 'info' | 'warning' = 'info') => {
    switch (type) {
      case 'success':
        success(title, message)
        break
      case 'error':
        error(title, message)
        break
      case 'warning':
        warning(title, message)
        break
      default:
        info(title, message)
        break
    }
  }

  // Modal helpers
  const showInputModal = (title: string, content: string, onConfirm: (value: string) => void, onCancel?: () => void) => {
    setModal({
      isOpen: true,
      title,
      content,
      type: 'input',
      inputValue: '',
      onConfirm: (value?: string) => onConfirm(value || ''),
      onCancel
    })
  }

  const showConfirmModal = (title: string, content: string, onConfirm: () => void, onCancel?: () => void) => {
    setModal({
      isOpen: true,
      title,
      content,
      type: 'confirm',
      onConfirm: () => onConfirm(),
      onCancel
    })
  }

  const closeModal = () => {
    setModal(prev => ({ ...prev, isOpen: false }))
  }

  const handleSaveTrip = async () => {
    if (!sessionId) {
      showToast('Session Error', 'Session not found. Cannot save trip.', 'error')
      return
    }

    // Show input modal for trip title
    showInputModal(
      'Save Trip',
      'Enter a title for your saved trip (optional):',
      async (title) => {
        closeModal()
        setIsLoading(prev => ({ ...prev, save: true }))

        try {
          const response = await fetch(`${API_URL}/api/save-trip`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              session_id: sessionId,
              title: title || undefined,
              tags: [],
              notes: null
            })
          })

          if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Failed to save trip')
          }

          const result = await response.json()
          showToast('Trip Saved!', '🎉 Your trip has been saved successfully', 'success')
          
        } catch (error) {
          console.error('Error saving trip:', error)
          showToast('Save Failed', `${error instanceof Error ? error.message : 'Unknown error'}`, 'error')
        } finally {
          setIsLoading(prev => ({ ...prev, save: false }))
        }
      },
      () => closeModal() // onCancel
    )
  }

  const handleShareTrip = async () => {
    if (!sessionId) {
      showToast('Session Error', 'Session not found. Cannot share trip.', 'error')
      return
    }

    // Show input modal for trip title
    showInputModal(
      'Share Trip',
      'Enter a title for your shared trip (optional):',
      async (title) => {
        closeModal()
        setIsLoading(prev => ({ ...prev, share: true }))

        try {
          const response = await fetch(`${API_URL}/api/share-trip`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              session_id: sessionId,
              title: title || undefined,
              expires_in_days: 30
            })
          })

          if (!response.ok) {
            const error = await response.json()
            throw new Error(error.detail || 'Failed to share trip')
          }

          const result = await response.json()
          
          // Copy to clipboard
          if (navigator.clipboard && result.data?.share_url) {
            await navigator.clipboard.writeText(result.data.share_url)
            showToast('Link Copied!', '✅ Shareable link created and copied to clipboard', 'success')
          } else {
            showToast('Link Created', '✅ Shareable link has been created', 'success')
          }
          
        } catch (error) {
          console.error('Error sharing trip:', error)
          showToast('Share Failed', `${error instanceof Error ? error.message : 'Unknown error'}`, 'error')
        } finally {
          setIsLoading(prev => ({ ...prev, share: false }))
        }
      },
      () => closeModal() // onCancel
    )
  }

  const handleDownloadPDF = async () => {
    if (!sessionId) {
      showToast('Session Error', 'Session not found. Cannot download PDF.', 'error')
      return
    }

    setIsLoading(prev => ({ ...prev, pdf: true }))

    try {
      const response = await fetch(`${API_URL}/api/download-pdf/${sessionId}`)

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to generate PDF')
      }

      // Get filename from response headers
      const contentDisposition = response.headers.get('Content-Disposition') || ''
      const filenameMatch = contentDisposition.match(/filename="([^"]+)"/)
      const filename = filenameMatch ? filenameMatch[1] : `trip_itinerary_${itinerary.destination.replace(/\s+/g, '_').toLowerCase()}.pdf`

      // Create blob and download
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.style.display = 'none'
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      showToast('PDF Downloaded!', '📄 Your trip itinerary has been downloaded successfully', 'success')
      
    } catch (error) {
      console.error('Error downloading PDF:', error)
      showToast('Download Failed', `${error instanceof Error ? error.message : 'Unknown error'}`, 'error')
    } finally {
      setIsLoading(prev => ({ ...prev, pdf: false }))
    }
  }

  const toggleDay = (day: number) => {
    setExpandedDays(prev => 
      prev.includes(day) 
        ? prev.filter(d => d !== day)
        : [...prev, day]
    )
  }

  const formatCurrency = (amount: number | string | null | undefined) => {
    // Handle invalid or undefined values safely
    if (amount === null || amount === undefined) {
      return '₹0';
    }
    
    // Convert string to number if needed
    let numAmount: number;
    if (typeof amount === 'string') {
      // Remove non-numeric characters except decimal point
      const cleanedAmount = amount.replace(/[^0-9.]/g, '');
      numAmount = parseFloat(cleanedAmount);
    } else {
      numAmount = amount as number;
    }
    
    // Final validation
    if (isNaN(numAmount) || !isFinite(numAmount)) {
      return '₹0';
    }
    // Round to whole number to avoid decimal issues
    return `₹${Math.round(numAmount).toLocaleString()}`;
  }

  // Helper function to group activities by time periods
  const groupActivitiesByTimePeriod = (activities: any[]) => {
    const groups: { [key: string]: any[] } = {
      morning: [],
      afternoon: [],
      evening: [],
      other: []
    }
    
    activities.forEach(activity => {
      const time = activity.time || ''
      const hour = parseInt(time.split(':')[0]) || 0
      
      if (hour >= 6 && hour < 12) {
        groups.morning.push(activity)
      } else if (hour >= 12 && hour < 17) {
        groups.afternoon.push(activity)
      } else if (hour >= 17 && hour < 22) {
        groups.evening.push(activity)
      } else {
        groups.other.push(activity)
      }
    })
    
    return groups
  }

  // Helper function to get time period label and color
  const getTimePeriodInfo = (period: string) => {
    const info = {
      morning: { label: 'Morning', color: 'bg-yellow-100 text-yellow-800', icon: '🌅' },
      afternoon: { label: 'Afternoon', color: 'bg-blue-100 text-blue-800', icon: '☀️' },
      evening: { label: 'Evening', color: 'bg-purple-100 text-purple-800', icon: '🌙' },
      other: { label: 'Other', color: 'bg-gray-100 text-gray-800', icon: '⏰' }
    }
    return info[period as keyof typeof info] || info.other
  }

  // Hotel display component
  const HotelDisplay = ({ hotels }: { hotels: HotelData }) => {
    const [showAll, setShowAll] = useState(false);
    
    // Safety check for missing data
    if (!hotels || !hotels.options || hotels.options.length === 0) {
      return <p className="text-gray-600">No hotel options available.</p>;
    }
    
    // Show only the first 3 hotels initially, or all if showAll is true
    const displayedHotels = showAll ? hotels.options : hotels.options.slice(0, 3);
    
    return (
      <div>
        {/* Sample Data Disclaimer - Only show when status is not live_data */}
        {hotels.status !== 'live_data' && (
          <div className="bg-yellow-50 border border-yellow-200 p-2 rounded-lg mb-4 text-xs">
            <div className="flex items-center">
              <div className="mr-2 text-yellow-600">⚠️</div>
              <div>
                <p className="text-yellow-800 font-medium">
                  Sample data for demonstration purposes only
                </p>
                <p className="text-yellow-700">Showing {hotels.options.length} hotel options</p>
              </div>
            </div>
          </div>
        )}
        
        {/* Live Data Disclaimer - Show when using real API data */}
        {hotels.status === 'live_data' && (
          <div className="bg-blue-50 border border-blue-200 p-2 rounded-lg mb-4 text-xs">
            <div className="flex items-center">
              <div className="mr-2 text-blue-600">🌐</div>
              <div>
                <p className="text-blue-800 font-medium">
                  Real-time hotel data via SerpAPI
                </p>
                <p className="text-blue-700">Showing {hotels.options.length} hotel options</p>
              </div>
            </div>
          </div>
        )}
        
        {/* Hotel List */}
        <div 
          className="space-y-4 max-h-[500px] overflow-y-auto pr-2"
          style={{
            scrollbarWidth: 'thin',
            scrollbarColor: '#CBD5E0 transparent',
          }}
        >          
          {displayedHotels.map((hotel, idx) => (
            <div 
              key={hotel.id} 
              className="p-4 bg-gray-50 rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between items-start mb-2">
                <div>
                  <div className="flex items-center">
                    <h4 className="font-semibold text-gray-900 mr-2">
                      {hotel.name}
                    </h4>
                    {idx === 0 && (
                      <span className="bg-green-100 text-green-800 text-xs px-2 py-0.5 rounded">
                        Best Value
                      </span>
                    )}
                  </div>
                  <div className="flex items-center mt-1">
                    <div className="flex text-yellow-400 mr-1">
                      {[...Array(hotel.star_level || 0)].map((_, i) => (
                        <Star key={i} className="h-4 w-4 fill-current" />
                      ))}
                    </div>
                    <span className="text-sm text-gray-700">
                      {hotel.rating?.toFixed(1) || "N/A"} ({hotel.reviews_count || 0} reviews)
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-medium text-green-600 text-lg">
                    {formatCurrency(hotel.price_per_night)}/night
                  </p>
                  <p className="text-xs text-gray-600">
                    {formatCurrency(hotel.total_price)} total
                  </p>
                </div>
              </div>
              
              {/* Property details */}
              <div className="border-t border-gray-100 pt-3 mt-2">
                <div className="flex flex-wrap gap-1 mb-3">
                  {hotel.amenities?.slice(0, 5).map((amenity, index) => (
                    <span 
                      key={index}
                      className="inline-flex items-center bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded-full"
                    >
                      {amenity}
                    </span>
                  ))}
                  {hotel.amenities?.length > 5 && (
                    <span className="inline-flex items-center bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded-full">
                      +{hotel.amenities.length - 5} more
                    </span>
                  )}
                </div>
                
                <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
                  <div className="flex items-center">
                    <MapPin className="h-3 w-3 mr-1 text-gray-500" />
                    <span>{hotel.location || "Location N/A"}</span>
                  </div>
                  <div className="flex items-center">
                    <span>
                      {typeof hotel.distance_to_center === 'number' ? 
                        `${hotel.distance_to_center.toFixed(1)} km from center` : 
                        "Distance not available"
                      }
                    </span>
                  </div>
                  <div className="flex items-center">
                    <span>
                      Room: {hotel.room_type || "Standard"}
                    </span>
                  </div>
                  <div className="flex items-center">
                    {hotel.breakfast_included ? (
                      <span className="text-green-600">✓ Breakfast included</span>
                    ) : (
                      <span className="text-gray-500">✗ No breakfast</span>
                    )}
                  </div>
                </div>
                
                <div className="mt-3 pt-2 border-t border-gray-100 text-xs">
                  <span className={`
                    ${hotel.refundable ? 'text-green-600' : 'text-orange-500'} font-medium
                  `}>
                    {hotel.cancellation_policy || (hotel.refundable ? "Free cancellation" : "Non-refundable")}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        {/* Show More Button */}
        {hotels.options.length > 3 && (
          <div className="text-center mt-4">
            <button
              onClick={() => setShowAll(!showAll)}
              className="text-primary-600 font-medium text-sm hover:text-primary-700 focus:outline-none"
            >
              {showAll ? 'Show fewer options' : `Show all ${hotels.options.length} options`}
            </button>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="card mb-8">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Your AI-Generated Trip to {itinerary.destination}
            </h1>
            <div className="flex flex-wrap items-center gap-4 text-gray-600">
              <div className="flex items-center">
                <Calendar className="h-4 w-4 mr-1" />
                <span>{itinerary.total_days} days</span>
              </div>
              <div className="flex items-center">
                <DollarSign className="h-4 w-4 mr-1" />
                <span>{formatCurrency(itinerary.total_cost)}</span>
              </div>
              <div className="flex items-center">
                <MapPin className="h-4 w-4 mr-1" />
                <span>{itinerary.destination}</span>
              </div>
            </div>
          </div>
          
          <div className="flex gap-3 mt-4 lg:mt-0">
            <button 
              onClick={handleSaveTrip}
              disabled={isLoading.save}
              className="btn-secondary flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Heart className="h-4 w-4 mr-2" />
              {isLoading.save ? 'Saving...' : 'Save Trip'}
            </button>
            <button 
              onClick={handleShareTrip}
              disabled={isLoading.share}
              className="btn-secondary flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Share2 className="h-4 w-4 mr-2" />
              {isLoading.share ? 'Sharing...' : 'Share'}
            </button>
            <button 
              onClick={handleDownloadPDF}
              disabled={isLoading.pdf}
              className="btn-primary flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Download className="h-4 w-4 mr-2" />
              {isLoading.pdf ? 'Generating...' : 'Download PDF'}
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'itinerary', label: 'Day-by-Day Itinerary', icon: Calendar },
              { id: 'summary', label: 'Booking Details', icon: MapPin },
              { id: 'costs', label: 'Cost Breakdown', icon: DollarSign }
            ].map(tab => {
              const IconComponent = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <IconComponent className="h-4 w-4 mr-2" />
                  {tab.label}
                </button>
              )
            })}
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'itinerary' && (
        <div className="space-y-8">
          {itinerary.daily_itinerary?.map((day, index) => (
            <div key={day.day} className="card border-l-4 border-l-primary-500">
              <div 
                className="flex items-center justify-between cursor-pointer group hover:bg-gray-50 -m-6 p-6 rounded-lg transition-colors"
                onClick={() => toggleDay(day.day)}
              >
                <div className="flex items-center">
                  <div className="w-12 h-12 bg-primary-600 text-white rounded-full flex items-center justify-center font-bold mr-4">
                    {day.day}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      Day {day.day} - {day.date}
                    </h3>
                    <p className="text-gray-600 flex items-center flex-wrap gap-4">
                      <span className="flex items-center">
                        <Camera className="h-4 w-4 mr-1" />
                        {day.activities?.length || 0} activities
                      </span>
                      <span className="flex items-center">
                        <Utensils className="h-4 w-4 mr-1" />
                        {day.meals?.length || 0} meals
                      </span>
                      <span className="flex items-center">
                        <DollarSign className="h-4 w-4 mr-1" />
                        {formatCurrency(day.estimated_cost)}
                      </span>
                    </p>
                  </div>
                </div>
                {expandedDays.includes(day.day) ? (
                  <div className="flex items-center text-primary-600">
                    <span className="text-sm mr-2">Hide details</span>
                    <ChevronUp className="h-5 w-5" />
                  </div>
                ) : (
                  <div className="flex items-center text-gray-500 group-hover:text-primary-600">
                    <span className="text-sm mr-2">View details</span>
                    <ChevronDown className="h-5 w-5" />
                  </div>
                )}
              </div>

              {expandedDays.includes(day.day) && (
                <div className="mt-6 space-y-6">
                  {/* Activities */}
                  {day.activities && day.activities.length > 0 && (
                    <div className="bg-gradient-to-r from-emerald-50 to-teal-50 p-6 rounded-xl border border-emerald-200">
                      <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
                        <Camera className="h-5 w-5 mr-2 text-emerald-600" />
                        Activities & Experiences
                      </h4>
                      
                      {/* Grouped activities by time period */}
                      {Object.entries(groupActivitiesByTimePeriod(day.activities)).map(([period, activities]) => {
                        const { label, color, icon } = getTimePeriodInfo(period)
                        
                        if (activities.length === 0) return null;
                        
                        return (
                          <div key={period} className="mb-6 last:mb-0">
                            <div className={`inline-flex items-center text-xs font-semibold ${color} rounded-full py-2 px-4 mb-4 shadow-sm`}>
                              <span className="mr-2 text-sm">{icon}</span>
                              <span>{label}</span>
                            </div>
                            
                            <div className="space-y-4">
                              {activities.map((activity, idx) => (
                                <div key={idx} className="flex items-start p-4 bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow gap-4">
                                  <div className="w-20 text-sm font-semibold text-primary-600 flex-shrink-0 bg-primary-50 px-2 py-1 rounded">
                                    {activity.time}
                                  </div>
                                  <div className="flex-grow min-w-0">
                                    <h5 className="font-medium text-gray-900">{activity.name}</h5>
                                    {activity.description && (
                                      <p className="text-sm text-gray-600 mt-1">{activity.description}</p>
                                    )}
                                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                                      {activity.duration && (
                                        <span className="flex items-center">
                                          <Clock className="h-3 w-3 mr-1" />
                                          {activity.duration}
                                        </span>
                                      )}
                                      {activity.cost && (
                                        <span className="flex items-center">
                                          <DollarSign className="h-3 w-3 mr-1" />
                                          {formatCurrency(activity.cost)}
                                        </span>
                                      )}
                                      {activity.location && (
                                        <span className="flex items-center">
                                          <MapPin className="h-3 w-3 mr-1" />
                                          {activity.location}
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}

                  {/* Meals */}
                  {day.meals && day.meals.length > 0 && (
                    <div className="bg-gradient-to-r from-orange-50 to-amber-50 p-6 rounded-xl border border-orange-200">
                      <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
                        <Utensils className="h-5 w-5 mr-2 text-orange-600" />
                        Dining Experiences
                      </h4>
                      <div className="space-y-3">
                        {day.meals.map((meal, idx) => (
                          <div key={idx} className="flex items-center justify-between p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
                            <div className="flex items-center gap-4 flex-grow min-w-0">
                              <span className="w-20 text-sm font-semibold text-orange-600 flex-shrink-0 bg-orange-50 px-2 py-1 rounded">
                                {meal.time}
                              </span>
                              <div className="min-w-0">
                                <span className="font-medium text-gray-900">{meal.name}</span>
                                {meal.cuisine && (
                                  <span className="text-sm text-gray-600 ml-2">• {meal.cuisine}</span>
                                )}
                              </div>
                            </div>
                            {meal.cost && (
                              <span className="text-sm font-medium text-gray-900">
                                {formatCurrency(meal.cost)}
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Accommodation */}
                  {day.accommodation && (
                    <div className="bg-gradient-to-r from-indigo-50 to-purple-50 p-6 rounded-xl border border-indigo-200">
                      <h4 className="font-semibold text-gray-900 mb-4 flex items-center">
                        <Hotel className="h-5 w-5 mr-2 text-indigo-600" />
                        Your Stay
                      </h4>
                      <div className="p-4 bg-white rounded-lg border border-indigo-100 shadow-sm">
                        <div className="flex items-start justify-between">
                          <div>
                            <p className="font-semibold text-gray-900 text-lg">
                              {day.accommodation.name || 'Hotel Stay'}
                            </p>
                            {day.accommodation.location && (
                              <p className="text-sm text-gray-600 mt-1 flex items-center">
                                <MapPin className="h-4 w-4 mr-1" />
                                {day.accommodation.location}
                              </p>
                            )}
                            {day.accommodation.rating && (
                              <div className="flex items-center mt-2">
                                <Star className="h-4 w-4 text-yellow-500 mr-1" />
                                <span className="text-sm font-medium text-gray-700">
                                  {day.accommodation.rating}/5
                                </span>
                              </div>
                            )}
                          </div>
                          {day.accommodation.price_per_night && (
                            <div className="text-right">
                              <p className="text-sm text-gray-500">per night</p>
                              <p className="font-semibold text-lg text-green-600">
                                {formatCurrency(day.accommodation.price_per_night)}
                              </p>
                            </div>
                          )}
                        </div>
                        
                        {day.accommodation.amenities && day.accommodation.amenities.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-gray-100">
                            <div className="flex flex-wrap gap-2">
                              {day.accommodation.amenities.slice(0, 4).map((amenity: string, idx: number) => (
                                <span key={idx} className="text-xs bg-indigo-50 text-indigo-700 px-2 py-1 rounded-full">
                                  {amenity}
                                </span>
                              ))}
                              {day.accommodation.amenities.length > 4 && (
                                <span className="text-xs text-gray-500">
                                  +{day.accommodation.amenities.length - 4} more
                                </span>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {activeTab === 'summary' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Flight Information */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Plane className="h-5 w-5 mr-2 text-primary-600" />
              Flight Options
            </h3>
            {itinerary.flights?.options && Array.isArray(itinerary.flights.options) && itinerary.flights.options.length > 0 ? (
              <div className="space-y-4">
                {/* Flight summary header */}
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <p className="text-sm font-medium text-gray-700">
                      Found {itinerary.flights.options.length} flight options
                    </p>
                    <p className="text-xs text-gray-500">Scroll to view all options</p>
                  </div>
                  <div className="flex gap-2">
                    <button className="px-3 py-1 text-xs bg-blue-50 text-blue-600 rounded-full hover:bg-blue-100 focus:outline-none">
                      <span className="font-medium">Sort:</span> Cheapest
                    </button>
                  </div>
                </div>
                
                {/* Scroll indicator */}
                <div className="flex items-center justify-center mb-2 text-xs text-gray-400">
                  <ChevronDown className="h-3 w-3 animate-bounce" />
                  <span className="mx-1">Scroll to see more</span>
                  <ChevronDown className="h-3 w-3 animate-bounce" />
                </div>
                
                {/* All Flights in a scrollable container */}
                <div 
                  className="max-h-[500px] overflow-y-auto pr-1"
                  style={{
                    scrollbarWidth: 'thin',
                    scrollbarColor: '#CBD5E0 transparent',
                  }}
                >
                  <div className="space-y-3">
                    {itinerary.flights.options.map((flight, idx) => (
                      <div key={flight.id || idx} className="p-4 bg-gray-50 rounded-lg border border-gray-200 hover:shadow-md transition-shadow">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <div className="flex items-center">
                              <span className="font-medium text-gray-900 mr-2">
                                {Array.isArray(flight.airlines) ? flight.airlines.join(' + ') : 'Unknown Airline'}
                              </span>
                              {idx === 0 && (
                                <span className="bg-green-100 text-green-800 text-xs px-2 py-0.5 rounded">
                                  Best Value
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-2 mt-1">
                              <span className="text-sm py-0.5 px-2 bg-blue-50 text-blue-700 rounded-full">
                                {typeof flight.total_duration === 'string' ? flight.total_duration.replace('PT', '').replace('H', 'h ').replace('M', 'm').toLowerCase() : 'N/A'}
                              </span>
                              <span className="text-sm py-0.5 px-2 bg-gray-100 text-gray-700 rounded-full">
                                {flight.total_stops === 0 ? 'Direct' : `${flight.total_stops || '?'} stop(s)`}
                              </span>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="font-medium text-green-600 text-lg">
                              {formatCurrency(typeof flight.price_inr === 'number' ? flight.price_inr : 0)}
                            </p>
                            {flight.bookable_seats && flight.bookable_seats > 0 && (
                              <p className="text-xs text-orange-600">
                                {flight.bookable_seats} seats left
                              </p>
                            )}
                          </div>
                        </div>
                        
                        {/* Segments in a clearer layout */}
                        <div className="space-y-2 mt-3">
                          {Array.isArray(flight.segments) ? flight.segments.map((segment, segIdx) => (
                            <div key={segIdx} className="border-l-2 border-blue-200 pl-3 py-1">
                              <div className="flex items-center mb-1">
                                <span className="font-medium text-sm mr-2">{segment.flight_number || 'Flight'}</span>
                                <span className="text-xs text-gray-500">{segment.cabin || 'Economy'}</span>
                                {segment.aircraft && <span className="text-xs text-gray-500 ml-2">({segment.aircraft})</span>}
                              </div>
                              <div className="flex items-center justify-between">
                                <div className="text-sm">
                                  <span className="font-medium">{segment.departure_airport || 'DEP'}</span>
                                  <span className="text-gray-500 ml-1">{String(segment.departure_time || 'N/A')}</span>
                                </div>
                                <div className="text-xs text-gray-400 mx-2">→</div>
                                <div className="text-sm">
                                  <span className="font-medium">{segment.arrival_airport || 'ARR'}</span>
                                  <span className="text-gray-500 ml-1">{String(segment.arrival_time || 'N/A')}</span>
                                </div>
                              </div>
                            </div>
                          )) : <div className="text-gray-500">No segment details available</div>}
                          
                          <div className="mt-2 pt-1 border-t border-gray-100 flex justify-between items-center">
                            <span className="text-xs text-gray-500">{flight.fare_type}</span>
                            {flight.instant_ticketing_required && (
                              <span className="text-xs text-red-600">⚡ Instant</span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                
                {/* Pricing Disclaimer - Only show for sample data */}
                {itinerary.flights.status !== 'live_data' && (
                  <div className="mt-4 p-2 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <div className="flex items-center">
                      <div className="mr-2 text-yellow-600">⚠️</div>
                      <div>
                        <p className="text-xs text-yellow-800 font-medium">
                          Sample data for demonstration purposes only
                        </p>
                      </div>
                    </div>
                  </div>
                )}
                
                {/* Live Data Disclaimer - Show for real API data */}
                {itinerary.flights.status === 'live_data' && (
                  <div className="mt-4 p-2 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center">
                      <div className="mr-2 text-blue-600">🌐</div>
                      <div>
                        <p className="text-xs text-blue-800 font-medium">
                          Real-time flight data via SerpAPI
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-gray-600">Flight options will be displayed here</p>
                <p className="text-xs text-gray-500 mt-1">Currently showing sample data</p>
              </div>
            )}
          </div>

          {/* Accommodation Summary */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Hotel className="h-5 w-5 mr-2 text-primary-600" />
              Hotel Options
            </h3>
            {itinerary.hotels && itinerary.hotels.options && itinerary.hotels.options.length > 0 ? (
              <div className="space-y-4">
                {/* Hotel summary header */}
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <p className="text-sm font-medium text-gray-700">
                      Found {itinerary.hotels.options.length} hotel options
                    </p>
                    <p className="text-xs text-gray-500">Scroll to view all options</p>
                  </div>
                  <div className="flex gap-2">
                    <button className="px-3 py-1 text-xs bg-blue-50 text-blue-600 rounded-full hover:bg-blue-100 focus:outline-none">
                      <span className="font-medium">Sort:</span> Best Value
                    </button>
                  </div>
                </div>
                
                {/* Scroll indicator */}
                <div className="flex items-center justify-center mb-2 text-xs text-gray-400">
                  <ChevronDown className="h-3 w-3 animate-bounce" />
                  <span className="mx-1">Scroll to see more</span>
                  <ChevronDown className="h-3 w-3 animate-bounce" />
                </div>
                
                {/* Hotel display component */}
                <HotelDisplay hotels={itinerary.hotels} />
              </div>
            ) : itinerary.accommodation_summary ? (
              <div className="space-y-3">
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="font-medium">
                    {itinerary.accommodation_summary.type || 'Hotel'}
                  </p>
                  {itinerary.accommodation_summary.cost && (
                    <p className="text-sm font-medium text-green-600">
                      {formatCurrency(itinerary.accommodation_summary.cost)} total
                    </p>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-gray-600">Accommodation recommendations based on your preferences.</p>
            )}
          </div>

          {/* Recommendations */}
          <div className="card lg:col-span-2">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Star className="h-5 w-5 mr-2 text-primary-600" />
              AI Recommendations
            </h3>
            {itinerary.recommendations && itinerary.recommendations.length > 0 ? (
              <ul className="space-y-2">
                {itinerary.recommendations.map((recommendation, index) => (
                  <li key={index} className="flex items-start">
                    <Star className="h-4 w-4 text-yellow-500 mr-2 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-700">{recommendation}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-600">Personalized recommendations based on your trip.</p>
            )}
          </div>
        </div>
      )}

      {activeTab === 'costs' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Cost Breakdown
            </h3>
            {(() => {
              // Calculate proper cost breakdown with correct math
              const flightsCost = itinerary.flights?.options?.[0]?.price_inr || (itinerary.total_cost * 0.3);
              const accommodationCost = itinerary.hotels?.options?.[0]?.total_price || (itinerary.total_cost * 0.4);
              const activitiesCost = itinerary.total_cost * 0.15;
              const mealsCost = itinerary.total_cost * 0.15;
              
              const calculatedTotal = flightsCost + accommodationCost + activitiesCost + mealsCost;
              
              const costBreakdown = [
                { category: 'Flights', cost: flightsCost },
                { category: 'Accommodation', cost: accommodationCost },
                { category: 'Activities', cost: activitiesCost },
                { category: 'Meals', cost: mealsCost }
              ];
              
              return (
                <div className="space-y-4">
                  {costBreakdown.map(({ category, cost }) => (
                    <div key={category} className="flex justify-between items-center py-2 border-b border-gray-100 last:border-0">
                      <span className="text-gray-700 font-medium">{category}</span>
                      <span className="font-semibold text-gray-900">
                        {formatCurrency(cost)}
                      </span>
                    </div>
                  ))}
                  
                  <div className="border-t-2 border-gray-200 pt-4 mt-4">
                    <div className="flex justify-between items-center">
                      <span className="text-lg font-semibold text-gray-900">Total</span>
                      <span className="text-xl font-bold text-primary-600">
                        {formatCurrency(calculatedTotal)}
                      </span>
                    </div>
                  </div>
                  
                  {/* Show breakdown percentages */}
                  <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                    <h4 className="text-sm font-medium text-gray-700 mb-3">Cost Distribution</h4>
                    <div className="space-y-2">
                      {costBreakdown.map(({ category, cost }) => {
                        const percentage = ((cost / calculatedTotal) * 100);
                        return (
                          <div key={category} className="flex items-center justify-between text-sm">
                            <span className="text-gray-600">{category}</span>
                            <div className="flex items-center gap-2">
                              <div className="w-16 bg-gray-200 rounded-full h-2">
                                <div 
                                  className="bg-primary-500 h-2 rounded-full" 
                                  style={{ width: `${percentage}%` }}
                                ></div>
                              </div>
                              <span className="font-medium text-gray-700 w-10 text-right">
                                {percentage.toFixed(0)}%
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              );
            })()}
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Daily Budget
            </h3>
            {(() => {
              // Calculate daily costs from the itinerary
              const totalDailyCosts = itinerary.daily_itinerary?.reduce((sum, day) => sum + (day.estimated_cost || 0), 0) || 0;
              const averageDailyCost = totalDailyCosts / (itinerary.total_days || 1);
              const flightsCost = itinerary.flights?.options?.[0]?.price_inr || (itinerary.total_cost * 0.3);
              const accommodationCost = itinerary.hotels?.options?.[0]?.total_price || (itinerary.total_cost * 0.4);
              const calculatedTotal = flightsCost + accommodationCost + totalDailyCosts;
              
              return (
                <div className="space-y-4">
                  <div className="p-4 bg-gradient-to-r from-primary-50 to-blue-50 rounded-lg border border-primary-200">
                    <p className="text-sm text-primary-700 mb-1">Average per day</p>
                    <p className="text-3xl font-bold text-primary-900">
                      {formatCurrency(averageDailyCost)}
                    </p>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                      <p className="text-xs text-green-700 mb-1">Total Trip Cost</p>
                      <p className="text-lg font-semibold text-green-800">
                        {formatCurrency(calculatedTotal)}
                      </p>
                    </div>
                    <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                      <p className="text-xs text-blue-700 mb-1">Daily Activities</p>
                      <p className="text-lg font-semibold text-blue-800">
                        {formatCurrency(averageDailyCost)}
                      </p>
                    </div>
                  </div>
                  
                  <div className="text-sm text-gray-600 space-y-1">
                    <p className="flex items-center">
                      <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                      Includes accommodation, meals, and activities
                    </p>
                    <p className="flex items-center">
                      <span className="w-2 h-2 bg-yellow-400 rounded-full mr-2"></span>
                      Excludes shopping and personal expenses
                    </p>
                    <p className="flex items-center">
                      <span className="w-2 h-2 bg-blue-400 rounded-full mr-2"></span>
                      Prices may vary based on season and availability
                    </p>
                  </div>
                  
                  {/* Budget vs Actual */}
                  {itinerary.total_cost && (
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Budget Analysis</h4>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Original Budget:</span>
                        <span className="font-medium">{formatCurrency(itinerary.total_cost)}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Calculated Cost:</span>
                        <span className="font-medium">{formatCurrency(calculatedTotal)}</span>
                      </div>
                      <div className="flex justify-between items-center mt-1 pt-1 border-t border-gray-200">
                        <span className="text-sm font-medium text-gray-700">
                          {calculatedTotal <= itinerary.total_cost ? 'Under Budget:' : 'Over Budget:'}
                        </span>
                        <span className={`font-semibold ${calculatedTotal <= itinerary.total_cost ? 'text-green-600' : 'text-red-600'}`}>
                          {formatCurrency(Math.abs(itinerary.total_cost - calculatedTotal))}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              );
            })()}
          </div>
        </div>
      )}

      {/* Toast notifications */}
      <ToastContainer toasts={toasts} onRemove={removeToast} />

      {/* Modal dialog */}
      <Modal
        isOpen={modal.isOpen}
        title={modal.title}
        onClose={closeModal}
      >
        <div className="space-y-4">
          <p className="text-gray-700">{modal.content}</p>
          
          {modal.type === 'input' && (
            <input
              type="text"
              value={modal.inputValue || ''}
              onChange={(e) => setModal(prev => ({ ...prev, inputValue: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter title..."
              autoFocus
            />
          )}
          
          <div className="flex justify-end space-x-3">
            <button
              onClick={() => {
                if (modal.onCancel) modal.onCancel()
                else closeModal()
              }}
              className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={() => {
                if (modal.onConfirm) {
                  modal.onConfirm(modal.inputValue)
                }
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              {modal.type === 'input' ? 'Save' : 'Confirm'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
