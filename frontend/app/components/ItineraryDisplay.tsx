'use client'

import { useState } from 'react'
import { 
  MapPin, Calendar, Users, DollarSign, Plane, Hotel, 
  Camera, Utensils, Clock, Star, ChevronDown, ChevronUp,
  Download, Share2, Heart
} from 'lucide-react'

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

interface TripItinerary {
  destination: string
  total_days: number
  total_cost: number
  currency: string
  daily_itinerary: DayItinerary[]
  flights: FlightData
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
}

export default function ItineraryDisplay({ itinerary }: ItineraryDisplayProps) {
  const [expandedDays, setExpandedDays] = useState<number[]>([1])
  const [activeTab, setActiveTab] = useState<'itinerary' | 'summary' | 'costs'>('itinerary')
  const [showAllFlights, setShowAllFlights] = useState<boolean>(false)

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
    return `₹${Math.round(amount).toLocaleString()}`;
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
            <button className="btn-secondary flex items-center">
              <Heart className="h-4 w-4 mr-2" />
              Save Trip
            </button>
            <button className="btn-secondary flex items-center">
              <Share2 className="h-4 w-4 mr-2" />
              Share
            </button>
            <button className="btn-primary flex items-center">
              <Download className="h-4 w-4 mr-2" />
              Download PDF
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
              { id: 'summary', label: 'Trip Summary', icon: MapPin },
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
        <div className="space-y-6">
          {itinerary.daily_itinerary?.map((day, index) => (
            <div key={day.day} className="card">
              <div 
                className="flex items-center justify-between cursor-pointer"
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
                    <p className="text-gray-600">
                      {day.activities?.length || 0} activities • {formatCurrency(day.estimated_cost)}
                    </p>
                  </div>
                </div>
                {expandedDays.includes(day.day) ? (
                  <ChevronUp className="h-5 w-5 text-gray-400" />
                ) : (
                  <ChevronDown className="h-5 w-5 text-gray-400" />
                )}
              </div>

              {expandedDays.includes(day.day) && (
                <div className="mt-6 space-y-6">
                  {/* Activities */}
                  {day.activities && day.activities.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                        <Camera className="h-4 w-4 mr-2 text-primary-600" />
                        Activities
                      </h4>
                      <div className="space-y-3">
                        {day.activities.map((activity, idx) => (
                          <div key={idx} className="flex items-start p-3 bg-gray-50 rounded-lg">
                            <div className="w-16 text-sm font-medium text-gray-600 flex-shrink-0">
                              {activity.time}
                            </div>
                            <div className="flex-grow">
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
                  )}

                  {/* Meals */}
                  {day.meals && day.meals.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                        <Utensils className="h-4 w-4 mr-2 text-primary-600" />
                        Dining
                      </h4>
                      <div className="space-y-2">
                        {day.meals.map((meal, idx) => (
                          <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                            <div className="flex items-center">
                              <span className="w-16 text-sm font-medium text-gray-600">
                                {meal.time}
                              </span>
                              <div>
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
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                        <Hotel className="h-4 w-4 mr-2 text-primary-600" />
                        Accommodation
                      </h4>
                      <div className="p-3 bg-gray-50 rounded-lg">
                        <p className="font-medium text-gray-900">
                          {day.accommodation.name || 'Hotel Stay'}
                        </p>
                        {day.accommodation.location && (
                          <p className="text-sm text-gray-600">{day.accommodation.location}</p>
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
                
                {/* Pricing Disclaimer */}
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
              Accommodation
            </h3>
            {itinerary.accommodation_summary ? (
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
            {itinerary.cost_breakdown ? (
              <div className="space-y-3">
                {Object.entries(itinerary.cost_breakdown).map(([category, cost]) => (
                  <div key={category} className="flex justify-between items-center">
                    <span className="text-gray-700 capitalize">
                      {category.replace('_', ' ')}
                    </span>
                    <span className="font-medium">
                      {formatCurrency(cost as number)}
                    </span>
                  </div>
                ))}
                <div className="border-t pt-3 mt-3">
                  <div className="flex justify-between items-center font-semibold text-lg">
                    <span>Total</span>
                    <span className="text-primary-600">
                      {formatCurrency(itinerary.total_cost)}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-gray-600">Cost breakdown will be calculated based on your itinerary.</p>
            )}
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Daily Budget
            </h3>
            <div className="space-y-3">
              <div className="p-4 bg-primary-50 rounded-lg">
                <p className="text-sm text-primary-700 mb-1">Average per day</p>
                <p className="text-2xl font-bold text-primary-900">
                  {formatCurrency(Math.round(itinerary.total_cost / itinerary.total_days))}
                </p>
              </div>
              <div className="text-sm text-gray-600">
                <p>• Includes accommodation, meals, and activities</p>
                <p>• Excludes shopping and personal expenses</p>
                <p>• Prices may vary based on season and availability</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
