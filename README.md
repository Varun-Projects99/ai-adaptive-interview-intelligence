
# InterviewIQ — Setup Guide (Windows)

## STEP 1 — Create virtual environment

```cmd
cd "C:\Users\Varun B\OneDrive\Desktop\Ai_claude\backend"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

> If PyAudio fails: `pip install pipwin` then `pipwin install pyaudio`

## STEP 2 — Add your Anthropic API key

Open `.env` and replace `your_anthropic_api_key_here` with your real key.
Get one at: https://console.anthropic.com

## STEP 3 — Run Flask server

```cmd
cd backend
set ANTHROPIC_API_KEY=your_key_here
python app.py
```

Server starts at: http://localhost:5000

## STEP 4 — Open the app

Double-click `frontend/index.html` in your browser (Chrome recommended).
Allow camera and microphone when prompted.

---

## INTEGRITY VIOLATIONS

| Type         | Trigger                        |
|--------------|--------------------------------|
| Tab Switch   | Candidate switches browser tab |
| Camera Exit  | Face absent for 3+ frames      |
| Window Move  | Browser window dragged/moved   |

**3 total violations = session auto-terminated**

---

## API ENDPOINTS

| Endpoint                    | Method | Description              |
|-----------------------------|--------|--------------------------|
| /api/session/start          | POST   | Create session           |
| /api/resume/upload          | POST   | Upload PDF + get skills  |
| /api/questions/generate     | POST   | Generate AI questions    |
| /api/questions/next         | POST   | Get next question        |
| /api/answer/submit          | POST   | Submit + evaluate answer |
| /api/emotion/analyze        | POST   | Analyze webcam frame     |
| /api/voice/analyze          | POST   | Analyze audio clip       |
| /api/integrity/violation    | POST   | Record violation         |
| /api/recording/save         | POST   | Save session recording   |
| /api/report/generate        | POST   | Generate final report    |
