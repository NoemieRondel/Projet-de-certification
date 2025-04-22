import pytest
import sys
import os
# Obtient le chemin absolu du répertoire racine du projet
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Ajoute le répertoire racine à sys.path s'il n'y est pas déjà
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from sentence_transformers import SentenceTransformer, util
from scripts.generate_keywords_scientific_articles import extract_keywords, keyword_list, MAX_KEYWORDS

# Préparation du modèle et des embeddings (une seule fois)
model = SentenceTransformer('all-MiniLM-L6-v2')
keyword_embeddings = model.encode(keyword_list, convert_to_tensor=True)

SIMILARITY_THRESHOLD = 0.7


def test_extract_keywords_empty_text():
    result = extract_keywords("", keyword_embeddings, keyword_list, SIMILARITY_THRESHOLD)
    assert result == []


def test_extract_keywords_none_text():
    result = extract_keywords(None, keyword_embeddings, keyword_list, SIMILARITY_THRESHOLD)
    assert result == []


def test_extract_keywords_irrelevant_text():
    text = "ravioli marshmallow and jellybeans dancing on Saturn"
    result = extract_keywords(text, keyword_embeddings, keyword_list, SIMILARITY_THRESHOLD)
    assert isinstance(result, list)
    assert len(result) <= MAX_KEYWORDS
    # Très probablement aucun mot-clé pertinent
    assert len(result) == 0


def test_extract_keywords_meaningful_text():
    text = "This paper explores Transformer architectures and Transfer Learning in neural networks."
    threshold_for_test = 0.5
    result = extract_keywords(text, keyword_embeddings, keyword_list, threshold_for_test)
    assert isinstance(result, list)
    assert len(result) <= MAX_KEYWORDS
    assert any("Transformer" in kw or "Transfer Learning" in kw for kw in result)


def test_extract_keywords_does_not_return_duplicates():
    text = "AI AI AI AI AI AI AI AI AI AI"
    result = extract_keywords(text, keyword_embeddings, keyword_list, SIMILARITY_THRESHOLD)
    assert len(result) == len(set(result))  # pas de doublons


def test_extract_keywords_with_high_threshold():
    text = "This study discusses BERT and large language models for NLP tasks."
    high_threshold = 0.95  # Très strict
    result = extract_keywords(text, keyword_embeddings, keyword_list, high_threshold)
    # Résultat potentiellement vide si aucun mot-clé ne dépasse 0.95
    assert isinstance(result, list)
    assert all(isinstance(kw, str) for kw in result)
    assert len(result) <= MAX_KEYWORDS


def test_extract_keywords_with_low_threshold():
    text = "This study discusses BERT and large language models for NLP tasks."
    low_threshold = 0.3  # Très permissif
    result = extract_keywords(text, keyword_embeddings, keyword_list, low_threshold)
    # Il pourrait renvoyer beaucoup plus de mots-clés, mais MAX_KEYWORDS limite à 10
    assert isinstance(result, list)
    assert len(result) == MAX_KEYWORDS
