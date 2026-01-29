#!/usr/bin/env python3
"""
Advanced AI Chat Model for Medical Assistant
Uses IBM watsonx.ai for intelligent medical responses
"""

import os
import re
from typing import Dict, List, Tuple, Optional
import json
from dotenv import load_dotenv

load_dotenv()

# Initialize Watsonx
Model = None
GenParams = None
try:
    from ibm_watson_machine_learning.foundation_models import Model
    from ibm_watson_machine_learning.metanames import GenTextParamsMetaNames as GenParams

    WATSONX_API_KEY = os.getenv("WATSONX_API_KEY")
    WATSONX_URL = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")
    WATSONX_MODEL_ID = os.getenv("WATSONX_MODEL_ID", "ibm/granite-13b-instruct-v2")

    WATSONX_AVAILABLE = bool(WATSONX_API_KEY and WATSONX_URL and WATSONX_PROJECT_ID)

    if WATSONX_AVAILABLE:
        wml_credentials = {
            "url": WATSONX_URL,
            "apikey": WATSONX_API_KEY,
        }
        print("✅ Watsonx.ai credentials loaded (Model created per-request)")
    else:
        wml_credentials = None
        print("⚠️ Watsonx.ai credentials not fully configured (WATSONX_API_KEY, WATSONX_URL, WATSONX_PROJECT_ID)")
except ImportError:
    WATSONX_AVAILABLE = False
    wml_credentials = None
    print("⚠️ IBM Watson Machine Learning SDK not installed. Install with: pip install ibm-watson-machine-learning")
except Exception as e:
    WATSONX_AVAILABLE = False
    wml_credentials = None
    print(f"⚠️ Watsonx.ai initialization failed: {e}")

def get_medical_system_prompt() -> str:
    """Medical system prompt tuned for medication-focused assistance."""
    return """You are a medical AI assistant. You must ONLY handle medical topics.

Your purpose: help the user understand symptoms and provide medication suggestions.

Rules:
- Be concise, structured, and clinically cautious.
- Do NOT provide non-medical content.
- Do NOT claim to be a doctor and do NOT claim you can prescribe. When asked for prescriptions, provide: "prescription options a clinician may consider" and recommend seeing a licensed clinician.
- Always include safety guidance: allergies, contraindications, pregnancy, age, comorbidities, interactions, and "when to seek urgent care".
- If symptoms are severe (chest pain, severe shortness of breath, stroke signs, severe allergic reaction, suicidal ideation), instruct immediate emergency care (911/112).

Output format:
1) Likely issue (brief)
2) Recommended meds (OTC first; then prescription options to discuss with a clinician)
3) Dosage guidance (general ranges, not individualized)
4) Warnings / contraindications
5) When to seek urgent care
6) Next questions (1-3 clarifying questions)
"""

def chat_completion_watsonx(message: str, context: List[Dict] = None) -> Optional[str]:
    """
    Generate AI response using IBM Watsonx for medical chat.

    Model expects: Model(model_id, credentials, params=None, project_id=None).
    generate_text(prompt, params) returns str (generated text) or may return dict in some SDK versions.
    """
    if not WATSONX_AVAILABLE or not wml_credentials or not Model or not GenParams:
        return None

    try:
        system_prompt = get_medical_system_prompt()

        # Build context from conversation history
        context_text = ""
        if context:
            context_text = "\n\nPrevious conversation:\n"
            for msg in context[-3:]:
                role = "User" if msg.get("role") == "user" or msg.get("type") == "user" else "Assistant"
                content = msg.get("content") or msg.get("user_message") or msg.get("ai_response", "")
                if content:
                    context_text += f"{role}: {content}\n"

        full_prompt = f"""{system_prompt}

{context_text}

User Query: {message}

Assistant Response:"""

        parameters = {
            GenParams.MAX_NEW_TOKENS: 500,
            GenParams.TEMPERATURE: 0.7,
            GenParams.REPETITION_PENALTY: 1.1,
        }
        if hasattr(GenParams, "DECODING_METHOD"):
            parameters[GenParams.DECODING_METHOD] = "greedy"
        if hasattr(GenParams, "TOP_P"):
            parameters[GenParams.TOP_P] = 0.9

        model = Model(
            model_id=WATSONX_MODEL_ID,
            credentials=wml_credentials,
            params=parameters,
            project_id=WATSONX_PROJECT_ID,
        )

        response = model.generate_text(prompt=full_prompt, params=parameters)

        # generate_text returns str; fallback if SDK returns dict
        if isinstance(response, str):
            generated_text = response.strip()
        elif isinstance(response, dict):
            res = response.get("results") or []
            generated_text = (res[0].get("generated_text") if res else "") or ""
            generated_text = str(generated_text).strip()
        else:
            generated_text = str(response or "").strip()

        if "Assistant Response:" in generated_text:
            generated_text = generated_text.split("Assistant Response:")[-1].strip()
        if not generated_text:
            return None
        return generated_text

    except Exception as e:
        print(f"❌ Watsonx API error: {e}")
        import traceback
        traceback.print_exc()
        return None

