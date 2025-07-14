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
import RecalloVisual3D from "../components/RecalloVisual3D";

const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_KEY
);

const ChatInterface = () => {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [controller, setController] = useState(null);
  const [userId, setUserId] = useState(null);
  const [isHistoryOpen, setIsHistoryOpen] = useState(true);
  const [conversationId, setConversationId] = useState(null);
  const [currentConv, setCurrentConv] = useState(null);
  const chatContainerRef = useRef(null);
  const [useDocumentMode, setUseDocumentMode] = useState(false);

  const [user, setUser] = useState(null);
  
    useEffect(() => {
      const fetchUser = async () => {
        const { data, error } = await supabase.auth.getUser();
        if (!error && data?.user) {
          setUser(data.user);
        }
      };
      fetchUser();
    }, []);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    // Get Supabase session and extract user_id
    const fetchSession = async () => {
      const {
        data: { session },
      } = await supabase.auth.getSession();

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
    setCurrentConv(convId);
    setConversationId(convId);

   // ✅ Fetch messages for selected conversation
   try {
    const response = await fetch(`http://127.0.0.1:5000/api/conversations/${convId}/logs`);
    if (response.ok) {
      const logs = await response.json();

      const convertedMessages = logs.flatMap((log) => [
        { id: `user-${log.message_id}`, type: "user", text: log.user_message },
        { id: `ai-${log.message_id}`, type: "ai", text: log.response_message }
      ]);

      setMessages(convertedMessages);
    }
  } catch (error) {
    console.error("Error fetching messages:", error);
    setMessages([]);
  }
};


  const handleSend = async () => {
    if (input.trim() === "") return;

    if (controller) controller.abort();
    const abortController = new AbortController();
    setController(abortController);

    const userMsg = {
      id: Date.now(),
      type: "user",
      text: input,
    };

    const processingMsg = {
      id: "loading-spinner",
      type: "ai",
      text: "Recallo is processing...",
      isProcessing: true,
    };

    setMessages((prev) => [...prev, userMsg, processingMsg]);
    setInput("");
    setLoading(true);

    try {
      // Prepare request body with conversation_id if available
      const requestBody = {
        message: input,
        user_id: userId
      };

      // Include conversation_id if we have one (for continuing same conversation)
      if (currentConv) {
        requestBody.conversation_id = currentConv;
      }

      const response = await fetch(
        `http://127.0.0.1:5000/${useDocumentMode ? "ask" : "chat"}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(requestBody),
          signal: abortController.signal,
        }
      );

      const data = await response.json();
      console.log("\ud83d\udce9 Full API Response:", data);

      // IMPORTANT: Update currentConv with the conversation_id from response
      if (data.conversation_id && !currentConv) {
        setCurrentConv(data.conversation_id);
        console.log("🆔 Set conversation ID:", data.conversation_id);
      }

      // Replace processing message with actual response
      const aiReply = {
        id: Date.now() + 1,
        type: "ai",
        text: data.response || "Sorry, I couldn't generate a response.",
      };

      setMessages((prev) =>
        prev.map((msg) => (msg.id === "loading-spinner" ? aiReply : msg))
      );
    } catch (error) {
      console.error("Error:", error);
      const errorReply = {
        id: Date.now() + 2,
        type: "ai",
        text:
          error.name === "AbortError"
            ? "\u26a0\ufe0f Response stopped by user."
            : "\u26a0\ufe0f Something went wrong. Please try again.",
      };
      setMessages((prev) =>
        prev.map((msg) => (msg.id === "loading-spinner" ? errorReply : msg))
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
        text: `\ud83d\udcce Uploaded: ${file.name}`,
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
    if (controller) {
      controller.abort();
      setController(null);
    }
    setLoading(false);
  };

  return (
    <div
      className="chatinterface"
      style={{ height: "100vh", display: "flex", flexDirection: "column" }}
    >
       {/* History Panel */}
      <History
        isLoggedIn={!!userId}
        isHistoryOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        userId={userId}
        onSelectConversation={handleSelectConversation} // ✅ passed!
        onNewConversation={handleNewConversation}
      />
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
          <RecalloVisual3D />
          {/* <img
            src={aivis}
            alt="ai_visualiser"
            className="img-fluid visual_img"
          /> */}
          <h2 className="grad_text mt-2">Hello
                  {user?.user_metadata?.full_name
                    ? `, ${user.user_metadata.full_name}`
                    : ""}! Ask Recallo</h2>
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
                    <FontAwesomeIcon icon={faSpinner} spin /> Recallo is
                    processing...
                  </div>
                ) : (
                  <Typewriter key={msg.id} text={msg.text} />
                )}
              </div>
            )}
          </div>
        ))}
      </div>

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