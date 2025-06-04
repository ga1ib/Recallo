import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ChatProvider } from './context/ChatContext';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';

export default function App() {
  return (
    <ChatProvider>
      <BrowserRouter>
        <div className="flex flex-col min-h-screen">
          {/* You could add a Header here if needed */}
          <main className="flex-grow">
            <Routes>
              <Route path="/" element={<Navigate to="/home" replace />} />
              <Route path="/home" element={<Home />} />
              <Route path="/dashboard" element={<Dashboard />} />
            </Routes>
          </main>
          <footer className="text-center py-4 text-sm text-gray-500">
            © {new Date().getFullYear()} Recallo. All rights reserved.
          </footer>
        </div>
      </BrowserRouter>
    </ChatProvider>
  );
}
