import React from "react";
import { 
  ListTodo, 
  FileSliders, 
  ListTree, 
  Notebook, 
  ChartPie, 
  BookOpenCheck, 
  FolderArchive, 
  History, 
  User, 
  Cog,
  EqualApproximately,
  MessageCircle 
} from 'lucide-react';
import recalloLogo from "../assets/recallo.png";
import { useLocation, Link } from "react-router-dom";

const menuItems = [
  { icon: <ListTodo />, label: "To-Do List", path: "/todo" },
  { icon: <FileSliders />, label: "Your Resources", path: "/resource" },
  { icon: <ListTree />, label: "Create Topics", path: "/topics" },
  { icon: <Notebook />, label: "Study Metrics", path: "/studymetrics" },
  { icon: <ChartPie />, label: "Progress", path: "/progress" },
  { icon: <BookOpenCheck />, label: "Exams", path: "/exam" },
  { icon: <FolderArchive />, label: "Archive Topics", path: "/archive" },
  { icon: <Cog />, label: "Settings", path: "/settings" },
];

const Sidebar = ({
  isOpen,
  toggleSidebar,
  toggleHistory,
  isHistoryOpen,
  isLoggedIn,
}) => {
  const location = useLocation();

  const handleSidebarToggle = () => {
    toggleSidebar();
    if (isHistoryOpen) toggleHistory();
  };

  // Check if current page is NOT the chat page
  const isNotChatPage = location.pathname !== "/chat";

  return (
    <div className={`sidebar ${isOpen ? "open" : "collapsed"}`}>
      {/* Fixed Header */}
      <div className="sidebar-header">
        {isOpen && (
          <Link to="/">
            <img
              src={recalloLogo}
              alt="Recallo Logo"
              className="img-fluid logo"
            />
          </Link>
        )}
        <EqualApproximately
          onClick={handleSidebarToggle}
          className="toggle-icon sidebar-toggler"
          style={{ color: "#ffffff", cursor: "pointer", fontSize: "1.5rem" }}
        />
      </div>

      {/* Scrollable Content Area */}
      <div className="sidebar-content">
        {isLoggedIn ? (
          <>
            {/* Main Menu Section */}
            <div className="sidebar-main-menu">
              <ul className="sidebar-menu">
                {menuItems.map((item, index) => {
                  const isActive = location.pathname === item.path;
                  return (
                    <li
                      key={index}
                      className="menu-item"
                      style={{
                        backgroundColor: isActive
                          ? "var(--cs-border)"
                          : "transparent",
                      }}
                    >
                      <Link to={item.path} className="d-flex align-items-center text-white text-decoration-none w-100">
                        <span className="icon me-2">{item.icon}</span>
                        {isOpen && <span className="label">{item.label}</span>}
                      </Link>
                    </li>
                  );
                })}

                {/* History Menu Item */}
                <li
                  onClick={toggleHistory}
                  className="menu-item"
                  style={{
                    backgroundColor: isHistoryOpen
                      ? "var(--cs-border)"
                      : "transparent",
                  }}
                >
                  <span className="icon me-2">
                    <History />
                  </span>
                  {isOpen && <span className="label">History</span>}
                </li>
              </ul>
            </div>

            {/* Profile Section */}
            <div className="profile_section">
              {/* Profile Menu Item */}
              <li
                className="menu-item"
                style={{
                  backgroundColor:
                    location.pathname === "/profile"
                      ? "var(--cs-border)"
                      : "transparent",
                }}
              >
                <Link to="/profile" className="d-flex align-items-center text-white text-decoration-none w-100">
                  <span className="icon me-2">
                    <User />
                  </span>
                  {isOpen && <span className="label">Profile</span>}
                </Link>
              </li>

              {/* Return to Chat - Show only when NOT on chat page */}
              {isNotChatPage && (
                <li className="menu-item chat_return">
                  <Link to="/chat" className="d-flex align-items-center text-decoration-none w-100">
                    <span className="icon me-2 cicon">
                      <MessageCircle />
                    </span>
                    {isOpen && <span className="label chat_label">Return to Chat</span>}
                  </Link>
                </li>
              )}
            </div>
          </>
        ) : (
          isOpen && (
            <div className="sidebar-login-message text-center mt-4">
              <p className="mb-4 text-start">
                Recallo is much more than that. <br />
                <strong>Sign in to start your study journey!</strong>
              </p>
              <div className="d-flex flex-column gap-2">
                <Link to="/signin" className="btn btn-cs">
                  Log In
                </Link>
                <Link to="/signin" className="btn btn-cs">
                  Sign Up
                </Link>
              </div>
            </div>
          )
        )}
      </div>
    </div>
  );
};

export default Sidebar;