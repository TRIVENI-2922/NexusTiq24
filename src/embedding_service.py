import os
import numpy as np
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
# CREATE EMBEDDING
# ==================================================

def create_embedding(text):

    if not text or not text.strip():
        raise ValueError(
            "Text cannot be empty"
        )

    client = get_client()


    response = client.models.embed_content(

        model="gemini-embedding-001",

        contents=text

    )


    embedding = response.embeddings[0].values


    return np.array(
        embedding,
        dtype=np.float32
    )


# ==================================================
# COSINE SIMILARITY
# ==================================================

def cosine_similarity(
    vector_a,
    vector_b
):

    vector_a = np.asarray(
        vector_a,
        dtype=np.float32
    )

    vector_b = np.asarray(
        vector_b,
        dtype=np.float32
    )


    norm_a = np.linalg.norm(
        vector_a
    )

    norm_b = np.linalg.norm(
        vector_b
    )


    if norm_a == 0 or norm_b == 0:

        return 0.0


    return float(
        np.dot(
            vector_a,
            vector_b
        )
        /
        (
            norm_a * norm_b
        )
    )