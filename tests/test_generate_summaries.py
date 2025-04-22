import pytest
import sys
import os
# Obtient le chemin absolu du répertoire racine du projet
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Ajoute le répertoire racine à sys.path s'il n'y est pas déjà
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from scripts.generate_summaries import generate_summary

# Chargement du modèle (comme dans ton script principal)
MODEL_NAME = "facebook/bart-large-cnn"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)


def test_generate_summary_minimal_text():
    text = (
        "Artificial intelligence (AI) is a field of computer science focused on creating systems capable of performing tasks "
        "that typically require human intelligence. These tasks include learning, reasoning, problem-solving, perception, and language understanding."
    )
    summary = generate_summary(text, max_length=100, min_length=20)
    assert isinstance(summary, str)
    assert len(summary.split()) >= 20
    assert len(summary) > 0


def test_generate_summary_empty_text():
    summary = generate_summary("", max_length=100, min_length=20)
    assert summary == "" or isinstance(summary, str)


def test_generate_summary_long_text():
    # Génère un long texte répétitif
    text = "Machine learning is great. " * 100
    summary = generate_summary(text, max_length=150, min_length=50)
    assert isinstance(summary, str)
    assert len(summary.split()) >= 30
