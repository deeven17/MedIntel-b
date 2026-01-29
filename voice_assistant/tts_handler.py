"""
Text-to-Speech Handler
Handles multilingual text-to-speech conversion using gTTS and pyttsx3
Supports Telugu, Hindi, and English with natural voice synthesis
"""

import io
import os
import tempfile
from typing import Dict, Any, Optional
import logging
from gtts import gTTS
import pyttsx3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TTSHandler:
    def __init__(self):
        # Language mapping for gTTS
        self.language_codes = {
            'en': 'en',
            'hi': 'hi',
            'te': 'te',
            'ta': 'ta',
            'kn': 'kn',
            'ml': 'ml',
            'bn': 'bn',
            'gu': 'gu',
            'mr': 'mr',
            'pa': 'pa'
        }
        
        # Initialize pyttsx3 for offline TTS
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)  # Speed of speech
            self.engine.setProperty('volume', 0.9)  # Volume level (0.0 to 1.0)
            self.offline_available = True
            logger.info("Offline TTS engine initialized successfully")
        except Exception as e:
            logger.warning(f"Offline TTS not available: {e}")
            self.offline_available = False
        
        # Medical response templates in different languages
        self.response_templates = {
            'en': {
                'heart_result': "Based on your symptoms, I've analyzed your heart health. The prediction shows {prediction} with {risk_percentage}% risk level. Please consult a doctor for detailed examination.",
                'alzheimer_result': "I've analyzed your cognitive health. The prediction indicates {prediction} with {risk_percentage}% risk level. Please schedule a consultation with a neurologist.",
                'appointment_confirmed': "Your appointment has been scheduled. You will receive confirmation details via WhatsApp shortly.",
                'contact_doctor': "I'll notify the doctor about your request. Please provide your contact number if you haven't already.",
                'general_response': "I understand you mentioned {symptoms}. Please provide more details about your symptoms for better assistance.",
                'error_response': "I'm sorry, I couldn't understand your request clearly. Please try speaking again or contact our support team."
            },
            'hi': {
                'heart_result': "आपके लक्षणों के आधार पर, मैंने आपके हृदय स्वास्थ्य का विश्लेषण किया है। भविष्यवाणी {prediction} दिखाती है जिसमें {risk_percentage}% जोखिम स्तर है। विस्तृत जांच के लिए कृपया डॉक्टर से सलाह लें।",
                'alzheimer_result': "मैंने आपके संज्ञानात्मक स्वास्थ्य का विश्लेषण किया है। भविष्यवाणी {prediction} दिखाती है जिसमें {risk_percentage}% जोखिम स्तर है। कृपया न्यूरोलॉजिस्ट के साथ परामर्श का समय निर्धारित करें।",
                'appointment_confirmed': "आपका अपॉइंटमेंट निर्धारित हो गया है। आपको जल्द ही व्हाट्सऐप के माध्यम से पुष्टि विवरण प्राप्त होगा।",
                'contact_doctor': "मैं आपके अनुरोध के बारे में डॉक्टर को सूचित करूंगा। यदि आपने पहले से नहीं दिया है तो कृपया अपना संपर्क नंबर प्रदान करें।",
                'general_response': "मैं समझ गया कि आपने {symptoms} का उल्लेख किया है। बेहतर सहायता के लिए कृपया अपने लक्षणों के बारे में अधिक विवरण प्रदान करें।",
                'error_response': "मुझे खेद है, मैं आपके अनुरोध को स्पष्ट रूप से समझ नहीं सका। कृपया फिर से बोलने का प्रयास करें या हमारी सहायता टीम से संपर्क करें।"
            },
            'te': {
                'heart_result': "మీ లక్షణాల ఆధారంగా, నేను మీ గుండె ఆరోగ్యాన్ని విశ్లేషించాను. అంచనా {prediction} చూపిస్తుంది {risk_percentage}% ప్రమాద స్థాయితో. వివరణాత్మక పరీక్ష కోసం దయచేసి వైద్యుడిని సంప్రదించండి.",
                'alzheimer_result': "నేను మీ అభిజ్ఞా ఆరోగ్యాన్ని విశ్లేషించాను. అంచనా {prediction} చూపిస్తుంది {risk_percentage}% ప్రమాద స్థాయితో. దయచేసి న్యూరాలజిస్ట్‌తో సంప్రదింపు షెడ్యూల్ చేయండి.",
                'appointment_confirmed': "మీ అపాయింట్మెంట్ షెడ్యూల్ చేయబడింది. మీరు త్వరలో వాట్సాప్ ద్వారా నిర్ధారణ వివరాలను అందుకుంటారు.",
                'contact_doctor': "నేను మీ అభ్యర్థన గురించి వైద్యుడికి తెలియజేస్తాను. మీరు ఇంతకు ముందు ఇవ్వకపోతే దయచేసి మీ కాంటాక్ట్ నంబర్‌ను అందించండి.",
                'general_response': "మీరు {symptoms} గురించి ప్రస్తావించారని నేను అర్థం చేసుకున్నాను. మెరుగైన సహాయం కోసం దయచేసి మీ లక్షణాల గురించి మరింత వివరాలను అందించండి.",
                'error_response': "క్షమించండి, నేను మీ అభ్యర్థనను స్పష్టంగా అర్థం చేసుకోలేకపోయాను. దయచేసి మళ్లీ మాట్లాడడానికి ప్రయత్నించండి లేదా మా మద్దతు బృందాన్ని సంప్రదించండి."
            }
        }
    
    def generate_response(self, intent: str, language: str, **kwargs) -> str:
        """
        Generate appropriate response text based on intent and language
        """
        if language not in self.response_templates:
            language = 'en'  # Fallback to English
        
        templates = self.response_templates[language]
        
        if intent == 'heart' and 'heart_result' in templates:
            return templates['heart_result'].format(**kwargs)
        elif intent == 'alzheimer' and 'alzheimer_result' in templates:
            return templates['alzheimer_result'].format(**kwargs)
        elif intent == 'appointment' and 'appointment_confirmed' in templates:
            return templates['appointment_confirmed']
        elif intent == 'contact' and 'contact_doctor' in templates:
            return templates['contact_doctor']
        elif intent == 'general' and 'general_response' in templates:
            return templates['general_response'].format(**kwargs)
        else:
            return templates['error_response']
    
    def text_to_speech(self, text: str, language: str, use_offline: bool = False) -> Dict[str, Any]:
        """
        Convert text to speech using gTTS or pyttsx3
        Returns audio data as bytes
        """
        try:
            if use_offline and self.offline_available:
                return self._offline_tts(text, language)
            else:
                return self._online_tts(text, language)
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return {
                'audio_data': None,
                'success': False,
                'error': str(e)
            }
    
    def _online_tts(self, text: str, language: str) -> Dict[str, Any]:
        """
        Use gTTS for online text-to-speech
        """
        try:
            # Map language code for gTTS
            tts_language = self.language_codes.get(language, 'en')
            
            # Create gTTS object
            tts = gTTS(text=text, lang=tts_language, slow=False)
            
            # Generate audio data
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            
            logger.info(f"Generated TTS audio for language: {language}")
            
            return {
                'audio_data': audio_buffer.getvalue(),
                'success': True,
                'method': 'gTTS',
                'language': language
            }
            
        except Exception as e:
            logger.error(f"gTTS error: {e}")
            # Fallback to offline TTS if available
            if self.offline_available:
                return self._offline_tts(text, language)
            else:
                return {
                    'audio_data': None,
                    'success': False,
                    'error': str(e)
                }
    
    def _offline_tts(self, text: str, language: str) -> Dict[str, Any]:
        """
        Use pyttsx3 for offline text-to-speech
        """
        try:
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                temp_path = temp_file.name
            
            # Configure voice based on language (limited support)
            voices = self.engine.getProperty('voices')
            if voices:
                # Try to find appropriate voice for language
                if language == 'hi' and len(voices) > 1:
                    self.engine.setProperty('voice', voices[1].id)  # Usually female voice
                elif language == 'te' and len(voices) > 2:
                    self.engine.setProperty('voice', voices[2].id)  # Try different voice
            
            # Generate speech and save to file
            self.engine.save_to_file(text, temp_path)
            self.engine.runAndWait()
            
            # Read the generated audio file
            with open(temp_path, 'rb') as audio_file:
                audio_data = audio_file.read()
            
            # Clean up temporary file
            os.unlink(temp_path)
            
            logger.info(f"Generated offline TTS audio for language: {language}")
            
            return {
                'audio_data': audio_data,
                'success': True,
                'method': 'pyttsx3',
                'language': language
            }
            
        except Exception as e:
            logger.error(f"Offline TTS error: {e}")
            return {
                'audio_data': None,
                'success': False,
                'error': str(e)
            }
    
    def get_available_voices(self) -> Dict[str, Any]:
        """
        Get information about available voices
        """
        if not self.offline_available:
            return {'offline_available': False}
        
        try:
            voices = self.engine.getProperty('voices')
            voice_info = []
            
            for i, voice in enumerate(voices):
                voice_info.append({
                    'id': voice.id,
                    'name': voice.name,
                    'languages': voice.languages,
                    'gender': voice.gender,
                    'age': voice.age
                })
            
            return {
                'offline_available': True,
                'voices': voice_info,
                'current_rate': self.engine.getProperty('rate'),
                'current_volume': self.engine.getProperty('volume')
            }
            
        except Exception as e:
            logger.error(f"Error getting voice info: {e}")
            return {
                'offline_available': True,
                'error': str(e)
            }
