'use client'

import { useState } from 'react'
import { 
  MapPin, Calendar, Users, DollarSign, Plane, Hotel, 
  Camera, Utensils, Clock, Star, ChevronDown, ChevronUp,
  Download, Share2, Heart
} from 'lucide-react'

interface TripItinerary {
  destination: string
  total_days: number
  total_cost: number
  currency: string
  daily_itinerary: DayItinerary[]
  flights: any
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

  const toggleDay = (day: number) => {
    setExpandedDays(prev => 
      prev.includes(day) 
        ? prev.filter(d => d !== day)
        : [...prev, day]
    )
  }

  const formatCurrency = (amount: number) => {
    return `₹${amount.toLocaleString()}`
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
              Flight Details
            </h3>
            {itinerary.flights ? (
              <div className="space-y-3">
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="font-medium">Outbound Flight</p>
                  <p className="text-sm text-gray-600">
                    Status: {itinerary.flights.status || 'Recommended options available'}
                  </p>
                  {itinerary.flights.cost && (
                    <p className="text-sm font-medium text-green-600">
                      From {formatCurrency(itinerary.flights.cost)}
                    </p>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-gray-600">Flight details will be provided based on your preferences.</p>
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
