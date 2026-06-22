import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import IsolationForest

class MLAnomalyDetector:
    def __init__(self):
        """
        Initializes the TF-IDF Vectorizer and Isolation Forest for anomaly detection.
        """
        self.vectorizer = TfidfVectorizer(max_features=1000)
        # contamination represents the proportion of outliers in the data set
        self.clf = IsolationForest(contamination=0.1, random_state=42)
        
    def analyze_batch(self, documents: list[str]) -> list[dict]:
        """
        Analyzes a batch of text documents and identifies anomalies (outliers).
        
        Args:
            documents: List of full text extracted from PDFs.
            
        Returns:
            List of dictionaries containing the anomaly score and status for each document.
        """
        if len(documents) < 3:
            # Not enough data to confidently detect anomalies using ML
            return [{"is_anomaly": False, "score": 0.0, "reason": "샘플 부족(최소 3개 이상 필요)"} for _ in documents]
            
        try:
            # 1. Vectorize text (TF-IDF)
            X = self.vectorizer.fit_transform(documents).toarray()
            
            # 2. Fit the model and predict
            # Returns 1 for inliers, -1 for outliers
            predictions = self.clf.fit_predict(X)
            
            # 3. Get anomaly scores (lower is more anomalous)
            # decision_function returns average anomaly score of X of the base classifiers.
            # The anomaly score of an input sample is computed as the mean anomaly score of the trees in the forest.
            scores = self.clf.decision_function(X)
            
            results = []
            for pred, score in zip(predictions, scores):
                is_anomaly = (pred == -1)
                
                # Normalize score for UI (0 to 100, where 100 is highly anomalous)
                # decision_function gives negative for anomalies, positive for normal
                # Let's map it: negative scores map to higher anomaly percentage
                normalized_score = max(0.0, min(100.0, -score * 500 + 50))
                
                reason = "머신러닝(Isolation Forest) 군집 분석 결과 정상 패턴 이탈" if is_anomaly else "정상 패턴"
                
                results.append({
                    "is_anomaly": bool(is_anomaly),
                    "score": float(normalized_score),
                    "reason": reason
                })
                
            return results
        except Exception as e:
            return [{"is_anomaly": False, "score": 0.0, "reason": f"ML 분석 오류: {str(e)}"} for _ in documents]
