# NexusTiq24 – Healthcare Patient Intake Triage Assistant

## Overview

NexusTiq24 is a healthcare patient intake and triage assistant designed to process incomplete patient descriptions in plain language.

The system identifies relevant symptoms, asks targeted follow-up questions when important information is missing, and applies deterministic triage rules to recommend an urgency level and department.

The system does not diagnose patients. When information is insufficient or a case may be high-risk, it escalates the case for human clinical review instead of guessing.

## Key Features

- Plain-language patient symptom intake
- Targeted follow-up questions
- Deterministic rule-based triage
- Chest pain danger-sign detection
- Breathing difficulty assessment
- Injury and bleeding assessment
- Fever assessment
- Abdominal pain assessment
- Human clinical review escalation
- Negation-aware symptom handling
- Gemini-powered patient information extraction
- Gemini embeddings for semantic retrieval
- Local rule retrieval and grounding
- Rule ID and reasoning shown with every recommendation
- Patient-reported information separated from follow-up information
- Remaining unknown information displayed
- Automated triage tests using pytest

## Technology Stack

### Backend

- Python
- Flask
- Google Gemini API
- NumPy

### AI / Retrieval

- Gemini for structured patient-information extraction
- `gemini-embedding-001` for embeddings
- Local semantic retrieval
- Deterministic triage rules stored in JSON

### Frontend

- HTML
- CSS
- JavaScript

### Testing

- pytest

## Project Structure

```text
NexusTiq24/
├── data/
│   ├── triage_rules.json
│   └── rule_embeddings.json
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── src/
│   ├── __init__.py
│   ├── gemini_service.py
│   ├── triage_engine.py
│   ├── embedding_service.py
│   └── retrieval_service.py
├── tests/
│   └── test_triage.py
├── app.py
├── requirements.txt
├── pytest.ini
├── .gitignore
└── README.md