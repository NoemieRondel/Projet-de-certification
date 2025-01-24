import os
import json
import logging
from sentence_transformers import SentenceTransformer, util

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Charger le modèle pré-entraîné pour la similarité sémantique
logging.info("Chargement du modèle pré-entraîné pour la similarité sémantique.")
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


# Embedding des mots-clés pour comparaison
logging.info("Encodage des mots-clés pour la comparaison.")
keyword_embeddings = model.encode(keyword_list, convert_to_tensor=True)

# Limite des mots-clés et seuil de similarité
MAX_KEYWORDS = 15
SIMILARITY_THRESHOLD = 0.2


# Fonction pour extraire les mots-clés les plus pertinents
def extract_keywords(text, embeddings, candidates, threshold):
    if not text or not text.strip():
        return ""

    # Encodage du texte et calcul de la similarité
    logging.info("Encodage du texte et calcul de la similarité.")
    text_embedding = model.encode(text, convert_to_tensor=True)
    cosine_scores = util.cos_sim(text_embedding, embeddings)[0]

    # Filtrer les termes avec un seuil de similarité
    filtered_terms = [
        candidates[i] for i in range(len(cosine_scores)) if cosine_scores[i] > threshold
    ]

    # Trier les termes par pertinence
    sorted_terms = [candidates[i] for i in cosine_scores.argsort(descending=True)]
    return sorted_terms[:MAX_KEYWORDS]


# Chemin du fichier JSON
json_file_path = "articles.json"

# Charger les données depuis le fichier JSON
if os.path.exists(json_file_path):
    logging.info(f"Chargement des données depuis {json_file_path}.")
    with open(json_file_path, "r", encoding="utf-8") as file:
        articles = json.load(file)
else:
    logging.error(f"Le fichier {json_file_path} est introuvable.")
    articles = []

# Enrichissement des mots-clés pour chaque article
logging.info("Enrichissement des mots-clés pour chaque article.")
for article in articles:
    full_content = article.get("full_content", "")
    current_keywords = article.get("keywords", "")

    # Vérifier si les mots-clés doivent être générés (champ vide ou inexistant)
    if not current_keywords:
        logging.info(f"Traitement de l'article : {article.get('title', 'Sans titre')}")

        # Extraire les mots-clés à partir du contenu complet
        new_keywords = extract_keywords(full_content, keyword_embeddings, keyword_list, SIMILARITY_THRESHOLD)

        # Ajouter les mots-clés au JSON
        article["keywords"] = ";".join(sorted(set(new_keywords)))

# Sauvegarder les données mises à jour dans le fichier JSON
logging.info(f"Sauvegarde des données mises à jour dans {json_file_path}.")
with open(json_file_path, "w", encoding="utf-8") as file:
    json.dump(articles, file, indent=4, ensure_ascii=False)

logging.info("Enrichissement des mots-clés terminé. Fichier JSON mis à jour.")
