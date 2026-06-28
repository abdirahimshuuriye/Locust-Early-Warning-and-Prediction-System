# 🦗 Locust Early Warning and Prediction System

## Development of an Early Warning and Prediction System for Locust Outbreaks Using Logistic Regression and Support Vector Machine

This project was developed as a graduation thesis to support the early detection of desert locust outbreaks using machine learning techniques. The system predicts whether environmental conditions indicate a potential locust outbreak based on historical environmental data.

---

# Abstract

Desert locust outbreaks pose a serious threat to agriculture, food security, and rural livelihoods across many regions of Africa, the Middle East, and Asia. Traditional monitoring methods rely heavily on manual field observations and often fail to provide timely warnings for decision-makers.

This project presents a machine learning-based Early Warning and Prediction System that analyzes environmental factors including rainfall (PPT), maximum temperature (TMAX), soil moisture, region, country, year, and month to predict possible locust outbreaks.

Two supervised machine learning algorithms were implemented and evaluated:

- Logistic Regression (LR)
- Support Vector Machine (SVM)

The models were compared using Accuracy, Precision, Recall, and F1 Score. Support Vector Machine (SVM) achieved the best performance and was selected as the final prediction model.

---

# Features

- User Authentication System
- Dashboard
- Locust Outbreak Prediction
- Machine Learning Model Selection
- Logistic Regression Prediction
- Support Vector Machine Prediction
- Confidence Score
- Accuracy Score
- Precision Score
- Recall Score
- F1 Score
- Prediction Explanation
- Recommended Action
- Prediction Reports
- Risk Map
- User Management
- Activity Logs
- Feedback Management
- Profile Management

---

# Machine Learning Models

The system implements two binary classification algorithms:

## Logistic Regression (LR)

- Accuracy: **96.29%**
- Precision: **95.94%**
- Recall: **90.87%**
- F1 Score: **93.34%**

## Support Vector Machine (SVM)

- Accuracy: **97.85%**
- Precision: **97.82%**
- Recall: **94.59%**
- F1 Score: **96.18%**

SVM demonstrated the highest overall performance and was selected as the final deployment model.

---

# Dataset

The prediction model uses environmental variables:

- Region
- Country
- Start Year
- Start Month
- Rainfall (PPT)
- Maximum Temperature (TMAX)
- Soil Moisture
- Locust Presence (Target Variable)

Dataset File:

```
dataset/LocustLensFinalDataset.csv
```

---

# Technologies Used

## Backend

- Python
- Flask
- MySQL

## Frontend

- HTML5
- CSS3
- JavaScript
- Jinja2 Templates

## Machine Learning

- Scikit-learn
- Pandas
- NumPy
- Joblib

---

# System Modules

- Login System
- Dashboard
- Prediction Module
- Model Comparison
- Reports
- Risk Map
- User Management
- Feedback
- Activity Logs
- Profile

---

# Project Structure

```
LocustPredictionSystem/

│
├── app.py
├── config.py
├── requirements.txt
│
├── database/
│
├── dataset/
│
├── ml/
│   ├── predict.py
│   ├── train_model.py
│   └── models/
│
├── models/
│
├── static/
│
└── templates/
```

---

# Installation

Clone the repository

```bash
git clone https://github.com/abdirahimshuuriye/Locust-Early-Warning-and-Prediction-System.git
```

Move into the project

```bash
cd LocustPredictionSystem
```

Create virtual environment

```bash
python -m venv venv
```

Activate virtual environment

Mac/Linux

```bash
source venv/bin/activate
```

Windows

```bash
venv\Scripts\activate
```

Install requirements

```bash
pip install -r requirements.txt
```

Run the system

```bash
python app.py
```

Open your browser

```
http://127.0.0.1:5000
```

---

# Performance Evaluation

| Model | Accuracy | Precision | Recall | F1 Score |
|--------|---------:|----------:|--------:|---------:|
| Logistic Regression | 96.29% | 95.94% | 90.87% | 93.34% |
| Support Vector Machine | **97.85%** | **97.82%** | **94.59%** | **96.18%** |

---

# Authors

**Abdirahiim Ali Mohamud**

**Abdimajiid Ali Mohamud**

Department of Computer Science

Graduation Project

2026

---

# Supervisor

Prof. Eng. Abdulle Hassan Mohamud.

---

# License

This project was developed solely for academic and research purposes as part of a university graduation project.
