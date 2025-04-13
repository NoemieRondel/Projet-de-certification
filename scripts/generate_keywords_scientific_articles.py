import os
import json
import logging
from datetime import datetime
from sentence_transformers import SentenceTransformer, util

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Chemins des fichiers
JSON_FILE = "arxiv_articles.json"
MONITORING_FILE = "monitoring.json"

# Timer début
start_time = datetime.now()


# Fonction pour enregistrer les métriques dans un fichier centralisé
def save_monitoring_entry(script_name, data):
    if os.path.exists(MONITORING_FILE):
        with open(MONITORING_FILE, "r", encoding="utf-8") as f:
            monitoring = json.load(f)
    else:
        monitoring = {"entries": []}

    timestamp = datetime.now().isoformat()
    entry = {
        "timestamp": timestamp,
        "script": script_name,
        **data
    }
    monitoring["entries"].append(entry)

    with open(MONITORING_FILE, "w", encoding="utf-8") as f:
        json.dump(monitoring, f, indent=4)

# Charger le modèle SentenceTransformer
logging.info("Chargement du modèle SentenceTransformer.")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Liste de mots-clés
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

# Embeddings des mots-clés
logging.info("Encodage des mots-clés.")
keyword_embeddings = model.encode(keyword_list, convert_to_tensor=True)

# Paramètres
MAX_KEYWORDS = 10
SIMILARITY_THRESHOLD = 0.8


# Fonction d'extraction
def extract_keywords(text, embeddings, candidates, threshold):
    if not text or not text.strip():
        return []
    text_embedding = model.encode(text, convert_to_tensor=True)
    cosine_scores = util.cos_sim(text_embedding, embeddings)[0]

    # Crée une liste de tuples (score, index) pour faciliter le tri
    scored_candidates = [(cosine_scores[i], candidates[i]) for i in range(len(candidates))]

    # Filtre les termes dont le score est supérieur au seuil
    filtered_scored_candidates = [item for item in scored_candidates if item[0] > threshold]

    # Trie les termes filtrés par score de similarité décroissant
    sorted_filtered_candidates = sorted(filtered_scored_candidates, key=lambda item: item[0], reverse=True)

    # Retourne les MAX_KEYWORDS premiers termes (si la liste n'est pas vide)
    return [term for score, term in sorted_filtered_candidates[:MAX_KEYWORDS]]


# Chargement des articles
logging.info(f"Chargement des articles depuis {JSON_FILE}.")
if os.path.exists(JSON_FILE):
    with open(JSON_FILE, "r", encoding="utf-8") as json_file:
        articles = json.load(json_file)
else:
    logging.error(f"Fichier {JSON_FILE} introuvable.")
    articles = []

# Traitement
logging.info("Extraction des mots-clés pour chaque article.")
for article in articles:
    abstract = article.get("abstract", "")
    new_keywords = extract_keywords(abstract, keyword_embeddings, keyword_list, SIMILARITY_THRESHOLD)
    article["keywords"] = ";".join(new_keywords)

# Sauvegarde
logging.info(f"Sauvegarde dans {JSON_FILE}.")
with open(JSON_FILE, "w", encoding="utf-8") as json_file:
    json.dump(articles, json_file, ensure_ascii=False, indent=4)

# Monitoring
end_time = datetime.now()
duration = (end_time - start_time).total_seconds()
total_articles = len(articles)
empty_abstracts = sum(1 for a in articles if not (a.get("abstract", "") or"").strip())
average_keywords = sum(len(a.get("keywords", "").split(";")) for a in articles) / total_articles if total_articles else 0

monitoring_data = {
    "duration_seconds": round(duration, 2),
    "scientific_articles_count": total_articles,
    "empty_abstracts_count": empty_abstracts,
    "average_keywords_per_scientific_article": round(average_keywords, 2)
}

save_monitoring_entry("extract_scientific_keywords", monitoring_data)
logging.info("Monitoring mis à jour dans monitoring.json.")