def chat_completion(message: str, context: List[Dict] = None) -> str:
    """
    Generate AI response using watsonx.ai (no OpenAI).
    """
    response = chat_completion_watsonx(message, context)
    if response:
        print("✅ Using Watsonx.ai")
        return response
    
    # Fall back to enhanced rule-based system (keeps the app usable if watsonx isn't configured)
    print("⚠️ Watsonx unavailable; using rule-based fallback")
    return enhanced_rule_based_response(message)

def enhanced_rule_based_response(message: str) -> str:
    """
    Enhanced rule-based medical responses
    """
    message_lower = message.lower()
    
    # Emergency responses
    emergency_patterns = [
        r'heart attack|chest pain|severe chest|crushing chest',
        r'stroke|facial droop|slurred speech|weakness on one side',
        r'can\'t breathe|difficulty breathing|choking|suffocating',
        r'unconscious|passed out|fainted|not responding',
        r'severe bleeding|heavy bleeding|bleeding won\'t stop',
        r'suicidal|want to die|harm myself'
    ]
    
    for pattern in emergency_patterns:
        if re.search(pattern, message_lower):
            return "🚨 MEDICAL EMERGENCY: This requires immediate medical attention! Please call emergency services (911/112) right now or go to the nearest emergency room. Do not delay seeking help."
    
    # Urgent but not emergency
    urgent_patterns = [
        r'high fever|fever over 103|fever with rash',
        r'severe headache|worst headache|thunderclap headache',
        r'severe abdominal pain|acute abdomen',
        r'severe allergic reaction|anaphylaxis',
        r'severe dehydration|can\'t keep fluids down'
    ]
    
    for pattern in urgent_patterns:
        if re.search(pattern, message_lower):
            return "⚠️ URGENT: This needs prompt medical attention. Please contact your doctor immediately or visit urgent care within the next few hours. Monitor your symptoms closely."
    
    # Specific condition responses
    if re.search(r'fever|cold|flu', message_lower):
        if re.search(r'high|severe|over 101', message_lower):
            return "For high fever (above 101.3°F/38.5°C), monitor closely and consider contacting your doctor. Stay hydrated, rest, and use fever-reducing medications as directed. If fever persists or worsens, seek medical care."
        else:
            return "For mild fever, rest, stay hydrated, and monitor your temperature. Over-the-counter fever reducers can help. If symptoms persist beyond 3-5 days or worsen, consult a healthcare provider."
    
    if re.search(r'headache|migraine', message_lower):
        if re.search(r'severe|worst|thunderclap', message_lower):
            return "Severe headaches require medical evaluation, especially if sudden onset or 'worst headache ever.' Keep a headache diary and consult your doctor. Consider emergency care if accompanied by fever, neck stiffness, or neurological symptoms."
        else:
            return "For mild to moderate headaches, try rest, hydration, and over-the-counter pain relief. Identify and avoid triggers. If headaches are frequent, severe, or changing pattern, consult a healthcare provider."
    
    if re.search(r'cough|chest|breathing', message_lower):
        if re.search(r'severe|can\'t breathe|shortness of breath', message_lower):
            return "Severe breathing difficulties require immediate medical attention. If you're having trouble breathing, call emergency services or go to the ER immediately."
        else:
            return "For mild respiratory symptoms, rest, stay hydrated, and use a humidifier. Monitor for worsening symptoms. If cough persists beyond 2-3 weeks or worsens, consult a healthcare provider."
    
    if re.search(r'stomach|nausea|vomiting|diarrhea', message_lower):
        return "For gastrointestinal symptoms, stay hydrated with clear fluids, eat bland foods, and rest. Avoid dairy and fatty foods. If symptoms persist beyond 2-3 days, include blood, or are severe, consult a healthcare provider."
    
    if re.search(r'pain|ache|sore', message_lower):
        return "For pain management, try rest, ice/heat therapy, and over-the-counter pain relievers. If pain is severe, persistent, or accompanied by other concerning symptoms, consult a healthcare provider."
    
    # General response
    return "I understand you're experiencing health concerns. While I can provide general guidance, it's important to consult with a healthcare professional for proper evaluation and treatment. If symptoms are severe or concerning, please seek medical attention promptly."

