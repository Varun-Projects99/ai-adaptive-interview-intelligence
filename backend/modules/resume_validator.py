"""
Resume Document Validator Module
Provides structural, content, and section analysis to determine whether an uploaded
PDF is a genuine candidate resume/CV or an invalid document (e.g., Interview Performance Report,
Invoice, Question Paper, Project Report, User Manual, Certificate).
Supports student/fresher resumes containing Education, Technical Skills, Projects, and Certifications.
"""

import re

# Strong positive section headers indicative of a resume
STRONG_RESUME_HEADERS = [
    "technical skills", "skills", "skills & technologies", "technical expertise",
    "technical proficiencies", "core competencies", "programming skills",
    "tools & technologies", "key skills", "technical skill set",
    "work experience", "professional experience", "employment history", "employment",
    "experience", "internships", "work history",
    "education", "academic background", "academic qualifications", "qualifications",
    "projects", "academic projects", "personal projects", "key projects",
    "certifications", "certificates", "achievements", "publications",
    "professional summary", "summary", "objective", "profile", "about me",
    "curriculum vitae", "resume"
]

# Negative phrase categories for non-resume documents
INTERVIEW_REPORT_SIGNALS = [
    "interview performance report", "performance report", "interview results",
    "overall readiness", "technical competency", "voice confidence & pacing",
    "voice confidence", "emotion & composure", "adaptive difficulty path",
    "integrity summary", "tab switches", "camera exits", "window moves",
    "key action recommendations", "detailed question review", "interview scores",
    "100/100", "session terminated", "performance evaluation report",
    "analytics report", "aggregate score", "measures speaking rate",
    "avoidance of filler words", "voice tone variation", "webcam analysis",
    "ai assessment feedback", "question review", "interview session"
]

INVOICE_SIGNALS = [
    "invoice", "bill to", "amount due", "subtotal", "payment terms",
    "tax invoice", "total due", "invoice number", "invoice date"
]

QUESTION_PAPER_SIGNALS = [
    "question paper", "maximum marks:", "time allowed:", "attempt all questions",
    "section a", "section b", "roll no:", "answer all questions",
    "multiple choice questions"
]

RESEARCH_PAPER_SIGNALS = [
    "ieee transactions", "doi:", "arxiv:", "references",
    "conclusion and future work"
]

PROJECT_REPORT_SIGNALS = [
    "project report", "submitted by", "submitted to", "in partial fulfillment of",
    "department of", "academic year", "guide:", "coordinator:", "table of contents"
]

CERTIFICATE_SIGNALS = [
    "certificate of completion", "this is to certify that", "has successfully completed"
]

USER_MANUAL_SIGNALS = [
    "user manual", "installation guide", "getting started", "troubleshooting"
]


