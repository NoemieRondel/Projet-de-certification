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

# Charger le modèle préentraîné pour la similarité sémantique
model = SentenceTransformer('all-MiniLM-L6-v2')

# Liste des mots-clés prédéfinis
keywords_list = [
    "Artificial Intelligence", "Machine Learning", "Deep Learning", "Natural Language Processing",
    "Computer Vision", "Reinforcement Learning", "Big Data", "Data Science", "Robotics",
    "Ethics", "Governance", "Healthcare", "Finance", "Education", "Autonomous Systems",
    "Cybersecurity", "IoT", "Edge Computing", "Cloud Computing", "AI Fairness",
    "Explainability", "Neural Networks", "AI Regulation", "Digital Transformation",
    "AI Applications", "AI Research", "Sustainability", "Predictive Analytics",
    "AI Deployment", "Data Privacy", "Generative AI", "AI Strategy"
]

# Embedding des mots-clés pour les comparaisons
keyword_embeddings = model.encode(keywords_list, convert_to_tensor=True)

# Seuil de pertinence
THRESHOLD = 0.7
MAX_KEYWORDS = 10


# Fonction pour extraire les mots-clés les plus pertinents en fonction du texte
def extract_keywords(text):
    # Vérification de texte vide
    if not text.strip():
        return ""

    # Encodage du texte
    text_embedding = model.encode(text, convert_to_tensor=True)

    # Calcul de la similarité entre le texte et les mots-clés
    cosine_scores = util.cos_sim(text_embedding, keyword_embeddings)[0]

    # Association des scores aux mots-clés
    scored_keywords = [
        (keywords_list[i], cosine_scores[i].item())
        for i in range(len(keywords_list))
    ]

    # Filtrer par seuil et trier par score décroissant
    filtered_keywords = [kw for kw, score in scored_keywords if score >= THRESHOLD]

    # Limiter à MAX_KEYWORDS
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
    SELECT id, {table['text_field']}
    FROM {table['name']}
    """
    cursor.execute(select_query)
    rows = cursor.fetchall()

    for row in rows:
        record_id, text = row
        if text:  # Si le champ texte n'est pas vide
            keywords = extract_keywords(text)
            if keywords:  # Si des mots-clés pertinents sont trouvés
                update_query = f"""
                UPDATE {table['name']}
                SET {table['keywords_field']} = %s
                WHERE id = %s
                """
                cursor.execute(update_query, (keywords, record_id))

# Valider les changements et fermer la connexion
connection.commit()
cursor.close()
connection.close()

print("Extraction des mots-clés terminée, base de données mise à jour.")
