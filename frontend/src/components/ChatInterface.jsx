import React, { useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faPaperPlane, faPenToSquare, faStop } from "@fortawesome/free-solid-svg-icons";
import FileUpload from "./FileUpload";
import aivis from "../assets/ai-assistant.png";

const ChatInterface = () => {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);

  const handleSend = () => {
    if (input.trim() === "") return;

    const newMessage = {
      id: Date.now(),
      type: "user",
      text: input,
    };

    setMessages([...messages, newMessage]);
    setInput("");

    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          type: "ai",
          text: "This is a sample AI response to your question.",
        },
      ]);
    }, 1000);
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
    <div className="chatinterface">
      <div className="chat-header text-center">
        <img src={aivis} alt="ai_visualiser" className="img-fluid visual_img" />
        <h2 className="grad_text">Ask Recallo</h2>
      </div>

      {/* Chat Response Section protoype model not ready */}
      {/* <div className="chat-response-section">
        <div className="chat-response user">
          <p>
            <strong>You:</strong> What is quantum computing?
          </p>
          <div className="message-actions d-flex mt-3">
            <button className="btn chat_ic me-2">
              <FontAwesomeIcon
                icon="fa-solid fa-pen-to-square"
                size="2xs"
                style={{ color: "#ffffff" }}
              />
            </button>
            <button className="btn chat_ic">
              <FontAwesomeIcon
                icon="fa-solid fa-stop"
                size="2xs"
                style={{ color: "#ffffff" }}
              />
            </button>
          </div>
        </div>
        <div className="chat-response ai">
          <p>
            <strong className="d-flex align-items-center mb-3"> <img src={aivis} alt="ai_visualiser" className="img-fluid visual_img rec_img" />Recallo:</strong> Quantum computing is a type of computation that
            takes advantage of quantum phenomena...
          </p>
        </div>
      </div> */}

      <div className="chat-response-section">
        {messages.map((msg) => (
          <div key={msg.id} className={`chat-response ${msg.type}`}>
            {msg.type === "user" ? (
              <>
                <p>
                  <strong>You:</strong> {msg.text}
                </p>
                <div className="message-actions message-actions d-flex mt-3">
                  <button className="btn chat_ic me-2" onClick={() => handleEdit(msg.id)}>
                    <FontAwesomeIcon icon={faPenToSquare} style={{ color: "#ffffff" }} />
                  </button>
                  <button className="btn chat_ic" onClick={handleStop}>
                    <FontAwesomeIcon icon={faStop} style={{ color: "#ffffff" }} />
                  </button>
                </div>
              </>
            ) : (
              <p>
                <strong className="d-flex align-items-center mb-3">
                  <img src={aivis} alt="ai_visualiser" className="img-fluid visual_img rec_img" />
                  Recallo:
                </strong>  
                {msg.text}
              </p>
            )}
          </div>
        ))}
      </div>

      <div className="chat-input-section">
        <FileUpload onFileSelect={handleFileSelect} />
        <textarea
          rows={1}
          placeholder="Type your question here..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button className="send-button btn btn-cs" onClick={handleSend}>
          <FontAwesomeIcon icon={faPaperPlane} />
        </button>
      </div>
    </div>
  );
};

export default ChatInterface;
