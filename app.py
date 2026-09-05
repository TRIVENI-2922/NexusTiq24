import os
import json
import re

from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

from src.gemini_service import extract_patient_info
from src.triage_engine import evaluate_triage
from src.retrieval_service import retrieve_rules


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY is not set.")


# ============================================================
# FLASK APP
# ============================================================

app = Flask(
    __name__,
    static_folder="frontend",
    static_url_path=""
)


# ============================================================
# LOAD TRIAGE RULES
# ============================================================

RULES_FILE = os.path.join(
    os.path.dirname(__file__),
    "data",
    "triage_rules.json"
)


def load_rules():
    try:
        with open(RULES_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as error:
        print("Error loading triage rules:", error)
        return []


TRIAGE_RULES = load_rules()


def get_rule_by_id(rule_id):
    """
    Return the complete rule for the selected rule_id.
    """

    for rule in TRIAGE_RULES:
        if rule.get("rule_id") == rule_id:
            return rule

    return {
        "rule_id": rule_id,
        "condition": "Information is insufficient to safely apply a triage rule",
        "urgency": "HUMAN_REVIEW",
        "department": "Human Clinical Triage",
        "criteria": [],
        "action": "Escalate to a human rather than guessing",
        "escalate": True
    }


# ============================================================
# TEXT HELPERS
# ============================================================

def contains_any(text, phrases):
    """
    Check whether any phrase exists in text.
    """

    text = text.lower()

    for phrase in phrases:
        if phrase.lower() in text:
            return True

    return False


def is_negated(text, phrase):
    """
    Basic negation detection.

    Examples:
        'no difficulty breathing'
        'do not have difficulty breathing'
        'without difficulty breathing'
    """

    text = text.lower()
    phrase = phrase.lower()

    index = text.find(phrase)

    if index == -1:
        return False

    before = text[max(0, index - 50):index]

    negation_patterns = [
        "no ",
        "not ",
        "don't ",
        "do not ",
        "doesn't ",
        "does not ",
        "without ",
        "never "
    ]

    for pattern in negation_patterns:
        if pattern in before:
            return True

    return False


def symptom_present(text, phrases):
    """
    Detect a symptom while trying to avoid
    simple negated statements.
    """

    for phrase in phrases:

        if phrase.lower() in text.lower():

            if not is_negated(text, phrase):
                return True

    return False


# ============================================================
# FALLBACK FOLLOW-UP QUESTIONS
# ============================================================

def get_fallback_questions(patient_text):
    """
    Used only when Gemini does not provide
    usable follow-up questions.
    """

    text = patient_text.lower()

    questions = []

    # --------------------------------------------------------
    # Chest pain
    # --------------------------------------------------------

    if symptom_present(
        text,
        [
            "chest pain",
            "pain in my chest",
            "chest hurts",
            "chest discomfort"
        ]
    ):

        questions = [
            {
                "question": "How long have you had the chest pain?",
                "type": "text"
            },
            {
                "question": "How severe is the pain on a scale of 1 to 10?",
                "type": "number"
            },
            {
                "question": "Does the pain spread to your arm or jaw?",
                "type": "yes_no"
            },
            {
                "question": "Are you having difficulty breathing?",
                "type": "yes_no"
            },
            {
                "question": "Have you fainted or lost consciousness?",
                "type": "yes_no"
            },
            {
                "question": "Are you having cold sweats?",
                "type": "yes_no"
            }
        ]

        return questions

    # --------------------------------------------------------
    # Breathing difficulty
    # --------------------------------------------------------

    if symptom_present(
        text,
        [
            "difficulty breathing",
            "shortness of breath",
            "breathing problem",
            "cannot breathe",
            "can't breathe"
        ]
    ):

        questions = [
            {
                "question": "How severe is the breathing difficulty?",
                "type": "number"
            },
            {
                "question": "Can you speak normally in full sentences?",
                "type": "yes_no"
            },
            {
                "question": "Are your lips or face turning blue?",
                "type": "yes_no"
            },
            {
                "question": "Have you fainted or lost consciousness?",
                "type": "yes_no"
            }
        ]

        return questions

    # --------------------------------------------------------
    # Fever
    # --------------------------------------------------------

    if symptom_present(
        text,
        [
            "fever",
            "high temperature",
            "temperature"
        ]
    ):

        questions = [
            {
                "question": "What is your temperature, if you have measured it?",
                "type": "text"
            },
            {
                "question": "How severe are your symptoms?",
                "type": "number"
            },
            {
                "question": "Are you having difficulty breathing?",
                "type": "yes_no"
            },
            {
                "question": "Have you fainted or lost consciousness?",
                "type": "yes_no"
            }
        ]

        return questions

    # --------------------------------------------------------
    # Injury
    # --------------------------------------------------------

    if symptom_present(
        text,
        [
            "injury",
            "injured",
            "accident",
            "wound"
        ]
    ):

        questions = [
            {
                "question": "Is there uncontrolled bleeding?",
                "type": "yes_no"
            },
            {
                "question": "Did you lose consciousness?",
                "type": "yes_no"
            },
            {
                "question": "Would you describe the injury as severe?",
                "type": "yes_no"
            }
        ]

        return questions

    # --------------------------------------------------------
    # Abdominal pain
    # --------------------------------------------------------

    if symptom_present(
        text,
        [
            "abdominal pain",
            "stomach pain",
            "pain in my abdomen"
        ]
    ):

        questions = [
            {
                "question": "How severe is the abdominal pain on a scale of 1 to 10?",
                "type": "number"
            },
            {
                "question": "Are you having difficulty breathing?",
                "type": "yes_no"
            },
            {
                "question": "Have you fainted or lost consciousness?",
                "type": "yes_no"
            }
        ]

        return questions

    return []


# ============================================================
# NORMALIZE FOLLOW-UP QUESTIONS
# ============================================================

def normalize_follow_up_questions(questions):
    """
    Convert Gemini questions into a predictable format.
    """

    normalized = []

    if not isinstance(questions, list):
        return normalized

    for question in questions:

        if isinstance(question, str):

            text = question.strip()

            if not text:
                continue

            normalized.append({
                "question": text,
                "type": detect_question_type(text)
            })

            continue

        if isinstance(question, dict):

            text = (
                question.get("question")
                or question.get("text")
                or question.get("prompt")
                or ""
            )

            text = str(text).strip()

            if not text:
                continue

            question_type = (
                question.get("type")
                or detect_question_type(text)
            )

            normalized.append({
                "question": text,
                "type": question_type
            })

    return normalized


def detect_question_type(question):
    """
    Determine frontend input type.
    """

    q = question.lower()

    if (
        "scale of 1 to 10" in q
        or "1-10" in q
        or "severity" in q
    ):
        return "number"

    if (
        "how long" in q
        or "duration" in q
        or "when did" in q
        or "temperature" in q
    ):
        return "text"

    return "yes_no"


# ============================================================
# FILTER ALREADY ANSWERED QUESTIONS
# ============================================================

def filter_answered_questions(questions, answers):
    """
    Remove questions that were already answered.
    """

    if not questions:
        return []

    if not answers:
        return questions

    answered_questions = set()

    for question, answer in answers.items():

        if answer is None:
            continue

        answer = str(answer).strip()

        if answer:
            answered_questions.add(
                question.strip().lower()
            )

    remaining = []

    for question in questions:

        question_text = question.get(
            "question",
            ""
        ).strip().lower()

        if question_text not in answered_questions:
            remaining.append(question)

    return remaining


# ============================================================
# CONVERT FRONTEND ANSWERS
# ============================================================

def normalize_answers(raw_answers):
    """
    Frontend sends:

    [
        {
            "question": "...",
            "answer": "...",
            "type": "yes_no"
        }
    ]

    Convert it into:

    {
        "question": "answer"
    }
    """

    if isinstance(raw_answers, dict):
        return raw_answers

    if not isinstance(raw_answers, list):
        return {}

    answers = {}

    for item in raw_answers:

        if not isinstance(item, dict):
            continue

        question = str(
            item.get("question", "")
        ).strip()

        answer = str(
            item.get("answer", "")
        ).strip()

        if question and answer:
            answers[question] = answer

    return answers


# ============================================================
# API: ANALYZE PATIENT
# ============================================================

@app.route("/api/analyze", methods=["POST"])
def analyze_patient():

    try:

        data = request.get_json(silent=True) or {}

        patient_text = str(
            data.get("patient_text", "")
        ).strip()

        if not patient_text:

            return jsonify({
                "error": "Patient description is required."
            }), 400

        # ----------------------------------------------------
        # Convert follow-up answers
        # ----------------------------------------------------

        raw_answers = data.get(
            "answers",
            {}
        )

        answers = normalize_answers(
            raw_answers
        )

        # ----------------------------------------------------
        # Gemini patient extraction
        # ----------------------------------------------------

        try:

            extracted = extract_patient_info(
                patient_text
            )

            if not isinstance(extracted, dict):
                extracted = {}

        except Exception as error:

            print(
                "Gemini extraction error:",
                error
            )

            extracted = {}

        # ----------------------------------------------------
        # Get Gemini follow-up questions
        # ----------------------------------------------------

        gemini_questions = normalize_follow_up_questions(
            extracted.get(
                "follow_up_questions",
                []
            )
        )

        # ----------------------------------------------------
        # Fallback questions
        # ----------------------------------------------------

        fallback_questions = get_fallback_questions(
            patient_text
        )

        # Prefer Gemini questions only if they are usable.
        # Otherwise use deterministic fallback questions.
        if gemini_questions:

            follow_up_questions = gemini_questions

        else:

            follow_up_questions = fallback_questions

        # ----------------------------------------------------
        # Remove questions already answered
        # ----------------------------------------------------

        remaining_questions = filter_answered_questions(
            follow_up_questions,
            answers
        )

        # ----------------------------------------------------
        # Deterministic triage
        # ----------------------------------------------------

        triage = evaluate_triage(
            patient_text,
            answers
        )

        if not isinstance(triage, dict):

            triage = {
                "rule_id": "UN-001",
                "urgency": "HUMAN_REVIEW",
                "department": "Human Clinical Triage",
                "reasoning": (
                    "Information is insufficient "
                    "to safely apply a triage rule."
                ),
                "human_review": True,
                "escalate": True
            }

        # ----------------------------------------------------
        # Exact final rule
        # ----------------------------------------------------

        selected_rule_id = triage.get(
            "rule_id",
            "UN-001"
        )

        final_rule = get_rule_by_id(
            selected_rule_id
        )

        # ----------------------------------------------------
        # Semantic retrieval
        # ----------------------------------------------------

        try:

            retrieved_rules = retrieve_rules(
                patient_text,
                top_k=3
            )

        except Exception as error:

            print(
                "Retrieval error:",
                error
            )

            retrieved_rules = []

        # ----------------------------------------------------
        # Patient information
        # ----------------------------------------------------

        patient_information = {
            "main_complaint": extracted.get(
                "main_complaint",
                ""
            ),

            "patient_reported": extracted.get(
                "patient_reported",
                extracted.get(
                    "reported_symptoms",
                    []
                )
            ),

            "remaining_unknowns": [
                item.get("question", "")
                for item in remaining_questions
            ]
        }

        # If Gemini did not provide a main complaint,
        # use a safe simple fallback.
        if not patient_information["main_complaint"]:

            text_lower = patient_text.lower()

            if "chest pain" in text_lower:
                patient_information["main_complaint"] = "chest pain"

            elif "fever" in text_lower:
                patient_information["main_complaint"] = "fever"

            elif (
                "abdominal pain" in text_lower
                or "stomach pain" in text_lower
            ):
                patient_information["main_complaint"] = (
                    "abdominal pain"
                )

            elif (
                "difficulty breathing" in text_lower
                or "shortness of breath" in text_lower
            ):
                patient_information["main_complaint"] = (
                    "breathing difficulty"
                )

            elif (
                "injury" in text_lower
                or "injured" in text_lower
            ):
                patient_information["main_complaint"] = "injury"

        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        response_data = {

            "triage_result": triage,

            "patient_information":
                patient_information,

            "final_rule":
                final_rule,

            "retrieved_rules":
                retrieved_rules,

            "follow_up_questions":
                remaining_questions
        }

        return jsonify(response_data)

    except Exception as error:

        print(
            "API error:",
            error
        )

        return jsonify({
            "error": (
                "Unable to analyze the patient. "
                "Please try again."
            )
        }), 500


# ============================================================
# SERVE FRONTEND
# ============================================================

@app.route("/")
def serve_index():

    return send_from_directory(
        "frontend",
        "index.html"
    )


# ============================================================
# SERVE STATIC FILES
# ============================================================

@app.route("/<path:path>")
def serve_static(path):

    file_path = os.path.join(
        app.static_folder,
        path
    )

    if os.path.isfile(file_path):

        return send_from_directory(
            app.static_folder,
            path
        )

    return send_from_directory(
        app.static_folder,
        "index.html"
    )


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("NexusTiq24 Healthcare Triage Assistant")
    print("=" * 60)
    print("Server: http://localhost:8000")
    print("Press CTRL+C to stop the server.")
    print("=" * 60)

    app.run(
        host="0.0.0.0",
        port=8000,
        debug=False
    )