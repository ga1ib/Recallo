import React from 'react';
import ChatInterface from '../components/ChatInterface';

export default function Dashboard() {
  return (
    <div className="flex flex-col lg:flex-row min-h-screen">
      {/* Sidebar / Memory Graph (placeholder) */}
      <aside className="lg:w-1/4 bg-stone-950 shadow-lg p-6 hidden lg:block">
        <h2 className="text-2xl font-semibold mb-4 text-stone-200">
          Recallo Dashboard
        </h2>
        <p className="text-gray-600 mb-6">
          Your personalized memory overview.
        </p>
        {/* Placeholder for memory graph or navigation links */}
        <div className="h-64 bg-stone-800 rounded-lg flex items-center justify-center text-gray-400">
          Memory Graph
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-grow bg-stone-950 p-6 flex flex-col items-center">
        <div className="w-full max-w-3xl">
          <div className="bg-stone-900 rounded-2xl shadow-xl p-6 flex flex-col h-96">
            <h2 className="text-2xl font-semibold text-stone-200 mb-4">
              Chat with Recallo
            </h2>
            <ChatInterface />
          </div>
        </div>
      </main>
    </div>
  );
}
