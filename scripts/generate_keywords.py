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

# Liste des mots-clés prédéfinis
keywords_list = [
    "Artificial Intelligence", "Machine Learning", "Deep Learning",
    "Natural Language Processing", "Computer Vision",
    "Reinforcement Learning", "Big Data", "Data Science", "Robotics",
    "Ethics", "Governance", "Healthcare", "Finance", "Education", "Autonomous Systems", "Cybersecurity", "IoT", "Edge Computing", "Cloud Computing", "AI Fairness", "Explainability",
    "Neural Networks", "AI Regulation", "Digital Transformation", "AI Applications", "AI Research","Sustainability", "Predictive Analytics", "AI Deployment", "Data Privacy", "Generative AI", "AI Strategy", "Artificial General Intelligence (AGI)", "Federated Learning", "Transfer Learning",
    "Zero-shot Learning", "Few-shot Learning", "Fine-tuning", "Active Learning", "Self-supervised Learning", "Unsupervised Learning", "Graph Neural Networks (GNN)", "Contrastive Learning", "Large Language Models (LLM)", "Transformer Models", "Microsoft Azure AI", "OpenAI", "Mistral", "Anthropic Claude", "Google Bard", "Smartphone", "Telecommunications"
]

# Embedding des mots-clés pour les comparaisons
keyword_embeddings = model.encode(keywords_list, convert_to_tensor=True)

# Seuil de pertinence
THRESHOLD = 0.35  # Réduction du seuil pour capturer plus de mots-clés
MAX_KEYWORDS = 10


# Fonction pour extraire les mots-clés les plus pertinents
def extract_keywords(text):
    if not text or not text.strip():
        return ""  # Retourne vide si le texte est invalide

    # Encodage du texte et calcul de la similarité
    text_embedding = model.encode(text, convert_to_tensor=True)
    cosine_scores = util.cos_sim(text_embedding, keyword_embeddings)[0]

    # Filtrer par seuil et limiter le nombre de mots-clés
    filtered_keywords = [
        keywords_list[i] for i in range(len(keywords_list)) 
        if cosine_scores[i].item() >= THRESHOLD
    ]
    return ";".join(filtered_keywords[:MAX_KEYWORDS])


# Tables et champs concernés
tables = [
    {"name": "articles", "text_field": "content", "keywords_field": "keywords"},
    {"name": "videos", "text_field": "description", "keywords_field": "keywords"},
    {"name": "scientific_articles", "text_field": "abstract", "keywords_field": "keywords"}
]

# Traitement des tables
for table in tables:
    print(f"Traitement de la table {table['name']}...")
    select_query = f"""
    SELECT id, {table['text_field']}, {table['keywords_field']}
    FROM {table['name']}
    """
    cursor.execute(select_query)
    rows = cursor.fetchall()

    print(f"{len(rows)} enregistrements trouvés dans la table {table['name']}.")

    for record_id, text, current_keywords in rows:
        if text:  # Si le champ texte n'est pas vide
            new_keywords = extract_keywords(text)
            if new_keywords:  # Si des mots-clés pertinents sont trouvés
                updated_keywords = new_keywords
                if current_keywords:  # Si des mots-clés existent, les combiner
                    current_keywords_set = set(current_keywords.split(";"))
                    new_keywords_set = set(new_keywords.split(";"))
                    combined_keywords = current_keywords_set.union(new_keywords_set)
                    updated_keywords = ";".join(combined_keywords)

                try:
                    update_query = f"""
                    UPDATE {table['name']}
                    SET {table['keywords_field']} = %s
                    WHERE id = %s
                    """
                    cursor.execute(update_query, (updated_keywords, record_id))
                except mysql.connector.Error as e:
                    print(f"Erreur SQL pour l'ID {record_id} : {e}")

# Valider les changements et fermer la connexion
connection.commit()
cursor.close()
connection.close()

print("Extraction des mots-clés terminée et base de données mise à jour")
