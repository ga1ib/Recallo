import React, { useState } from 'react';
import Sidebar from "../components/Sidebar";
import ChatInterface from "../components/ChatInterface";
import History from "../components/History";

const Chat = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const toggleSidebar = () => setIsSidebarOpen((prev) => !prev);

  // dummy login check
  const isLoggedIn = localStorage.getItem("userToken") !== null;

  return (
    <div className="container-fluid p-0 chat">
      <div className="row">
        <div className="col-md-2">
          {/* is logged in for dummy check */}
          <Sidebar isOpen={isSidebarOpen} toggleSidebar={toggleSidebar} isLoggedIn={isLoggedIn} />
          {/* <Sidebar isOpen={isSidebarOpen} toggleSidebar={toggleSidebar}/> */}
        </div>
        <div className="col-md-8">
          <ChatInterface />
        </div>
        <div className="col-md-2">
          {isSidebarOpen && <History isLoggedIn={isLoggedIn} />}
        </div>
      </div>
    </div>
  );
};

export default Chat;



// check login status dummy 
// localStorage.setItem("userToken", "demo_token");
// localStorage.removeItem("userToken");
