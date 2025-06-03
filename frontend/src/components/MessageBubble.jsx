import React from 'react';

export default function MessageBubble({ sender, text }) {
  const isUser = sender === 'user';
  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
      key={text}
    >
      <div
        className={`max-w-[80%] px-4 py-2 rounded-2xl shadow-sm break-words ${
          isUser
            ? 'bg-indigo-600 text-white rounded-bl-2xl rounded-tr-2xl'
            : 'bg-white text-gray-800 rounded-br-2xl rounded-tl-2xl'
        }`}
      >
        {text}
      </div>
    </div>
  );
}
