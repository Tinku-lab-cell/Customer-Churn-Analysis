# -*- coding: utf-8 -*-
"""Customer Churn Analysis.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1qFIpjQfo6HiBYbnv_ILsj-VlBC1iBsh8

**Import Necessary Libraries:**
"""

import pandas as pd
import numpy as np
import random
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix, precision_score, recall_score, f1_score, roc_auc_score

"""# Synthetic Data generation
# > - These functions are used to generate synthetic data for a customer churn analysis
"""

def generate_customer_id(size):
    return np.arange(1, size + 1)

def generate_age(size):
    return np.random.randint(18, 80, size)

def generate_gender(size):
    return np.random.choice(['Male', 'Female'], size)

def generate_contract_type(size):
    return np.random.choice(['Month-to-month', 'One year', 'Two year'], size)

def generate_monthly_charges(size):
    return np.random.uniform(30, 100, size)

def generate_total_charges(size, monthly_charges, tenure):
    return monthly_charges * tenure

def generate_tech_support(size):
    return np.random.choice(['Yes', 'No'], size)

def generate_internet_service(size):
    return np.random.choice(['DSL', 'Fiber optic', 'No'], size)

def generate_tenure(size):
    return np.random.randint(1, 72, size)

def generate_paperless_billing(size):
    return np.random.choice(['Yes', 'No'], size)

def generate_payment_method(size):
    return np.random.choice(['Electronic check', 'Mailed check', 'Bank transfer', 'Credit card'], size)

def generate_churn(size, churn_rate=0.2):
    return np.random.choice(['Yes', 'No'], size, p=[churn_rate, 1 - churn_rate])

def introduce_missing_values(df, missing_rate=0.05):
    for column in df.columns:
        if column not in ['CustomerID', 'Churn']:
            mask = np.random.rand(len(df)) < missing_rate
            df.loc[mask, column] = np.nan
    return df

def introduce_outliers(df, outlier_rate=0.01):
    for column in ['Age', 'MonthlyCharges', 'TotalCharges', 'Tenure']:
        mask = np.random.rand(len(df)) < outlier_rate
        df.loc[mask, column] = df[column].max() * 10
    return df

def introduce_inconsistencies(df, inconsistency_rate=0.01):
    for column in ['Gender', 'ContractType', 'InternetService', 'PaymentMethod']:
        mask = np.random.rand(len(df)) < inconsistency_rate
        df.loc[mask, column] = 'Unknown'
    return df

"""**Calling out the defined function:**


"""

size = 5000 # records
data = {
    'CustomerID': generate_customer_id(size),
    'Age': generate_age(size),
    'Gender': generate_gender(size),
    'ContractType': generate_contract_type(size),
    'MonthlyCharges': generate_monthly_charges(size),
    'Tenure': generate_tenure(size),
    'TechSupport': generate_tech_support(size),
    'InternetService': generate_internet_service(size),
    'PaperlessBilling': generate_paperless_billing(size),
    'PaymentMethod': generate_payment_method(size),
    'Churn': generate_churn(size)
}

df = pd.DataFrame(data)
df['TotalCharges'] = generate_total_charges(size, df['MonthlyCharges'], df['Tenure'])

# Introduce data quality issues
df = introduce_missing_values(df)
df = introduce_outliers(df)
df = introduce_inconsistencies(df)

# Create derived features
df['AverageMonthlyCharges'] = df['TotalCharges'] / df['Tenure']
df['CustomerLifetimeValue'] = df['MonthlyCharges'] * df['Tenure']

# Display the first few rows of the dataset
print(df.head())

"""**Checking the data quality**

#Missing Values:
"""

print(df.isnull().sum())

import matplotlib.pyplot as plt
import seaborn as sns


sns.set(style="whitegrid")


plt.figure(figsize=(12, 8))
for i, column in enumerate(['Age', 'MonthlyCharges', 'TotalCharges', 'Tenure'], 1):
    plt.subplot(2, 2, i)
    sns.histplot(df[column], bins=30, kde=True)
    plt.title(f'Histogram of {column}')
plt.tight_layout()
plt.show()

"""**Unique Values**

"""

for column in ['Gender', 'ContractType', 'InternetService', 'PaymentMethod']:
    print(f" {column}: {df[column].unique()}")

