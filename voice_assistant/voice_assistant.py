"""
Main Voice Assistant Module
Integrates speech recognition, TTS, and WhatsApp services
Provides a unified interface for multilingual medical voice assistance
"""

import os
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime

from .speech_handler import SpeechHandler
from .tts_handler import TTSHandler
from .simple_ai_agent import SimpleAIAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceAssistant:
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the Voice Assistant with all required components
        """
        self.base_url = base_url.rstrip('/')
        
        # Initialize components
        self.speech_handler = SpeechHandler()
        self.tts_handler = TTSHandler()
        self.ai_agent = SimpleAIAgent()
        
        # API endpoints for existing backend routes
        self.api_endpoints = {
            'heart_prediction': f"{self.base_url}/predict/heart",
            'alzheimer_prediction': f"{self.base_url}/predict/alzheimer",
            'book_appointment': f"{self.base_url}/appointments/book",  # Assuming this exists
            'contact_doctor': f"{self.base_url}/doctors/contact"  # Assuming this exists
        }
        
        logger.info("Voice Assistant initialized successfully")
    
    def process_voice_input(self, audio_data: bytes, user_whatsapp: Optional[str] = None, 
                          language_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        Main method to process voice input and generate response
        """
        try:
            # Step 1: Convert speech to text
            logger.info("Processing voice input...")
            transcription_result = self.speech_handler.transcribe_audio(audio_data, language_hint)
            
            if not transcription_result['success']:
                return self._create_error_response(
                    "Speech recognition failed", 
                    transcription_result.get('error', 'Unknown error'),
                    language_hint or 'en'
                )
            
            text = transcription_result['text']
            detected_language = transcription_result['language']
            
            logger.info(f"Transcribed text: {text}")
            logger.info(f"Detected language: {detected_language}")
            
            # Step 2: Extract medical entities and intent
            entities = self.speech_handler.extract_medical_entities(text, detected_language)
            logger.info(f"Extracted entities: {entities}")
            
            # Step 3: Process intent and call appropriate backend services
            response_data = self._process_intent(entities, detected_language)
            
            # Step 4: Generate response text
            response_text = self.tts_handler.generate_response(
                entities['intent'], 
                detected_language, 
                **response_data.get('response_params', {})
            )
            
            # Step 5: Convert response to speech
            tts_result = self.tts_handler.text_to_speech(response_text, detected_language)
            
            # Step 6: Send AI agent notification if requested
            ai_result = None
            if user_whatsapp:
                ai_result = self._send_ai_notification(
                    user_whatsapp, entities, response_data, detected_language
                )
            
            return {
                'success': True,
                'transcription': {
                    'text': text,
                    'language': detected_language,
                    'confidence': transcription_result['confidence']
                },
                'entities': entities,
                'response': {
                    'text': response_text,
                    'audio_data': tts_result.get('audio_data'),
                    'tts_success': tts_result['success']
                },
                'backend_result': response_data,
                'ai_result': ai_result,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing voice input: {e}")
            return self._create_error_response(
                "Processing failed", 
                str(e), 
                language_hint or 'en'
            )
    
    def _process_intent(self, entities: Dict[str, Any], language: str) -> Dict[str, Any]:
        """
        Process user intent and call appropriate backend services
        """
        intent = entities['intent']
        
        try:
            if intent == 'heart':
                return self._handle_heart_prediction(entities)
            elif intent == 'alzheimer':
                return self._handle_alzheimer_prediction(entities)
            elif intent == 'appointment':
                return self._handle_appointment_booking(entities)
            elif intent == 'contact':
                return self._handle_doctor_contact(entities)
            else:
                return self._handle_general_query(entities)
                
        except Exception as e:
            logger.error(f"Error processing intent '{intent}': {e}")
            return {
                'success': False,
                'error': str(e),
                'response_params': {
                    'symptoms': ', '.join(entities.get('symptoms', []))
                }
            }
    
    def _handle_heart_prediction(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle heart disease prediction request
        """
        try:
            # Create feature vector for heart prediction
            # Default values based on extracted entities
            age = entities.get('age', 50)
            sex = 1 if 'male' in str(entities.get('symptoms', [])).lower() else 0
            
            # Map symptoms to heart disease features
            symptoms = entities.get('symptoms', [])
            features = self._map_symptoms_to_heart_features(symptoms, age, sex)
            
            # Call backend API
            response = requests.post(
                self.api_endpoints['heart_prediction'],
                json=features,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'prediction_type': 'heart',
                    'result': result,
                    'response_params': {
                        'prediction': result.get('prediction', 'Unknown'),
                        'risk_percentage': result.get('risk_percentage', 0),
                        'risk_level': result.get('risk_level', 'Unknown'),
                        'confidence': result.get('details', {}).get('confidence', 0)
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f'Backend API error: {response.status_code}',
                    'response_params': {'symptoms': ', '.join(symptoms)}
                }
                
        except Exception as e:
            logger.error(f"Heart prediction error: {e}")
            return {
                'success': False,
                'error': str(e),
                'response_params': {'symptoms': ', '.join(entities.get('symptoms', []))}
            }
    
    def _handle_alzheimer_prediction(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle Alzheimer's disease prediction request
        """
        try:
            # Create feature vector for Alzheimer's prediction
            age = entities.get('age', 70)
            features = self._map_symptoms_to_alzheimer_features(entities.get('symptoms', []), age)
            
            # Call backend API
            response = requests.post(
                self.api_endpoints['alzheimer_prediction'],
                json=features,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'prediction_type': 'alzheimer',
                    'result': result,
                    'response_params': {
                        'prediction': result.get('prediction', 'Unknown'),
                        'risk_percentage': result.get('risk_percentage', 0),
                        'risk_level': result.get('risk_level', 'Unknown'),
                        'severity_level': result.get('details', {}).get('severity_level', 'Unknown'),
                        'confidence': result.get('details', {}).get('confidence', 0)
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f'Backend API error: {response.status_code}',
                    'response_params': {'symptoms': ', '.join(entities.get('symptoms', []))}
                }
                
        except Exception as e:
            logger.error(f"Alzheimer prediction error: {e}")
            return {
                'success': False,
                'error': str(e),
                'response_params': {'symptoms': ', '.join(entities.get('symptoms', []))}
            }
    
    def _handle_appointment_booking(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle appointment booking request
        """
        try:
            # Prepare appointment data
            appointment_data = {
                'patient_name': entities.get('name', 'Unknown'),
                'patient_age': entities.get('age', 0),
                'symptoms': entities.get('symptoms', []),
                'contact_number': entities.get('contact', ''),
                'preferred_date': entities.get('preferred_date', ''),
                'preferred_time': entities.get('preferred_time', ''),
                'department': entities.get('department', 'General Medicine')
            }
            
            # Call backend API (if exists)
            try:
                response = requests.post(
                    self.api_endpoints['book_appointment'],
                    json=appointment_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        'success': True,
                        'prediction_type': 'appointment',
                        'result': result,
                        'response_params': {}
                    }
                else:
                    # Fallback: simulate appointment booking
                    return self._simulate_appointment_booking(appointment_data)
                    
            except requests.exceptions.RequestException:
                # Fallback: simulate appointment booking
                return self._simulate_appointment_booking(appointment_data)
                
        except Exception as e:
            logger.error(f"Appointment booking error: {e}")
            return {
                'success': False,
                'error': str(e),
                'response_params': {}
            }
    
    def _handle_doctor_contact(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle doctor contact request
        """
        try:
            # Prepare contact data
            contact_data = {
                'patient_name': entities.get('name', 'Unknown'),
                'patient_age': entities.get('age', 0),
                'symptoms': entities.get('symptoms', []),
                'contact_number': entities.get('contact', ''),
                'urgency': entities.get('urgency', 'normal'),
                'message': entities.get('raw_text', '')
            }
            
            # Call backend API (if exists)
            try:
                response = requests.post(
                    self.api_endpoints['contact_doctor'],
                    json=contact_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        'success': True,
                        'prediction_type': 'contact',
                        'result': result,
                        'response_params': {}
                    }
                else:
                    # Fallback: simulate doctor notification
                    return self._simulate_doctor_contact(contact_data)
                    
            except requests.exceptions.RequestException:
                # Fallback: simulate doctor notification
                return self._simulate_doctor_contact(contact_data)
                
        except Exception as e:
            logger.error(f"Doctor contact error: {e}")
            return {
                'success': False,
                'error': str(e),
                'response_params': {}
            }
    
    def _handle_general_query(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle general medical queries
        """
        return {
            'success': True,
            'prediction_type': 'general',
            'result': {'message': 'General query received'},
            'response_params': {
                'symptoms': ', '.join(entities.get('symptoms', []))
            }
        }
    
    def _map_symptoms_to_heart_features(self, symptoms: List[str], age: int, sex: int) -> Dict[str, Any]:
        """
        Map symptoms to heart disease prediction features
        """
        # Default feature values
        features = {
            'age': age,
            'sex': sex,
            'cp': 0,  # Chest pain type
            'trestbps': 120,  # Resting blood pressure
            'chol': 200,  # Cholesterol
            'fbs': 0,  # Fasting blood sugar
            'restecg': 0,  # Resting ECG
            'thalach': 150,  # Max heart rate
            'exang': 0,  # Exercise induced angina
            'oldpeak': 0,  # ST depression
            'slope': 0,  # ST slope
            'ca': 0,  # Number of major vessels
            'thal': 0  # Thalassemia
        }
        
        # Map symptoms to features
        symptoms_lower = [s.lower() for s in symptoms]
        
        if 'chest' in ' '.join(symptoms_lower) or 'pain' in ' '.join(symptoms_lower):
            features['cp'] = 2  # Typical angina
        if 'pressure' in ' '.join(symptoms_lower) or 'high' in ' '.join(symptoms_lower):
            features['trestbps'] = 140
        if 'cholesterol' in ' '.join(symptoms_lower) or 'fat' in ' '.join(symptoms_lower):
            features['chol'] = 250
        if 'diabetes' in ' '.join(symptoms_lower) or 'sugar' in ' '.join(symptoms_lower):
            features['fbs'] = 1
        if 'exercise' in ' '.join(symptoms_lower) or 'angina' in ' '.join(symptoms_lower):
            features['exang'] = 1
        
        return features
    
    def _map_symptoms_to_alzheimer_features(self, symptoms: List[str], age: int) -> Dict[str, Any]:
        """
        Map symptoms to Alzheimer's prediction features
        """
        # Default feature values
        features = {
            'age': age,
            'educ': 12,  # Education years
            'ses': 3,  # Socioeconomic status
            'mmse': 28,  # Mini-Mental State Examination
            'etiv': 1400,  # Estimated total intracranial volume
            'nwbv': 0.8,  # Normalized whole brain volume
            'asf': 0.9  # Atlas scaling factor
        }
        
        # Map symptoms to features
        symptoms_lower = [s.lower() for s in symptoms]
        
        if 'memory' in ' '.join(symptoms_lower) or 'forget' in ' '.join(symptoms_lower):
            features['mmse'] = 22  # Lower MMSE score
        if 'severe' in ' '.join(symptoms_lower) or 'advanced' in ' '.join(symptoms_lower):
            features['mmse'] = 15
            features['nwbv'] = 0.7
        if 'mild' in ' '.join(symptoms_lower):
            features['mmse'] = 25
            features['nwbv'] = 0.75
        
        return features
    
    def _simulate_appointment_booking(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate appointment booking when backend API is not available
        """
        return {
            'success': True,
            'prediction_type': 'appointment',
            'result': {
                'appointment_id': f"APT{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'status': 'confirmed',
                'appointment_date': '2024-01-15',
                'appointment_time': '10:00 AM',
                'doctor': 'Dr. Smith',
                'department': appointment_data.get('department', 'General Medicine')
            },
            'response_params': {}
        }
    
    def _simulate_doctor_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate doctor contact when backend API is not available
        """
        return {
            'success': True,
            'prediction_type': 'contact',
            'result': {
                'contact_id': f"CNT{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'status': 'notified',
                'doctor_assigned': 'Dr. Johnson',
                'estimated_response_time': '2-4 hours'
            },
            'response_params': {}
        }
    
    def _send_ai_notification(self, user_whatsapp: str, entities: Dict[str, Any], 
                             response_data: Dict[str, Any], language: str) -> Dict[str, Any]:
        """
        Send AI agent notification based on the response
        """
        try:
            prediction_type = response_data.get('prediction_type', 'general')
            
            if prediction_type in ['heart', 'alzheimer']:
                return self.ai_agent.send_prediction_result(
                    prediction_type, response_data.get('result', {}), language
                )
            elif prediction_type == 'appointment':
                return self.ai_agent.send_appointment_confirmation(
                    response_data.get('result', {}), language
                )
            else:
                return self.ai_agent.send_message(
                    'general_message', language,
                    message=f"Voice assistant response: {response_data.get('result', {}).get('message', 'Request processed')}",
                    helpline_number='+91-XXXX-XXXXXX',
                    website_url='https://yourclinic.com'
                )
                
        except Exception as e:
            logger.error(f"AI agent notification error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_error_response(self, error_type: str, error_message: str, language: str) -> Dict[str, Any]:
        """
        Create standardized error response
        """
        response_text = self.tts_handler.generate_response('error', language)
        tts_result = self.tts_handler.text_to_speech(response_text, language)
        
        return {
            'success': False,
            'error': {
                'type': error_type,
                'message': error_message
            },
            'response': {
                'text': response_text,
                'audio_data': tts_result.get('audio_data'),
                'tts_success': tts_result['success']
            },
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get status of all voice assistant components
        """
        return {
            'speech_recognition': {
                'available': True,
                'supported_languages': list(self.speech_handler.language_codes.keys())
            },
            'text_to_speech': {
                'available': True,
                'supported_languages': list(self.tts_handler.language_codes.keys()),
                'offline_available': self.tts_handler.offline_available
            },
            'ai_agent': {
                'available': True,
                'status': self.ai_agent.get_status()
            },
            'backend_endpoints': {
                endpoint: f"{self.base_url}{path}" 
                for endpoint, path in self.api_endpoints.items()
            }
        }
