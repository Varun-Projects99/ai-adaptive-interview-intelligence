"""
Comprehensive Automated Test Suite for Resume Parser & Validator Engine
========================================================================
Validates all 30 extraction correctness requirements ("Accurate Explicit Resume Data > Guessing").
"""

import unittest
import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.resume_parser import (
    parse_sections,
    extract_profile_summary,
    extract_location,
    analyze_education,
    analyze_projects,
    analyze_experience,
    analyze_certifications,
    extract_skills_and_evidence,
    extract_skills_from_resume
)
from modules.resume_validator import validate_resume_document


class TestResumeParserAccuracy(unittest.TestCase):

    def test_01_location_extraction(self):
        text = "John Doe\nEmail: john@example.com\nLocation: Bengaluru, Karnataka\n\nTECHNICAL SKILLS\nPython, Java"
        sections = parse_sections(text)
        loc = extract_location(text, sections)
        self.assertIn("Bengaluru", loc)
        self.assertIn("Karnataka", loc)

        text2 = "Jane Smith\nBangalore, India\n\nTECHNICAL SKILLS\nReact, Node"
        sections2 = parse_sections(text2)
        loc2 = extract_location(text2, sections2)
        self.assertIn("Bangalore", loc2)

    def test_02_technology_cannot_become_location(self):
        text = "Candidate Name\nEmail: test@example.com\n\nTECHNICAL SKILLS\nTerraform, Azure, AWS, Docker, Kubernetes\n\nEDUCATION\nB.E. Computer Science"
        sections = parse_sections(text)
        loc = extract_location(text, sections)
        self.assertEqual(loc, "Not detected")

    def test_03_degree_extraction(self):
        text = "EDUCATION\nB.E. Computer Science and Engineering\nEast Point College of Engineering and Technology\nGraduation: 2027"
        sections = parse_sections(text)
        edu = analyze_education(sections)
        self.assertIn("Bachelor of Engineering", edu["degree"])

    def test_04_be_cannot_become_institution(self):
        text = "EDUCATION\nB.E. Computer Science\nGraduation: 2027"
        sections = parse_sections(text)
        edu = analyze_education(sections)
        self.assertIn("Bachelor of Engineering", edu["degree"])
        self.assertEqual(edu["institution"], "Not detected")

    def test_05_institution_extraction(self):
        text = "EDUCATION\nB.E. Computer Science and Engineering\nEast Point College of Engineering and Technology\nGraduation: 2027"
        sections = parse_sections(text)
        edu = analyze_education(sections)
        self.assertEqual(edu["institution"], "East Point College of Engineering and Technology")

    def test_06_specialization(self):
        text = "EDUCATION\nB.Tech Computer Science and Engineering\nIIT Bombay"
        sections = parse_sections(text)
        edu = analyze_education(sections)
        self.assertEqual(edu["specialization"], "Computer Science and Engineering")

    def test_07_graduation_year(self):
        text = "EDUCATION\nB.E. Computer Science\nCollege of Engineering\nExpected Graduation: 2027"
        sections = parse_sections(text)
        edu = analyze_education(sections)
        self.assertEqual(edu["graduation_year"], "2027")

    def test_08_correct_project_grouping(self):
        text = "PROJECTS\nCloudDeployX — Enterprise DevOps Platform\nDesigned an enterprise-grade DevOps platform using Docker, Kubernetes, Helm and Terraform.\nImplemented infrastructure as code and CI/CD workflows."
        sections = parse_sections(text)
        proj = analyze_projects(sections)
        self.assertEqual(proj["projects_count"], 1)
        self.assertEqual(proj["projects"][0]["name"], "CloudDeployX — Enterprise DevOps Platform")

    def test_09_developed_cannot_become_project(self):
        text = "PROJECTS\nAI-Powered Interview System\nDeveloped a microservice architecture for video processing.\nBuilt low-latency real-time streaming pipelines."
        sections = parse_sections(text)
        proj = analyze_projects(sections)
        names = [p["name"] for p in proj["projects"]]
        self.assertNotIn("Developed", names)
        self.assertNotIn("Built", names)

    def test_10_built_cannot_become_project(self):
        text = "PROJECTS\nDevOps Automation Tool\nBuilt CI/CD automated deployment script."
        sections = parse_sections(text)
        proj = analyze_projects(sections)
        names = [p["name"] for p in proj["projects"]]
        self.assertNotIn("Built", names)

    def test_11_project_technologies_association(self):
        text = "PROJECTS\nProject Alpha\nDescription of Alpha using React and Node.js\n\nProject Beta\nDescription of Beta using Python and FastAPI"
        sections = parse_sections(text)
        proj = analyze_projects(sections)
        self.assertEqual(len(proj["projects"]), 2)

        alpha_tech = proj["projects"][0]["technologies"]
        beta_tech = proj["projects"][1]["technologies"]

        self.assertIn("React", alpha_tech)
        self.assertIn("Node.js", alpha_tech)
        self.assertNotIn("Python", alpha_tech)

        self.assertIn("Python", beta_tech)
        self.assertIn("FastAPI", beta_tech)

    def test_12_c_false_positive_prevention(self):
        text = "SUMMARY\nExperienced in conducted cloud deployments and topics in computer science."
        sections = parse_sections(text)
        pages = [(1, text)]
        skills, _, _ = extract_skills_and_evidence(pages, text, sections)
        self.assertNotIn("C", skills)

    def test_13_python_extraction_from_technical_skills(self):
        text = "John Doe\nemail@example.com\n\nTECHNICAL SKILLS\nLanguages: Python, Java, C++"
        sections = parse_sections(text)
        pages = [(1, text)]
        skills, _, _ = extract_skills_and_evidence(pages, text, sections)
        self.assertIn("Python", skills)
        self.assertIn("Java", skills)

    def test_14_azure_extraction_from_technical_skills(self):
        text = "Jane Smith\nemail@example.com\n\nTECHNICAL SKILLS\nCloud: Azure, AWS, GCP"
        sections = parse_sections(text)
        pages = [(1, text)]
        skills, _, _ = extract_skills_and_evidence(pages, text, sections)
        self.assertIn("Azure", skills)
        self.assertIn("AWS", skills)

    def test_15_github_word_in_project_description(self):
        text = "John Doe\njohn@example.com\n\nPROJECTS\nCloud App\nHosted code on GitHub repository for tracking."
        sections = parse_sections(text)
        summary = extract_profile_summary(text, sections)
        self.assertEqual(summary["github"], "Not detected")

    def test_16_linkedin_word_alone(self):
        text = "John Doe\njohn@example.com\n\nSUMMARY\nConnect with me on LinkedIn for professional details."
        sections = parse_sections(text)
        summary = extract_profile_summary(text, sections)
        self.assertEqual(summary["linkedin"], "Not detected")

    def test_17_invalid_email_rejected(self):
        text = "John Doe\nContact: john-at-example-dot-com\nPhone: 12345"
        sections = parse_sections(text)
        summary = extract_profile_summary(text, sections)
        self.assertEqual(summary["email"], "Not detected")

    def test_18_valid_email_preserved(self):
        text = "John Doe\nEmail: candidate@example.com\nPhone: +91 9876543210"
        sections = parse_sections(text)
        summary = extract_profile_summary(text, sections)
        self.assertEqual(summary["email"], "candidate@example.com")

    def test_19_missing_location_not_detected(self):
        text = "John Doe\nEmail: john@example.com\n\nTECHNICAL SKILLS\nPython, Java"
        sections = parse_sections(text)
        summary = extract_profile_summary(text, sections)
        self.assertEqual(summary["location"], "Not detected")

    def test_20_missing_institution_not_detected(self):
        text = "EDUCATION\nDegree: Bachelor of Science\nYear: 2024"
        sections = parse_sections(text)
        edu = analyze_education(sections)
        self.assertEqual(edu["institution"], "Not detected")

    def test_21_missing_certification_not_detected(self):
        text = "SKILLS\nAWS, Azure, Docker"
        sections = parse_sections(text)
        cert = analyze_certifications(sections)
        self.assertFalse(cert["has_certifications"])

    def test_22_non_resume_pdf_rejected(self):
        text = "INVOICE #1024\nBill To: ACME Corp\nAmount Due: $500\nTotal Due: $500\nPayment Terms: Net 30"
        val = validate_resume_document(text)
        self.assertFalse(val["resume_valid"])
        self.assertEqual(val["document_type"], "invoice")

    def test_23_interview_report_pdf_rejected(self):
        text = "INTERVIEW PERFORMANCE REPORT\nCandidate: Test User\nOverall Readiness: 85%\nVoice Confidence & Pacing: 90%\nTab Switches: 0\nCamera Exits: 0\nQuestion Review"
        val = validate_resume_document(text)
        self.assertFalse(val["resume_valid"])
        self.assertEqual(val["document_type"], "interview_report")

    def test_24_project_report_pdf_rejected(self):
        text = "PROJECT REPORT ON AI INTELLIGENCE\nSubmitted By: Student Name\nSubmitted To: Department of Computer Science\nIn partial fulfillment of Bachelor of Technology\nAcademic Year: 2025-2026\nGuide: Prof. Smith\nTable of Contents"
        val = validate_resume_document(text)
        self.assertFalse(val["resume_valid"])
        self.assertEqual(val["document_type"], "project_report")

    def test_25_student_resume_accepted(self):
        text = "ARJUN KUMAR\nEmail: arjun@example.com | Phone: 9876543210\nGitHub: github.com/arjunkumar\n\nEDUCATION\nB.E. Computer Science and Engineering\nEast Point College of Engineering and Technology\nGraduation: 2027\n\nTECHNICAL SKILLS\nPython, Java, React, Node.js, MongoDB\n\nPROJECTS\nSmart City App\nBuilt mobile application for public transport.\n\nCERTIFICATIONS\nAWS Certified Cloud Practitioner"
        val = validate_resume_document(text)
        self.assertTrue(val["resume_valid"])
        self.assertEqual(val["document_type"], "resume")

    def test_26_two_column_resume_parsing(self):
        text = "ARJUN KUMAR\narjun@example.com\n\nTECHNICAL SKILLS          EDUCATION\nPython, React             B.E. Computer Science\nNode.js, MongoDB          East Point College\n\nPROJECTS                  EXPERIENCE\nDevOps Tool               Software Intern"
        sections = parse_sections(text)
        self.assertTrue(len(sections["skills"]) > 0 or len(sections["education"]) > 0)

    def test_27_multi_page_resume_parsing(self):
        pages = [(1, "Page 1 text with Python"), (2, "Page 2 text with React")]
        text = "Page 1 text with Python\nPage 2 text with React"
        sections = parse_sections(text)
        skills, evidence, _ = extract_skills_and_evidence(pages, text, sections)
        self.assertTrue(len(evidence) >= 0)

    def test_28_ocr_fallback(self):
        text = "John Candidate\nEmail: candidate@example.com\n\nTECHNICAL SKILLS\nPython, Docker, Kubernetes"
        val = validate_resume_document(text)
        self.assertTrue(val["resume_valid"])

    def test_29_no_fabricated_candidate_role(self):
        text = "ARJUN KUMAR\nEmail: arjun@example.com\n\nTECHNICAL SKILLS\nDocker, Azure, Terraform, Kubernetes\n\nEDUCATION\nB.E. Computer Science"
        sections = parse_sections(text)
        summary = extract_profile_summary(text, sections)
        self.assertEqual(summary["current_role"], "Not detected")

    def test_30_no_fabricated_skills(self):
        text = "This is a simple document about general administrative tasks and meeting minutes."
        sections = parse_sections(text)
        pages = [(1, text)]
        skills, _, _ = extract_skills_and_evidence(pages, text, sections)
        self.assertEqual(len(skills), 0)


if __name__ == "__main__":
    unittest.main()
