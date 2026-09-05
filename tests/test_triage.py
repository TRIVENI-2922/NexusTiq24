from src.triage_engine import evaluate_triage


def test_chest_pain_with_breathing_difficulty():
    result = evaluate_triage(
        "I have chest pain",
        {
            "Are you having difficulty breathing?": "yes"
        }
    )

    assert result["rule_id"] == "CP-001"
    assert result["urgency"] == "EMERGENCY"


def test_chest_pain_without_danger_sign():
    result = evaluate_triage(
        "I have chest pain",
        {
            "Are you having difficulty breathing?": "no",
            "Have you fainted or lost consciousness?": "no",
            "Are you having cold sweats?": "no",
            "Does the pain spread to your arm or jaw?": "no"
        }
    )

    assert result["rule_id"] == "UN-001"
    assert result["urgency"] == "HUMAN_REVIEW"


def test_fever():
    result = evaluate_triage(
        "I have fever",
        {}
    )

    assert result["rule_id"] == "FV-001"
    assert result["urgency"] == "URGENT"


def test_abdominal_pain():
    result = evaluate_triage(
        "I have abdominal pain",
        {}
    )

    assert result["rule_id"] == "AB-001"
    assert result["urgency"] == "URGENT"


def test_severe_injury():
    result = evaluate_triage(
        "I had an injury",
        {
            "Do you have uncontrolled bleeding?": "yes"
        }
    )

    assert result["rule_id"] == "IN-001"
    assert result["urgency"] == "EMERGENCY"


def test_unknown_case():
    result = evaluate_triage(
        "I don't feel well",
        {}
    )

    assert result["rule_id"] == "UN-001"
    assert result["urgency"] == "HUMAN_REVIEW"