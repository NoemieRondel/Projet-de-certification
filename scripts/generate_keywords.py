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
    "Telecommunications"
]

# Embedding des mots-clés pour les comparaisons
keyword_embeddings = model.encode(keywords_list, convert_to_tensor=True)

# Limite des mots-clés à extraire
MAX_KEYWORDS = 10
SIMILARITY_THRESHOLD = 0.2


# Fonction pour extraire les mots-clés les plus pertinents
def extract_keywords(text):
    if not text or not text.strip():
        return ""  # Retourne vide si le texte est invalide

    # Encodage du texte et calcul de la similarité
    text_embedding = model.encode(text, convert_to_tensor=True)
    cosine_scores = util.cos_sim(text_embedding, keyword_embeddings)[0]

    # Filtrer les mots-clés avec un seuil de similarité
    filtered_keywords = [
        keywords_list[i] for i in range(len(cosine_scores)) if cosine_scores[i] > SIMILARITY_THRESHOLD
    ]

    if not filtered_keywords:
        return ""  # Retourne vide si aucun mot-clé n'atteint le seuil

    # Trier les mots-clés et retourner les plus pertinents
    sorted_keywords = [keywords_list[i] for i in cosine_scores.argsort(descending=True)]
    return ";".join(sorted_keywords[:MAX_KEYWORDS])


# Traitement des articles dans la table article_content
select_query = """
    SELECT ac.article_id, ac.content, a.keywords
    FROM article_content ac
    JOIN articles a ON ac.article_id = a.id
    WHERE ac.content IS NOT NULL
"""
cursor.execute(select_query)
rows = cursor.fetchall()

for article_id, content, current_keywords in rows:
    print(f"Traitement de l'article ID {article_id}...")

    # Extraire les mots-clés à partir du contenu de l'article
    new_keywords = extract_keywords(content)

    if new_keywords:  # Si des mots-clés sont trouvés
        updated_keywords = new_keywords

        # Si des mots-clés existent déjà dans la table articles, les combiner
        if current_keywords:
            current_keywords_set = set(current_keywords.split(";"))
            new_keywords_set = set(new_keywords.split(";"))
            combined_keywords = current_keywords_set.union(new_keywords_set)
            updated_keywords = ";".join(combined_keywords)

        # Mise à jour des mots-clés dans la table articles
        try:
            update_query = "UPDATE articles SET keywords = %s WHERE id = %s"
            cursor.execute(update_query, (updated_keywords, article_id))
        except mysql.connector.Error as e:
            print(f"Erreur SQL pour l'ID {article_id}: {e}")
    else:
        print(f"Aucun mot-clé extrait pour l'article ID {article_id}.")

# Valider les changements et fermer la connexion
connection.commit()
cursor.close()
connection.close()

print("Extraction des mots-clés terminée et base de données mise à jour.")
