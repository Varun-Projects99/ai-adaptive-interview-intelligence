# ai-adaptive-interview-intelligence
ai-adaptive-interview-intelligence/
│
├── backend//
│   ├── app.py
│   ├── config.py
│   ├── requirements.txt
│   │
│   ├── routes/
│   │   ├── auth_routes.py
│   │   ├── interview_routes.py
│   │   ├── resume_routes.py
│   │   └── analytics_routes.py
│   │
│   ├── services/
│   │   ├── resume_intelligence.py
│   │   ├── question_generator.py
│   │   ├── adaptive_engine.py
│   │   ├── emotion_analyzer.py
│   │   ├── confidence_analyzer.py
│   │   ├── scoring_engine.py
│   │   └── video_stream_processor.py
│   │
│   ├── database/
│   │   ├── db_connection.py
│   │   └── schemas.py
│   │
│   ├── uploads/
│   │
│   └── trained_models/
│       ├── emotion_model.h5
│       ├── confidence_model.pkl
│       └── skill_classifier.pkl
│
├── datasets/
│   ├── emotion_dataset/
│   ├── speech_confidence_dataset/
│   ├── interview_questions_dataset/
│   └── resume_skill_dataset/
│
├── model_training/
│   ├── train_emotion_model.py
│   ├── train_confidence_model.py
│   └── train_skill_classifier.py
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   └── services/
│
├── tests/
│
├── docs/
│
├── .env
├── .gitignore
└── README.md
