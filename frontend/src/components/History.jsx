import React, { useState, useEffect } from "react";
import { Power, Plus, Search } from "lucide-react";


const History = ({
  isLoggedIn,
  isHistoryOpen,
  onClose,
  userId,
  onSelectConversation, // NEW: callback → conversation_id
  onNewConversation     // NEW: callback to parent
}) => {
  const [conversations, setConversations] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");

  // 1️⃣ Fetch all conversations when panel opens
  useEffect(() => {
    if (isHistoryOpen && isLoggedIn && userId) {
      fetch(`http://127.0.0.1:5000/api/conversations?user_id=${userId}`)
        .then((res) => {
          if (res.ok) {
            return res.json();
          }
          throw new Error('Failed to fetch conversations');
        })
        .then(setConversations)
        .catch((error) => {
          console.error('Error fetching conversations:', error);
          setConversations([]);
        });
    }
  }, [isHistoryOpen, isLoggedIn, userId]);

  const filtered = conversations.filter((c) =>
    (c.title || "").toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleNew = async () => {
    try {
      // Ask parent to create a new conversation
      const newId = await onNewConversation();
      if (newId) {
        onSelectConversation(newId);
        // Add the new conversation to the list immediately
        const newConversation = {
          conversation_id: newId,
          title: "New Chat",
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        };
        setConversations([newConversation, ...conversations]);
      }
    } catch (error) {
      console.error('Error creating new conversation:', error);
    }
  };

  return (
    <div className={`history-panel bg-dark text-white p-3 ${isHistoryOpen ? "open" : ""}`}>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h5 className="m-0">Chat History</h5>
        <Power onClick={onClose} style={{ cursor: "pointer" }} />
      </div>

      {isLoggedIn && (
        <>
          <button
            className="btn btn-outline-light btn-sm mb-2 w-100 d-flex align-items-center justify-content-center gap-2"
            onClick={handleNew}
          >
            <Plus size={16} /> New Chat
          </button>

          <div className="input-group input-group-sm mb-3">
            <span className="input-group-text bg-secondary border-0">
              <Search size={16} />
            </span>
            <input
              className="form-control bg-dark text-white border-0"
              placeholder="Search chats"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <ul className="list-group list-group-flush chat-list">
            {filtered.length > 0 ? (
              filtered.map((c) => (
                <li
                  key={c.conversation_id}
                  className="list-group-item bg-dark text-white border-secondary rounded my-1"
                  onClick={() => onSelectConversation(c.conversation_id)}
                  style={{ cursor: "pointer" }}
                >
                  {c.title}
                </li>
              ))
            ) : (
              <p className="text-white-50">No chats found.</p>
            )}
          </ul>
        </>
      )}

      {!isLoggedIn && (
        <div className="text-white-50 mt-4">
          <p>Please <strong>sign in</strong> to access your chat history.</p>
        </div>
      )}
    </div>
  );
};

export default History;
