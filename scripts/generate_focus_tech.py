import os
import re
import mysql.connector
from dotenv import load_dotenv
from transformers import pipeline

# Charger les variables d'environnement
load_dotenv()

# Connexion à la base de données
db_config = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

# Liste enrichie des mots-clés
TECH_KEYWORDS = [
    # Frameworks et bibliothèques
    "TensorFlow", "PyTorch", "Keras", "Scikit-learn", "Hugging Face",
    "Transformers", "FastAI", "NLTK", "spaCy", "ONNX", "OpenCV",

    # Modèles et technologies de traitement du langage naturel
    "GPT", "BERT", "RoBERTa", "T5", "Llama", "XLNet", "DistilBERT", "ALBERT",
    "OPT", "Mistral", "Claude", "Anthropic", "ChatGPT", "Codex",
    "Retrieval-Augmented Generation (RAG)", "Zero-shot Learning",
    "Few-shot Learning", "Prompt Engineering", "Fine-tuning",
    "Knowledge Distillation", "Self-supervised Learning",
    "Reinforcement Learning from Human Feedback (RLHF)",

    # Modèles génératifs
    "Stable Diffusion", "DALL-E", "GANs", "VAEs", "NeRF", "DreamBooth",
    "ControlNet",

    # Concepts d'IA
    "Neural Architecture Search (NAS)", "Federated Learning",
    "Model Pruning", "Data Augmentation", "Transfer Learning", "Meta-learning",
    "Active Learning", "Contrastive Learning", "Curriculum Learning",
    "Synthetic Data Generation", "Hybrid AI Systems",
    "Automated Machine Learning (AutoML)",

    # Vision par ordinateur
    "YOLO", "ViT", "EfficientNet", "ResNet", "Faster R-CNN", "Mask R-CNN",
    "DETR", "Swin Transformer", "OpenPose", "CLIP",
    "SAM (Segment Anything Model)",

    # Technologies de reconnaissance vocale et synthèse
    "Whisper", "Speech-to-Text", "Text-to-Speech", "Wav2Vec", "Tacotron",
    "DeepSpeech", "WaveNet", "Voice Cloning", "AudioLM",

    # Plateformes cloud et outils collaboratifs
    "Microsoft Azure", "AWS AI", "Google Cloud AI", "IBM Watson", "Oracle AI",
    "H2O.ai", "DataRobot", "Azure OpenAI Service", "Vertex AI",
    "Anthropic AI", "OpenAI Codex", "Copilot", "GitHub Copilot",
    "Copilot Studio",

    # Bases de données et outils Big Data
    "Neo4j", "Snowflake", "BigQuery", "Elasticsearch", "MongoDB Atlas",
    "Pandas", "Dask",

    # Applications spécifiques
    "Knowledge Graphs", "Graph Neural Networks (GNN)",
    "Recommendation Systems", "Predictive Analytics",
    "Intelligent Automation", "RPA (Robotic Process Automation)",

    # Normes et protocoles
    "ISO 30465", "IEEE 7000", "GDPR Compliance", "Explainable AI (XAI)",
    "Fairness in AI",

    # Outils et intégrations DevOps
    "Docker", "Kubernetes", "MLflow", "TensorBoard", "Weights & Biases",
    "Airflow", "DVC",

    # Chatbots et assistants
    "Rasa", "Dialogflow", "Botpress", "Amazon Lex", "Microsoft Bot Framework",

    # Open Source
    "LangChain", "Haystack", "SentenceTransformers",

    # Divers
    "Edge AI", "TinyML", "Quantum AI", "AI Ethics", "Explainability",
    "Synthetic Data", "Transferability Testing"
]


# Modèle de NER
def load_ner_model():
    print("Chargement du modèle...")
    ner_pipeline = pipeline("ner", model="dslim/bert-base-NER", grouped_entities=True)
    print("Modèle chargé avec succès.")
    return ner_pipeline


# Extraction des technologies via liste et heuristiques
def extract_focus_tech(content, ner_pipeline):
    found_techs = set()

    # Vérifier avec TECH_KEYWORDS
    for tech in TECH_KEYWORDS:
        if tech.lower() in content.lower():
            found_techs.add(tech)

    # Vérifier avec le modèle NER
    ner_results = ner_pipeline(content)
    for entity in ner_results:
        word = entity["word"]
        # Filtrage pour éviter les noms de personnes/villes
        if entity["entity_group"] == "ORG" or word in TECH_KEYWORDS:
            found_techs.add(word)

    # Supprimer les doublons
    return "; ".join(sorted(found_techs))


# Connexion à la base de données
def connect_to_db():
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        print("Connexion réussie à la base de données.")
        return connection
    except mysql.connector.Error as err:
        print(f"Erreur de connexion : {err}")
        return None


# Mise à jour des articles
def update_articles():
    ner_pipeline = load_ner_model()
    connection = connect_to_db()

    if not connection:
        return

    try:
        cursor = connection.cursor(dictionary=True)

        # Récupérer les articles sans focus_tech
        cursor.execute("""
            SELECT ac.article_id, ac.content
            FROM article_content ac
            LEFT JOIN articles a ON ac.article_id = a.id
            WHERE a.focus_tech IS NULL OR a.focus_tech = '';
        """)
        articles = cursor.fetchall()
        print(f"Nombre d'articles à traiter : {len(articles)}")

        for article in articles:
            content = article["content"]
            article_id = article["article_id"]

            # Extraire focus_tech
            focus_tech = extract_focus_tech(content, ner_pipeline)

            if focus_tech:
                # Mettre à jour l'article
                cursor.execute("""
                    UPDATE articles
                    SET focus_tech = %s
                    WHERE id = %s;
                """, (focus_tech, article_id))
                print(f"Article {article_id} mis à jour avec : {focus_tech}")
            else:
                print(f"Aucun focus_tech trouvé pour l'article {article_id}.")

        connection.commit()
        print("Mises à jour validées.")

    except Exception as e:
        print(f"Erreur lors du traitement : {e}")

    finally:
        if connection:
            connection.close()
            print("Connexion à la base de données fermée.")


# Exécution principale
if __name__ == "__main__":
    update_articles()
