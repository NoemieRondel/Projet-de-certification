import json
import logging
import os
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# Configurer le modèle Hugging Face
MODEL_NAME = "facebook/bart-large-cnn"

# Configurer le logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Fichiers
JSON_FILE = "articles.json"
MONITORING_FILE = "monitoring.json"

# Timer début
start_time = datetime.now()

logging.info("Chargement du modèle Hugging Face...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)


# Fonction de résumé
def generate_summary(content, max_length=200, min_length=50):
    logging.info("Début de la génération du résumé.")
    inputs = tokenizer(
        content,
        return_tensors="pt",
        truncation=True,
        max_length=1024
    )
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


# Fonction pour enregistrer les métriques dans un fichier unique
def save_monitoring_entry(script_name, data):
    if os.path.exists(MONITORING_FILE):
        with open(MONITORING_FILE, "r", encoding="utf-8") as f:
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

    with open(MONITORING_FILE, "w", encoding="utf-8") as f:
        json.dump(monitoring, f, indent=4)


# Fonction principale
def main():
    try:
        with open(JSON_FILE, "r", encoding="utf-8") as file:
            articles = json.load(file)
        logging.info(f"{len(articles)} articles chargés depuis {JSON_FILE}.")
    except FileNotFoundError:
        logging.error(f"Le fichier {JSON_FILE} est introuvable.")
        return
    except json.JSONDecodeError:
        logging.error(f"Erreur lors du chargement du fichier {JSON_FILE}.")
        return

    total_articles = len(articles)
    empty_contents = 0
    summaries_generated = 0

    for article in articles:
        if article.get("summary") not in [None, "", "No summary available."]:
            continue

        full_content = article.get("full_content", "")
        if not full_content.strip():
            empty_contents += 1
            continue

        try:
            word_count = len(full_content.split())
            if word_count < 300:
                max_length = 100
            elif word_count < 1000:
                max_length = 200
            else:
                max_length = 300

            summary = generate_summary(full_content, max_length=max_length)
            article["summary"] = summary
            summaries_generated += 1
        except Exception as e:
            logging.error(f"Erreur lors de la génération du résumé pour l'article '{article.get('title', 'Sans titre')}': {e}")

    try:
        with open(JSON_FILE, "w", encoding="utf-8") as file:
            json.dump(articles, file, ensure_ascii=False, indent=4)
        logging.info(f"Fichier {JSON_FILE} mis à jour avec les résumés.")
    except Exception as e:
        logging.error(f"Erreur lors de la sauvegarde du fichier : {e}")

    # Monitoring
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    average_summary_length = sum(len(a.get("summary", "").split()) for a in articles if a.get("summary")) / summaries_generated if summaries_generated else 0

    monitoring_data = {
        "duration_seconds": round(duration, 2),
        "articles_count": total_articles,
        "empty_full_content_count": empty_contents,
        "summaries_generated": summaries_generated,
        "average_summary_word_count": round(average_summary_length, 2)
    }

    save_monitoring_entry("generate_summaries", monitoring_data)
    logging.info("Monitoring mis à jour dans monitoring.json.")


if __name__ == "__main__":
    main()
