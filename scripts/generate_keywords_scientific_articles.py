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

# Liste mise à jour des mots-clés pour l'IA et les sciences
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

# Embedding des mots-clés pour comparaison
keyword_embeddings = model.encode(keyword_list, convert_to_tensor=True)

# Limite des mots-clés et seuil de similarité
MAX_KEYWORDS = 10
SIMILARITY_THRESHOLD = 0.8


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
    SELECT sa.id, sa.abstract, sa.keywords
    FROM scientific_articles sa
    WHERE sa.abstract IS NOT NULL
"""
cursor.execute(select_query)
rows = cursor.fetchall()

# Enrichissement des mots-clés pour chaque article scientifique
for id, abstract, current_keywords in rows:
    print(f"Traitement de l'article scientifique ID {id}...")

    # Extraire les nouveaux mots-clés
    new_keywords = extract_keywords(abstract, keyword_embeddings, keyword_list, SIMILARITY_THRESHOLD)

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
        update_query = "UPDATE scientific_articles SET keywords = %s WHERE id = %s"
        cursor.execute(update_query, (updated_keywords, id))
    except mysql.connector.Error as e:
        print(f"Erreur SQL pour l'article scientifique ID {id}: {e}")

# Valider les changements et fermer la connexion
connection.commit()
cursor.close()
connection.close()

print("Enrichissement des mots-clés terminé. Base de données mise à jour.")
