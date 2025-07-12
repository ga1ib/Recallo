import React, { useState, useEffect, useRef } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faPenToSquare,
  faStop,
  faSpinner,
} from "@fortawesome/free-solid-svg-icons";
import aivis from "../assets/ai-assistant.png";
import Typewriter from "./Typewriter";
import ChatInput from "./ChatInput";
import History from "./History";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_KEY
);

const ChatInterface = () => {
  // State variables from both components
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [controller, setController] = useState(null);
  const [userId, setUserId] = useState(null);
  const [useDocumentMode, setUseDocumentMode] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [currentConv, setCurrentConv] = useState(null);
  const [messages, setMessages] = useState([]);
  const chatContainerRef = useRef(null);

  // Scroll to bottom on new messages
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  // Fetch user session on mount
  useEffect(() => {
    const fetchSession = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (session?.user?.id) {
        setUserId(session.user.id);
      }
    };
    fetchSession();
  }, []);

  // Create new conversation
  const handleNewConversation = async () => {
    if (!userId) {
      console.error("User not logged in");
      return null;
    }

    try {
      const response = await fetch("http://127.0.0.1:5000/api/conversations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId }),
      });

      if (response.ok) {
        const newConversation = await response.json();
        const newConvId = newConversation.conversation_id;
        setCurrentConv(newConvId);
        setMessages([]);
        return newConvId;
      } else {
        console.error("Failed to create new conversation");
        return null;
      }
    } catch (error) {
      console.error("Error creating new conversation:", error);
      return null;
    }
  };

  // Select conversation from history
  const handleSelectConversation = async (convId) => {
    setHistoryOpen(false);
    setCurrentConv(convId);

    try {
      // Fetch messages for this conversation
      const response = await fetch(`http://127.0.0.1:5000/api/conversations/${convId}/logs`);
      if (response.ok) {
        const logs = await response.json();

        // Convert backend logs to frontend message format
        const convertedMessages = [];
        logs.forEach((log) => {
          // Add user message
          convertedMessages.push({
            id: `user-${log.id}`,
            type: "user",
            text: log.user_message,
          });

          // Add AI response
          convertedMessages.push({
            id: `ai-${log.id}`,
            type: "ai",
            text: log.response_message,
          });
        });

        setMessages(convertedMessages);
      } else {
        console.error("Failed to fetch conversation messages");
        setMessages([]);
      }
    } catch (error) {
      console.error("Error fetching conversation messages:", error);
      setMessages([]);
    }
  };

  // Send message to API
  const handleSend = async () => {
    if (input.trim() === "") return;

    // Ensure we have a conversation
    let conversationId = currentConv;
    if (!conversationId) {
      conversationId = await handleNewConversation();
      if (!conversationId) {
        console.error("Failed to create conversation");
        return;
      }
    }

    if (controller) controller.abort();
    const abortController = new AbortController();
    setController(abortController);

    // User message
    const userMsg = {
      id: Date.now(),
      type: "user",
      text: input,
    };

    // Processing indicator
    const processingMsg = {
      id: "processing-" + Date.now(),
      type: "ai",
      text: "Recallo is processing...",
      isProcessing: true,
    };

    // Update UI immediately
    setMessages((prev) => [...prev, userMsg, processingMsg]);
    setInput("");
    setLoading(true);

    try {
      // API call (using Flask endpoint from second component)
      const response = await fetch(
        `http://127.0.0.1:5000/${useDocumentMode ? "ask" : "chat"}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: input,
            user_id: userId,
            conversation_id: conversationId
          }),
          signal: abortController.signal,
        }
      );

      const data = await response.json();
      console.log("API Response:", data);

      // Replace processing message with actual response
      const aiReply = {
        id: Date.now() + 1,
        type: "ai",
        text: data.response || "Sorry, I couldn't generate a response.",
      };

      setMessages((prev) =>
        prev.map((msg) => 
          msg.id === processingMsg.id ? aiReply : msg
        )
      );
    } catch (error) {
      console.error("Error:", error);
      const errorReply = {
        id: Date.now() + 2,
        type: "ai",
        text: error.name === "AbortError"
          ? "⚠️ Response stopped by user."
          : "⚠️ Something went wrong. Please try again.",
      };
      setMessages((prev) =>
        prev.map((msg) => 
          msg.id === processingMsg.id ? errorReply : msg
        )
      );
    } finally {
      setLoading(false);
      setController(null);
    }
  };

  // UI actions
  const handleFileSelect = (file) => {
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now(),
        type: "user",
        text: `📎 Uploaded: ${file.name}`,
      },
    ]);
  };

  const handleEdit = (id) => {
    const toEdit = messages.find((msg) => msg.id === id);
    if (toEdit) {
      setInput(toEdit.text);
      setMessages(messages.filter((msg) => msg.id !== id));
    }
  };

  const handleStop = () => {
    if (controller) controller.abort();
    setLoading(false);
    setController(null);
  };

  return (
    <div className="chatinterface" style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      {/* History Toggle Button */}
      <button 
        className="history-toggle"
        onClick={() => setHistoryOpen((o) => !o)}
      >
        {historyOpen ? "Close History" : "Open History"}
      </button>

      {/* History Panel */}
      <History
        isLoggedIn={!!userId}
        isHistoryOpen={historyOpen}
        onClose={() => setHistoryOpen(false)}
        userId={userId}
        onNewConversation={handleNewConversation}
        onSelectConversation={handleSelectConversation}
      />

      {/* Chat Content */}
      <div
        className="chat-response-section"
        ref={chatContainerRef}
        style={{
          flexGrow: 1,
          overflowY: "auto",
          padding: "10px",
          marginBottom: "50px",
        }}
      >
        <div className="chat-header text-center mb-4">
          <img
            src={aivis}
            alt="ai_visualiser"
            className="img-fluid visual_img"
          />
          <h2 className="grad_text">Ask Recallo</h2>
        </div>

        {/* Messages */}
        {messages.map((msg) => (
          <div key={msg.id} className={`chat-response ${msg.type}`}>
            {msg.type === "user" ? (
              <>
                <p style={{ whiteSpace: "pre-wrap", marginBottom: 0 }}>
                  <strong style={{ display: "block", marginBottom: "10px" }}>
                    You:
                  </strong>
                  {msg.text}
                </p>
                <div className="message-actions d-flex mt-3">
                  <button
                    className="btn chat_ic me-2"
                    onClick={() => handleEdit(msg.id)}
                  >
                    <FontAwesomeIcon
                      icon={faPenToSquare}
                      style={{ color: "#ffffff" }}
                    />
                  </button>
                  <button className="btn chat_ic" onClick={handleStop}>
                    <FontAwesomeIcon
                      icon={faStop}
                      style={{ color: "#ffffff" }}
                    />
                  </button>
                </div>
              </>
            ) : (
              <div>
                <strong className="d-flex align-items-center mb-3 ai_response">
                  <img
                    src={aivis}
                    alt="ai_visualiser"
                    className="img-fluid visual_img rec_img"
                  />
                  Recallo:
                </strong>
                {msg.isProcessing ? (
                  <div className="processing-spinner">
                    <FontAwesomeIcon icon={faSpinner} spin /> {msg.text}
                  </div>
                ) : (
                  <Typewriter key={msg.id} text={msg.text} />
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Input Area */}
      <ChatInput
        input={input}
        setInput={setInput}
        handleSend={handleSend}
        handleStop={handleStop}
        loading={loading}
        useDocumentMode={useDocumentMode}
        setUseDocumentMode={setUseDocumentMode}
        handleFileSelect={handleFileSelect}
      />
    </div>
  );
};

export default ChatInterface;