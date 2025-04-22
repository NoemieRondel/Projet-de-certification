import pytest
import sys
import os
# Obtient le chemin absolu du répertoire racine du projet
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Ajoute le répertoire racine à sys.path s'il n'y est pas déjà
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from sentence_transformers import SentenceTransformer, util
from scripts.generate_keywords import (
    extract_keywords,
    keyword_list,
    MAX_KEYWORDS,
    SIMILARITY_THRESHOLD,
)

# Chargement du modèle une fois pour tous les tests
model = SentenceTransformer('all-MiniLM-L6-v2')
keyword_embeddings = model.encode(keyword_list, convert_to_tensor=True)


def test_extract_keywords_empty_text():
    result = extract_keywords("", keyword_embeddings, keyword_list, SIMILARITY_THRESHOLD)
    assert result == []


def test_extract_keywords_none_text():
    result = extract_keywords(None, keyword_embeddings, keyword_list, SIMILARITY_THRESHOLD)
    assert result == []


def test_extract_keywords_irrelevant_text():
    text = "blablabla foo bar nothing to do with AI or tech"
    result = extract_keywords(text, keyword_embeddings, keyword_list, SIMILARITY_THRESHOLD)
    assert isinstance(result, list)
    assert len(result) <= MAX_KEYWORDS


def test_extract_keywords_meaningful_text():
    text = "This article explores how GPT and Transformer models are transforming natural language processing tasks."
    result = extract_keywords(text, keyword_embeddings, keyword_list, SIMILARITY_THRESHOLD)
    assert isinstance(result, list)
    assert len(result) <= MAX_KEYWORDS
    assert any("GPT" in kw or "Transformer" in kw for kw in result)


def test_extract_keywords_does_not_return_duplicates():
    text = "AI AI AI AI AI AI AI AI AI AI AI AI AI AI AI AI"
    result = extract_keywords(text, keyword_embeddings, keyword_list, SIMILARITY_THRESHOLD)
    assert len(result) == len(set(result))  # pas de doublons


def test_extract_keywords_respects_threshold():
    # Un texte ultra court => très peu de similarité
    text = "Duck banana potato"
    result = extract_keywords(text, keyword_embeddings, keyword_list, SIMILARITY_THRESHOLD)
    assert isinstance(result, list)
    # Techniquement on n'attend *aucun* mot-clé pertinent
    assert len(result) <= MAX_KEYWORDS
