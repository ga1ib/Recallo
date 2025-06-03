import React from 'react';
import { useNavigate } from 'react-router-dom';

export default function Home() {
  const navigate = useNavigate();

  return (
    <div className="relative flex items-center justify-center h-screen bg-gradient-to-br from-indigo-100 to-blue-50">
      {/* Decorative SVG Shapes (optional) */}
      <svg
        className="absolute inset-0 w-full h-full opacity-30"
        xmlns="http://www.w3.org/2000/svg"
        preserveAspectRatio="none"
        viewBox="0 0 600 600"
      >
        <defs>
          <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#6366F1" stopOpacity="0.2" />
            <stop offset="100%" stopColor="#3B82F6" stopOpacity="0.2" />
          </linearGradient>
        </defs>
        <circle cx="300" cy="300" r="300" fill="url(#grad1)" />
      </svg>

      {/* Card */}
      <div className="relative z-10 bg-white rounded-2xl shadow-xl max-w-md w-full p-8">
        <h1 className="text-4xl font-extrabold text-center text-indigo-600 mb-4">
          Welcome to Recallo
        </h1>
        <p className="text-lg text-gray-600 text-center mb-8">
          Your AI-powered study companion. Remember more, stress less.
        </p>
        <ul className="space-y-3 mb-8">
          <li className="flex items-center space-x-2">
            <svg
              className="w-6 h-6 text-green-500"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
            <span>Smart spaced-repetition scheduling</span>
          </li>
          <li className="flex items-center space-x-2">
            <svg
              className="w-6 h-6 text-green-500"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m-6-8h6"
              />
            
            </svg>
            <span>Multi-format input: text, PDF, images</span>
          </li>
          <li className="flex items-center space-x-2">
            <svg
              className="w-6 h-6 text-green-500"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M11 12a1 1 0 112 0 1 1 0 01-2 0zm-2 4a1 1 0 112 0 1 1 0 01-2 0z"
              />
          
            </svg>
            <span>Instant summarizations & chat-style Q&A</span>
          </li>
        </ul>
        <button
          onClick={() => navigate('/dashboard')}
          className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 rounded-lg transition-colors"
        >
          Get Started
        </button>
      </div>
    </div>
  );
}
