'use client'

import { Brain, CheckCircle, Clock, Plane, MapPin, Utensils, Camera } from 'lucide-react'

interface ProgressTrackerProps {
  progress: number
  currentStep: string
  details?: string
}

const PLANNING_STEPS = [
  { id: 'initializing', label: 'Initializing AI Agent', icon: Brain },
  { id: 'goal_interpretation', label: 'Understanding Your Goals', icon: MapPin },
  { id: 'flight_search', label: 'Finding Best Flights', icon: Plane },
  { id: 'hotel_search', label: 'Searching Accommodations', icon: MapPin },
  { id: 'attraction_search', label: 'Discovering Attractions', icon: Camera },
  { id: 'restaurant_search', label: 'Finding Great Restaurants', icon: Utensils },
  { id: 'itinerary_generation', label: 'Creating Your Itinerary', icon: CheckCircle },
]

export default function ProgressTracker({ progress, currentStep, details }: ProgressTrackerProps) {
  const currentStepIndex = PLANNING_STEPS.findIndex(step => 
    currentStep.toLowerCase().includes(step.id) || step.label.toLowerCase().includes(currentStep.toLowerCase())
  )

  return (
    <div className="max-w-4xl mx-auto">
      <div className="card">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-4">
            <Brain className="h-8 w-8 text-primary-600 animate-pulse" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            AI Agent is Planning Your Trip
          </h2>
          <p className="text-gray-600">
            Our intelligent agent is analyzing your preferences and creating the perfect itinerary
          </p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">Progress</span>
            <span className="text-sm font-medium text-primary-600">{Math.round(progress)}%</span>
          </div>
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${progress}%` }}
            ></div>
          </div>
        </div>

        {/* Current Step */}
        <div className="mb-8 p-4 bg-primary-50 rounded-lg border border-primary-200">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
                <Clock className="h-4 w-4 text-white" />
              </div>
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-medium text-primary-900">
                Currently: {currentStep || 'Processing...'}
              </h3>
              {details && (
                <p className="text-primary-700 mt-1">{details}</p>
              )}
            </div>
          </div>
        </div>

        {/* Steps List */}
        <div className="space-y-4">
          {PLANNING_STEPS.map((step, index) => {
            const isCompleted = index < currentStepIndex
            const isCurrent = index === currentStepIndex
            const isPending = index > currentStepIndex
            
            const IconComponent = step.icon

            return (
              <div
                key={step.id}
                className={`flex items-center p-4 rounded-lg transition-all duration-300 ${
                  isCompleted 
                    ? 'bg-green-50 border border-green-200' 
                    : isCurrent 
                      ? 'bg-primary-50 border border-primary-200 shadow-sm' 
                      : 'bg-gray-50 border border-gray-200'
                }`}
              >
                <div className="flex-shrink-0">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    isCompleted 
                      ? 'bg-green-500' 
                      : isCurrent 
                        ? 'bg-primary-600' 
                        : 'bg-gray-300'
                  }`}>
                    {isCompleted ? (
                      <CheckCircle className="h-5 w-5 text-white" />
                    ) : (
                      <IconComponent className={`h-5 w-5 ${
                        isCurrent ? 'text-white animate-pulse' : 'text-gray-600'
                      }`} />
                    )}
                  </div>
                </div>
                <div className="ml-4">
                  <h4 className={`font-medium ${
                    isCompleted 
                      ? 'text-green-900' 
                      : isCurrent 
                        ? 'text-primary-900' 
                        : 'text-gray-500'
                  }`}>
                    {step.label}
                  </h4>
                  <p className={`text-sm ${
                    isCompleted 
                      ? 'text-green-600' 
                      : isCurrent 
                        ? 'text-primary-600' 
                        : 'text-gray-400'
                  }`}>
                    {isCompleted ? '✓ Completed' : isCurrent ? 'In Progress...' : 'Pending'}
                  </p>
                </div>
              </div>
            )
          })}
        </div>

        {/* Fun Facts */}
        <div className="mt-8 p-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
          <h4 className="font-semibold text-gray-900 mb-3">Did you know?</h4>
          <div className="space-y-2 text-sm text-gray-700">
            <p>• Our AI agent considers over 50+ factors when planning your trip</p>
            <p>• We analyze real-time pricing and availability across multiple sources</p>
            <p>• The agent optimizes your itinerary for maximum enjoyment within budget</p>
            <p>• Each recommendation is personalized based on your specific interests</p>
          </div>
        </div>

        {/* Estimated Time */}
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            Estimated completion time: 2-3 minutes
          </p>
          <div className="flex justify-center mt-2">
            <div className="flex space-x-1">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="w-2 h-2 bg-primary-600 rounded-full animate-bounce"
                  style={{ animationDelay: `${i * 0.2}s` }}
                ></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
