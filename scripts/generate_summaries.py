import os
import mysql.connector
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# Charger les variables d'environnement
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Configurer le modèle Hugging Face
MODEL_NAME = "facebook/bart-large-cnn"  # Modèle de summarization

print("Chargement du modèle Hugging Face...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)


# Fonction de connexion à la base de données
def connect_db():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )


# Fonction pour générer un résumé
def generate_summary(article_text, max_length=200, min_length=50):
    # Tokenization avec tronçonnage
    inputs = tokenizer(
        article_text,
        return_tensors="pt",
        truncation=True,  # Coupe le texte au maximum supporté
        max_length=1024  # Longueur maximale pour BART
    )
    
    if inputs.input_ids.size(1) > 1024:  # Vérification pour éviter l'erreur
        raise ValueError(f"Texte trop long après tokenization : {len(article_text)} caractères.")

    # Génération du résumé
    summary_ids = model.generate(
        inputs.input_ids,
        max_length=max_length,
        min_length=min_length,
        length_penalty=2.0,
        num_beams=4,
        early_stopping=True
    )
    return tokenizer.decode(summary_ids[0], skip_special_tokens=True)


# Fonction principale
def main():
    print("Connexion à la base de données...")
    db = connect_db()
    cursor = db.cursor(dictionary=True)

    # Récupérer les articles sans résumé
    query = """
    SELECT a.id AS article_id, ac.content AS full_content
    FROM articles a
    INNER JOIN article_content ac ON a.id = ac.article_id
    WHERE a.content IS NULL OR a.content = ''
    """
    cursor.execute(query)
    articles = cursor.fetchall()

    print(f"{len(articles)} articles trouvés sans résumé.")

    for article in articles:
        article_id = article['article_id']
        full_content = article['full_content']

        # Déterminer la longueur du résumé dynamiquement
        word_count = len(full_content.split())
        if word_count < 300:
            max_length = 100
        elif word_count < 1000:
            max_length = 200
        else:
            max_length = 300

        print(f"Génération du résumé pour l'article {article_id}...")

        try:
            # Vérification de la longueur de l'article
            if len(full_content) > 4096:  # BART ne gère que 1024 tokens (environ 4000 caractères brut)
                print(f"Article {article_id} trop long, tronquons...")
                full_content = full_content[:4000]

            summary = generate_summary(full_content, max_length=max_length)

            # Mettre à jour la table articles avec le résumé
            update_query = "UPDATE articles SET content = %s WHERE id = %s"
            cursor.execute(update_query, (summary, article_id))
            db.commit()

            print(f"Résumé mis à jour pour l'article {article_id}.")
        except Exception as e:
            print(f"Erreur lors de la génération du résumé pour l'article {article_id}: {e}")

    cursor.close()
    db.close()
    print("Traitement terminé.")


if __name__ == "__main__":
    main()
