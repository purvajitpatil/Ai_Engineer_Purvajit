import os
import time
import json
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel
from pypdf import PdfReader
from docx import Document

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
load_dotenv(os.path.join(_ROOT, ".env"))

my_api_key = os.getenv("GROQ_API_KEY")
if not my_api_key:
    raise ValueError("GROQ_API_KEY not found in .env file.")

client = Groq(api_key=my_api_key)
MODEL  = "llama-3.3-70b-versatile"


class JobD(BaseModel):
    role: str
    required_skills: list[str]
    preferred_skills: list[str]
    minimum_experience: float | None
    education_requirements: list[str]
    responsibilities: list[str]

class Experience(BaseModel):
    company: str | None = None
    role: str | None = None
    duration: str | None = None
    description: str | None = None
    skills_used: list[str] = []

class Resume(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    total_experience_years: float | None = None
    skills: list[str] = []
    experiences: list[Experience] = []
    education: list[str] = []
    projects: list[str] = []
    certifications: list[str] = []

class MatchResult(BaseModel):
    score: float
    details: dict


def parse_job_description(job_description: str) -> JobD:
    jobd_schema = JobD.model_json_schema()
    system_prompt = f"""
You are an expert HR assistant.
Extract structured information from job descriptions.
Return ONLY valid JSON matching this schema:
{jobd_schema}
Do NOT return schema fields like "properties", "title", or "type".
Fill with actual values. Return null for missing numbers, [] for missing lists.
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze this job description:\n\n{job_description}"},
        ],
        response_format={"type": "json_object"},
    )
    return JobD(**json.loads(response.choices[0].message.content))


def parse_resume(resume_text: str) -> Resume:
    resume_schema = Resume.model_json_schema()
    system_prompt = f"""
You are an expert resume parser.
Extract information by meaning, not just headings.
Treat Experience, Work History, Employment, Internships as the same.
Collect skills from all sections.
Return ONLY valid JSON matching this schema:
{resume_schema}
Return null for missing values, [] for missing lists. Do not invent data.
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Parse this resume:\n\n{resume_text}"},
        ],
        response_format={"type": "json_object"},
    )
    return Resume(**json.loads(response.choices[0].message.content))


def final_score(job: JobD, resume: Resume) -> MatchResult:
    match_schema = MatchResult.model_json_schema()
    prompt = f"""
You are an HR recruiter. Compare the resume with the job description.

JOB DESCRIPTION:
{job.model_dump_json(indent=2)}

CANDIDATE RESUME:
{resume.model_dump_json(indent=2)}

Return JSON matching this schema:
{match_schema}

The "details" dict must include:
  - candidate_name
  - matching_skills
  - missing_important_skills
  - experience_requirement_met
  - overall_match_percentage
  - final_verdict
"""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return MatchResult(**json.loads(response.choices[0].message.content))


def read_pdf(file_path: Path) -> str:
    reader = PdfReader(file_path)
    return "\n".join(p.extract_text() for p in reader.pages if p.extract_text())

def read_docx(file_path: Path) -> str:
    doc = Document(file_path)
    text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    text += "\n" + cell.text
    return text

def read_resume_file(file_path: Path) -> str | None:
    if file_path.suffix.lower() == ".pdf":
        return read_pdf(file_path)
    elif file_path.suffix.lower() == ".docx":
        return read_docx(file_path)
    return None


def score_bar(score: float) -> str:
    filled = int(score) // 5
    return "#" * filled + "-" * (20 - filled)

def divider(title: str = "", width: int = 60):
    print("\n" + "=" * width)
    if title:
        print(f"  {title}")
        print("=" * width)

def print_candidate(label: str, candidate: dict):
    print(f"\n  {label}: {candidate['name']}")
    print(f"  Score : {candidate['score']}%  [{score_bar(candidate['score'])}]")
    for key, val in candidate["details"].items():
        print(f"  {key.replace('_', ' ').title():<30}: {val}")


JOB_DESCRIPTION = """
At Amazon, we are hiring Software Development Engineers (SDE-I).

Key Responsibilities:
- Design and develop scalable solutions using cloud-native architectures and microservices.
- Build and maintain resilient distributed systems that are scalable and fault-tolerant.
- Write clean, maintainable code following best practices.
- Work in an agile environment practicing CI/CD principles.
- Leverage GenAI and AI-powered tools to enhance development productivity.

Basic Qualifications:
- Proficiency in Python, Java, C++, Go, Rust, or TypeScript
- Experience with data structures, algorithms, and object-oriented design
- Bachelor's degree in Computer Science or related STEM field

Preferred Qualifications:
- Previous internship or project experience
- Experience with AWS, SQL/NoSQL databases, AI tools
- Strong problem-solving and communication skills
"""


def main():
    divider("[AI]  AI RESUME EVALUATOR  -  Groq / LLaMA-3.3-70b")

    print("\n[1/3] Parsing Job Description...")
    job = parse_job_description(JOB_DESCRIPTION)
    print(f"      Role              : {job.role}")
    print(f"      Min. Experience   : {job.minimum_experience} yrs")
    print(f"      Education         : {', '.join(job.education_requirements)}")

    resume_folder = Path(__file__).parent / "resumes"
    resume_folder.mkdir(exist_ok=True)

    resume_files = [f for f in resume_folder.iterdir() if f.suffix.lower() in (".pdf", ".docx")]

    if not resume_files:
        print(f"\n[!] No resumes found in '{resume_folder}'. Add PDF/DOCX files and re-run.")
        return

    print(f"\n[2/3] Found {len(resume_files)} resume(s). Analysing...\n")

    all_results: list[dict] = []

    for file_path in resume_files:
        print(f"  Processing : {file_path.name}")
        resume_text = read_resume_file(file_path)
        if not resume_text or not resume_text.strip():
            print("    -> Could not extract text. Skipping.\n")
            continue

        parsed = parse_resume(resume_text)
        time.sleep(3)

        result = final_score(job, parsed)
        time.sleep(3)

        print(f"    -> Score : {result.score}%\n")
        all_results.append({
            "name":    parsed.name or file_path.stem,
            "score":   result.score,
            "details": result.details,
        })

    if not all_results:
        print("[!] No resumes could be evaluated.")
        return

    all_results.sort(key=lambda c: c["score"], reverse=True)

    divider("TOP 2 CANDIDATES")
    for i, candidate in enumerate(all_results[:2], 1):
        print_candidate(f"Rank #{i}", candidate)

    divider("LOWEST 2 CANDIDATES")
    for i, candidate in enumerate(all_results[-2:], 1):
        print_candidate(f"Bottom #{i}", candidate)

    divider()
    print(f"  [3/3] Done! Evaluated {len(all_results)} candidate(s).")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
