import json
import logging
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# Configurer le modèle Hugging Face
MODEL_NAME = "facebook/bart-large-cnn"  # Modèle de summarization

# Configurer le logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logging.info("Chargement du modèle Hugging Face...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)


# Fonction pour générer un résumé
def generate_summary(content, max_length=200, min_length=50):
    logging.info("Début de la génération du résumé.")
    # Tokenization avec tronçonnage
    inputs = tokenizer(
        content,
        return_tensors="pt",
        truncation=True,
        max_length=1024
    )

    # Génération du résumé
    summary_ids = model.generate(
        inputs.input_ids,
        max_length=max_length,
        min_length=min_length,
        length_penalty=2.0,
        num_beams=4,
        early_stopping=True
    )
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    logging.info("Résumé généré avec succès.")
    return summary


# Fonction principale
def main():
    # Charger les articles depuis le fichier JSON
    try:
        with open("articles.json", "r", encoding="utf-8") as file:
            articles = json.load(file)
        logging.info(f"{len(articles)} articles chargés depuis articles.json.")
    except FileNotFoundError:
        logging.error("Le fichier articles.json est introuvable.")
        return
    except json.JSONDecodeError:
        logging.error("Erreur lors du chargement du fichier articles.json.")
        return

    for article in articles:
        # Vérifier si le résumé doit être généré
        if article.get("summary") not in [None, "", "No summary available."]:
            logging.info(f"Résumé déjà existant pour l'article '{article.get('title', 'Sans titre')}', passage au suivant.")
            continue  # Passer les articles ayant déjà un résumé valide

        full_content = article.get("full_content", "")
        if not full_content.strip():
            logging.warning(f"L'article '{article.get('title', 'Sans titre')}' n'a pas de contenu, ignoré.")
            continue

        logging.info(f"Génération du résumé pour l'article '{article.get('title', 'Sans titre')}'...")

        try:
            # Déterminer la longueur du résumé dynamiquement
            word_count = len(full_content.split())
            if word_count < 300:
                max_length = 100
            elif word_count < 1000:
                max_length = 200
            else:
                max_length = 300

            # Générer le résumé
            summary = generate_summary(full_content, max_length=max_length)

            # Mettre à jour l'article avec le résumé généré
            article["summary"] = summary

            logging.info(f"Résumé généré pour l'article '{article.get('title', 'Sans titre')}'.")

        except Exception as e:
            logging.error(f"Erreur lors de la génération du résumé pour l'article '{article.get('title', 'Sans titre')}': {e}")

    # Sauvegarder les articles mis à jour dans le fichier JSON
    try:
        with open("articles.json", "w", encoding="utf-8") as file:
            json.dump(articles, file, ensure_ascii=False, indent=4)
        logging.info("Traitement terminé. Fichier articles.json mis à jour.")
    except Exception as e:
        logging.error(f"Erreur lors de la sauvegarde des articles mis à jour dans articles.json: {e}")


if __name__ == "__main__":
    main()
