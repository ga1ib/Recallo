# 📧 Recallo Mailing System

## Overview
The Recallo mailing system automatically sends email notifications to users based on their quiz performance and preferences.

## Features

### 1. **Automatic Quiz Result Emails** ✅
- **Trigger**: Sent immediately after every quiz attempt
- **Content**: Personalized email with score and encouragement
- **Customization**: Different messages based on score ranges:
  - **8-10/10**: Congratulatory message
  - **5-7/10**: Encouraging message with improvement suggestions
  - **0-4/10**: Motivational message to try again

### 2. **Daily Reminder System** 📅
- **Trigger**: Daily emails for topics with scores < 8/10
- **Purpose**: Encourage users to retake quizzes to improve scores
- **Stop Condition**: Reminders stop when user scores 8+ on the topic

### 3. **Weekly Practice Reminders** 🗓️
- **Trigger**: Weekly emails for topics with scores ≥ 8/10
- **Purpose**: Help users maintain their knowledge

### 4. **User Settings Control** ⚙️
- **Global Settings**:
  - Email notifications on/off
  - Daily reminders on/off
- **Topic-Specific Settings**:
  - Enable/disable notifications per topic

## How It Works

### Automatic Email Flow
```
Quiz Submission → Score Calculation → Email Sent → Review Features Updated
```

### Scheduling System
```
Daily Cron Job → Check User Preferences → Send Reminders → Log Notifications
```

## API Endpoints

### Get User Notification Settings
```http
GET /api/notification-settings/{user_id}
```

### Update User Notification Settings
```http
PUT /api/notification-settings/{user_id}
Content-Type: application/json

{
  "global_settings": {
    "email_notifications_enabled": true,
    "daily_reminders_enabled": true
  },
  "topic_settings": {
    "topic_id_1": true,
    "topic_id_2": false
  }
}
```

### Manual Notification Trigger
```http
POST /api/run-notifications
```

## Database Tables

### user_notification_settings
- `user_id`: User identifier
- `email_notifications_enabled`: Global email toggle
- `daily_reminders_enabled`: Daily reminder toggle
- `updated_at`: Last update timestamp

### user_topic_notification_preferences
- `user_id`: User identifier
- `topic_id`: Topic identifier
- `enabled`: Topic-specific notification toggle
- `updated_at`: Last update timestamp

### user_topic_review_features
- `user_id`: User identifier
- `topic_id`: Topic identifier
- `title`: Topic title
- `quiz_score`: Latest quiz score
- `last_updated`: Last score update

### user_notifications
- `user_id`: User identifier
- `topic_id`: Topic identifier
- `notification_type`: "daily" or "weekly"
- `sent_at`: Timestamp when sent
- `sent_date`: Date (for duplicate prevention)
- `next_notification_at`: Next scheduled notification
- `status`: "sent"
- `message`: Email content

## Setup Instructions

### 1. Environment Variables
Ensure these are set in your `.env` file:
```env
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

### 2. Gmail App Password
1. Enable 2-factor authentication on Gmail
2. Generate an App Password
3. Use the App Password as `MAIL_PASSWORD`

### 3. Scheduling Options

#### Option A: Cron Job (Recommended)
```bash
# Run daily at 9 AM
0 9 * * * cd /path/to/backend && python notification_scheduler.py --once

# Run daily at 6 PM
0 18 * * * cd /path/to/backend && python notification_scheduler.py --once
```

#### Option B: Background Daemon
```bash
python notification_scheduler.py --daemon
```

#### Option C: Manual API Call
```bash
curl -X POST http://127.0.0.1:5000/api/run-notifications
```

## Frontend Integration

### Settings Page
- Navigate to `/settings` in the frontend
- Users can toggle email preferences
- Real-time saving with feedback

### Usage
1. User takes a quiz
2. Email is automatically sent with results
3. If score < 8, daily reminders are scheduled
4. User can manage preferences in Settings page

## Testing

### Test Email Sending
```python
# In Python console
from app import send_exam_result_email
send_exam_result_email("test@example.com", "Test User", "Sample Topic", 7.5)
```

### Test Notification Scheduler
```bash
python notification_scheduler.py --once
```

## Troubleshooting

### Common Issues
1. **Emails not sending**: Check Gmail App Password and 2FA
2. **Duplicate emails**: Check `user_notifications` table for proper deduplication
3. **Settings not saving**: Verify API endpoints are accessible

### Logs
- Check `notification_scheduler.log` for scheduler issues
- Check Flask app logs for email sending errors

## Security Notes
- Use App Passwords, not regular Gmail passwords
- Protect the `/api/run-notifications` endpoint in production
- Consider rate limiting for email sending
- Validate user permissions for settings updates
