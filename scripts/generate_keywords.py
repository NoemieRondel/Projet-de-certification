import os
import json
import logging
from datetime import datetime
from sentence_transformers import SentenceTransformer, util

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Chemins des fichiers
JSON_FILE = "articles.json"
MONITORING_FILE = "monitoring_articles_metrics.json"

# Début du timer
start_time = datetime.now()


# Fonction pour enregistrer les métriques dans un fichier centralisé
def save_monitoring_entry(script_name, data):
    if os.path.exists("monitoring.json"):
        with open("monitoring.json", "r", encoding="utf-8") as f:
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

    with open("monitoring.json", "w", encoding="utf-8") as f:
        json.dump(monitoring, f, indent=4)


# Chargement du modèle
logging.info("Chargement du modèle pré-entraîné.")
model = SentenceTransformer('all-MiniLM-L6-v2')

# Liste fusionnée des mots-clés (techniques et généralistes)
keyword_list = [
    # Généralistes
    "Artificial Intelligence", "Machine Learning", "Deep Learning",
    "Natural Language Processing", "Computer Vision",
    "Reinforcement Learning", "Big Data", "Data Science", "Robotics",
    "Ethics", "Governance", "Healthcare", "Finance", "Education",
    "Autonomous Systems", "Cybersecurity", "IoT", "Edge Computing",
    "Cloud Computing", "AI Fairness", "Explainability",
    "Neural Networks", "AI Regulation", "Digital Transformation",
    "AI Applications", "AI Research", "Sustainability",
    "Predictive Analytics", "AI Deployment", "Data Privacy", "Generative AI",
    "AI Strategy", "Federated Learning", "Transfer Learning",
    "Zero-shot Learning", "Few-shot Learning", "Fine-tuning"
    "Active Learning", "Self-supervised Learning", "Unsupervised Learning",
    "Graph Neural Networks (GNN)", "Contrastive Learning",
    "Large Language Models (LLM)", "Transformer Models", "Microsoft Azure AI",
    "OpenAI", "Mistral", "Anthropic Claude", "Google Bard", "Smartphone",
    "Telecommunications",
    # Techniques
    "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "Hugging Face",
    "Transformers", "FastAI", "NLTK", "spaCy", "ONNX", "OpenCV",
    "GPT", "BERT", "RoBERTa", "T5", "Llama", "XLNet", "DistilBERT", "ALBERT",
    "OPT", "ChatGPT", "Codex", "Retrieval-Augmented Generation (RAG)",
    "Prompt Engineering", "Knowledge Distillation",
    "Reinforcement Learning from Human Feedback (RLHF)",
    "Stable Diffusion", "DALL-E", "GANs", "VAEs", "NeRF", "DreamBooth",
    "ControlNet", "Neural Architecture Search (NAS)", "Meta-learning",
    "Model Pruning", "Data Augmentation", "Curriculum Learning",
    "Synthetic Data Generation", "Hybrid AI Systems",
    "Automated Machine Learning (AutoML)", "YOLO", "ViT", "EfficientNet",
    "ResNet", "Faster R-CNN", "Mask R-CNN", "DETR", "Swin Transformer",
    "OpenPose", "CLIP", "SAM (Segment Anything Model)", "Whisper",
    "Speech-to-Text", "Text-to-Speech", "Wav2Vec", "Tacotron",
    "DeepSpeech", "WaveNet", "Voice Cloning", "AudioLM", "Microsoft Azure",
    "AWS AI", "Google Cloud AI", "IBM Watson", "Oracle AI", "H2O.ai",
    "DataRobot", "Azure OpenAI Service", "Vertex AI", "Anthropic AI",
    "OpenAI Codex", "Copilot", "GitHub Copilot", "Copilot Studio",
    "Neo4j", "Snowflake", "BigQuery", "Elasticsearch", "MongoDB Atlas",
    "Pandas", "Dask", "Knowledge Graphs", "Recommendation Systems",
    "Intelligent Automation", "RPA (Robotic Process Automation)",
    "ISO 30465", "IEEE 7000", "GDPR Compliance", "Explainable AI (XAI)",
    "Fairness in AI", "Docker", "Kubernetes", "MLflow", "TensorBoard",
    "Weights & Biases", "Airflow", "DVC", "Rasa", "Dialogflow", "Botpress",
    "Amazon Lex", "Microsoft Bot Framework", "LangChain", "Haystack",
    "SentenceTransformers", "Edge AI", "TinyML", "Quantum AI", "AI Ethics",
    "Transferability Testing"
]


# Encodage des mots-clés
logging.info("Encodage des mots-clés pour la comparaison.")
keyword_embeddings = model.encode(keyword_list, convert_to_tensor=True)

# Paramètres de filtrage
MAX_KEYWORDS = 15
SIMILARITY_THRESHOLD = 0.2


# Fonction d'extraction
def extract_keywords(text, embeddings, candidates, threshold):
    if not text or not text.strip():
        return []

    logging.info("Encodage du texte et calcul des similarités.")
    text_embedding = model.encode(text, convert_to_tensor=True)
    cosine_scores = util.cos_sim(text_embedding, embeddings)[0]

    filtered_terms = [
        candidates[i] for i in range(len(cosine_scores)) if cosine_scores[i] > threshold
    ]

    sorted_terms = [candidates[i] for i in cosine_scores.argsort(descending=True)]
    return sorted_terms[:MAX_KEYWORDS]

# Chargement du fichier JSON
logging.info(f"Chargement des données depuis le fichier {JSON_FILE}.")
if os.path.exists(JSON_FILE):
    with open(JSON_FILE, "r", encoding="utf-8") as file:
        articles = json.load(file)
else:
    logging.error(f"Le fichier {JSON_FILE} est introuvable.")
    articles = []

# Enrichissement des articles
logging.info("Début de l’enrichissement des mots-clés.")
for article in articles:
    full_content = article.get("full_content", "")
    current_keywords = article.get("keywords", "")

    if not current_keywords:
        logging.info(f"Traitement de l'article : {article.get('title', 'Sans titre')}")
        new_keywords = extract_keywords(full_content, keyword_embeddings, keyword_list, SIMILARITY_THRESHOLD)
        article["keywords"] = ";".join(sorted(set(new_keywords)))

# Sauvegarde des articles enrichis
logging.info(f"Sauvegarde des articles enrichis dans {JSON_FILE}.")
with open(JSON_FILE, "w", encoding="utf-8") as file:
    json.dump(articles, file, indent=4, ensure_ascii=False)

# Calcul des métriques de monitoring
end_time = datetime.now()
duration = (end_time - start_time).total_seconds()
total_articles = len(articles)
empty_contents = sum(1 for a in articles if not (a.get("full_content") or "").strip())
average_keywords = sum(len(a.get("keywords", "").split(";")) for a in articles) / total_articles if total_articles else 0

monitoring_data = {
    "timestamp": datetime.now().isoformat(),
    "duration_seconds": round(duration, 2),
    "articles_count": total_articles,
    "empty_full_content_count": empty_contents,
    "average_keywords_per_article": round(average_keywords, 2)
}

save_monitoring_entry("extract_keywords", monitoring_data)
logging.info("Monitoring mis à jour dans monitoring.json.")