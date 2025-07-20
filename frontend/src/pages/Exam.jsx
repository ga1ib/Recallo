import React, { useState, useEffect, useCallback } from "react";
import Sidebar from "../components/Sidebar";
import History from "../components/History";
import useSession from "../utils/useSession";
import { EqualApproximately } from "lucide-react";
import "bootstrap/dist/css/bootstrap.min.css";
import { useLocation, useNavigate } from "react-router-dom";

const Exam = () => {
  const {
    user,
    isLoggedIn,
    isSidebarOpen,
    isHistoryOpen,
    toggleSidebar,
    toggleHistory,
  } = useSession();

  const location = useLocation();
  const navigate = useNavigate();
  const { topicTitle = "Sample Topic", fileName = "SampleFile.pdf" } =
    location.state || {};

  const [examStarted, setExamStarted] = useState(false);
  const [timeLeft, setTimeLeft] = useState(600); // 10 minutes in seconds
  const [answers, setAnswers] = useState(Array(10).fill(null));

  const sampleQuestions = Array.from({ length: 10 }, (_, i) => ({
    id: i + 1,
    text: `Question ${i + 1} sample text goes here?`,
    options: ["Option A", "Option B", "Option C", "Option D"],
  }));

  // Format time helper function
  const formatTime = useCallback((seconds) => {
    const m = String(Math.floor(seconds / 60)).padStart(2, "0");
    const s = String(seconds % 60).padStart(2, "0");
    return `${m}:${s}`;
  }, []);

  // Handle option selection
  const handleOptionChange = useCallback((qIndex, optionIndex) => {
    setAnswers(prev => {
      const updated = [...prev];
      updated[qIndex] = optionIndex;
      return updated;
    });
  }, []);

  // Handle exam submission
  const handleSubmit = useCallback((isTimeUp = false) => {
    const answeredCount = answers.filter((a) => a !== null).length;

    if (!isTimeUp && answeredCount !== sampleQuestions.length) {
      alert("Please answer all questions before submitting!");
      return;
    }

    // Prepare exam results data
    const examResults = {
      topic: topicTitle,
      fileName,
      totalQuestions: sampleQuestions.length,
      answeredCount,
      score: Math.round((answeredCount / sampleQuestions.length) * 100),
      timestamp: new Date().toISOString(),
    };

    // Store results in localStorage (or send to backend)
    const previousExams = JSON.parse(localStorage.getItem('examResults') || '[]');
    localStorage.setItem('examResults', JSON.stringify([...previousExams, examResults]));

    if (isTimeUp) {
      alert("⏰ Time's up! Submitting your exam...");
    } else {
      alert(
        `Exam complete. You answered ${answeredCount}/10 questions. Redirecting to progress page.`
      );
    }

    navigate("/progress", { state: examResults });
  }, [answers, navigate, sampleQuestions.length, topicTitle, fileName]);

  // Timer effect
  useEffect(() => {
    let timer;
    if (examStarted && timeLeft > 0) {
      timer = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } else if (timeLeft === 0) {
      handleSubmit(true);
    }

    return () => clearInterval(timer);
  }, [examStarted, timeLeft, handleSubmit]);

  // Tab close warning effect
  useEffect(() => {
    const handleTabClose = (e) => {
      if (examStarted) {
        e.preventDefault();
        handleSubmit();
        return (e.returnValue = "Are you sure you want to leave? Your exam will be submitted.");
      }
    };

    window.addEventListener("beforeunload", handleTabClose);
    return () => window.removeEventListener("beforeunload", handleTabClose);
  }, [examStarted, handleSubmit]);

  const allAnswered = answers.every((a) => a !== null);

  return (
    <div className="chat chat-wrapper chat_scroll d-flex min-vh-100">
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

      <div className="chat-content flex-grow-1 p-4 text-white d-flex flex-column chat_scroll">
        <div className="container">
          <div className="row">
            <div className="col-md-12 text-center">
              <h2 className="grad_text">Gear Up! It's Exam Time!</h2>
            </div>
          </div>
        </div>
        
        {!examStarted ? (
          <div className="container d-flex flex-column justify-content-center align-items-center text-center flex-grow-1">
            <div className="row">
              <div className="col-md-12">
                <div className="profile_card exam_rules">
                  <h2 className="mb-2">File: {fileName}</h2>
                  <h3 className="mb-2">Topic: {topicTitle}</h3>
                  <h5 className="mt-5 mb-2 text-start">Exam Rules:</h5>
                  <ul className="text-start">
                    <li>⏰ Total Time: 10 Minutes</li>
                    <li>📚 10 Questions – All Are Mandatory</li>
                    <li>🚫 No Tab-Hopping or Closing the Browser</li>
                    <li>⚠️ Closing the browser will submit your exam automatically</li>
                  </ul>
                  <h4 className="text-danger mt-3 timer-exam">
                    {formatTime(timeLeft)}
                  </h4>
                  <button
                    className="btn btn-cs mt-4"
                    onClick={() => setExamStarted(true)}
                  >
                    Start Exam
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="container">
            {/* Timer & Submit Button Row */}
            <div className="row mb-5 mt-5 align-items-center exam_time_header sticky-top bg-dark py-2">
              <div className="col-md-6">
                <h5 className="exam-timer mb-0">
                  Time Remaining: {formatTime(timeLeft)}
                </h5>
              </div>
              <div className="col-md-6 text-end">
                <button 
                  className="btn btn-danger" 
                  onClick={() => handleSubmit(false)}
                  disabled={!allAnswered}
                >
                  {allAnswered ? "Submit Exam" : "Complete All Questions"}
                </button>
              </div>
            </div>

            {/* Questions in Two Columns */}
            <div className="row questions mt-3">
              {(() => {
                const total = sampleQuestions.length;
                const mid = Math.ceil(total / 2);
                const left = sampleQuestions.slice(0, mid);
                const right = sampleQuestions.slice(mid);

                return (
                  <>
                    <div className="col-md-6">
                      {left.map((q, i) => (
                        <div key={q.id} className="mb-4 mcq p-3 bg-dark rounded">
                          <h6 className="mb-3">
                            {i + 1}. {q.text}
                          </h6>
                          {q.options.map((opt, j) => (
                            <div className="form-check mb-2" key={j}>
                              <input
                                className="form-check-input"
                                type="radio"
                                name={`question-${i}`}
                                id={`q${i}-opt${j}`}
                                checked={answers[i] === j}
                                onChange={() => handleOptionChange(i, j)}
                                required
                              />
                              <label
                                className="form-check-label ms-2"
                                htmlFor={`q${i}-opt${j}`}
                              >
                                {opt}
                              </label>
                            </div>
                          ))}
                        </div>
                      ))}
                    </div>

                    <div className="col-md-6">
                      {right.map((q, i) => (
                        <div key={q.id} className="mb-4 mcq p-3 bg-dark rounded">
                          <h6 className="mb-3">
                            {i + mid + 1}. {q.text}
                          </h6>
                          {q.options.map((opt, j) => (
                            <div className="form-check mb-2" key={j}>
                              <input
                                className="form-check-input"
                                type="radio"
                                name={`question-${i + mid}`}
                                id={`q${i + mid}-opt${j}`}
                                checked={answers[i + mid] === j}
                                onChange={() => handleOptionChange(i + mid, j)}
                                required
                              />
                              <label
                                className="form-check-label ms-2"
                                htmlFor={`q${i + mid}-opt${j}`}
                              >
                                {opt}
                              </label>
                            </div>
                          ))}
                        </div>
                      ))}
                    </div>
                  </>
                );
              })()}
            </div>
          </div>
        )}

        <span className="navbar-toggler-menu">
          <EqualApproximately
            className="d-md-none position-fixed top-0 start-0 m-3"
            onClick={toggleSidebar}
            style={{ zIndex: 99, cursor: "pointer" }}
          />
        </span>
      </div>
    </div>
  );
};

export default Exam;