"""
Multilingual Voice Assistant Module for Medical Prediction App
Supports Telugu, Hindi, and English voice input/output
"""

from .speech_handler import SpeechHandler
from .tts_handler import TTSHandler
from .simple_ai_agent import SimpleAIAgent
from .voice_assistant import VoiceAssistant

__all__ = ['SpeechHandler', 'TTSHandler', 'SimpleAIAgent', 'VoiceAssistant']
