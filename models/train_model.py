import joblib

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)


DATASET_PATH = "SMSSpamCollection"
MODEL_PATH = "spam_classifier.joblib"


messages = []
labels = []


# ==============================
# LOAD DATASET
# ==============================

with open(DATASET_PATH, "r", encoding="utf-8") as file:

    for line in file:

        line = line.strip()

        if not line:
            continue

        parts = line.split("\t", 1)

        if len(parts) != 2:
            continue

        label, message = parts

        messages.append(message)

        if label == "spam":
            labels.append(1)
        else:
            labels.append(0)


print("\n===== DATASET LOADED =====")
print("Total messages:", len(messages))
print("Spam messages:", labels.count(1))
print("Normal messages:", labels.count(0))


# ==============================
# TRAIN / TEST SPLIT
# ==============================

X_train, X_test, y_train, y_test = train_test_split(
    messages,
    labels,
    test_size=0.20,
    random_state=42,
    stratify=labels
)


print("\n===== DATA SPLIT =====")
print("Training samples:", len(X_train))
print("Testing samples:", len(X_test))


# ==============================
# CREATE MODEL
# ==============================

model = Pipeline([
    (
        "vectorizer",
        CountVectorizer()
    ),
    (
        "classifier",
        MultinomialNB()
    )
])


# ==============================
# TRAIN MODEL
# ==============================

print("\nTraining model...")

model.fit(X_train, y_train)


# ==============================
# MAKE PREDICTIONS
# ==============================

y_pred = model.predict(X_test)


# ==============================
# MODEL EVALUATION
# ==============================

accuracy = accuracy_score(y_test, y_pred)

precision = precision_score(
    y_test,
    y_pred,
    zero_division=0
)

recall = recall_score(
    y_test,
    y_pred,
    zero_division=0
)

f1 = f1_score(
    y_test,
    y_pred,
    zero_division=0
)

matrix = confusion_matrix(
    y_test,
    y_pred
)


print("\n===== MODEL EVALUATION =====")

print(f"Accuracy : {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall   : {recall:.4f}")
print(f"F1-score : {f1:.4f}")

print("\nConfusion Matrix:")
print(matrix)


# ==============================
# TRAIN FINAL MODEL
# ==============================

print("\nTraining final model using full dataset...")

model.fit(messages, labels)


# ==============================
# SAVE MODEL
# ==============================

joblib.dump(
    model,
    MODEL_PATH
)


print("\n===== MODEL TRAINING COMPLETE =====")

print("Training samples:", len(messages))
print("Model type:", type(model).__name__)
print("Model saved as:", MODEL_PATH)
print("Model trained successfully.")