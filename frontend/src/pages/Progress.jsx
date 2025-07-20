import React, { useState, useEffect } from "react";
import Sidebar from "../components/Sidebar";
import History from "../components/History";
import useSession from "../utils/useSession";
import { EqualApproximately, ChevronDown, ChevronUp } from "lucide-react";
import { CircularProgressbar, buildStyles } from "react-circular-progressbar";
import "react-circular-progressbar/dist/styles.css";
import "bootstrap/dist/css/bootstrap.min.css";

const Progress = () => {
  const {
    user,
    userId,
    isLoggedIn,
    isSidebarOpen,
    isHistoryOpen,
    toggleSidebar,
    toggleHistory,
  } = useSession();

  const [expandedTopics, setExpandedTopics] = useState({});
  const [progressData, setProgressData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProgress = async () => {
      setLoading(true);
      try {
        const response = await fetch(`http://127.0.0.1:5000/api/progress/${userId}`);
        if (response.ok) {
          const data = await response.json();
          setProgressData(data);
        } else {
          console.error("Error fetching progress:", response.statusText);
          setProgressData([]);
        }
      } catch (error) {
        console.error("Error fetching progress:", error.message);
        setProgressData([]);
      }
      setLoading(false);
    };

    if (userId) {
      fetchProgress();
    }
  }, [userId]);

  const toggleHistoryView = (topicId) => {
    setExpandedTopics((prev) => ({
      ...prev,
      [topicId]: !prev[topicId],
    }));
  };

  // Transform the API data to match the frontend structure
  const transformData = (data) => {
    return data.map((item, index) => ({
      topicId: item.topic_id || `t${index + 1}`,
      fileName: item.file_name || "Document",
      topicTitle: item.topic_title || `Topic ${index + 1}`,
      latestScore: item.latest_score || 0,
      totalAttempts: item.total_attempts || 1,
      overallProgress: item.overall_progress_percent || 0,
      history: item.attempt_history || [
        {
          attempt_number: 1,
          score: item.latest_score || 0,
          submitted_at: new Date().toISOString(),
          improvement: null
        }
      ]
    }));
  };

  const transformedData = transformData(progressData);
  
  const groupedTopics = transformedData.reduce((acc, curr) => {
    if (curr.latestScore === null) return acc;
    if (!acc[curr.fileName]) acc[curr.fileName] = [];
    acc[curr.fileName].push(curr);
    return acc;
  }, {});

  const hasResults = Object.keys(groupedTopics).length > 0;

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
          userId={user?.id}
          isHistoryOpen={isHistoryOpen}
          onClose={toggleHistory}
        />
      </div>

      <div className="chat-content flex-grow-1 p-4 text-white">
        <div className="container text-center mb-4 mt-4">
          <h2 className="grad_text">Your Progress Overview</h2>
        </div>

        <div className="container">
          {loading ? (
            <div className="d-flex justify-content-center align-items-center" style={{ height: "150px" }}>
              <div className="spinner-border text-primary" role="status" />
            </div>
          ) : !hasResults ? (
            <div className="text-center mt-5">
              <h5 className="text-warning">
                📌 Take exams for progress overview
              </h5>
            </div>
          ) : (
            Object.entries(groupedTopics).map(([fileName, topics]) => (
              <div key={fileName} className="mb-5">
                <h4 className="text-white mb-3">
                  <i className="bi bi-file-earmark-text me-2"></i>
                  {fileName}
                </h4>
                <div className="row">
                  {topics.map((topic, idx) => (
                    <div className="col-md-6 col-xl-4 mb-4" key={idx}>
                      <div className="card topic_card text-white">
                        <div className="card-body">
                          <h5 className="card-title mb-1">
                            {topic.topicTitle}
                          </h5>
                          <div className="my-3" style={{ width: 60 }}>
                            <CircularProgressbar
                              value={topic.latestScore * 10}
                              text={`${topic.latestScore}/10`}
                              styles={buildStyles({
                                textColor: "white",
                                pathColor:
                                  topic.latestScore >= 8
                                    ? "#28a745"
                                    : "#ffc107",
                                trailColor: "#444",
                              })}
                            />
                          </div>

                          <div className="mt-3 marks_progress">
                            <button
                              className="btn btn-sm btn-outline w-100 d-flex justify-content-between align-items-center text-white ans_drp"
                              onClick={() => toggleHistoryView(topic.topicId)}
                            >
                              Exam Marks History
                              {expandedTopics[topic.topicId] ? (
                                <ChevronUp size={16} />
                              ) : (
                                <ChevronDown size={16} />
                              )}
                            </button>
                            {expandedTopics[topic.topicId] && (
                              <div className="mt-2">
                                {topic.history.length > 0 &&
                                  topic.history.map((entry, i) => {
                                    // Use the improvement value from backend if available, otherwise calculate
                                    const improvement = entry.improvement !== null ? entry.improvement : 0;
                                    const trend =
                                      improvement > 0 ? (
                                        <span className="text-success">
                                          +{improvement.toFixed(1)} ↑
                                        </span>
                                      ) : improvement < 0 ? (
                                        <span className="text-danger">
                                          {improvement.toFixed(1)} ↓
                                        </span>
                                      ) : (
                                        <span className="text-secondary">
                                          {i === 0 ? "First attempt" : "0 →"}
                                        </span>
                                      );
                                    return (
                                      <div key={i} className="marks_hitory">
                                        <div className="d-flex justify-content-between test_details_progress">
                                          <strong>Test {entry.attempt_number || i + 1}</strong>
                                          <span className="text-muted small">
                                            {new Date(entry.submitted_at || entry.timestamp).toLocaleString()}
                                          </span>
                                        </div>
                                        <div className="d-flex justify-content-between align-items-center mt-2">
                                          <span>
                                            <strong>{entry.score}/10</strong> (
                                            {trend})
                                          </span>
                                          <button
                                            className="btn btn-sm btn-answer"
                                            onClick={() =>
                                              alert(
                                                `Redirect to review of Test ${
                                                  entry.attempt_number || i + 1
                                                }`
                                              )
                                            }
                                          >
                                            Answer Analysis
                                          </button>
                                        </div>
                                      </div>
                                    );
                                  })}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))
          )}
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

export default Progress;