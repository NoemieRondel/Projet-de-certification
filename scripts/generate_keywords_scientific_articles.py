import os
import json
import logging
from datetime import datetime
from sentence_transformers import SentenceTransformer, util

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Chemin vers le fichier JSON
JSON_FILE = "arxiv_articles.json"

# Charger le modèle pré-entraîné
logging.info("Chargement du modèle pré-entraîné.")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Liste des mots-clés prédéfinis
keyword_list = [
    "Artificial Intelligence", "Machine Learning", "Deep Learning",
    "Natural Language Processing", "Reinforcement Learning",
    "Computer Vision", "Neural Networks", "Transformers",
    "Convolutional Neural Networks (CNN)", "Few-shot Learning",
    "Generative Adversarial Networks (GAN)", "Attention Mechanism", "BERT",
    "GPT", "T5", "Self-supervised Learning", "Transfer Learning",
    "Federated Learning", "Reinforcement Learning from Human Feedback (RLHF)",
    "Knowledge Graphs", "Graph Neural Networks (GNN)", "Quantum Computing",
    "AI Ethics", "Bias in AI", "Explainable AI (XAI)", "AI Fairness",
    "Data Privacy", "Data Security", "Synthetic Data",
    "Benchmarking AI Models", "AI for Healthcare",
    "AI for Autonomous Systems", "Robotics", "Causal Inference",
    "Statistical Learning", "Bayesian Networks",
    "Deep Reinforcement Learning", "Meta-Learning", "Model Compression",
    "Pruning in Neural Networks", "Knowledge Distillation",
    "Model Explainability", "Transferability Testing", "Zero-shot Learning",
    "Active Learning", "Semi-supervised Learning", "AI Governance",
    "AI Regulation", "AI for Social Good", "Ethical AI",
    "Multi-agent Systems", "AI for Finance", "AI for Education",
    "Neural Architecture Search (NAS)", "Adversarial Attacks",
    "AI in Robotics", "Automated Machine Learning (AutoML)",
    "AI and Cloud Computing", "Edge AI", "Explainability in AI",
    "AI in Healthcare", "AI in Manufacturing", "AI Model Interpretability",
    "AI Safety", "Multi-modal Learning",  "Speech-to-Text", "Text-to-Speech",
    "Natural Language Understanding (NLU)", "Recurrent Neural Networks (RNN)",
    "AI for Cybersecurity", "AI Deployment"
]

# Encoder les mots-clés en embeddings
logging.info("Encodage des mots-clés pour la comparaison.")
keyword_embeddings = model.encode(keyword_list, convert_to_tensor=True)

# Limite des mots-clés extraits et seuil de similarité
MAX_KEYWORDS = 10
SIMILARITY_THRESHOLD = 0.8


def extract_keywords(text, embeddings, candidates, threshold):
    """
    Extrait les mots-clés les plus pertinents d'un texte donné.
    """
    if not text or not text.strip():
        return []

    # Encoder le texte et calculer les similarités cosinus
    logging.info("Encodage du texte et calcul des similarités.")
    text_embedding = model.encode(text, convert_to_tensor=True)
    cosine_scores = util.cos_sim(text_embedding, embeddings)[0]

    # Filtrer les mots-clés selon le seuil
    filtered_terms = [
        candidates[i] for i in range(len(cosine_scores)) if cosine_scores[i] > threshold
    ]

    # Trier les mots-clés par pertinence
    sorted_terms = [candidates[i] for i in cosine_scores.argsort(descending=True)]

    return sorted_terms[:MAX_KEYWORDS]


# Charger le fichier JSON
logging.info(f"Chargement des données depuis le fichier {JSON_FILE}.")
if os.path.exists(JSON_FILE):
    with open(JSON_FILE, "r", encoding="utf-8") as json_file:
        articles = json.load(json_file)
else:
    logging.error(f"Le fichier {JSON_FILE} n'existe pas.")
    articles = []

# Ajouter les mots-clés à chaque article
logging.info(f"Enrichissement des mots-clés pour chaque article dans {JSON_FILE}.")
for article in articles:
    abstract = article.get("abstract", "")

    # Extraire les mots-clés s'il y a un résumé
    new_keywords = extract_keywords(abstract, keyword_embeddings, keyword_list, SIMILARITY_THRESHOLD)

    # Ajouter les mots-clés au dictionnaire de l'article
    article["keywords"] = ";".join(new_keywords)

# Sauvegarder les articles enrichis dans le fichier JSON
logging.info(f"Sauvegarde des articles enrichis dans {JSON_FILE}.")
with open(JSON_FILE, "w", encoding="utf-8") as json_file:
    json.dump(articles, json_file, ensure_ascii=False, indent=4)

logging.info(f"Enrichissement des mots-clés terminé. Le fichier '{JSON_FILE}' a été mis à jour.")