def process_medical_chat(message: str, user_email: str = None, context: List[Dict] = None) -> Dict:
    """
    Process medical chat and extract structured information with enhanced context awareness
    """
    message_lower = message.lower()
    
    # Determine urgency level using enhanced patterns
    emergency_patterns = [
        r'heart attack|chest pain|severe chest|crushing chest',
        r'stroke|facial droop|slurred speech|weakness on one side',
        r'can\'t breathe|difficulty breathing|choking|suffocating',
        r'unconscious|passed out|fainted|not responding',
        r'severe bleeding|heavy bleeding|bleeding won\'t stop',
        r'suicidal|want to die|harm myself'
    ]
    
    urgent_patterns = [
        r'high fever|fever over 103|fever with rash',
        r'severe headache|worst headache|thunderclap headache',
        r'severe abdominal pain|acute abdomen',
        r'severe allergic reaction|anaphylaxis',
        r'severe dehydration|can\'t keep fluids down'
    ]
    
    urgency = "normal"
    if any(re.search(pattern, message_lower) for pattern in emergency_patterns):
        urgency = "emergency"
    elif any(re.search(pattern, message_lower) for pattern in urgent_patterns):
        urgency = "urgent"
    
    # Enhanced category detection
    categories = {
        'cardiovascular': ['heart', 'chest', 'blood pressure', 'pulse', 'cardiac', 'chest pain', 'heart attack'],
        'respiratory': ['breathing', 'cough', 'lungs', 'asthma', 'shortness of breath', 'can\'t breathe'],
        'neurological': ['headache', 'dizzy', 'confusion', 'memory', 'brain', 'stroke', 'migraine'],
        'gastrointestinal': ['stomach', 'nausea', 'vomiting', 'diarrhea', 'digestive', 'abdominal pain'],
        'musculoskeletal': ['pain', 'muscle', 'joint', 'bone', 'back', 'neck', 'ache', 'sore'],
        'infectious': ['fever', 'cold', 'flu', 'infection', 'viral', 'bacterial'],
        'mental_health': ['anxiety', 'depression', 'stress', 'panic', 'mood', 'mental'],
        'general': ['fatigue', 'weakness', 'general', 'overall']
    }
    
    detected_category = 'general'
    max_matches = 0
    for category, keywords in categories.items():
        matches = sum(1 for keyword in keywords if keyword in message_lower)
        if matches > max_matches:
            max_matches = matches
            detected_category = category
    
    # Extract keywords using regex patterns
    keywords = []
    for category, category_keywords in categories.items():
        for keyword in category_keywords:
            if keyword in message_lower:
                keywords.append(keyword)
    
    # Remove duplicates and limit
    keywords = list(set(keywords))[:8]
    
    # Prepare context for AI (normalize format)
    normalized_context = None
    if context:
        normalized_context = []
        for msg in context:
            if isinstance(msg, dict):
                # Handle different message formats
                if "user_message" in msg and "ai_response" in msg:
                    # Chat history format
                    normalized_context.append({
                        "role": "user",
                        "content": msg.get("user_message", "")
                    })
                    normalized_context.append({
                        "role": "assistant",
                        "content": msg.get("ai_response", "")
                    })
                elif "type" in msg:
                    # Frontend format
                    normalized_context.append({
                        "role": "user" if msg.get("type") == "user" else "assistant",
                        "content": msg.get("content", "")
                    })
                elif "role" in msg:
                    # Already normalized
                    normalized_context.append(msg)
    
    # Generate response with context awareness
    response = chat_completion(message, normalized_context)
    
    return {
        "response": response,
        "urgency": urgency,
        "category": detected_category,
        "keywords": keywords
    }
