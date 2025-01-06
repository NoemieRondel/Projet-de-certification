import os
import mysql.connector
from sentence_transformers import SentenceTransformer, util
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration de la connexion à la base de données
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Connexion à la base de données
connection = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)
cursor = connection.cursor()

# Charger le modèle pré-entraîné pour la similarité sémantique
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
    "AI Strategy", "Artificial General Intelligence (AGI)",
    "Federated Learning", "Transfer Learning", "Zero-shot Learning",
    "Few-shot Learning", "Fine-tuning", "Active Learning",
    "Self-supervised Learning", "Unsupervised Learning",
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
keyword_embeddings = model.encode(keyword_list, convert_to_tensor=True)

# Limite des mots-clés et seuil de similarité
MAX_KEYWORDS = 15
SIMILARITY_THRESHOLD = 0.2


# Fonction pour extraire les mots-clés les plus pertinents
def extract_keywords(text, embeddings, candidates, threshold):
    if not text or not text.strip():
        return ""

    # Encodage du texte et calcul de la similarité
    text_embedding = model.encode(text, convert_to_tensor=True)
    cosine_scores = util.cos_sim(text_embedding, embeddings)[0]

    # Filtrer les termes avec un seuil de similarité
    filtered_terms = [
        candidates[i] for i in range(len(cosine_scores)) if cosine_scores[i] > threshold
    ]

    # Trier les termes par pertinence
    sorted_terms = [candidates[i] for i in cosine_scores.argsort(descending=True)]
    return sorted_terms[:MAX_KEYWORDS]


# Récupérer les articles dans la base de données
select_query = """
    SELECT ac.article_id, ac.content, a.keywords
    FROM article_content ac
    JOIN articles a ON ac.article_id = a.id
    WHERE ac.content IS NOT NULL
"""
cursor.execute(select_query)
rows = cursor.fetchall()

# Enrichissement des mots-clés pour chaque article
for article_id, content, current_keywords in rows:
    print(f"Traitement de l'article ID {article_id}...")

    # Extraire les nouveaux mots-clés
    new_keywords = extract_keywords(content, keyword_embeddings, keyword_list, SIMILARITY_THRESHOLD)

    # Fusionner avec les mots-clés existants
    if current_keywords:
        existing_keywords = set(current_keywords.split(";"))
    else:
        existing_keywords = set()

    # Ajouter les nouveaux mots-clés sans duplication
    updated_keywords_set = existing_keywords.union(set(new_keywords))
    updated_keywords = ";".join(sorted(updated_keywords_set))

    # Mise à jour dans la base de données
    try:
        update_query = "UPDATE articles SET keywords = %s WHERE id = %s"
        cursor.execute(update_query, (updated_keywords, article_id))
    except mysql.connector.Error as e:
        print(f"Erreur SQL pour l'article ID {article_id}: {e}")

# Valider les changements et fermer la connexion
connection.commit()
cursor.close()
connection.close()

print("Enrichissement des mots-clés terminé. Base de données mise à jour.")
