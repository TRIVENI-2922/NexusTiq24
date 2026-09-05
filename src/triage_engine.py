import json
from pathlib import Path


# ==================================================
# RULES FILE
# ==================================================

RULES_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "triage_rules.json"
)


# ==================================================
# LOAD RULES
# ==================================================

def load_rules():

    with open(
        RULES_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ==================================================
# NORMALIZE TEXT
# ==================================================

def normalize(text):

    return str(text).lower().strip()


# ==================================================
# CHECK YES ANSWER
# ==================================================

def answer_is_yes(answer):

    return normalize(answer) in [
        "yes",
        "y",
        "true",
        "1",
        "present"
    ]


# ==================================================
# GET POSITIVE FOLLOW-UP ANSWERS
# ==================================================

def get_positive_answers(answers):

    positive_text = []

    for question, answer in answers.items():

        if answer_is_yes(answer):

            positive_text.append(
                normalize(question)
            )

    return " ".join(
        positive_text
    )


# ==================================================
# CHECK POSITIVE PHRASE SAFELY
# ==================================================

def has_positive_phrase(
    text,
    phrase
):

    text = normalize(text)
    phrase = normalize(phrase)


    # ------------------------------------------
    # NEGATION PATTERNS
    # ------------------------------------------

    negative_patterns = [

        f"no {phrase}",

        f"not {phrase}",

        f"without {phrase}",

        f"don't have {phrase}",

        f"do not have {phrase}",

        f"doesn't have {phrase}",

        f"does not have {phrase}"

    ]


    for pattern in negative_patterns:

        if pattern in text:

            return False


    return phrase in text


# ==================================================
# CHECK FOLLOW-UP ANSWER
# ==================================================

def follow_up_is_yes(
    answers,
    keywords
):

    for question, answer in answers.items():

        if not answer_is_yes(answer):

            continue


        question_text = normalize(
            question
        )


        for keyword in keywords:

            if normalize(keyword) in question_text:

                return True


    return False


# ==================================================
# EVALUATE TRIAGE
# ==================================================

def evaluate_triage(
    patient_text,
    answers
):

    rules = load_rules()


    patient_text = normalize(
        patient_text
    )


    if not isinstance(
        answers,
        dict
    ):

        answers = {}


    # ==================================================
    # FOLLOW-UP POSITIVE INFORMATION
    # ==================================================

    positive_answers = (
        get_positive_answers(
            answers
        )
    )


    combined_text = (
        patient_text
        + " "
        + positive_answers
    )


    # ==================================================
    # CHEST PAIN
    # ==================================================

    chest_pain_present = (
        has_positive_phrase(
            patient_text,
            "chest pain"
        )
        or
        follow_up_is_yes(
            answers,
            [
                "chest pain"
            ]
        )
    )


    if chest_pain_present:


        chest_danger_signs = [

            "difficulty breathing",

            "fainting",

            "fainted",

            "cold sweat",

            "pain spreading to arm",

            "pain spreading to jaw",

            "severe chest pain"

        ]


        danger_found = False


        for sign in chest_danger_signs:

            if has_positive_phrase(
                combined_text,
                sign
            ):

                danger_found = True

                break


        # ------------------------------------------
        # CHEST PAIN + FOLLOW-UP DANGER SIGN
        # ------------------------------------------

        if not danger_found:

            if follow_up_is_yes(
                answers,
                [
                    "difficulty breathing",
                    "breathing"
                ]
            ):

                danger_found = True


        if not danger_found:

            if follow_up_is_yes(
                answers,
                [
                    "faint",
                    "consciousness"
                ]
            ):

                danger_found = True


        if not danger_found:

            if follow_up_is_yes(
                answers,
                [
                    "cold sweat"
                ]
            ):

                danger_found = True


        if danger_found:

            rule = next(
                r for r in rules
                if r["rule_id"] == "CP-001"
            )


            return {

                "urgency":
                    rule["urgency"],

                "department":
                    rule["department"],

                "rule_id":
                    rule["rule_id"],

                "reason":
                    rule["condition"],

                "action":
                    rule["action"],

                "escalate":
                    True

            }


        # ------------------------------------------
        # CHEST PAIN WITHOUT ENOUGH INFORMATION
        # ------------------------------------------

        rule = next(
            r for r in rules
            if r["rule_id"] == "UN-001"
        )


        return {

            "urgency":
                "HUMAN_REVIEW",

            "department":
                "Human Clinical Triage",

            "rule_id":
                "UN-001",

            "reason":
                (
                    "Chest pain is present but "
                    "no emergency danger sign has "
                    "been established."
                ),

            "action":
                (
                    "Human clinical triage is required "
                    "because information is insufficient."
                ),

            "escalate":
                True

        }


    # ==================================================
    # BREATHING DIFFICULTY
    # ==================================================

    breathing_present = (

        has_positive_phrase(
            patient_text,
            "difficulty breathing"
        )

        or

        has_positive_phrase(
            patient_text,
            "breathing difficulty"
        )

        or

        follow_up_is_yes(
            answers,
            [
                "difficulty breathing",
                "breathing difficulty",
                "breathing"
            ]
        )

    )


    if breathing_present:


        severe_breathing = (

            has_positive_phrase(
                combined_text,
                "severe difficulty breathing"
            )

            or

            follow_up_is_yes(
                answers,
                [
                    "severe difficulty breathing"
                ]
            )

        )


        cannot_speak = (

            has_positive_phrase(
                combined_text,
                "cannot speak normally"
            )

            or

            follow_up_is_yes(
                answers,
                [
                    "cannot speak normally",
                    "speak normally"
                ]
            )

        )


        blue_lips = (

            has_positive_phrase(
                combined_text,
                "blue lips"
            )

            or

            follow_up_is_yes(
                answers,
                [
                    "blue lips"
                ]
            )

        )


        fainting = (

            has_positive_phrase(
                combined_text,
                "fainting"
            )

            or

            has_positive_phrase(
                combined_text,
                "fainted"
            )

            or

            follow_up_is_yes(
                answers,
                [
                    "faint",
                    "consciousness"
                ]
            )

        )


        # ------------------------------------------
        # BREATHING + DANGER SIGN
        # ------------------------------------------

        if (
            severe_breathing
            or cannot_speak
            or blue_lips
            or fainting
        ):

            rule = next(
                r for r in rules
                if r["rule_id"] == "BD-001"
            )


            return {

                "urgency":
                    rule["urgency"],

                "department":
                    rule["department"],

                "rule_id":
                    rule["rule_id"],

                "reason":
                    rule["condition"],

                "action":
                    rule["action"],

                "escalate":
                    True

            }


        # ------------------------------------------
        # BREATHING DIFFICULTY ALONE
        # ------------------------------------------

        rule = next(
            r for r in rules
            if r["rule_id"] == "UN-001"
        )


        return {

            "urgency":
                "HUMAN_REVIEW",

            "department":
                "Human Clinical Triage",

            "rule_id":
                "UN-001",

            "reason":
                (
                    "Difficulty breathing is present "
                    "but severity and emergency danger "
                    "signs are not sufficiently established."
                ),

            "action":
                (
                    "Human clinical triage is required "
                    "because information is insufficient."
                ),

            "escalate":
                True

        }


    # ==================================================
    # INJURY
    # ==================================================

    injury_present = (

        has_positive_phrase(
            patient_text,
            "injury"
        )

        or

        has_positive_phrase(
            patient_text,
            "bleeding"
        )

        or

        follow_up_is_yes(
            answers,
            [
                "injury",
                "bleeding"
            ]
        )

    )


    if injury_present:


        uncontrolled_bleeding = (

            has_positive_phrase(
                combined_text,
                "uncontrolled bleeding"
            )

            or

            follow_up_is_yes(
                answers,
                [
                    "uncontrolled bleeding"
                ]
            )

        )


        loss_of_consciousness = (

            has_positive_phrase(
                combined_text,
                "loss of consciousness"
            )

            or

            has_positive_phrase(
                combined_text,
                "fainted"
            )

            or

            follow_up_is_yes(
                answers,
                [
                    "faint",
                    "consciousness"
                ]
            )

        )


        severe_injury = (

            has_positive_phrase(
                combined_text,
                "severe injury"
            )

            or

            follow_up_is_yes(
                answers,
                [
                    "severe injury"
                ]
            )

        )


        # ------------------------------------------
        # INJURY + DANGER SIGN
        # ------------------------------------------

        if (
            uncontrolled_bleeding
            or loss_of_consciousness
            or severe_injury
        ):

            rule = next(
                r for r in rules
                if r["rule_id"] == "IN-001"
            )


            return {

                "urgency":
                    rule["urgency"],

                "department":
                    rule["department"],

                "rule_id":
                    rule["rule_id"],

                "reason":
                    rule["condition"],

                "action":
                    rule["action"],

                "escalate":
                    True

            }


    # ==================================================
    # FEVER
    # ==================================================

    fever_present = (

        has_positive_phrase(
            patient_text,
            "fever"
        )

    )


    if fever_present:

        rule = next(
            r for r in rules
            if r["rule_id"] == "FV-001"
        )


        return {

            "urgency":
                rule["urgency"],

            "department":
                rule["department"],

            "rule_id":
                rule["rule_id"],

            "reason":
                rule["condition"],

            "action":
                rule["action"],

            "escalate":
                False

        }


    # ==================================================
    # ABDOMINAL PAIN
    # ==================================================

    abdominal_pain_present = (

        has_positive_phrase(
            patient_text,
            "abdominal pain"
        )

        or

        has_positive_phrase(
            patient_text,
            "stomach pain"
        )

    )


    if abdominal_pain_present:

        rule = next(
            r for r in rules
            if r["rule_id"] == "AB-001"
        )


        return {

            "urgency":
                rule["urgency"],

            "department":
                rule["department"],

            "rule_id":
                rule["rule_id"],

            "reason":
                rule["condition"],

            "action":
                rule["action"],

            "escalate":
                False

        }


    # ==================================================
    # UNKNOWN
    # ==================================================

    rule = next(
        r for r in rules
        if r["rule_id"] == "UN-001"
    )


    return {

        "urgency":
            rule["urgency"],

        "department":
            rule["department"],

        "rule_id":
            rule["rule_id"],

        "reason":
            rule["condition"],

        "action":
            rule["action"],

        "escalate":
            True

    }