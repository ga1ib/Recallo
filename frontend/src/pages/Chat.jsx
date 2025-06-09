import React, { useState } from 'react';
import Sidebar from "../components/Sidebar";
import ChatInterface from "../components/ChatInterface";
import History from "../components/History";

const Chat = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const toggleSidebar = () => setIsSidebarOpen((prev) => !prev);
  return (
    <div className="container-fluid p-0 chat">
      <div className="row">
        <div className="col-md-2">
<Sidebar isOpen={isSidebarOpen} toggleSidebar={toggleSidebar} />
        </div>
        <div className="col-md-8">
 <ChatInterface />
        </div>
        <div className="col-md-2">
{isSidebarOpen && <History />}
        </div>
      </div>
    </div>
  );
};

export default Chat;
