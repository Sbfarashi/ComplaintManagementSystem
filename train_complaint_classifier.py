import csv
from pathlib import Path

from joblib import dump
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "ml_data" / "complaint_training_data.csv"
MODEL_FILE = BASE_DIR / "ml_data" / "complaint_classifier.joblib"


def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

    with DATA_FILE.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        rows = list(csv.DictReader(file))

    texts = [row["text"].strip() for row in rows]
    categories = [row["category"].strip() for row in rows]

    if not texts or any(not text for text in texts):
        raise ValueError("The dataset is empty or contains blank complaint text.")

    if len(set(categories)) < 2:
        raise ValueError("At least two complaint categories are required.")

    X_train, X_test, y_train, y_test = train_test_split(
        texts,
        categories,
        test_size=0.25,
        random_state=42,
        stratify=categories
    )

    model = Pipeline([
        ("tfidf", TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            sublinear_tf=True
        )),
        ("classifier", MultinomialNB(alpha=0.5))
    ])

    print("Training complaint classification model...")
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    print("\nModel evaluation")
    print("----------------")
    print("Training examples:", len(X_train))
    print("Testing examples:", len(X_test))
    print("Accuracy:", round(accuracy_score(y_test, predictions) * 100, 2), "%")

    labels = sorted(set(categories))
    print("\nClassification report:")
    print(classification_report(
        y_test,
        predictions,
        labels=labels,
        target_names=labels,
        zero_division=0
    ))

    # Train the final model using all available examples.
    model.fit(texts, categories)
    dump(model, MODEL_FILE)

    print("Final model saved successfully:")
    print(MODEL_FILE)


if __name__ == "__main__":
    main()
