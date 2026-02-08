# --- 1. 載入套件與資料 ---
"""
Predict diabetes risk using classification models with EDA, preprocessing, hyperparameter tuning, cross-validation, and SHAP analysis.
"""

# Data handling
import pandas as pd
import numpy as np
import io

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns
import shap

# Machine learning
from sklearn.model_selection import (
    train_test_split, cross_val_score,
    GridSearchCV, KFold
)
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, confusion_matrix, classification_report,
    roc_auc_score, roc_curve
)

import os
import argparse

# Create results directory if not exists
RESULTS_DIR = "results"
os.makedirs(RESULTS_DIR, exist_ok=True)

# Hyperparameter grids for GridSearchCV for each model
PARAM_GRIDS = {
    "Logistic Regression": {
        "C": [0.01, 0.1, 1, 10],
        "penalty": ["l2"],
        "solver": ["liblinear"]
    },
    "Decision Tree": {
        "max_depth": [None, 3, 5, 7],
        "min_samples_split": [2, 5, 10]
    },
    "Random Forest": {
        "n_estimators": [50, 100, 200],
        "max_depth": [None, 5, 10]
    }
}

# Helper: save text lines to a simple CSV (1 column per line)
def save_text_as_csv(filename, text_lines):
    """
    Save a list of text lines to a CSV file with one column.
    
    Inputs:
        filename (str): Path to output CSV file.
        text_lines (list of str): Lines of text to save.
    Outputs:
        None (writes file)
    """
    with open(filename, "w", encoding="utf-8") as f:
        for line in text_lines:
            f.write(f"\"{line.strip()}\"\n")

def load_data(path):
    """
    Load CSV, save raw data and metadata to CSV files, return DataFrame.
    
    Inputs:
        path (str): Path to input CSV file.
    Outputs:
        df (pd.DataFrame): Loaded data.
    """
    df = pd.read_csv(path)
    
    # Save DataFrame to CSV
    df.to_csv(os.path.join(RESULTS_DIR, "raw_data.csv"), index=False)
    
    # Save df.info() to CSV
    buffer = io.StringIO()
    df.info(buf=buffer)
    info_lines = buffer.getvalue().splitlines()
    save_text_as_csv(os.path.join(RESULTS_DIR, "data_info.csv"), info_lines)

    # Save first 5 rows as CSV
    df.head().to_csv(os.path.join(RESULTS_DIR, "data_head.csv"), index=False)
    return df

def preprocess(df):
    """
    Replace zeros with NaN in specified columns, fill missing with medians, save processed data.
    
    Inputs:
        df (pd.DataFrame): Raw data.
    Outputs:
        df (pd.DataFrame): Preprocessed data.
    """
    cols = ["Glucose","BloodPressure","SkinThickness","Insulin","BMI"]
    # Replace physiologically impossible zeros with NaN
    df[cols] = df[cols].replace(0, np.nan)
    # Fill missing values with median of each column
    df = df.fillna(df.median())
    # Save preprocessed data
    df.to_csv(os.path.join(RESULTS_DIR, "processed_data.csv"), index=False)
    return df

def plot_eda(df):
    """
    Generate and save distribution, histogram, and correlation heatmap plots.
    
    Inputs:
        df (pd.DataFrame): Data to visualize.
    Outputs:
        None (saves plots)
    """
    # 1. Distribution Plot
    sns.countplot(x="Outcome", data=df)
    plt.title("Diabetes Distribution (0=No, 1=Yes)")
    plt.savefig(os.path.join(RESULTS_DIR, "diabetes_distribution.png"))
    plt.close()
    
    # 2. Histograms
    df.hist(bins=30, figsize=(15,10))
    plt.tight_layout()
    # Note: plt.title() after hist() affects only last subplot; better to omit or add suptitle
    plt.savefig(os.path.join(RESULTS_DIR, "feature_histograms.png"))
    plt.close()

    # 3. Correlation Heatmap
    plt.figure(figsize=(10,8))
    sns.heatmap(df.corr(), annot=True, cmap="coolwarm", fmt=".2f")
    plt.title("Correlation Heatmap")
    plt.savefig(os.path.join(RESULTS_DIR, "correlation_heatmap.png"))
    plt.close()

