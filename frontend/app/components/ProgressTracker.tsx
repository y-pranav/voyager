'use client'

import { Brain, CheckCircle, Clock } from 'lucide-react'

interface ProgressTrackerProps {
  progress: number
  currentStep: string
  details?: string
}

export default function ProgressTracker({ progress, currentStep, details }: ProgressTrackerProps) {
  const isCompleted = progress >= 100

  return (
    <div className="max-w-4xl mx-auto">
      <div className="card">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-4">
            {isCompleted ? (
              <CheckCircle className="h-8 w-8 text-green-600" />
            ) : (
              <Brain className="h-8 w-8 text-primary-600 animate-pulse" />
            )}
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            {isCompleted ? 'Trip Planning Complete!' : 'AI Agent is Planning Your Trip'}
          </h2>
          <p className="text-gray-600">
            {isCompleted 
              ? 'Your personalized itinerary has been created successfully'
              : 'Our intelligent agent is analyzing your preferences and creating the perfect itinerary'
            }
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
        <div className={`mb-8 p-6 rounded-lg border ${
          isCompleted 
            ? 'bg-green-50 border-green-200' 
            : 'bg-primary-50 border-primary-200'
        }`}>
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                isCompleted ? 'bg-green-500' : 'bg-primary-600'
              }`}>
                {isCompleted ? (
                  <CheckCircle className="h-6 w-6 text-white" />
                ) : (
                  <Clock className="h-6 w-6 text-white animate-pulse" />
                )}
              </div>
            </div>
            <div className="ml-4">
              <h3 className={`text-xl font-semibold ${
                isCompleted ? 'text-green-900' : 'text-primary-900'
              }`}>
                {isCompleted ? 'Complete!' : `Currently: ${currentStep || 'Processing...'}`}
              </h3>
              {details && (
                <p className={`mt-1 ${
                  isCompleted ? 'text-green-700' : 'text-primary-700'
                }`}>
                  {details}
                </p>
              )}
              {!isCompleted && (
                <p className="text-primary-600 mt-2">
                  Analyzing your preferences and creating your personalized itinerary...
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Fun Facts - Only show when processing */}
        {!isCompleted && (
          <>
            <div className="mt-8 p-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg">
              <h4 className="font-semibold text-gray-900 mb-3">Did you know?</h4>
              <div className="space-y-2 text-sm text-gray-700">
                <p>• Our AI agent considers multiple factors when planning your trip</p>
                <p>• We create personalized recommendations based on your interests</p>
                <p>• The agent optimizes your itinerary for maximum enjoyment within budget</p>
                <p>• Each suggestion is tailored to your specific travel preferences</p>
              </div>
            </div>

            {/* Estimated Time */}
            <div className="mt-6 text-center">
              <p className="text-sm text-gray-600">
                Estimated completion time: 1-2 minutes
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
          </>
        )}
      </div>
    </div>
  )
}
