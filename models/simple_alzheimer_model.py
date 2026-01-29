#!/usr/bin/env python3
"""
Simple Alzheimer's Disease Prediction Model
Uses basic machine learning with proper feature handling
"""

import numpy as np
import joblib
import os
from typing import List, Dict

class SimpleAlzheimerModel:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.feature_names = ['age', 'educ', 'ses', 'mmse', 'etiv', 'nwbv', 'asf']
        self.load_model()
    
    def load_model(self):
        """Load the Alzheimer's model"""
        try:
            # Try different possible paths
            model_paths = [
                "models/alzheimer_model.pkl",
                "./models/alzheimer_model.pkl",
                os.path.join(os.path.dirname(__file__), "alzheimer_model.pkl")
            ]
            scaler_paths = [
                "models/alzheimer_scaler.pkl",
                "./models/alzheimer_scaler.pkl", 
                os.path.join(os.path.dirname(__file__), "alzheimer_scaler.pkl")
            ]
            encoder_paths = [
                "models/alzheimer_label_encoder.pkl",
                "./models/alzheimer_label_encoder.pkl",
                os.path.join(os.path.dirname(__file__), "alzheimer_label_encoder.pkl")
            ]
            
            model_loaded = False
            for model_path in model_paths:
                for scaler_path in scaler_paths:
                    for encoder_path in encoder_paths:
                        if os.path.exists(model_path) and os.path.exists(scaler_path) and os.path.exists(encoder_path):
                            self.model = joblib.load(model_path)
                            self.scaler = joblib.load(scaler_path)
                            self.label_encoder = joblib.load(encoder_path)
                            print(f"✅ Alzheimer's model loaded from {model_path}")
                            model_loaded = True
                            break
                    if model_loaded:
                        break
                if model_loaded:
                    break
            
            if not model_loaded:
                print("⚠️ Model files not found, using rule-based prediction")
                self.model = None
                self.scaler = None
                self.label_encoder = None
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.model = None
            self.scaler = None
            self.label_encoder = None
    
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
            
            age, educ, ses, mmse, etiv, nwbv, asf = features
            
            if self.model is not None and self.scaler is not None and self.label_encoder is not None:
                # Use trained model
                X = np.array(features).reshape(1, -1)
                X_scaled = self.scaler.transform(X)
                
                # Get prediction probabilities
                probabilities = self.model.predict_proba(X_scaled)[0]
                prediction_class = self.model.predict(X_scaled)[0]
                
                # Decode the prediction
                severity_levels = self.label_encoder.classes_
                predicted_severity = severity_levels[prediction_class]
                
                # Calculate individual probabilities
                normal_prob = probabilities[0] * 100 if len(probabilities) > 0 else 0
                mild_prob = probabilities[1] * 100 if len(probabilities) > 1 else 0
                moderate_prob = probabilities[2] * 100 if len(probabilities) > 2 else 0
                severe_prob = probabilities[3] * 100 if len(probabilities) > 3 else 0
                
                # Calculate overall risk percentage
                risk_percentage = mild_prob + moderate_prob + severe_prob
                
                # Determine risk level
                if risk_percentage >= 70:
                    risk_level = "High"
                elif risk_percentage >= 40:
                    risk_level = "Medium"
                else:
                    risk_level = "Low"
                
                confidence = max(probabilities) * 100
                
            else:
                # Rule-based fallback prediction based on MMSE score and other factors
                risk_score = 0
                
                # MMSE score is the most important factor (0-30, lower is worse)
                if mmse < 10:
                    risk_score += 4
                    predicted_severity = "Severe"
                elif mmse < 18:
                    risk_score += 3
                    predicted_severity = "Moderate"
                elif mmse < 24:
                    risk_score += 2
                    predicted_severity = "Mild"
                else:
                    risk_score += 0
                    predicted_severity = "Normal"
                
                # Age factor
                if age > 80:
                    risk_score += 2
                elif age > 70:
                    risk_score += 1
                elif age > 60:
                    risk_score += 0.5
                
                # Education level (higher education = lower risk)
                if educ < 8:
                    risk_score += 1
                elif educ < 12:
                    risk_score += 0.5
                
                # Socioeconomic status (lower SES = higher risk)
                if ses < 2:
                    risk_score += 1
                elif ses < 3:
                    risk_score += 0.5
                
                # Brain volume factors
                if nwbv < 0.7:  # Normalized whole brain volume
                    risk_score += 1
                
                if etiv > 1500:  # Estimated total intracranial volume
                    risk_score += 0.5
                
                # Calculate probabilities based on risk score
                max_risk = 10
                risk_percentage = min((risk_score / max_risk) * 100, 95)
                
                # Calculate individual probabilities
                if predicted_severity == "Severe":
                    severe_prob = risk_percentage
                    moderate_prob = 0
                    mild_prob = 0
                    normal_prob = 100 - risk_percentage
                elif predicted_severity == "Moderate":
                    severe_prob = risk_percentage * 0.3
                    moderate_prob = risk_percentage * 0.7
                    mild_prob = 0
                    normal_prob = 100 - risk_percentage
                elif predicted_severity == "Mild":
                    severe_prob = 0
                    moderate_prob = risk_percentage * 0.2
                    mild_prob = risk_percentage * 0.8
                    normal_prob = 100 - risk_percentage
                else:  # Normal
                    severe_prob = 0
                    moderate_prob = 0
                    mild_prob = risk_percentage * 0.1
                    normal_prob = 100 - risk_percentage
                
                # Determine risk level
                if risk_percentage >= 70:
                    risk_level = "High"
                elif risk_percentage >= 40:
                    risk_level = "Medium"
                else:
                    risk_level = "Low"
                
                confidence = 85.0  # High confidence for rule-based system
            
            # Format prediction text
            if predicted_severity == "Normal":
                prediction_text = "No Alzheimer's Disease"
            elif predicted_severity == "Mild":
                prediction_text = "Mild Cognitive Impairment"
            elif predicted_severity == "Moderate":
                prediction_text = "Moderate Alzheimer's Disease"
            else:
                prediction_text = "Severe Alzheimer's Disease"
            
            return {
                "prediction": prediction_text,
                "risk_percentage": round(risk_percentage, 1),
                "risk_level": risk_level,
                "severity_level": predicted_severity,
                "confidence": round(confidence, 1),
                "model_used": "Trained Model" if self.model is not None else "Rule-Based Analysis",
                "mild_probability": round(mild_prob, 1),
                "moderate_probability": round(moderate_prob, 1),
                "severe_probability": round(severe_prob, 1),
                "normal_probability": round(normal_prob, 1)
            }
            
        except Exception as e:
            print(f"❌ Error in prediction: {e}")
            return {
                "prediction": "Prediction Error",
                "risk_percentage": 50,
                "risk_level": "Unknown",
                "severity_level": "Unknown",
                "confidence": 0.0,
                "model_used": "Error",
                "mild_probability": 0,
                "moderate_probability": 0,
                "severe_probability": 0,
                "normal_probability": 100
            }

# Global model instance
simple_alzheimer_model = SimpleAlzheimerModel()

def predict_alzheimer_disease(features: List[float]) -> Dict:
    """Main function to predict Alzheimer's disease"""
    return simple_alzheimer_model.predict(features)
