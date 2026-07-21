# AI Resume Evaluator

An AI-powered resume screening tool built with **Python**, **Groq (LLaMA-3.3-70b)**, and **Pydantic**.

Paste a Job Description → drop resumes in a folder → get every candidate scored 0–100% in seconds.

---

## How It Works

```
Job Description (text)
        │
        ▼  LLM Call 1
    JobD (Pydantic model)
        │
        ├──── Resume 1 (PDF/DOCX)
        │         │  LLM Call 2 → Resume model
        │         │  LLM Call 3 → MatchResult (score + details)
        │
        ├──── Resume 2 ...
        │
        └──── Ranked output: Top 2 / Bottom 2 candidates
```

---

## Tech Stack

| Library | Purpose |
|---|---|
| `groq` | LLaMA-3.3-70b API (free tier) |
| `pydantic` | Structured, validated LLM output |
| `pypdf` | PDF text extraction |
| `python-docx` | DOCX text extraction |
| `python-dotenv` | API key from `.env` |

---

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/purvajitpatil/Ai_Engineer_Purvajit.git
cd Ai_Engineer_Purvajit

# 2. Install dependencies
pip install groq pypdf python-docx python-dotenv pydantic

# 3. Add your Groq API key
echo GROQ_API_KEY=your_key_here > .env

# Get a free key at: https://console.groq.com/keys

# 4. Drop resumes into the folder
#    week1/day2/resumes/  (PDF or DOCX)

# 5. Run
python week1/day2/main.py
```

---

## Output Example

```
============================================================
  [AI]  AI RESUME EVALUATOR  -  Groq / LLaMA-3.3-70b
============================================================

[1/3] Parsing Job Description...
      Role              : Software Development Engineer (SDE-I)

[2/3] Found 3 resume(s). Analysing...

  Processing : carol_singh.pdf  ->  Score : 92%
  Processing : alice_johnson.pdf  ->  Score : 87%
  Processing : bob_martinez.pdf  ->  Score : 31%

============================================================
  TOP 2 CANDIDATES
============================================================

  Rank #1: Carol Singh
  Score : 92%  [##################--]
  Matching Skills               : Python, FastAPI, Docker, AWS, LangChain
  Final Verdict                 : Strong match with extensive AI/ML experience

  Rank #2: Alice Johnson
  Score : 87%  [#################---]
  Matching Skills               : Python, Docker, AWS, Kubernetes
  Final Verdict                 : Excellent backend engineer with cloud experience
```

---

## Project Structure

```
Ai_Engineer_Purvajit/
├── .env                  ← API keys (not committed)
├── .gitignore
├── README.md
└── week1/
    └── day2/
        ├── main.py       ← main script
        └── resumes/      ← drop your PDF/DOCX files here
```

---

## Get a Free Groq API Key

1. Go to [console.groq.com/keys](https://console.groq.com/keys)
2. Sign up (free)
3. Create a key and paste it in `.env`
