import React from "react";
import TextareaAutosize from "react-textarea-autosize";
import FileUpload from "./FileUpload";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faSpinner } from "@fortawesome/free-solid-svg-icons";
import { MoveUpRight } from "lucide-react";
import { Ban } from "lucide-react";

const ChatInput = ({
  input,
  setInput,
  handleSend,
  handleStop,
  loading,
  useDocumentMode,
  setUseDocumentMode,
  handleFileSelect,
}) => {
  return (
    <div className="chat-input-section">
      <div className="chat-textarea-wrapper">
        <TextareaAutosize
          rows={1}
          placeholder="Type your question here..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          className="chat-textarea"
        />
      </div>
      <div className="chat-actions">
        {/* file select */}
        <div className="fl_action d-flex align-items-center ">
          <FileUpload onFileSelect={handleFileSelect} />
          <button
            className="btn btn-cs ms-2 btn-otl"
            onClick={() => setUseDocumentMode(!useDocumentMode)}
          >
            {useDocumentMode ? "Switch to Chat Mode" : "Switch to Document Mode"}
          </button>
        </div>
        {/* send stop button */}
        <div className="msg_send d-flex">
          <button className="btn btn-otl stop_btn" onClick={handleStop}>
            <Ban style={{ color: "#ffffff" }} />
          </button>
          <button className="send-button btn btn-cs btn-otl" onClick={handleSend}>
            {loading ? (
              <FontAwesomeIcon icon={faSpinner} spin />
            ) : (
              <MoveUpRight />
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default React.memo(ChatInput);