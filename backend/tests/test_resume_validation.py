"""
Test Suite: Resume Document Validation & Technical Skill Extraction
Tests exact document classification, negative signal rejection (interview performance reports, invoices, question papers, generic technical PDFs), and accurate skill extraction.
"""

import unittest
from modules.resume_validator import validate_resume_document
from modules.resume_parser import extract_skills_from_resume, analyze_resume_data


class TestResumeValidationAndExtraction(unittest.TestCase):

    # --------------------------------------------------------------------------
    # VALID RESUME FIXTURES (1 - 8)
    # --------------------------------------------------------------------------

    def test_01_standard_software_engineer_resume(self):
        text = """
        John Doe
        john.doe@email.com | +1-555-0199 | linkedin.com/in/johndoe | github.com/johndoe
        San Francisco, CA

        PROFESSIONAL SUMMARY
        Senior Software Engineer with 5+ years of experience building scalable backend microservices and web applications.

        TECHNICAL SKILLS
        Languages: Python, Java, JavaScript, C++
        Frameworks: FastAPI, Flask, React, Django
        Databases: PostgreSQL, MongoDB, Redis
        DevOps: Docker, Kubernetes, AWS

        WORK EXPERIENCE
        Software Engineer | Tech Corp | 2021 - Present
        - Architected high-throughput REST APIs using Python and FastAPI.
        - Deployed microservices on AWS using Docker and Kubernetes.

        EDUCATION
        B.Tech in Computer Science | State University | 2017 - 2021
        """
        val = validate_resume_document(text)
        self.assertTrue(val["resume_valid"])
        self.assertEqual(val["document_type"], "resume")
        self.assertGreaterEqual(val["resume_confidence"], 70)

        skills = extract_skills_from_resume(text)
        self.assertIn("Python", skills)
        self.assertIn("Java", skills)
        self.assertIn("FastAPI", skills)
        self.assertIn("Docker", skills)

    def test_02_one_page_student_resume(self):
        text = """
        Jane Smith
        jane.smith@university.edu | (555) 234-5678 | github.com/janesmith

        EDUCATION
        B.S. Computer Science, Stanford University, GPA: 3.8/4.0 (2020 - 2024)

        SKILLS
        Programming: Python, C++, Java, SQL
        Web: HTML, CSS, JavaScript, React

        PROJECTS
        AI Chatbot - Built using Python, Flask, and MongoDB.
        """
        val = validate_resume_document(text)
        self.assertTrue(val["resume_valid"])

        skills = extract_skills_from_resume(text)
        self.assertIn("Python", skills)
        self.assertIn("C++", skills)
        self.assertIn("React", skills)

    def test_03_two_page_professional_resume(self):
        text = """
        Alex Rivera
        alex.rivera@devmail.com | +44 7700 900077 | linkedin.com/in/arivera

        EXECUTIVE SUMMARY
        Lead Solutions Architect with 10+ years experience in enterprise cloud migrations.

        TECHNICAL EXPERTISE
        Cloud Architecture: AWS, Azure, Terraform
        Containers: Docker, Kubernetes
        Databases: MySQL, PostgreSQL, Oracle

        PROFESSIONAL EXPERIENCE
        Principal Architect | CloudScale Inc | 2018 - Present
        - Led migration of legacy monolith to AWS ECS and Kubernetes.

        Senior Developer | Enterprise Systems | 2013 - 2018
        - Developed Java Spring Boot services handling 1M+ daily transactions.

        EDUCATION & CERTIFICATIONS
        M.S. Software Engineering | Oxford University (2011 - 2013)
        AWS Certified Solutions Architect
        """
        val = validate_resume_document(text)
        self.assertTrue(val["resume_valid"])

        skills = extract_skills_from_resume(text)
        self.assertIn("AWS", skills)
        self.assertIn("Docker", skills)
        self.assertIn("Kubernetes", skills)

    def test_04_resume_with_technical_skills_heading(self):
        text = """
        Mark Taylor
        mark@taylor.io | +1 415 555 0122

        TECHNICAL SKILLS
        Languages: Python, TypeScript, SQL
        Tools: Git, VS Code, Postman

        EXPERIENCE
        Developer | DevAgency | 2022 - Present
        
        EDUCATION
        B.E. Information Technology (2018 - 2022)
        """
        val = validate_resume_document(text)
        self.assertTrue(val["resume_valid"])
        skills = extract_skills_from_resume(text)
        self.assertIn("Python", skills)
        self.assertIn("TypeScript", skills)

    def test_05_resume_with_skills_heading(self):
        text = """
        Sarah Connor
        sarah@cyber.com | 555-987-6543 | github.com/sconnor

        SUMMARY
        Full Stack Developer with expertise in React and Node.js.

        SKILLS
        React, Node.js, Express.js, MongoDB, Tailwind CSS

        EXPERIENCE
        Full Stack Engineer | Cyberdyne | 2021 - Present

        EDUCATION
        Bachelor of Computer Applications | 2017 - 2020
        """
        val = validate_resume_document(text)
        self.assertTrue(val["resume_valid"])
        skills = extract_skills_from_resume(text)
        self.assertIn("React", skills)
        self.assertIn("Node.js", skills)

    def test_06_resume_with_skills_across_categories(self):
        text = """
        David Miller
        david@miller.dev | 555-111-2222 | linkedin.com/in/dmiller

        TECHNICAL PROFICIENCIES
        Frontend & UI: HTML, CSS, JavaScript, React.js
        Backend Frameworks: FastAPI, Flask, Django
        Databases & Storage: PostgreSQL, Redis

        WORK EXPERIENCE
        Software Engineer | Acme Systems | 2020 - Present

        EDUCATION
        B.S. Software Engineering | 2016 - 2020
        """
        val = validate_resume_document(text)
        self.assertTrue(val["resume_valid"])
        skills = extract_skills_from_resume(text)
        self.assertIn("React", skills)
        self.assertIn("FastAPI", skills)

    def test_07_resume_with_projects_containing_additional_skills(self):
        text = """
        Elena Rostova
        elena@rostova.tech | +1-555-0144 | github.com/erostova

        TECHNICAL SKILLS
        Python, C++, SQL

        PROJECTS
        Containerized Microservice Pipeline:
        - Designed REST APIs with FastAPI.
        - Deployed application using Docker and Kubernetes on AWS.

        EDUCATION
        B.Tech Computer Science | 2019 - 2023
        """
        val = validate_resume_document(text)
        self.assertTrue(val["resume_valid"])
        skills = extract_skills_from_resume(text)
        self.assertIn("Python", skills)
        self.assertIn("Docker", skills)

    def test_08_resume_without_explicit_resume_title(self):
        text = """
        Michael Zhang
        michael.zhang@dev.com | 555-333-4444 | github.com/mzhang

        PROFILE
        Backend Software Engineer specializing in Python and Distributed Systems.

        CORE COMPETENCIES
        Python, Go (Golang), Java, Redis, Kafka

        EXPERIENCE
        Backend Engineer | DataCorp | 2021 - Present

        EDUCATION
        B.S. Computer Science | MIT | 2017 - 2021
        """
        val = validate_resume_document(text)
        self.assertTrue(val["resume_valid"])
        skills = extract_skills_from_resume(text)
        self.assertIn("Python", skills)

    # --------------------------------------------------------------------------
    # INVALID DOCUMENT FIXTURES (9 - 20)
    # --------------------------------------------------------------------------

    def test_09_interview_performance_report_regression(self):
        """Regression fixture for report1.pdf failure case"""
        text = """
        InterviewIQ — Performance Report
        Candidate: User Session 8/30/26

        Overall Readiness: 75%
        Aggregate Score: 399 / 500
        Technical Competency: Developing
        Voice Confidence & Pacing: Nervous
        Measures Speaking Rate: 127 wpm
        Voice Tone Variation: Avoidance of Filler Words
        Emotion & Composure: Good
        Adaptive Difficulty Path: Early Stage

        Integrity Summary:
        Tab Switches: 2
        Camera Exits: 1
        Window Moves: 3
        Strike Count: 0

        Key Action Recommendations:
        Evaluates the depth of candidate answers.

        Detailed Question Review:
        1. Explain Python decorators and list comprehension.
        Score: 8/10
        AI Assessment Feedback: Candidate knows Python syntax well.
        """
        val = validate_resume_document(text)
        self.assertFalse(val["resume_valid"])
        self.assertEqual(val["document_type"], "interview_report")
        self.assertIn("interview performance report", val["reason"].lower())

        skills = extract_skills_from_resume(text)
        self.assertEqual(skills, [], "Interview performance report MUST NOT produce extracted skills!")

    def test_10_interview_result_pdf(self):
        text = """
        Interview Results & Candidate Assessment Report
        Date: 2026-09-15
        Session ID: sess_99812

        Candidate Performance Summary:
        Overall Readiness: High
        Technical Competency: 85/100
        Voice Confidence & Pacing: Excellent
        Integrity Summary: Pass
        Tab Switches: 0
        Camera Exits: 0

        AI Assessment Feedback:
        Candidate demonstrated solid understanding of software engineering concepts.
        """
        val = validate_resume_document(text)
        self.assertFalse(val["resume_valid"])
        self.assertEqual(val["document_type"], "interview_report")
        self.assertEqual(extract_skills_from_resume(text), [])

    def test_11_academic_question_paper(self):
        text = """
        Department of Computer Science & Engineering
        Mid-Semester Examination — Question Paper
        Subject: Data Structures & Algorithms
        Time Allowed: 3 Hours
        Maximum Marks: 100

        Attempt all questions.
        Section A: Multiple Choice Questions (20 Marks)
        1. What is the time complexity of binary search in Python or C++?
        2. Explain garbage collection in Java.

        Section B: Long Answer Questions
        3. Write a program to implement a binary search tree in C++.
        """
        val = validate_resume_document(text)
        self.assertFalse(val["resume_valid"])
        self.assertEqual(val["document_type"], "question_paper")
        self.assertEqual(extract_skills_from_resume(text), [])

    def test_12_research_paper(self):
        text = """
        Deep Convolutional Neural Networks for Image Recognition
        IEEE Transactions on Pattern Analysis

        ABSTRACT:
        In this paper we present a novel neural network architecture for computer vision.
        We benchmark our model against standard Python, PyTorch, and TensorFlow baselines.

        INTRODUCTION:
        Recent advances in AI and Machine Learning have transformed image classification.

        REFERENCES:
        [1] LeCun et al., Gradient-based learning applied to document recognition.
        [2] Krizhevsky et al., ImageNet classification with deep CNNs.
        """
        val = validate_resume_document(text)
        self.assertFalse(val["resume_valid"])
        self.assertEqual(extract_skills_from_resume(text), [])

    def test_13_project_report(self):
        text = """
        Final Year Project Report
        Title: E-Commerce System Development
        Submitted by: Group 14

        Table of Contents
        1. Introduction
        2. System Design
        3. Implementation using React, Node.js, and MySQL
        4. Testing Results
        """
        val = validate_resume_document(text)
        self.assertFalse(val["resume_valid"])
        self.assertEqual(extract_skills_from_resume(text), [])

    def test_14_certificate(self):
        text = """
        Certificate of Completion
        This is to certify that John Doe has successfully completed the online course
        Mastering Python and Machine Learning Development.
        Date: August 2025
        """
        val = validate_resume_document(text)
        self.assertFalse(val["resume_valid"])
        self.assertEqual(val["document_type"], "certificate")
        self.assertEqual(extract_skills_from_resume(text), [])

    def test_15_invoice(self):
        text = """
        TAX INVOICE
        Invoice Number: INV-2026-901
        Date: 2026-09-01
        Bill To: Acme Corp

        Item: Python Consultancy Services
        Subtotal: $1,500.00
        Tax (10%): $150.00
        Amount Due: $1,650.00
        Payment Terms: Net 30
        """
        val = validate_resume_document(text)
        self.assertFalse(val["resume_valid"])
        self.assertEqual(val["document_type"], "invoice")
        self.assertEqual(extract_skills_from_resume(text), [])

    def test_16_generic_technical_documentation(self):
        text = """
        FastAPI Framework Documentation
        Installation Guide & Getting Started

        To install FastAPI, run:
        $ pip install fastapi uvicorn

        Table of Contents:
        - Environment Setup
        - Creating First REST Endpoint
        - Connecting to MongoDB Database
        """
        val = validate_resume_document(text)
        self.assertFalse(val["resume_valid"])
        self.assertEqual(extract_skills_from_resume(text), [])

    def test_17_random_pdf_containing_keywords(self):
        text = """
        Cheatsheet & Syntax Overview:
        Python features dynamic typing.
        Java uses a JVM virtual machine.
        React uses a virtual DOM.
        Docker creates isolated containers.
        """
        val = validate_resume_document(text)
        self.assertFalse(val["resume_valid"])
        self.assertEqual(extract_skills_from_resume(text), [])

    def test_18_presentation_pdf(self):
        text = """
        Slide 1: Cloud Migration Strategy
        Agenda:
        - Overview of AWS Services
        - Docker and Kubernetes Benefits
        - Next Steps for Engineering Team
        """
        val = validate_resume_document(text)
        self.assertFalse(val["resume_valid"])
        self.assertEqual(extract_skills_from_resume(text), [])

    def test_19_job_description_pdf(self):
        text = """
        Job Opening: Senior Full Stack Engineer
        Company: CloudTech Solutions
        Location: Remote

        We are looking for an experienced developer with expertise in:
        - Python, FastAPI, and Flask
        - React, JavaScript, and TypeScript
        - PostgreSQL and Docker

        Responsibilities:
        - Design scalable cloud architecture on AWS.
        """
        val = validate_resume_document(text)
        self.assertFalse(val["resume_valid"])
        self.assertEqual(extract_skills_from_resume(text), [])

    def test_20_interviewiq_performance_report_direct(self):
        text = """
        INTERVIEWIQ PERFORMANCE EVALUATION REPORT
        Candidate Evaluation Date: September 2026

        Overall Readiness: 65%
        Technical Competency: Intermediate
        Voice Confidence & Pacing: 80%
        Emotion & Composure: Stable
        Adaptive Difficulty Path: Medium
        Integrity Summary: Verified Clean

        Tab Switches: 0
        Camera Exits: 0
        Window Moves: 0

        Detailed Question Review:
        Question 1: Explain React virtual DOM and state hooks.
        Question 2: How does Docker containerization work?
        """
        val = validate_resume_document(text)
        self.assertFalse(val["resume_valid"])
        self.assertEqual(val["document_type"], "interview_report")
        
        analysis = analyze_resume_data("dummy_path") # raw string via fallback or mocked text
        # Direct check on analyze_resume_data with invalid text
        val_direct = validate_resume_document(text)
        self.assertFalse(val_direct["resume_valid"])
        self.assertEqual(extract_skills_from_resume(text), [])

    # --------------------------------------------------------------------------
    # FALSE POSITIVE PROTECTION TESTS
    # --------------------------------------------------------------------------

    def test_false_positive_protections(self):
        # 1. "500 ml water" should not produce Machine Learning
        text_ml = "Recipe calls for 500 ml water and 200 g flour."
        self.assertEqual(extract_skills_from_resume(text_ml), [])

        # 2. "Go to the settings page" should not produce Go
        text_go = "Please go to the settings page and click save."
        self.assertEqual(extract_skills_from_resume(text_go), [])

        # 3. "Ruby was the author's name" should not produce Ruby
        text_ruby = "The book was written by Ruby Smith in 1998."
        self.assertEqual(extract_skills_from_resume(text_ruby), [])


if __name__ == "__main__":
    unittest.main()