def split_and_scale(df):
    """
    Split data into train/test sets and standardize features.
    
    Inputs:
        df (pd.DataFrame): Preprocessed data.
    Outputs:
        X_train_s (np.ndarray): Scaled training features.
        X_test_s (np.ndarray): Scaled testing features.
        y_train (pd.Series): Training labels.
        y_test (pd.Series): Testing labels.
        X_scaled (np.ndarray): Scaled full feature set.
        X (pd.DataFrame): Original features.
        y (pd.Series): Original labels.
    """
    X = df.drop("Outcome", axis=1)
    y = df["Outcome"]
    # Split data into train/test sets with stratification
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    # Standardize features using training set only
    scaler = StandardScaler().fit(X_train)
    X_train_s = scaler.transform(X_train)
    X_test_s  = scaler.transform(X_test)
    X_scaled = scaler.transform(X)
    return X_train_s, X_test_s, y_train, y_test, X_scaled, X, y

def train_baseline(X_train, y_train):
    """
    Fit baseline classification models on training data.
    
    Inputs:
        X_train (np.ndarray): Scaled training features.
        y_train (pd.Series): Training labels.
    Outputs:
        models (dict): Trained models keyed by name.
    """
    models = {
        "Logistic Regression": LogisticRegression(),
        "Decision Tree": DecisionTreeClassifier(random_state=42),
        "Random Forest": RandomForestClassifier(random_state=42)
    }
    # Fit baseline models
    for m in models.values():
        m.fit(X_train, y_train)
    return models

def evaluate(models, X_test, y_test):
    """
    Evaluate baseline models on test data and save classification reports.
    
    Inputs:
        models (dict): Trained models.
        X_test (np.ndarray): Scaled test features.
        y_test (pd.Series): Test labels.
    Outputs:
        None (writes classification_reports.csv)
    
    Note: Only baseline models are evaluated here; tuned models are not re-evaluated.
    """
    # Store classification reports in a single CSV
    all_reports = []
    for name, m in models.items():
        y_pred = m.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        auc_score = roc_auc_score(y_test, m.predict_proba(X_test)[:,1])
        report_dict = classification_report(y_test, y_pred, output_dict=True)
        report_df = pd.DataFrame(report_dict).T
        report_df["model"] = name
        report_df["accuracy_score"] = acc
        report_df["roc_auc_score"] = auc_score
        all_reports.append(report_df)

    # Concatenate all classification reports
    final_report_df = pd.concat(all_reports)
    final_report_df.to_csv(os.path.join(RESULTS_DIR, "classification_reports.csv"), index=True)

def plot_confusion(models, X_test, y_test):
    """
    Plot and save confusion matrices for each model.
    
    Inputs:
        models (dict): Trained models.
        X_test (np.ndarray): Scaled test features.
        y_test (pd.Series): Test labels.
    Outputs:
        None (saves plot images)
    """
    for name, m in models.items():
        cm = confusion_matrix(y_test, m.predict(X_test))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues")
        plt.title(f"Confusion Matrix - {name}")
        plt.xlabel("Predicted")
        plt.ylabel("Actual")
        plt.savefig(os.path.join(RESULTS_DIR, f"confusion_matrix_{name.replace(' ','_')}.png"))
        plt.close()

def plot_roc(models, X_test, y_test):
    """
    Plot ROC curves for each model and save figure.
    
    Inputs:
        models (dict): Trained models.
        X_test (np.ndarray): Scaled test features.
        y_test (pd.Series): Test labels.
    Outputs:
        None (saves roc_curve.png)
    """
    plt.figure(figsize=(8,6))
    for name, m in models.items():
        fpr, tpr, _ = roc_curve(y_test, m.predict_proba(X_test)[:,1])
        auc_val = roc_auc_score(y_test, m.predict_proba(X_test)[:,1])
        plt.plot(fpr, tpr, label=f"{name} (AUC={auc_val:.2f})")
    plt.plot([0,1],[0,1],'k--')
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve")
    plt.legend()
    plt.grid()
    plt.savefig(os.path.join(RESULTS_DIR, "roc_curve.png"))
    plt.close()

def plot_feature_importance(rf, feature_names):
    """
    Plot and save feature importance from Random Forest model.
    
    Inputs:
        rf (RandomForestClassifier): Trained random forest model.
        feature_names (pd.Index or list): Feature names.
    Outputs:
        None (saves feature_importance.png)
    """
    imp = pd.Series(rf.feature_importances_, index=feature_names).sort_values()
    imp.plot(kind="barh")
    plt.title("Random Forest Feature Importance")
    plt.savefig(os.path.join(RESULTS_DIR, "feature_importance.png"))
    plt.close()