def validate_resume_document(raw_text: str) -> dict:
    """
    Analyzes document text structurally and deterministically calculates a
    resume confidence score (0-100) and document classification type.
    """
    if not raw_text or len(raw_text.strip()) < 30:
        return {
            "resume_valid": False,
            "document_type": "empty_document",
            "resume_confidence": 0,
            "reason": "The uploaded document contains no readable text or is empty.",
            "positive_signals": [],
            "negative_signals": ["empty_text"]
        }

    text_lower = raw_text.lower()
    lines = [line.strip().lower() for line in raw_text.split("\n") if line.strip()]

    positive_signals = []
    negative_signals = []

    # 1. Check for Contact & Profile Signals
    has_email = bool(re.search(r'[\w\.-]+@[\w\.-]+\.\w+', raw_text))
    has_phone = bool(re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', raw_text))
    has_link = bool(re.search(r'linkedin\.com|github\.com|portfolio|gitlab\.com', text_lower))

    if has_email:
        positive_signals.append("email_found")
    if has_phone:
        positive_signals.append("phone_found")
    if has_link:
        positive_signals.append("profile_links_found")

    # 2. Check for Resume Section Headings
    matched_sections = set()
    for line in lines:
        if len(line) <= 50:
            for header in STRONG_RESUME_HEADERS:
                if header in line:
                    matched_sections.add(header)

    for sec in matched_sections:
        positive_signals.append(f"section:{sec}")

    # 3. Check for Structural Patterns
    has_dates = bool(re.search(r'\b(20\d{2}|19\d{2})\s*[-–—\to]+\s*(20\d{2}|19\d{2}|present|current)\b', text_lower))
    has_degree = bool(re.search(r'\b(b\.?tech|b\.?e\.?|b\.?s\.?|m\.?tech|m\.?s\.?|bachelor|master|degree|gpa|cgpa)\b', text_lower))

    if has_dates:
        positive_signals.append("employment_dates_found")
    if has_degree:
        positive_signals.append("degree_education_found")

    # 4. Check for Negative Signals
    report_matches = [sig for sig in INTERVIEW_REPORT_SIGNALS if sig in text_lower]
    invoice_matches = [sig for sig in INVOICE_SIGNALS if sig in text_lower]
    exam_matches = [sig for sig in QUESTION_PAPER_SIGNALS if sig in text_lower]
    paper_matches = [sig for sig in RESEARCH_PAPER_SIGNALS if sig in text_lower]
    proj_report_matches = [sig for sig in PROJECT_REPORT_SIGNALS if sig in text_lower]
    cert_matches = [sig for sig in CERTIFICATE_SIGNALS if sig in text_lower]

    for m in report_matches:
        negative_signals.append(f"interview_report:{m}")
    for m in invoice_matches:
        negative_signals.append(f"invoice:{m}")
    for m in exam_matches:
        negative_signals.append(f"question_paper:{m}")
    for m in paper_matches:
        negative_signals.append(f"research_paper:{m}")
    for m in proj_report_matches:
        negative_signals.append(f"project_report:{m}")
    for m in cert_matches:
        negative_signals.append(f"certificate:{m}")

    # 5. Deterministic Scoring Calculation
    score = 0

    # Contact info (+35 max)
    if has_email: score += 15
    if has_phone: score += 10
    if has_link: score += 10

    # Resume section headers (+45 max)
    header_points = min(len(matched_sections) * 15, 45)
    score += header_points

    # Structural patterns (+20 max)
    if has_dates: score += 10
    if has_degree: score += 10

    # Penalties for negative indicators
    report_penalty = len(report_matches) * 20
    invoice_penalty = len(invoice_matches) * 25
    exam_penalty = len(exam_matches) * 25
    proj_report_penalty = len(proj_report_matches) * 25

    total_penalty = report_penalty + invoice_penalty + exam_penalty + proj_report_penalty
    final_confidence = max(0, min(100, score - total_penalty))

    # 6. Classification Decision Logic
    if len(report_matches) >= 3 or (len(report_matches) >= 1 and len(matched_sections) == 0):
        return {
            "resume_valid": False,
            "document_type": "interview_report",
            "resume_confidence": final_confidence,
            "reason": "This document appears to be an interview performance report. Please upload a valid candidate resume.",
            "positive_signals": positive_signals,
            "negative_signals": negative_signals
        }

    if len(invoice_matches) >= 3:
        return {
            "resume_valid": False,
            "document_type": "invoice",
            "resume_confidence": final_confidence,
            "reason": "This document appears to be an invoice or billing document. Please upload a valid candidate resume.",
            "positive_signals": positive_signals,
            "negative_signals": negative_signals
        }

    if len(exam_matches) >= 2:
        return {
            "resume_valid": False,
            "document_type": "question_paper",
            "resume_confidence": final_confidence,
            "reason": "This document appears to be an academic question paper or exam. Please upload a valid candidate resume.",
            "positive_signals": positive_signals,
            "negative_signals": negative_signals
        }

    if len(proj_report_matches) >= 3:
        return {
            "resume_valid": False,
            "document_type": "project_report",
            "resume_confidence": final_confidence,
            "reason": "This document appears to be an academic/project report. Please upload a valid candidate resume.",
            "positive_signals": positive_signals,
            "negative_signals": negative_signals
        }

    if len(cert_matches) >= 1 and len(matched_sections) <= 1 and not has_dates:
        return {
            "resume_valid": False,
            "document_type": "certificate",
            "resume_confidence": final_confidence,
            "reason": "This document appears to be a course/event certificate. Please upload a full candidate resume.",
            "positive_signals": positive_signals,
            "negative_signals": negative_signals
        }

    # Student Resume Support: Education + Skills + Projects/Certifications
    is_student_resume = (has_degree or "education" in text_lower) and (len(matched_sections) >= 2) and (has_email or has_phone or has_link)

    is_valid_resume = (
        (final_confidence >= 40 or is_student_resume) and
        (len(matched_sections) >= 1 or (has_email and (has_dates or has_degree))) and
        total_penalty < 30
    )

    if is_valid_resume:
        return {
            "resume_valid": True,
            "document_type": "resume",
            "resume_confidence": max(60, final_confidence),
            "reason": "Valid resume structure and technical candidate sections verified.",
            "positive_signals": positive_signals,
            "negative_signals": negative_signals
        }

    return {
        "resume_valid": False,
        "document_type": "unknown_document",
        "resume_confidence": final_confidence,
        "reason": "This document does not appear to be a resume. Please upload a valid resume.",
        "positive_signals": positive_signals,
        "negative_signals": negative_signals
    }
