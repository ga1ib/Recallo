import React from "react";
import { FaBars } from "react-icons/fa";
import recalloLogo from "../assets/recallo.png";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";

const Sidebar = ({ isOpen, toggleSidebar }) => {
  return (
    <div className={`sidebar ${isOpen ? "open" : "collapsed"}`}>
      <div>
        <div className="sidebar-header">
          <FontAwesomeIcon
            icon="fa-solid fa-equals"
            onClick={toggleSidebar}
            style={{ color: "#ffffff", cursor: "pointer" }}
          />
          {isOpen && (
            <div className="sidebar-logo">
              <img
                src={recalloLogo}
                alt="Recallo Logo"
                className="img-fluid logo mt-4 mb-3"
              />
            </div>
          )}
        </div>
        {isOpen && (
          <ul className="sidebar-menu">
            <li>📋 To-Do List</li>
            <li>📚 Your Resources</li>
            <li>✅ Covered Topics</li>
            <li>⚠️ Weak Areas</li>
            <li>🧮 Progress </li>
            <li>📚 Quizzes</li>
            <li>📆 Exam Tracker</li>
            <li>⚙️ Settings</li>
          </ul>
        )}
      </div>
      <div className="profile_section">
        {isOpen && (
          <ul className="sidebar-menu">
            <li>👤 Profile</li>
          </ul>
        )}
      </div>
    </div>
  );
};

export default Sidebar;
