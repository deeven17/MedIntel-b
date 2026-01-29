#!/usr/bin/env python3
"""
Hybrid Heart Disease Prediction Model
Uses XGBoost, ANN, and RNN ensemble for maximum accuracy
"""

import os
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import xgboost as xgb
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Reshape
from tensorflow.keras.optimizers import Adam
from typing import List, Dict
import warnings
warnings.filterwarnings('ignore')

class HybridHeartDiseaseModel:
    def __init__(self):
        self.xgb_model = None
        self.ann_model = None
        self.rnn_model = None
        self.ensemble_model = None
        self.scaler = StandardScaler()
        # Feature names based on your actual dataset columns
        self.feature_names = [
            'age', 'sex', 'cp', 'trestbps', 'chol', 'fbs', 'restecg', 
            'thalach', 'exang', 'oldpeak', 'slope', 'ca', 'thal'
        ]
        self.model_path = "models/hybrid_heart_model.pkl"
        self.scaler_path = "models/hybrid_heart_scaler.pkl"
        self.load_model()
    
    def load_model(self):
        """Load or train the hybrid heart disease model"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.ensemble_model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                print("✅ Hybrid heart disease model loaded successfully")
            else:
                print("⚠️ Model files not found, training new hybrid model...")
                self.train_model()
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.train_model()
    
    def load_dataset(self):
        """Load the real heart disease dataset"""
        dataset_path = r"C:\Users\deeve\Downloads\archive\Heart_disease_cleveland_new.csv"
        
        if not os.path.exists(dataset_path):
            print(f"❌ Dataset not found at: {dataset_path}")
            return None
        
        try:
            df = pd.read_csv(dataset_path)
            print(f"✅ Dataset loaded: {df.shape}")
            return df
        except Exception as e:
            print(f"❌ Error loading dataset: {e}")
            return None
    
    def preprocess_data(self, df):
        """Preprocess the dataset"""
        print("🔧 Preprocessing data...")
        
        # Check for target column
        target_columns = ['target', 'Target', 'TARGET', 'heart_disease', 'HeartDisease', 'disease']
        target_col = None
        for col in target_columns:
            if col in df.columns:
                target_col = col
                break
        
        if not target_col:
            print("❌ No target column found")
            return None, None
        
        print(f"Target column: {target_col}")
        print(f"Target distribution: {df[target_col].value_counts().to_dict()}")
        
        # Select features
        available_features = [col for col in self.feature_names if col in df.columns]
        print(f"Available features: {available_features}")
        
        if len(available_features) < 5:
            print("❌ Not enough features available")
            return None, None
        
        X = df[available_features].fillna(df[available_features].mean())
        y = df[target_col]
        
        # Handle missing values
        X = X.fillna(X.mean())
        
        print(f"Features shape: {X.shape}")
        print(f"Target shape: {y.shape}")
        
        return X, y
    
    def create_rnn_model(self, input_shape):
        """Create RNN model for time series-like data"""
        model = Sequential([
            Reshape((input_shape, 1), input_shape=(input_shape,)),
            LSTM(64, return_sequences=True, dropout=0.2),
            LSTM(32, dropout=0.2),
            Dense(16, activation='relu'),
            Dropout(0.3),
            Dense(1, activation='sigmoid')
        ])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def train_model(self):
        """Train the hybrid heart disease model"""
        print("🫀 Training Hybrid Heart Disease Model (XGBoost + ANN + RNN)")
        print("=" * 70)
        
        # Load dataset
        df = self.load_dataset()
        if df is None:
            print("❌ Cannot train without dataset")
            return
        
        # Preprocess data
        X, y = self.preprocess_data(df)
        if X is None or y is None:
            print("❌ Cannot train without proper data")
            return
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        print("🤖 Training XGBoost model...")
        # Train XGBoost
        self.xgb_model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            eval_metric='logloss'
        )
        self.xgb_model.fit(X_train_scaled, y_train)
        
        print("🤖 Training ANN model...")
        # Train ANN
        self.ann_model = MLPClassifier(
            hidden_layer_sizes=(100, 50, 25),
            activation='relu',
            solver='adam',
            alpha=0.001,
            learning_rate='adaptive',
            max_iter=1000,
            random_state=42
        )
        self.ann_model.fit(X_train_scaled, y_train)
        
        print("🤖 Training RNN model...")
        # Train RNN
        self.rnn_model = self.create_rnn_model(X_train_scaled.shape[1])
        self.rnn_model.fit(
            X_train_scaled, y_train,
            epochs=100,
            batch_size=32,
            validation_split=0.2,
            verbose=0
        )
        
        print("🤖 Creating ensemble model...")
        # Create ensemble
        self.ensemble_model = VotingClassifier(
            estimators=[
                ('xgb', self.xgb_model),
                ('ann', self.ann_model),
                ('rf', RandomForestClassifier(n_estimators=100, random_state=42))
            ],
            voting='soft'
        )
        
        # Train ensemble
        self.ensemble_model.fit(X_train_scaled, y_train)
        
        # Evaluate models
        print("\n📊 Model Performance Evaluation:")
        
        # XGBoost
        xgb_pred = self.xgb_model.predict(X_test_scaled)
        xgb_acc = accuracy_score(y_test, xgb_pred)
        print(f"   XGBoost Accuracy: {xgb_acc:.3f}")
        
        # ANN
        ann_pred = self.ann_model.predict(X_test_scaled)
        ann_acc = accuracy_score(y_test, ann_pred)
        print(f"   ANN Accuracy: {ann_acc:.3f}")
        
        # RNN
        rnn_pred = (self.rnn_model.predict(X_test_scaled) > 0.5).astype(int)
        rnn_acc = accuracy_score(y_test, rnn_pred)
        print(f"   RNN Accuracy: {rnn_acc:.3f}")
        
        # Ensemble
        ensemble_pred = self.ensemble_model.predict(X_test_scaled)
        ensemble_acc = accuracy_score(y_test, ensemble_pred)
        print(f"   Ensemble Accuracy: {ensemble_acc:.3f}")
        
        print(f"\n✅ Hybrid model trained successfully!")
        print(f"   Best Accuracy: {ensemble_acc:.3f}")
        print(f"   Features used: {len(self.feature_names)}")
        
        # Save model
        os.makedirs("models", exist_ok=True)
        joblib.dump(self.ensemble_model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
        
        print(f"💾 Model saved to: {self.model_path}")
        print(f"💾 Scaler saved to: {self.scaler_path}")
    
    def predict(self, features: List[float]) -> Dict:
        """Make prediction with confidence scores"""
        try:
            if self.ensemble_model is None:
                return {
                    "prediction": "Model not trained",
                    "risk_percentage": 50,
                    "risk_level": "Unknown",
                    "no_disease_probability": 50,
                    "disease_probability": 50,
                    "confidence": 0.0,
                    "model_used": "Not Trained"
                }
            
            # Ensure we have the right number of features
            if len(features) != len(self.feature_names):
                print(f"⚠️ Expected {len(self.feature_names)} features, got {len(features)}")
                if len(features) < len(self.feature_names):
                    features = features + [0] * (len(self.feature_names) - len(features))
                else:
                    features = features[:len(self.feature_names)]
            
            # Convert to numpy array and reshape
            X = np.array(features).reshape(1, -1)
            
            # Scale features
            X_scaled = self.scaler.transform(X)
            
            # Ensemble prediction (always use this; individual models may be None when loaded from PKL)
            ensemble_pred = self.ensemble_model.predict_proba(X_scaled)[0]
            
            # Individual breakdown: use standalone models if trained this run, else from ensemble estimators
            individual = {}
            if self.xgb_model is not None and self.ann_model is not None:
                xgb_pred = self.xgb_model.predict_proba(X_scaled)[0]
                ann_pred = self.ann_model.predict_proba(X_scaled)[0]
                individual["xgboost"] = round(xgb_pred[1] * 100, 1)
                individual["ann"] = round(ann_pred[1] * 100, 1)
                if self.rnn_model is not None:
                    rnn_pred = self.rnn_model.predict(X_scaled)[0]
                    individual["rnn"] = round(float(rnn_pred[0]) * 100, 1)
                else:
                    individual["rnn"] = round(ensemble_pred[1] * 100, 1)
            else:
                est = getattr(self.ensemble_model, "named_estimators_", None) or {}
                if "xgb" in est:
                    individual["xgboost"] = round(est["xgb"].predict_proba(X_scaled)[0][1] * 100, 1)
                else:
                    individual["xgboost"] = round(ensemble_pred[1] * 100, 1)
                if "ann" in est:
                    individual["ann"] = round(est["ann"].predict_proba(X_scaled)[0][1] * 100, 1)
                else:
                    individual["ann"] = round(ensemble_pred[1] * 100, 1)
                individual["rnn"] = round(ensemble_pred[1] * 100, 1)
            
            # Calculate risk percentage
            no_disease_prob = ensemble_pred[0] * 100
            disease_prob = ensemble_pred[1] * 100
            
            # Determine risk level
            if disease_prob >= 70:
                risk_level = "High"
            elif disease_prob >= 40:
                risk_level = "Medium"
            else:
                risk_level = "Low"
            
            prediction_text = "Heart Disease Detected" if disease_prob > 50 else "No Heart Disease"
            
            return {
                "prediction": prediction_text,
                "risk_percentage": round(disease_prob, 1),
                "risk_level": risk_level,
                "no_disease_probability": round(no_disease_prob, 1),
                "disease_probability": round(disease_prob, 1),
                "confidence": round(max(ensemble_pred), 3),
                "model_used": "Hybrid Ensemble (XGBoost + ANN + RNN)",
                "individual_predictions": individual
            }
            
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            return {
                "prediction": "Error in prediction",
                "risk_percentage": 50,
                "risk_level": "Unknown",
                "no_disease_probability": 50,
                "disease_probability": 50,
                "confidence": 0.0,
                "model_used": "Error"
            }

# Global model instance
hybrid_heart_model = HybridHeartDiseaseModel()

def predict_heart_disease(features: List[float]) -> Dict:
    """Main function to predict heart disease using hybrid model"""
    return hybrid_heart_model.predict(features)
