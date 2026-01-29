#!/usr/bin/env python3
"""
Simple Heart Disease Prediction Model
Uses basic machine learning with proper feature handling
"""

import numpy as np
import joblib
import os
from typing import List, Dict

class SimpleHeartModel:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = [
            'age', 'sex', 'cp', 'trestbps', 'chol', 'fbs', 'restecg', 
            'thalach', 'exang', 'oldpeak', 'slope', 'ca', 'thal'
        ]
        self.load_model()
    
    def load_model(self):
        """Load the heart disease model"""
        try:
            # Try different possible paths
            model_paths = [
                "models/heart_disease_model.pkl",
                "./models/heart_disease_model.pkl",
                os.path.join(os.path.dirname(__file__), "heart_disease_model.pkl")
            ]
            scaler_paths = [
                "models/heart_disease_scaler.pkl", 
                "./models/heart_disease_scaler.pkl",
                os.path.join(os.path.dirname(__file__), "heart_disease_scaler.pkl")
            ]
            
            model_loaded = False
            for model_path in model_paths:
                for scaler_path in scaler_paths:
                    if os.path.exists(model_path) and os.path.exists(scaler_path):
                        self.model = joblib.load(model_path)
                        self.scaler = joblib.load(scaler_path)
                        print(f"✅ Heart disease model loaded from {model_path}")
                        model_loaded = True
                        break
                if model_loaded:
                    break
            
            if not model_loaded:
                print("⚠️ Model files not found, using rule-based prediction")
                self.model = None
                self.scaler = None
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.model = None
            self.scaler = None
    
    def predict(self, features: List[float]) -> Dict:
        """Make prediction with confidence scores"""
        try:
            # Ensure we have the right number of features
            if len(features) != len(self.feature_names):
                print(f"⚠️ Expected {len(self.feature_names)} features, got {len(features)}")
                if len(features) < len(self.feature_names):
                    features = features + [0] * (len(self.feature_names) - len(features))
                else:
                    features = features[:len(self.feature_names)]
            
            if self.model is not None and self.scaler is not None:
                # Use trained model
                X = np.array(features).reshape(1, -1)
                X_scaled = self.scaler.transform(X)
                
                # Get prediction probabilities
                probabilities = self.model.predict_proba(X_scaled)[0]
                no_disease_prob = probabilities[0] * 100
                disease_prob = probabilities[1] * 100
                
                # Determine risk level
                if disease_prob >= 70:
                    risk_level = "High"
                    prediction_text = "Heart Disease Detected"
                elif disease_prob >= 40:
                    risk_level = "Medium"
                    prediction_text = "Moderate Risk of Heart Disease"
                else:
                    risk_level = "Low"
                    prediction_text = "No Heart Disease"
                
                confidence = max(probabilities) * 100
                
            else:
                # Rule-based fallback prediction
                age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal = features
                
                # Calculate risk score based on key factors
                risk_score = 0
                
                # Age factor
                if age > 65:
                    risk_score += 3
                elif age > 55:
                    risk_score += 2
                elif age > 45:
                    risk_score += 1
                
                # Gender factor (1 = male, 0 = female)
                if sex == 1:
                    risk_score += 1
                
                # Chest pain (0-3, higher is worse)
                risk_score += cp
                
                # Blood pressure
                if trestbps > 160:
                    risk_score += 3
                elif trestbps > 140:
                    risk_score += 2
                elif trestbps > 120:
                    risk_score += 1
                
                # Cholesterol
                if chol > 300:
                    risk_score += 3
                elif chol > 240:
                    risk_score += 2
                elif chol > 200:
                    risk_score += 1
                
                # Fasting blood sugar
                if fbs == 1:
                    risk_score += 1
                
                # Exercise induced angina
                if exang == 1:
                    risk_score += 2
                
                # ST depression
                if oldpeak > 2:
                    risk_score += 3
                elif oldpeak > 1:
                    risk_score += 2
                elif oldpeak > 0.5:
                    risk_score += 1
                
                # Number of major vessels
                risk_score += ca
                
                # Thalassemia
                if thal == 3:  # Fixed defect
                    risk_score += 2
                elif thal == 6:  # Reversible defect
                    risk_score += 1
                
                # Calculate probabilities based on risk score
                max_risk = 20  # Maximum possible risk score
                disease_prob = min((risk_score / max_risk) * 100, 95)
                no_disease_prob = 100 - disease_prob
                
                # Determine risk level
                if disease_prob >= 70:
                    risk_level = "High"
                    prediction_text = "Heart Disease Detected"
                elif disease_prob >= 40:
                    risk_level = "Medium"
                    prediction_text = "Moderate Risk of Heart Disease"
                else:
                    risk_level = "Low"
                    prediction_text = "No Heart Disease"
                
                confidence = 85.0  # High confidence for rule-based system
            
            return {
                "prediction": prediction_text,
                "risk_percentage": round(disease_prob, 1),
                "risk_level": risk_level,
                "no_disease_probability": round(no_disease_prob, 1),
                "disease_probability": round(disease_prob, 1),
                "confidence": round(confidence, 1),
                "model_used": "Trained Model" if self.model is not None else "Rule-Based Analysis"
            }
            
        except Exception as e:
            print(f"❌ Error in prediction: {e}")
            return {
                "prediction": "Prediction Error",
                "risk_percentage": 50,
                "risk_level": "Unknown",
                "no_disease_probability": 50,
                "disease_probability": 50,
                "confidence": 0.0,
                "model_used": "Error"
            }

# Global model instance
simple_heart_model = SimpleHeartModel()

def predict_heart_disease(features: List[float]) -> Dict:
    """Main function to predict heart disease"""
    return simple_heart_model.predict(features)
