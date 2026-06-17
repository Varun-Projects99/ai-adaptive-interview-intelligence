"""
Voice Confidence Analysis Module
Scores speech rate, pauses, tone variation, filler words → 0-100 confidence score.
"""

import os, re
import numpy as np
import librosa
import speech_recognition as sr

FILLERS = ["um","uh","like","you know","basically","literally","sort of","kind of","i mean","actually"]


def analyze_voice_confidence(path: str) -> dict:
    if not os.path.exists(path):
        return _default("file_not_found")
    try:
        y, sr_rate = librosa.load(path, sr=16000)
        dur = librosa.get_duration(y=y, sr=sr_rate)
        if dur < 0.5:
            return _default("too_short")

        transcript, filler_score = _fillers(path)
        rate_score  = _speech_rate(path, dur)
        pause_score = _pauses(y, sr_rate)
        tone_score  = _tone(y, sr_rate)

        score = int(rate_score*0.25 + pause_score*0.30 + tone_score*0.25 + filler_score*0.20)
        score = max(0, min(100, score))

        label = ("Confident" if score>=75 else "Moderate" if score>=55 else
                 "Nervous"   if score>=35 else "Very Nervous")

        return {
            "confidence_score": score, "confidence_label": label,
            "duration_seconds": round(dur, 1), "transcript": transcript,
            "breakdown": {"speech_rate": round(rate_score,1), "pauses": round(pause_score,1),
                          "tone_variation": round(tone_score,1), "filler_words": round(filler_score,1)},
            "tips": _tips(rate_score, pause_score, tone_score, filler_score)
        }
    except Exception as e:
        print(f"[VoiceAnalyzer] {e}")
        return _default("error")


def _speech_rate(path, dur):
    try:
        r = sr.Recognizer()
        with sr.AudioFile(path) as src:
            audio = r.record(src)
        wpm = len(r.recognize_google(audio).split()) / dur * 60
        return 95 if 120<=wpm<=160 else 80 if 100<=wpm<=180 else 60 if 80<=wpm<=200 else 35
    except:
        return 65

def _pauses(y, sr_rate):
    fl  = int(0.025*sr_rate); hop = int(0.010*sr_rate)
    eng = np.array([np.sum(y[i:i+fl]**2) for i in range(0,len(y)-fl,hop)])
    r   = np.sum(eng < np.percentile(eng,20)) / len(eng)
    return 90 if r<0.20 else 75 if r<0.30 else 55 if r<0.40 else 40 if r<0.50 else 25

def _tone(y, sr_rate):
    try:
        f0, vf, _ = librosa.pyin(y, fmin=80, fmax=400, sr=sr_rate)
        vf0 = f0[vf>0]
        if len(vf0)<10: return 50
        v = np.std(vf0)/(np.mean(vf0)+1e-6)
        return 90 if 0.08<=v<=0.25 else 70 if 0.05<=v<=0.35 else 50 if v>=0.03 else 35
    except:
        return 60

def _fillers(path):
    try:
        r = sr.Recognizer()
        with sr.AudioFile(path) as src:
            audio = r.record(src)
        t = r.recognize_google(audio).lower()
        cnt = sum(len(re.findall(r'\b'+re.escape(f)+r'\b', t)) for f in FILLERS)
        ratio = cnt / max(len(t.split()),1)
        return t, (95 if ratio<0.03 else 75 if ratio<0.07 else 55 if ratio<0.12 else 30)
    except:
        return "", 65

def _tips(rate, pause, tone, filler):
    tips = []
    if rate   < 60: tips.append("Speak more steadily — aim for 120–160 words per minute.")
    if pause  < 50: tips.append("Reduce long pauses. Breathe and continue without hesitation.")
    if tone   < 50: tips.append("Vary your pitch to sound more engaged and confident.")
    if filler < 55: tips.append("Cut filler words (um, uh, like). Pause briefly instead.")
    return tips or ["Great voice delivery! Keep it up."]

def _default(reason):
    return {"confidence_score":50,"confidence_label":"Moderate","duration_seconds":0,
            "transcript":"","breakdown":{},"tips":["Voice analysis unavailable."],"reason":reason}