"""**Fill missing values for numerical columns with the mean**

"""

numerical_columns = ['Age', 'MonthlyCharges', 'TotalCharges', 'Tenure', 'AverageMonthlyCharges', 'CustomerLifetimeValue']
for column in numerical_columns:
    df[column].fillna(df[column].mean(), inplace=True)

"""**Fill missing values for categorical columns with the mode**

"""

categorical_columns = ['Gender', 'ContractType', 'TechSupport', 'InternetService', 'PaperlessBilling', 'PaymentMethod']
for column in categorical_columns:
    df[column].fillna(df[column].mode()[0], inplace=True)

# Verify that there are no missing values left
print(df.isnull().sum())

"""**label encoding for categorical features to convert them into numerical format**.

"""

label_encoder = LabelEncoder()


for column in categorical_columns:
    df[column] = label_encoder.fit_transform(df[column])
df['Churn'] = label_encoder.fit_transform(df['Churn'])

"""**checking missing values**

"""

df.isnull().sum()

"""**modeling**

**test train split 80 | 20 ratio**
"""

from sklearn.model_selection import train_test_split


X = df.drop(['CustomerID', 'Churn'], axis=1)
y = df['Churn']

X_train_full, X_temp, y_train_full, y_temp = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp)

# Create interaction terms
df['MonthlyCharges_Tenure'] = df['MonthlyCharges'] * df['Tenure']
df['Age_Tenure'] = df['Age'] * df['Tenure']

# Update the feature set
X_train_full['MonthlyCharges_Tenure'] = X_train_full['MonthlyCharges'] * X_train_full['Tenure']
X_train_full['Age_Tenure'] = X_train_full['Age'] * X_train_full['Tenure']

X_val['MonthlyCharges_Tenure'] = X_val['MonthlyCharges'] * X_val['Tenure']
X_val['Age_Tenure'] = X_val['Age'] * X_val['Tenure']

X_test['MonthlyCharges_Tenure'] = X_test['MonthlyCharges'] * X_test['Tenure']
X_test['Age_Tenure'] = X_test['Age'] * X_test['Tenure']

"""**Model Building**

"""

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from xgboost import XGBClassifier
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.metrics import classification_report, confusion_matrix, precision_score, recall_score, f1_score, roc_auc_score

"""**Random Forest**

"""

# Random Forest
rf = RandomForestClassifier(class_weight='balanced', random_state=42)
param_grid_rf = {
    'n_estimators': [50, 100, 200],
    'max_depth': [5, 10, 15],
    'min_samples_split': [2, 5, 10]
}

grid_search_rf = GridSearchCV(rf, param_grid_rf, cv=3, scoring='precision', n_jobs=-1)
grid_search_rf.fit(X_train_full, y_train_full)

best_rf = grid_search_rf.best_estimator_

# Evaluate on validation set
y_val_pred_rf = best_rf.predict(X_val)
print("Random Forest Validation Results:")
print(classification_report(y_val, y_val_pred_rf))
print("Confusion Matrix:")
print(confusion_matrix(y_val, y_val_pred_rf))
print("Precision:", precision_score(y_val, y_val_pred_rf))
print("Recall:", recall_score(y_val, y_val_pred_rf))
print("F1 Score:", f1_score(y_val, y_val_pred_rf))
print("ROC AUC Score:", roc_auc_score(y_val, y_val_pred_rf))

"""**Logistic Regression**

"""

# Logistic Regression
log_reg = LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42)
log_reg.fit(X_train_full, y_train_full)

# Evaluate on validation set
y_val_pred_log_reg = log_reg.predict(X_val)
print("Logistic Regression Validation Results:")
print(classification_report(y_val, y_val_pred_log_reg))
print("Confusion Matrix:")
print(confusion_matrix(y_val, y_val_pred_log_reg))
print("Precision:", precision_score(y_val, y_val_pred_log_reg))
print("Recall:", recall_score(y_val, y_val_pred_log_reg))
print("F1 Score:", f1_score(y_val, y_val_pred_log_reg))
print("ROC AUC Score:", roc_auc_score(y_val, y_val_pred_log_reg))

"""**Gradient Bossting**

"""

