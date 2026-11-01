import os
import joblib
import pandas as pd

import warnings

class DetectionModel:
    def __init__(self, model_path=None):
        if model_path is None:
            model_path = os.path.join(os.path.dirname(__file__), "..", "..", "models", "rf_model.joblib")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}. Please run train_model.py first.")
            
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            self.model = joblib.load(model_path)
            
        # Expected features in this exact order
        self.feature_cols = [
            'bytes_sent', 'bytes_received', 'connections', 
            'failed_logins', 'dns_requests', 'cpu_usage', 'mem_usage'
        ]

    def predict(self, features_dict, threshold=0.45):
        """
        Takes a dictionary of recent activity features for a device and returns a threat score.
        Uses ensemble probability with calibrated threshold and defense-in-depth SOC heuristics.
        
        Returns:
            is_threat (bool): True if attack detected.
            score (float): Probability score of the attack (0.0 to 1.0)
        """
        df = pd.DataFrame([features_dict])
        
        # Ensure missing columns are filled with 0 and order is correct
        for col in self.feature_cols:
            if col not in df.columns:
                df[col] = 0.0
                
        df = df[self.feature_cols]
        
        # Predict probability of attack (class 1)
        probs = self.model.predict_proba(df)[0]
        score = float(probs[1]) if len(probs) > 1 else 0.0
        
        # Enterprise Defense-in-Depth Heuristics (Security Guardrails)
        heuristic_triggered = False
        failed_logins = float(features_dict.get('failed_logins', 0))
        bytes_sent = float(features_dict.get('bytes_sent', 0))
        connections = float(features_dict.get('connections', 0))
        dns_reqs = float(features_dict.get('dns_requests', 0))
        cpu = float(features_dict.get('cpu_usage', 0))
        mem = float(features_dict.get('mem_usage', 0))
        
        if failed_logins >= 5 or (failed_logins >= 3 and bytes_sent > 10000):
            heuristic_triggered = True
        elif connections >= 15:
            heuristic_triggered = True
        elif bytes_sent >= 100000:
            heuristic_triggered = True
        elif dns_reqs >= 10:
            heuristic_triggered = True
        elif cpu >= 80.0 and mem >= 80.0:
            heuristic_triggered = True
            
        if heuristic_triggered:
            score = max(score, 0.85)
            
        is_threat = bool(score >= threshold or heuristic_triggered)
        return is_threat, score
