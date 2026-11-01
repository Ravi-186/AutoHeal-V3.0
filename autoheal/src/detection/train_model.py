import os
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix
from src.detection.feature_extractor import extract_features, label_data
from src.detection.generate_dataset import generate_data

def main():
    print("--- AutoHeal Module 2: Detection Model Training ---")
    data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
    
    # 1. Clean previous data
    if os.path.exists(data_dir):
        for f in os.listdir(data_dir):
            if f.endswith(".csv"):
                os.remove(os.path.join(data_dir, f))
                
    # 2. Generate new data and get the labels
    attack_labels = generate_data()
    
    print("\nExtracting features from logs...")
    df = extract_features(data_dir)
    
    print("Applying labels...")
    df = label_data(df, attack_labels)
    
    print(f"\nTotal 1-minute windows: {len(df)}")
    print(f"Normal windows: {len(df) - df['is_attack'].sum()}")
    print(f"Attack windows: {df['is_attack'].sum()}")
    
    # 3. Train the model
    feature_cols = ['bytes_sent', 'bytes_received', 'connections', 'failed_logins', 'dns_requests', 'cpu_usage', 'mem_usage']
    
    X = df[feature_cols]
    y = df['is_attack']
    
    # Split into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print("\nTraining Random Forest Classifier...")
    clf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    clf.fit(X_train, y_train)
    
    # 4. Evaluate
    y_pred = clf.predict(X_test)
    
    print("\n--- Evaluation Metrics ---")
    print(f"Accuracy:  {accuracy_score(y_test, y_pred):.4f}")
    print(f"Precision: {precision_score(y_test, y_pred, zero_division=0):.4f}")
    print(f"Recall:    {recall_score(y_test, y_pred, zero_division=0):.4f}")
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    # 5. Save the model
    model_dir = os.path.join(os.path.dirname(__file__), "..", "..", "models")
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "rf_model.joblib")
    joblib.dump(clf, model_path)
    print(f"\nModel saved to {model_path}")

if __name__ == "__main__":
    main()
