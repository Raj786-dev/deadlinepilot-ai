# DeadlinePilot AI

AI-powered deadline assistant. Type a deadline in plain language,
and it extracts the due date, breaks the work into subtasks,
schedules them, and warns you when you are at risk of missing it.

## Features
- Natural language deadline parsing (Gemini API)
- Automatic subtask breakdown and scheduling
- Progress tracking
- At-risk detection (remaining work vs. available time)

## Setup
pip install streamlit google-genai
Create key.txt with your Gemini API key
python -m streamlit run app.py

## Future scope
Telegram/WhatsApp reminders, daily AI briefing, Google Calendar sync
