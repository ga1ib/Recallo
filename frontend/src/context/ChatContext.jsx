import React, { createContext, useState, useEffect } from 'react';

export const ChatContext = createContext();

export function ChatProvider({ children }) {
  const [chatHistory, setChatHistory] = useState(() => {
    const saved = localStorage.getItem('recallo_chat');
    return saved ? JSON.parse(saved) : [];
  });

  useEffect(() => {
    localStorage.setItem('recallo_chat', JSON.stringify(chatHistory));
  }, [chatHistory]);

  const addMessage = (msg) => {
    setChatHistory((prev) => [...prev, msg]);
  };

  return (
    <ChatContext.Provider value={{ chatHistory, addMessage }}>
      {children}
    </ChatContext.Provider>
  );
}