# Gradient Boosting
gb = GradientBoostingClassifier(random_state=42)
param_grid_gb = {
    'n_estimators': [50, 100, 200],
    'learning_rate': [0.01, 0.1, 0.2],
    'max_depth': [3, 5, 7]
}

grid_search_gb = GridSearchCV(gb, param_grid_gb, cv=3, scoring='precision', n_jobs=-1)
grid_search_gb.fit(X_train_full, y_train_full)

best_gb = grid_search_gb.best_estimator_

# Evaluate on validation set
y_val_pred_gb = best_gb.predict(X_val)
print("Gradient Boosting Validation Results:")
print(classification_report(y_val, y_val_pred_gb))
print("Confusion Matrix:")
print(confusion_matrix(y_val, y_val_pred_gb))
print("Precision:", precision_score(y_val, y_val_pred_gb))
print("Recall:", recall_score(y_val, y_val_pred_gb))
print("F1 Score:", f1_score(y_val, y_val_pred_gb))
print("ROC AUC Score:", roc_auc_score(y_val, y_val_pred_gb))

"""> ###  **XG Boost**

"""

# Initialize XGBoost model
xgb = XGBClassifier(eval_metric='logloss', random_state=42)
# Define the parameter grid
param_grid_xgb = {
    'n_estimators': [50, 100, 200],
    'learning_rate': [0.01, 0.1, 0.2],
    'max_depth': [3, 5, 7]
}

# Set up GridSearchCV
grid_search_xgb = GridSearchCV(xgb, param_grid_xgb, cv=3, scoring='precision', n_jobs=-1)
grid_search_xgb.fit(X_train_full, y_train_full)

# Get the best model
best_xgb = grid_search_xgb.best_estimator_

# Evaluate on validation set
y_val_pred_xgb = best_xgb.predict(X_val)

# Print evaluation metrics
print("XGBoost Validation Results:")
print(classification_report(y_val, y_val_pred_xgb, zero_division=1))  # Handle division by zero
print("Confusion Matrix:")
print(confusion_matrix(y_val, y_val_pred_xgb))
print("Precision:", precision_score(y_val, y_val_pred_xgb, zero_division=1))
print("Recall:", recall_score(y_val, y_val_pred_xgb, zero_division=1))
print("F1 Score:", f1_score(y_val, y_val_pred_xgb, zero_division=1))
print("ROC AUC Score:", roc_auc_score(y_val, y_val_pred_xgb))

"""**Model Selection and Evaluation**

"""

# Compare precision scores of the models on the validation set
precision_scores = {
    'Logistic Regression': precision_score(y_val, y_val_pred_log_reg),
    'Random Forest': precision_score(y_val, y_val_pred_rf),
    'Gradient Boosting': precision_score(y_val, y_val_pred_gb),
    'XGBoost': precision_score(y_val, y_val_pred_xgb)
}

# Select the model with the highest precision
best_model_name = max(precision_scores, key=precision_scores.get)
best_model = {
    'Logistic Regression': log_reg,
    'Random Forest': best_rf,
    'Gradient Boosting': best_gb,
    'XGBoost': best_xgb
}[best_model_name]

print(f"The best model based on precision is: {best_model_name}")

# Evaluate the best model on the test set
best_model = best_xgb  # Replace with the best model based on validation results
y_test_pred = best_model.predict(X_test)

print("Best Model Test Results:")
print(classification_report(y_test, y_test_pred))
print("Confusion Matrix:")
print(confusion_matrix(y_test, y_test_pred))
print("Precision:", precision_score(y_test, y_test_pred))
print("Recall:", recall_score(y_test, y_test_pred))
print("F1 Score:", f1_score(y_test, y_test_pred))
print("ROC AUC Score:", roc_auc_score(y_test, y_test_pred))

"""**Feature Importance**"""

if isinstance(best_model, (RandomForestClassifier, GradientBoostingClassifier, XGBClassifier)):
    feature_importances = best_model.feature_importances_
    feature_names = X_train_full.columns
    importance_df = pd.DataFrame({'Feature': feature_names, 'Importance': feature_importances})
    importance_df = importance_df.sort_values(by='Importance', ascending=False)
    print(importance_df)

    # Plot feature importances
    plt.figure(figsize=(12, 6))
    sns.barplot(x='Importance', y='Feature', data=importance_df)
    plt.title('Feature Importances')
    plt.show()