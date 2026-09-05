import json
from pathlib import Path

import numpy as np

from src.embedding_service import (
    create_embedding,
    cosine_similarity
)


# ==================================================
# PROJECT PATHS
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

RULES_PATH = BASE_DIR / "data" / "triage_rules.json"

CACHE_PATH = BASE_DIR / "data" / "rule_embeddings.json"


# ==================================================
# LOAD TRIAGE RULES
# ==================================================

def load_rules():

    with open(
        RULES_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


# ==================================================
# CONVERT RULE INTO SEARCHABLE TEXT
# ==================================================

def rule_to_text(rule):

    criteria = ", ".join(
        rule.get("criteria", [])
    )

    return (
        f"Category: {rule.get('category', '')}. "
        f"Condition: {rule.get('condition', '')}. "
        f"Criteria: {criteria}. "
        f"Urgency: {rule.get('urgency', '')}. "
        f"Department: {rule.get('department', '')}. "
        f"Action: {rule.get('action', '')}."
    )


# ==================================================
# CREATE RULE EMBEDDINGS
# ==================================================

def create_rule_embeddings():

    rules = load_rules()

    cached_rules = []

    for rule in rules:

        rule_text = rule_to_text(rule)

        print(
            f"Creating embedding for {rule['rule_id']}..."
        )

        embedding = create_embedding(
            rule_text
        )

        cached_rules.append({
            "rule_id": rule["rule_id"],
            "text": rule_text,
            "embedding": embedding.tolist(),
            "rule": rule
        })

    with open(
        CACHE_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            cached_rules,
            file,
            indent=2
        )

    print(
        "Rule embeddings cached successfully."
    )

    return cached_rules


# ==================================================
# LOAD CACHED EMBEDDINGS
# ==================================================

def load_cached_embeddings():

    if not CACHE_PATH.exists():

        return create_rule_embeddings()


    with open(
        CACHE_PATH,
        "r",
        encoding="utf-8"
    ) as file:

        cached_rules = json.load(file)


    for item in cached_rules:

        item["embedding"] = np.array(
            item["embedding"],
            dtype=np.float32
        )


    return cached_rules


# ==================================================
# RETRIEVE MOST SIMILAR RULES
# ==================================================

def retrieve_rules(
    patient_text,
    top_k=3
):

    if not patient_text:

        return []


    # ----------------------------------------------
    # EMBED PATIENT QUERY
    # ----------------------------------------------

    patient_embedding = create_embedding(
        patient_text
    )


    # ----------------------------------------------
    # LOAD LOCAL RULE EMBEDDINGS
    # ----------------------------------------------

    embedded_rules = (
        load_cached_embeddings()
    )


    results = []


    # ----------------------------------------------
    # CALCULATE SIMILARITY
    # ----------------------------------------------

    for item in embedded_rules:

        similarity = cosine_similarity(
            patient_embedding,
            item["embedding"]
        )


        results.append({

            "rule_id":
                item["rule_id"],

            "similarity":
                float(similarity),

            "rule":
                item["rule"],

            "text":
                item["text"]

        })


    # ----------------------------------------------
    # SORT BY SIMILARITY
    # ----------------------------------------------

    results.sort(
        key=lambda item:
            item["similarity"],
        reverse=True
    )


    # ----------------------------------------------
    # RETURN TOP K
    # ----------------------------------------------

    return results[:top_k]