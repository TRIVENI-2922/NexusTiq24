import os
import json

from google import genai


# ==================================================
# GEMINI CLIENT
# ==================================================

def get_client():

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set"
        )

    return genai.Client(
        api_key=api_key
    )


# ==================================================
# EXTRACT PATIENT INFORMATION
# ==================================================

def extract_patient_info(patient_text):

    client = get_client()

    prompt = f"""
You are a healthcare patient intake assistant.

Your ONLY job is to organize information that the patient
has explicitly reported and identify information that is
still missing for deterministic triage.

IMPORTANT SAFETY RULES:

1. Do NOT diagnose the patient.
2. Do NOT invent symptoms.
3. Do NOT assume symptoms that the patient did not report.
4. Treat explicit patient statements as facts.
5. Respect negation carefully.
   Example:
   "I do not have difficulty breathing"
   means difficulty breathing is NOT reported.
6. Keep patient-reported symptoms separate from missing information.
7. Ask ONLY relevant follow-up questions.
8. Do NOT ask questions unrelated to the patient's main complaint.
9. Do NOT repeat information that the patient has already provided.
10. Use simple English.
11. Return ONLY valid JSON.
12. Do not use markdown.
13. Do not add explanations outside JSON.

SUPPORTED TRIAGE CATEGORIES:

- fever
- injury
- chest pain
- breathing difficulty
- abdominal pain
- unknown / unclear complaint

FOLLOW-UP QUESTION RULES:

For CHEST PAIN, relevant questions may include:
- How long have you had the chest pain?
- How severe is the pain on a scale of 1 to 10?
- Does the pain spread to your arm or jaw?
- Are you having difficulty breathing?
- Have you fainted or lost consciousness?
- Are you having cold sweats?

For BREATHING DIFFICULTY, relevant questions may include:
- How severe is the difficulty breathing?
- Can you speak normally?
- Do you have blue lips?
- Have you fainted or lost consciousness?
- When did the breathing difficulty start?

For INJURY, relevant questions may include:
- How severe is the injury?
- Is there uncontrolled bleeding?
- Did you lose consciousness?
- When did the injury happen?

For FEVER, relevant questions may include:
- How long have you had the fever?
- How severe is the fever or how high is the temperature?
- Are you having difficulty breathing?
- Have you fainted or lost consciousness?

For ABDOMINAL PAIN, relevant questions may include:
- How long have you had the abdominal pain?
- How severe is the pain on a scale of 1 to 10?
- Where exactly is the pain?
- Is the pain getting worse?
- Are you having any other serious symptoms?

For UNKNOWN OR UNCLEAR COMPLAINT:
Ask a small number of broad questions that help identify
the main complaint and possible urgent symptoms.

IMPORTANT:

Only ask a question if its answer is actually missing.

For example:

Patient:
"I have fever since yesterday."

Do NOT ask:
"How long have you had the fever?"

because the patient already said "since yesterday".

Instead, ask relevant missing questions such as:
- How high is your temperature?
- How severe are your symptoms?
- Are you having difficulty breathing?
- Have you fainted or lost consciousness?

Another example:

Patient:
"I have chest pain but I do not have difficulty breathing."

Do NOT report difficulty breathing as a patient symptom.

Do NOT ask:
"Are you having difficulty breathing?"

because the patient already answered NO.

Patient description:

{patient_text}

Return EXACTLY this JSON structure:

{{
    "main_complaint": "",
    "reported_symptoms": [],
    "missing_information": [],
    "follow_up_questions": []
}}

Remember:

The patient's own statements are FACTS.

Do not convert unknown information into symptoms.

Do not convert a denied symptom into a reported symptom.

Ask only relevant missing questions.
"""

    # ==================================================
    # CALL GEMINI
    # ==================================================

    response = client.models.generate_content(

        model="gemini-3.6-flash",

        contents=prompt

    )

    # ==================================================
    # GET RESPONSE TEXT
    # ==================================================

    text = response.text.strip()

    # ==================================================
    # REMOVE MARKDOWN CODE BLOCK IF PRESENT
    # ==================================================

    if text.startswith("```"):

        text = text.replace(
            "```json",
            ""
        )

        text = text.replace(
            "```",
            ""
        )

        text = text.strip()

    # ==================================================
    # PARSE JSON
    # ==================================================

    try:

        patient_info = json.loads(
            text
        )

    except json.JSONDecodeError as error:

        raise RuntimeError(
            f"Gemini returned invalid JSON: {error}"
        )

    # ==================================================
    # SAFETY CHECK
    # ==================================================

    if not isinstance(
        patient_info,
        dict
    ):

        raise RuntimeError(
            "Gemini response is not a JSON object"
        )

    # ==================================================
    # ENSURE REQUIRED FIELDS
    # ==================================================

    patient_info.setdefault(
        "main_complaint",
        ""
    )

    patient_info.setdefault(
        "reported_symptoms",
        []
    )

    patient_info.setdefault(
        "missing_information",
        []
    )

    patient_info.setdefault(
        "follow_up_questions",
        []
    )

    # ==================================================
    # TYPE SAFETY
    # ==================================================

    if not isinstance(
        patient_info["reported_symptoms"],
        list
    ):

        patient_info["reported_symptoms"] = []

    if not isinstance(
        patient_info["missing_information"],
        list
    ):

        patient_info["missing_information"] = []

    if not isinstance(
        patient_info["follow_up_questions"],
        list
    ):

        patient_info["follow_up_questions"] = []

    # ==================================================
    # RETURN
    # ==================================================

    return patient_info