// Chat.jsx
import Sidebar from "../components/Sidebar";
import ChatInterface from "../components/ChatInterface";
import History from "../components/History";
import { EqualApproximately } from "lucide-react";
import useSession from "../utils/useSession";
import { useNavigate } from "react-router-dom";


const Chat = () => {
    const {
    userId,
    isLoggedIn,
    isSidebarOpen,
    isHistoryOpen,
    toggleSidebar,
    toggleHistory,
  } = useSession();

  const navigate = useNavigate();

  // Handler for selecting a conversation
  const handleSelectConversation = (conversationId) => {
    // Navigate to chat with the selected conversation
    navigate(`/chat?conversation_id=${conversationId}`);
  };

  // Handler for creating new conversation
  const handleNewConversation = async () => {
    try {
      const response = await fetch('http://127.0.0.1:5000/api/conversations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, title: 'New Chat' })
      });

      if (response.ok) {
        const data = await response.json();
        return data.conversation_id;
      }
    } catch (error) {
      console.error('Error creating new conversation:', error);
    }
    return null;
  };

  return (
    <div className="chat chat-wrapper d-flex min-vh-100">
      <div className={`sidebar-area ${isSidebarOpen ? "open" : "collapsed"}`}>
        <Sidebar
          isOpen={isSidebarOpen}
          toggleSidebar={toggleSidebar}
          toggleHistory={toggleHistory}
          isHistoryOpen={isHistoryOpen}
          isLoggedIn={isLoggedIn}
        />
        <History
          isLoggedIn={isLoggedIn}
          userId={userId}
          isHistoryOpen={isHistoryOpen}
          onClose={toggleHistory}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
        />
      </div>

      <div className="chat-content flex-grow-1 position-relative">
        <div className="col-md-12 col-lg-12 col-xl-12 col-xxl-8 m-auto">
          <ChatInterface />
        </div>
        <span className="navbar-toggler-menu">
          <EqualApproximately
            className="d-md-none position-fixed top-0 start-0 m-3"
            onClick={toggleSidebar}
            style={{ zIndex: 99 }}
          />
        </span>
      </div>
    </div>
  );
};

export default Chat;
