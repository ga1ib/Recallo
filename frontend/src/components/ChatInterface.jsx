import React, { useState, useRef, useEffect, useContext } from 'react';
import MessageBubble from './MessageBubble';
import FileUpload from './FileUpload';
import Loader from './Loader';
import { ChatContext } from '../context/ChatContext';
import { FaPaperPlane } from 'react-icons/fa';

export default function ChatInterface() {
  const { chatHistory, addMessage } = useContext(ChatContext);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Scroll to bottom when new message arrives
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  const handleSend = async () => {
    if (!input.trim()) return;
    const userMessage = { sender: 'user', text: input.trim() };
    addMessage(userMessage);
    setInput('');
    setLoading(true);

    // Placeholder: simulate AI response after a delay
    setTimeout(() => {
      const botReply = {
        sender: 'bot',
        text:
          "Here's a placeholder response from Recallo. Once connected, your AI engine will answer here!",
      };
      addMessage(botReply);
      setLoading(false);
    }, 1200);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col flex-1 h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-stone-800 rounded-lg border">
        {chatHistory.map((msg, idx) => (
          <MessageBubble key={idx} sender={msg.sender} text={msg.text} />
        ))}
        {loading && <Loader />}
        <div ref={messagesEndRef} />
      </div>

      {/* File Upload & Text Input */}
      <div className="mt-4">
        <FileUpload />
      </div>

      <div className="sticky bottom-0 bg-stone-700 mt-4 rounded-lg shadow-inner">
        <div className="flex items-center space-x-2 p-2">
          <textarea
            className="flex-1 resize-none bg-stone-800 border border-stone-950 rounded-xl px-4 py-2 focus:outline-none text-white focus:ring-2 focus:ring-stone-800"
            rows={2}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
          />
          <button
            onClick={handleSend}
            className="p-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl transition-colors"
          >
            <FaPaperPlane />
          </button>
        </div>
      </div>
    </div>
  );
}