def tune_hyperparameters(models, X_train, y_train):
    """
    Perform hyperparameter tuning with GridSearchCV for each model.
    
    Inputs:
        models (dict): Baseline models.
        X_train (np.ndarray): Scaled training features.
        y_train (pd.Series): Training labels.
    Outputs:
        best (dict): Best estimators for each model.
    """
    best = {}
    tuning_results = []
    for name, m in models.items():
        # Grid search with 5-fold CV optimizing ROC AUC
        grid = GridSearchCV(m, PARAM_GRIDS[name], cv=5, scoring="roc_auc", n_jobs=-1)
        grid.fit(X_train, y_train)
        best[name] = grid.best_estimator_
        tuning_results.append({
            "model": name,
            "best_params": str(grid.best_params_),
            "best_auc": grid.best_score_
        })
    # Save hyperparameter tuning results
    pd.DataFrame(tuning_results).to_csv(os.path.join(RESULTS_DIR, "hyperparameter_tuning_results.csv"), index=False)
    return best

def cross_validate(models, X, y):
    """
    Perform 5-fold cross-validation and save results.
    
    Inputs:
        models (dict): Models to evaluate.
        X (np.ndarray): Scaled full feature set.
        y (pd.Series): Labels.
    Outputs:
        None (saves cross_validation_results.csv)
    """
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    cv_records = []
    for name, m in models.items():
        scores = cross_val_score(m, X, y, cv=kf, scoring="roc_auc", n_jobs=-1)
        cv_records.append({
            "model": name,
            "mean_auc": scores.mean(),
            "std_auc": scores.std()
        })
    pd.DataFrame(cv_records).to_csv(os.path.join(RESULTS_DIR, "cross_validation_results.csv"), index=False)

def shap_analysis(rf, X_train_raw, cols):
    """
    Perform SHAP analysis and save summary plots.
    
    Inputs:
        rf (RandomForestClassifier): Trained random forest model.
        X_train_raw (pd.DataFrame): Raw training features (unscaled).
        cols (list or pd.Index): Feature names.
    Outputs:
        None (saves shap_feature_importance.png and shap_summary.png)
    """
    explainer = shap.TreeExplainer(rf)
    vals = explainer.shap_values(X_train_raw)
    # Handle binary classification: shap_values returns list of arrays
    if isinstance(vals, list):
        # Select explanations for the positive class
        shap_vals = vals[1]
    else:
        shap_vals = vals

    # Bar plot
    shap.summary_plot(shap_vals, X_train_raw, plot_type="bar", show=False)
    plt.title("SHAP Feature Importance")
    plt.savefig(os.path.join(RESULTS_DIR, "shap_feature_importance.png"))
    plt.close()

    # Summary plot of the first 100 rows
    shap.summary_plot(shap_vals[:100], X_train_raw.iloc[:100], show=False)
    plt.title("SHAP Summary (first 100 rows)")
    plt.savefig(os.path.join(RESULTS_DIR, "shap_summary.png"))
    plt.close()

def main():
    """
    Main workflow:
    - Load and preprocess data
    - Perform exploratory data analysis
    - Split and scale data
    - Train baseline models and evaluate
    - Plot confusion matrices and ROC curves
    - Plot feature importances
    - Tune hyperparameters and cross-validate best models
    - Perform SHAP analysis on best random forest model
    
    CLI: pass --data <path/to/diabetes.csv> to override default location.
    """
    # Parse command‑line argument for data path
    parser = argparse.ArgumentParser(description="Diabetes prediction pipeline")
    parser.add_argument("--data", default="diabetes.csv",
                        help="Path to diabetes CSV file (default: ./diabetes.csv)")
    args = parser.parse_args()
    path = args.data
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Data file not found: {path}")
    df = load_data(path)
    df = preprocess(df)
    plot_eda(df)
    
    X_tr, X_te, y_tr, y_te, X_sc, X_raw, y = split_and_scale(df)
    base_models = train_baseline(X_tr, y_tr)
    evaluate(base_models, X_te, y_te)
    plot_confusion(base_models, X_te, y_te)
    plot_roc(base_models, X_te, y_te)
    plot_feature_importance(base_models["Random Forest"], X_raw.columns)
    
    best_models = tune_hyperparameters(base_models, X_tr, y_tr)
    cross_validate(best_models, X_sc, y)
    
    X_train_df = pd.DataFrame(X_tr, columns=X_raw.columns)
    shap_analysis(best_models["Random Forest"], X_train_df, X_raw.columns)

# Execute main pipeline
if __name__ == "__main__":
    main()