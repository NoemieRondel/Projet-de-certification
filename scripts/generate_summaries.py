import json
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# Configurer le modèle Hugging Face
MODEL_NAME = "facebook/bart-large-cnn"  # Modèle de summarization
print("Chargement du modèle Hugging Face...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)


# Fonction pour générer un résumé
def generate_summary(content, max_length=200, min_length=50):
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
    return tokenizer.decode(summary_ids[0], skip_special_tokens=True)


# Fonction principale
def main():
    # Charger les articles depuis le fichier JSON
    with open("articles.json", "r", encoding="utf-8") as file:
        articles = json.load(file)

    print(f"{len(articles)} articles chargés depuis articles.json.")

    for article in articles:
        # Vérifier si le résumé doit être généré
        if article.get("summary") not in [None, "", "No summary available."]:
            continue  # Passer les articles ayant déjà un résumé valide

        full_content = article.get("full_content", "")
        if not full_content.strip():
            print(f"L'article '{article.get('title', 'Sans titre')}' n'a pas de contenu, ignoré.")
            continue

        print(f"Génération du résumé pour l'article '{article.get('title', 'Sans titre')}'...")

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

            print(f"Résumé généré pour l'article '{article.get('title', 'Sans titre')}'.")

        except Exception as e:
            print(f"Erreur lors de la génération du résumé pour l'article '{article.get('title', 'Sans titre')}': {e}")

    # Sauvegarder les articles mis à jour dans le fichier JSON
    with open("articles.json", "w", encoding="utf-8") as file:
        json.dump(articles, file, ensure_ascii=False, indent=4)

    print("Traitement terminé. Fichier articles.json mis à jour.")


if __name__ == "__main__":
    main()
