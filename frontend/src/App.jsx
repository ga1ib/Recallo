import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import Dashboard from "./pages/Dashboard";
import Chat from "./pages/Chat";
import Signin from "./pages/Signin";
import ProtectedRoute from "./components/ProtectedRoute";
import Profile from "./pages/Profile";
import Todo from "./pages/Todo";
import Topics from "./pages/Topics";
import Exam from "./pages/Exam";
import Progress from "./pages/Progress";
import Archive from "./pages/Archive";
import Study_Metrics from "./pages/StudyMetrics";
import Settings from "./pages/Settings";
import Resource from "./pages/Resource";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/signin" element={<Signin />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/todo" element={<Todo />} />
        <Route path="/topics" element={<Topics />} />
        <Route path="/exam" element={<Exam />} />
        <Route path="/progress" element={<Progress />} />
        <Route path="/archive" element={<Archive />} />
        <Route path="/studymetrics" element={<Study_Metrics />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/resource" element={<Resource />} />
      </Routes>
    </Router>
  );
}

export default App;