# ml/model.py
from sklearn.ensemble import IsolationForest
import pandas as pd

class AnomalyDetector:
    def __init__(self, contamination=0.1):
        self.model = IsolationForest(contamination=contamination, random_state=42)

    def train(self, df: pd.DataFrame, features: list):
        self.features = features
        self.model.fit(df[features])

    def predict(self, df: pd.DataFrame):
        if not hasattr(self, 'features'):
            raise ValueError("Model has not been trained yet.") 
        scores = self.model.decision_function(df[self.features])
        labels = self.model.predict(df[self.features])
        df = df.copy()
        df['anomaly_score'] = scores
        df['is_anomaly'] = labels == -1
        return df