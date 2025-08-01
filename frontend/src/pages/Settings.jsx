import React, { useState, useEffect } from 'react';
import Sidebar from "../components/Sidebar";
import History from "../components/History";
import useSession from "../utils/useSession";
import "bootstrap/dist/css/bootstrap.min.css";

        const Settings = () => {
        const [settings, setSettings] = useState({
            global_settings: {
            email_notifications_enabled: true,
            daily_reminders_enabled: true,
            },
            topic_settings: {},
        });
        const [topics, setTopics] = useState([]);
        const [loading, setLoading] = useState(true);
        const [saving, setSaving] = useState(false);
        const [message, setMessage] = useState("");

        const {
            user,
            userId,
            isLoggedIn,
            isSidebarOpen,
            isHistoryOpen,
            toggleSidebar,
            toggleHistory,
        } = useSession();

        useEffect(() => {
            if (!userId) return;

            const fetchSettings = async () => {
                try {
                    const response = await fetch(`http://127.0.0.1:5000/api/notification-settings/${userId}`);
                    if (response.ok) {
                        const data = await response.json();
                        setSettings(data);
                    } else {
                        // If settings don't exist, use default settings
                        console.log("No settings found, using defaults");
                        setSettings({
                            global_settings: {
                                email_notifications_enabled: true,
                                daily_reminders_enabled: true
                            },
                            topic_settings: {}
                        });
                    }
                } catch (error) {
                    console.error("Error fetching settings:", error);
                    // Use default settings on error
                    setSettings({
                        global_settings: {
                            email_notifications_enabled: true,
                            daily_reminders_enabled: true
                        },
                        topic_settings: {}
                    });
                }
            };

            const fetchTopics = async () => {
                try {
                    const response = await fetch(`http://127.0.0.1:5000/api/topics/${userId}`);
                    if (response.ok) {
                        const data = await response.json();
                        setTopics(data);
                    } else {
                        console.error("Failed to fetch topics");
                        setTopics([]); // Set empty array if fetch fails
                    }
                } catch (error) {
                    console.error("Error fetching topics:", error);
                    setTopics([]); // Set empty array on error
                } finally {
                    setLoading(false);
                }
            };

            fetchSettings();
            fetchTopics();
        }, [userId]);

        const handleGlobalSettingChange = (setting, value) => {
            setSettings((prev) => ({
            ...prev,
            global_settings: {
                ...(prev?.global_settings || {}),
                [setting]: value,
            },
            }));
        };

        const handleTopicSettingChange = (topicId, enabled) => {
            setSettings((prev) => ({
            ...prev,
            topic_settings: {
                ...(prev?.topic_settings || {}),
                [topicId]: enabled,
            },
            }));
        };

        const saveSettings = async () => {
  if (!userId) {
    console.error("No userId available for saving settings");
    return;
  }

  if (!settings || !settings.global_settings) {
    console.error("Settings object is not properly initialized:", settings);
    return;
  }

  setSaving(true);
  setMessage("");

  try {
    console.log("Saving settings for user:", userId, "Settings:", settings);
    const response = await fetch(
      `http://127.0.0.1:5000/api/notification-settings/${userId}`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings),
      }
    );

    const text = await response.text();   // read raw body
    let payload;
    try { payload = JSON.parse(text); }   // try to parse JSON
    catch (e) { payload = text; }

    if (response.ok) {
      setMessage("Settings saved successfully!");
      setTimeout(() => setMessage(""), 3000);
    } else {
      console.error("Server responded with error:", payload);
      setMessage("Failed to save settings. Check console for details.");
    }
  } catch (error) {
    console.error("Network error saving settings:", error);
    setMessage("Network error. Please try again.");
  } finally {
    setSaving(false);
  }
};

        return (
            <div className="chat chat-wrapper d-flex min-vh-100">
            <div className={`sidebar-area ${isSidebarOpen ? "open" : "collapsed"}`}>
                <Sidebar isOpen={isSidebarOpen} toggleSidebar={toggleSidebar} toggleHistory={toggleHistory} isHistoryOpen={isHistoryOpen} isLoggedIn={isLoggedIn} />
                <History isLoggedIn={isLoggedIn} userId={user?.id} isHistoryOpen={isHistoryOpen} onClose={toggleHistory} />
            </div>

            <div className="chat-content flex-grow-1 p-4 text-white">
                <div className="container text-center mb-4 mt-4">
                <h2 className="grad_text">Notification Settings</h2>
                </div>

                {loading ? (
                <div className="d-flex justify-content-center align-items-center" style={{ height: "150px" }}>
                    <div className="spinner-border text-primary" role="status" />
                </div>
                ) : (
                <div className="container">
                    <div className="mb-5">
                    <h4 className="text-white mb-3">🌐 Global Settings</h4>
                    <div className="card p-3 mb-3 bg-dark text-white">
                        <div className="d-flex justify-content-between align-items-center">
                        <div>
                            <h5>Email Notifications</h5>
                            <p>Receive email notifications for quiz results</p>
                        </div>
                        <label className="toggle-switch">
                            <input
                            type="checkbox"
                            checked={settings?.global_settings?.email_notifications_enabled || false}
                            onChange={(e) => handleGlobalSettingChange("email_notifications_enabled", e.target.checked)}
                            />
                            <span className="slider"></span>
                        </label>
                        </div>
                    </div>

                    <div className="card p-3 bg-dark text-white">
                        <div className="d-flex justify-content-between align-items-center">
                        <div>
                            <h5>Daily Reminders</h5>
                            <p>Get daily reminders for topics where you scored below 8/10</p>
                        </div>
                        <label className="toggle-switch">
                            <input
                            type="checkbox"
                            checked={settings?.global_settings?.daily_reminders_enabled || false}
                            onChange={(e) => handleGlobalSettingChange("daily_reminders_enabled", e.target.checked)}
                            />
                            <span className="slider"></span>
                        </label>
                        </div>
                    </div>
                    </div>

                    <div className="mb-3">
                    <h4 className="text-white mb-3">📚 Topic-Specific Settings</h4>
                    <p className="text-white mb-5">Control notifications for individual topics. Disabled topics won't send any reminders.</p>

                    {topics.length === 0 ? (
                        <div className="text-center text-warning">
                        No topics found. Upload some documents to see topic-specific settings.
                        </div>
                    ) : (
                        <div className="row">
                        {topics.map((topic) => {
                            const isEnabled = settings.topic_settings[topic.topic_id] !== false;
                            return (
                            <div key={topic.topic_id} className="col-md-6 col-xl-4 mb-3">
                                <div className="card p-3 bg-dark text-white">
                                <div className="d-flex justify-content-between align-items-center">
                                    <div>
                                    <h5>{topic.title}</h5>
                                    <p className="mb-0">
                                        Status: <span className={`status ${topic.topic_status?.toLowerCase()}`}>{topic.topic_status || 'Not attempted'}</span>
                                    </p>
                                    </div>
                                    <label className="toggle-switch">
                                    <input
                                        type="checkbox"
                                        checked={isEnabled}
                                        onChange={(e) => handleTopicSettingChange(topic.topic_id, e.target.checked)}
                                    />
                                    <span className="slider"></span>
                                    </label>
                                </div>
                                </div>
                            </div>
                            );
                        })}
                        </div>
                    )}
                    </div>

                    <div className="text-center">
                    <button className="btn btn-answer" onClick={saveSettings} disabled={saving}>
                        {saving ? "💾 Saving..." : "💾 Save Settings"}
                    </button>
                    {message && (
                        <div className={`mt-3 ${message.includes("successfully") ? "text-success" : "text-danger"}`}>{message}</div>
                    )}
                    </div>

                    <div className="mt-5 text-white">
                    <h5>ℹ️ How it works</h5>
                    <ul>
                        <li><strong>Email Notifications:</strong> You'll receive an email after every quiz attempt with your score</li>
                        <li><strong>Daily Reminders:</strong> If you score below 8/10, you'll get daily reminders until you improve</li>
                        <li><strong>Topic Settings:</strong> Disable notifications for specific topics you don't want reminders about</li>
                        <li><strong>Weekly Practice:</strong> Topics with scores 8+ get weekly practice reminders</li>
                    </ul>
                    </div>
                </div>
                )}
            </div>
            </div>
        );
        };

        export default Settings;