"""
Speech Recognition Handler
Handles multilingual speech-to-text conversion using Google Speech Recognition API
Supports Telugu, Hindi, and English with auto-detection
"""

import io
import os
import re
import speech_recognition as sr
from langdetect import detect, LangDetectException
from typing import Optional, Dict, Any
import logging
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logging.warning("pydub not available, audio format conversion limited")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpeechHandler:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        
        # Language mapping for Google Speech Recognition
        self.language_codes = {
            'en': 'en-US',
            'hi': 'hi-IN', 
            'te': 'te-IN',
            'ta': 'ta-IN',
            'kn': 'kn-IN',
            'ml': 'ml-IN',
            'bn': 'bn-IN',
            'gu': 'gu-IN',
            'mr': 'mr-IN',
            'pa': 'pa-IN'
        }
        
        # Common medical terms in different languages (for better recognition)
        self.medical_keywords = {
            'en': ['heart', 'chest', 'pain', 'memory', 'forget', 'doctor', 'hospital', 'medicine', 'symptoms'],
            'hi': ['दिल', 'सीने', 'दर्द', 'याददाश्त', 'भूल', 'डॉक्टर', 'अस्पताल', 'दवा', 'लक्षण'],
            'te': ['గుండె', 'ఛాతీ', 'నొప్పి', 'గుర్తుంచుకోవడం', 'మరచిపోవడం', 'డాక్టర్', 'ఆసుపత్రి', 'మందులు', 'లక్షణాలు']
        }
    
    def detect_language(self, text: str) -> str:
        """
        Detect the language of the transcribed text
        Returns language code (en, hi, te, etc.)
        """
        try:
            detected_lang = detect(text)
            logger.info(f"Detected language: {detected_lang}")
            return detected_lang
        except LangDetectException:
            logger.warning("Could not detect language, defaulting to English")
            return 'en'
    
    def transcribe_audio(self, audio_file: bytes, language_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert audio to text using Google Speech Recognition
        Returns dict with transcription, detected language, and confidence
        """
        try:
            # Convert bytes to AudioFile
            audio_io = io.BytesIO(audio_file)
            
            # Try to convert audio to WAV format if pydub is available
            converted_audio = audio_file
            if PYDUB_AVAILABLE:
                try:
                    # Try to convert the audio to WAV format
                    audio = AudioSegment.from_file(audio_io)
                    wav_buffer = io.BytesIO()
                    audio.export(wav_buffer, format="wav", parameters=["-ar", "16000"])
                    wav_buffer.seek(0)
                    converted_audio = wav_buffer.read()
                    logger.info("Audio converted to WAV format using pydub")
                except Exception as conversion_error:
                    logger.warning(f"Audio conversion failed: {conversion_error}")
                    # Fall back to original audio
                    converted_audio = audio_file
            
            # Convert bytes to AudioFile for speech recognition
            audio_io = io.BytesIO(converted_audio)
            
            try:
                with sr.AudioFile(audio_io) as source:
                    # Adjust for ambient noise
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = self.recognizer.record(source)
            except Exception as audio_error:
                logger.warning(f"Could not read audio file directly: {audio_error}")
                # Try using AudioData instead
                try:
                    audio = sr.AudioData(converted_audio, 16000, 2)
                except Exception as e:
                    logger.error(f"Could not create AudioData: {e}")
                    return {
                        'text': '',
                        'language': 'en',
                        'confidence': 0.0,
                        'success': False,
                        'error': f'Audio format not supported: {str(e)}'
                    }
            
            # Try with language hint first if provided
            if language_hint and language_hint in self.language_codes:
                try:
                    text = self.recognizer.recognize_google(
                        audio, 
                        language=self.language_codes[language_hint]
                    )
                    detected_lang = language_hint
                    logger.info(f"Transcribed with language hint {language_hint}: {text}")
                except sr.UnknownValueError:
                    # Fall back to auto-detection
                    try:
                        text = self.recognizer.recognize_google(audio)
                        detected_lang = self.detect_language(text)
                    except sr.UnknownValueError:
                        return {
                            'text': '',
                            'language': language_hint or 'en',
                            'confidence': 0.0,
                            'success': False,
                            'error': 'Could not understand audio'
                        }
            else:
                # Auto-detect language
                try:
                    text = self.recognizer.recognize_google(audio)
                    detected_lang = self.detect_language(text)
                except sr.UnknownValueError:
                    return {
                        'text': '',
                        'language': 'en',
                        'confidence': 0.0,
                        'success': False,
                        'error': 'Could not understand audio'
                    }
            
            return {
                'text': text,
                'language': detected_lang,
                'confidence': 0.8,  # Google doesn't provide confidence scores
                'success': True
            }
            
        except sr.UnknownValueError:
            logger.error("Google Speech Recognition could not understand audio")
            return {
                'text': '',
                'language': 'en',
                'confidence': 0.0,
                'success': False,
                'error': 'Could not understand audio'
            }
        except sr.RequestError as e:
            logger.error(f"Could not request results from Google Speech Recognition service: {e}")
            return {
                'text': '',
                'language': 'en', 
                'confidence': 0.0,
                'success': False,
                'error': f'Speech recognition service error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Unexpected error in speech recognition: {e}")
            return {
                'text': '',
                'language': 'en',
                'confidence': 0.0,
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    def extract_medical_entities(self, text: str, language: str) -> Dict[str, Any]:
        """
        Extract medical entities from transcribed text
        Returns name, age, symptoms, and intent
        """
        text_lower = text.lower()
        
        # Name extraction patterns
        name_patterns = [
            r"name\s*(?:is|:)?\s*([A-Za-z\u0900-\u097F\u0C00-\u0C7F]{2,30}(?:\s[A-Za-z\u0900-\u097F\u0C00-\u0C7F]{2,30})?)",
            r"i am\s+([A-Za-z\u0900-\u097F\u0C00-\u0C7F]{2,30}(?:\s[A-Za-z\u0900-\u097F\u0C00-\u0C7F]{2,30})?)",
            r"this is\s+([A-Za-z\u0900-\u097F\u0C00-\u0C7F]{2,30}(?:\s[A-Za-z\u0900-\u097F\u0C00-\u0C7F]{2,30})?)",
            r"my name\s+(?:is\s+)?([A-Za-z\u0900-\u097F\u0C00-\u0C7F]{2,30}(?:\s[A-Za-z\u0900-\u097F\u0C00-\u0C7F]{2,30})?)"
        ]
        
        # Age extraction patterns
        age_patterns = [
            r"(\d{1,3})\s*years?\s*old",
            r"age\s*(?:is\s*)?(\d{1,3})",
            r"(\d{1,3})\s*yrs?",
            r"i am\s+(\d{1,3})\s*years?",
            r"(\d{1,3})\s*సంవత్సరాలు",  # Telugu
            r"(\d{1,3})\s*साल",  # Hindi
        ]
        
        # Extract name
        name = None
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                break
        
        # Extract age
        age = None
        for pattern in age_patterns:
            match = re.search(pattern, text_lower)
            if match:
                age = int(match.group(1))
                break
        
        # Extract symptoms based on language
        symptoms = []
        if language in self.medical_keywords:
            for keyword in self.medical_keywords[language]:
                if keyword in text_lower:
                    symptoms.append(keyword)
        
        # Intent detection
        intent = self._detect_intent(text_lower, language)
        
        return {
            'name': name,
            'age': age,
            'symptoms': symptoms,
            'intent': intent,
            'raw_text': text
        }
    
    def _detect_intent(self, text: str, language: str) -> str:
        """
        Detect user intent from the transcribed text
        """
        # Intent keywords in different languages
        intent_keywords = {
            'heart': {
                'en': ['heart', 'chest', 'cardiac', 'chest pain', 'heart attack'],
                'hi': ['दिल', 'सीने', 'हृदय', 'सीने में दर्द'],
                'te': ['గుండె', 'ఛాతీ', 'హృదయ', 'ఛాతీలో నొప్పి']
            },
            'alzheimer': {
                'en': ['memory', 'forget', 'alzheimer', 'dementia', 'remember'],
                'hi': ['याददाश्त', 'भूल', 'अल्जाइमर', 'भूलने की बीमारी'],
                'te': ['గుర్తుంచుకోవడం', 'మరచిపోవడం', 'అల్జైమర్', 'మతిభ్రమణ']
            },
            'appointment': {
                'en': ['appointment', 'book', 'schedule', 'visit', 'meet doctor'],
                'hi': ['अपॉइंटमेंट', 'बुक', 'मिलना', 'डॉक्टर से मिलना'],
                'te': ['అపాయింట్మెంట్', 'బుక్', 'కలవడం', 'డాక్టర్‌ను కలవడం']
            },
            'contact': {
                'en': ['contact', 'call', 'phone', 'emergency', 'help'],
                'hi': ['संपर्क', 'कॉल', 'फोन', 'आपातकाल', 'मदद'],
                'te': ['సంపర్కం', 'కాల్', 'ఫోన్', 'అత్యవసర', 'సహాయం']
            }
        }
        
        for intent_type, keywords in intent_keywords.items():
            if language in keywords:
                for keyword in keywords[language]:
                    if keyword in text:
                        return intent_type
        
        return 'general'
