import React, { useState, useEffect, useRef } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faPaperPlane,
  faPenToSquare,
  faStop,
  faSpinner,
} from "@fortawesome/free-solid-svg-icons";
import FileUpload from "./FileUpload";
import aivis from "../assets/ai-assistant.png";
import ReactMarkdown from "react-markdown";
import TextareaAutosize from "react-textarea-autosize";


const ChatInterface = () => {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false); // Track loading state

  // Reference to the chat container
  const chatContainerRef = useRef(null);

  // Scroll to the bottom whenever messages change
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop =
        chatContainerRef.current.scrollHeight;
    }
  }, [messages]); // This runs whenever the messages state changes

  const handleSend = async () => {
    if (input.trim() === "") return;

    // Add user message to the chat
    const newMessage = {
      id: Date.now(),
      type: "user",
      text: input,
    };

    setMessages([...messages, newMessage]);
    setInput("");
    setLoading(true); // Show loading spinner

    try {
      // Send user input to the Flask backend
      const response = await fetch("http://127.0.0.1:5000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: input }),
      });

      const data = await response.json();

      // After receiving the AI response, add it to the chat
      if (data.response) {
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now() + 1,
            type: "ai",
            text: data.response, // Display the AI response
          },
        ]);
      }
    } catch (error) {
      console.error("Error sending message to backend:", error);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          type: "ai",
          text: "Sorry, there was an error. Please try again later.",
        },
      ]);
    } finally {
      setLoading(false); // Hide loading spinner
    }
  };

  const handleFileSelect = (file) => {
    console.log("Selected file:", file);
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
    alert("Stop action triggered.");
  };

  return (
    <div
      className="chatinterface"
      style={{ height: "100vh", display: "flex", flexDirection: "column" }}
    >
      <div className="chat-header text-center">
        <img src={aivis} alt="ai_visualiser" className="img-fluid visual_img" />
        <h2 className="grad_text">Ask Recallo</h2>
      </div>

      {/* Entire chat window is scrollable */}
      <div
        className="chat-response-section"
        ref={chatContainerRef}
        style={{
          flexGrow: 1, // Allow the chat window to take available height
          overflowY: "auto", // Enable vertical scrolling
          padding: "10px",
          marginBottom: "50px", // Optional: Add space below for the input box
        }}
      >
        {messages.map((msg) => (
          <div key={msg.id} className={`chat-response ${msg.type}`}>
            {msg.type === "user" ? (
              <>
                <p>
                  <strong>You:</strong> {msg.text}
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
                {loading && msg.id === messages[messages.length - 1]?.id ? (
                  <div className="processing-spinner">
                    <FontAwesomeIcon icon={faSpinner} spin /> Processing...
                  </div>
                ) : (
                  <ReactMarkdown>{msg.text}</ReactMarkdown>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="chat-input-section" style={{ padding: "10px" }}>
        <FileUpload onFileSelect={handleFileSelect} />
        <TextareaAutosize
          rows={1}
          placeholder="Type your question here..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          style={{ width: "100%", padding: "10px" }}
        />
        <button className="send-button btn btn-cs" onClick={handleSend}>
          {loading ? (
            <FontAwesomeIcon icon={faSpinner} spin />
          ) : (
            <FontAwesomeIcon icon={faPaperPlane} />
          )}
        </button>
      </div>
    </div>
  );
};

export default ChatInterface;
