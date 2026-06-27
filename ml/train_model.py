import pandas as pd
import joblib
import os

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler, LabelEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Create models folder if it does not exist
os.makedirs("ml/models", exist_ok=True)

# Load dataset
df = pd.read_csv("dataset/LocustLensFinalDataset.csv")

print("Dataset Loaded Successfully")
print("Shape:", df.shape)

# Encode target variable
target_encoder = LabelEncoder()
df["LOCUSTPRESENT"] = target_encoder.fit_transform(df["LOCUSTPRESENT"])

# Features and target
X = df.drop("LOCUSTPRESENT", axis=1)
y = df["LOCUSTPRESENT"]

# Columns
categorical_cols = ["REGION", "COUNTRYNAME"]
numeric_cols = ["STARTYEAR", "STARTMONTH", "PPT", "TMAX", "SOILMOISTURE"]

# Preprocessing
preprocessor = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
        ("num", StandardScaler(), numeric_cols)
    ]
)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("Training Data:", len(X_train))
print("Testing Data:", len(X_test))

# Logistic Regression Pipeline
lr_model = Pipeline([
    ("preprocessor", preprocessor),
    ("model", LogisticRegression(max_iter=3000))
])

# SVM Pipeline
svm_model = Pipeline([
    ("preprocessor", preprocessor),
    ("model", SVC(probability=True))
])

# Train Logistic Regression
lr_model.fit(X_train, y_train)
lr_predictions = lr_model.predict(X_test)

lr_accuracy = accuracy_score(y_test, lr_predictions)
lr_precision = precision_score(y_test, lr_predictions)
lr_recall = recall_score(y_test, lr_predictions)
lr_f1 = f1_score(y_test, lr_predictions)

print("\nLogistic Regression Results:")
print("Accuracy:", round(lr_accuracy * 100, 2), "%")
print("Precision:", round(lr_precision * 100, 2), "%")
print("Recall:", round(lr_recall * 100, 2), "%")
print("F1 Score:", round(lr_f1 * 100, 2), "%")

# Train SVM
svm_model.fit(X_train, y_train)
svm_predictions = svm_model.predict(X_test)

svm_accuracy = accuracy_score(y_test, svm_predictions)
svm_precision = precision_score(y_test, svm_predictions)
svm_recall = recall_score(y_test, svm_predictions)
svm_f1 = f1_score(y_test, svm_predictions)

print("\nSVM Results:")
print("Accuracy:", round(svm_accuracy * 100, 2), "%")
print("Precision:", round(svm_precision * 100, 2), "%")
print("Recall:", round(svm_recall * 100, 2), "%")
print("F1 Score:", round(svm_f1 * 100, 2), "%")

# Save both models
joblib.dump(lr_model, "ml/models/logistic_regression_model.pkl")
joblib.dump(svm_model, "ml/models/svm_model.pkl")

# Save target encoder
joblib.dump(target_encoder, "ml/models/target_encoder.pkl")

# Save best model
if lr_accuracy > svm_accuracy:
    best_model = lr_model
    best_name = "Logistic Regression"
else:
    best_model = svm_model
    best_name = "Support Vector Machine"

joblib.dump(best_model, "ml/models/saved_model.pkl")

print("\nBest Model Saved:")
print(best_name)

print("\nFiles Created:")
print("ml/models/logistic_regression_model.pkl")
print("ml/models/svm_model.pkl")
print("ml/models/saved_model.pkl")
print("ml/models/target_encoder.pkl")