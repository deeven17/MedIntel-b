from fastapi import APIRouter, Depends, HTTPException
from dependencies import get_current_user
from datetime import datetime, timedelta
import json
import re
from database import users_col, predictions_col, reports_col, chat_col, db
from utils.medicine_service import (
    detect_medical_condition,
    get_medicine_recommendations,
    get_medicine_interactions,
    generate_medicine_summary,
)
from routes.notifications import notify_user_event

# Import your AI chat model
try:
    from models.advanced_ai_chat import chat_completion, process_medical_chat
    USE_AI_CHAT = True
    print("✅ AI Chat model loaded")
except ImportError as e:
    print(f"⚠️ AI Chat model not available: {e}")
    USE_AI_CHAT = False

router = APIRouter()

async def save_chat_history(
    user_email: str,
    user_message: str,
    ai_response: str,
    condition: str = None,
    medicines: dict = None,
    urgency: str = None,
    category: str = None,
    keywords: list = None,
    medicine_summary: str = None,
    interactions: list = None,
):
    """Save chat history to database"""
    try:
        chat_entry = {
            "user_email": user_email,
            "user_message": user_message,
            "ai_response": ai_response,
            "condition": condition,
            "medicines": medicines,
            "urgency": urgency,
            "category": category,
            "keywords": keywords or [],
            "medicine_summary": medicine_summary,
            "interactions": interactions or [],
            "timestamp": datetime.utcnow(),
            "type": "chat_interaction"
        }
        
        # Save to a new chat_history collection
        await chat_col.insert_one(chat_entry)
        print(f"✅ Chat history saved for user: {user_email}")
    except Exception as e:
        print(f"❌ Error saving chat history: {str(e)}")

async def get_user_history(user_email: str, limit: int = 50):
    """Get user's chat and prediction history"""
    try:
        # Get chat history
        chat_history = []
        async for doc in chat_col.find({"user_email": user_email}).sort("timestamp", -1).limit(limit):
            doc["_id"] = str(doc["_id"])
            chat_history.append(doc)
        
        # Get prediction history
        prediction_history = []
        async for doc in predictions_col.find({"user_email": user_email}).sort("timestamp", -1).limit(limit):
            doc["_id"] = str(doc["_id"])
            prediction_history.append(doc)
        
        return {
            "chat_history": chat_history,
            "prediction_history": prediction_history
        }
    except Exception as e:
        print(f"❌ Error getting user history: {str(e)}")
        return {"chat_history": [], "prediction_history": []}

@router.post("/chat-public")
async def chat_public_endpoint(data: dict):
    """Public chat endpoint for testing (no auth required)"""
    prompt = data.get("message", "")

    if not prompt:
        return {"reply": "Please provide a message."}

    try:
        # Detect medical condition from user prompt
        detected_condition = detect_medical_condition(prompt)
        medicines = None
        
        if USE_AI_CHAT:
            # Use enhanced AI model for response
            print(f"🤖 Processing public AI chat for message: {prompt}")

            # Process the medical chat with enhanced features (no context for public)
            chat_result = process_medical_chat(prompt, "public_user", None)
            ai_response = chat_result["response"]
            
            # Extract additional information
            urgency = chat_result.get("urgency", "normal")
            category = chat_result.get("category", "general_health")
            keywords = chat_result.get("keywords", [])

            print(f"🎯 Public AI Response: {ai_response[:100]}...")
            
            # Get medicine recommendations if condition detected
            # Adjust severity based on urgency level
            severity_map = {"emergency": "severe", "urgent": "urgent", "normal": "moderate"}
            severity = severity_map.get(urgency, "moderate")
            
            if detected_condition:
                medicines = get_medicine_recommendations(detected_condition, severity=severity)
                print(f"💊 Detected condition: {detected_condition} (severity: {severity})")
                
                # Generate medicine summary
                medicine_summary = generate_medicine_summary(detected_condition, medicines)
                
                # Check for drug interactions if multiple medicines
                interactions = []
                if medicines and len(medicines.get("medications", [])) > 1:
                    interactions = get_medicine_interactions(medicines["medications"])
            else:
                medicines = None
                medicine_summary = None
                interactions = []
            
            # Prepare response with medicine recommendations
            response_data = {
                "reply": ai_response,
                "detected_condition": detected_condition,
                "medicines": medicines,
                "medicine_summary": medicine_summary,
                "interactions": interactions,
                "urgency": urgency,
                "category": category,
                "keywords": keywords,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return response_data
        else:
            # Fallback to simple rule-based system if AI not available
            message_lower = prompt.lower()
            
            # Emergency responses - CHECK FIRST
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
                    ai_response = "🚨 MEDICAL EMERGENCY: This requires immediate medical attention! Please call emergency services (911/112) right now or go to the nearest emergency room. Do not delay seeking help."
                    
                    # Still detect condition and provide basic info for emergency
                    if detected_condition:
                        medicines = get_medicine_recommendations(detected_condition, severity="severe")
                        medicine_summary = generate_medicine_summary(detected_condition, medicines)
                        interactions = get_medicine_interactions(medicines["medications"]) if medicines and len(medicines.get("medications", [])) > 1 else []
                    else:
                        medicines = None
                        medicine_summary = None
                        interactions = []
                    
                    # Prepare emergency response
                    response_data = {
                        "reply": ai_response,
                        "detected_condition": detected_condition,
                        "medicines": medicines,
                        "medicine_summary": medicine_summary,
                        "interactions": interactions,
                        "urgency": "emergency",
                        "category": "emergency",
                        "keywords": ["emergency", "immediate care"],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    return response_data
            
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
                    ai_response = "⚠️ URGENT: This needs prompt medical attention. Please contact your doctor immediately or visit urgent care within the next few hours. Monitor your symptoms closely."
                    
                    # Still detect condition and provide basic info for urgent
                    if detected_condition:
                        medicines = get_medicine_recommendations(detected_condition, severity="urgent")
                        medicine_summary = generate_medicine_summary(detected_condition, medicines)
                        interactions = get_medicine_interactions(medicines["medications"]) if medicines and len(medicines.get("medications", [])) > 1 else []
                    else:
                        medicines = None
                        medicine_summary = None
                        interactions = []
                    
                    # Prepare urgent response
                    response_data = {
                        "reply": ai_response,
                        "detected_condition": detected_condition,
                        "medicines": medicines,
                        "medicine_summary": medicine_summary,
                        "interactions": interactions,
                        "urgency": "urgent",
                        "category": "urgent_care",
                        "keywords": ["urgent", "prompt care"],
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    return response_data
            
            # Simple rule-based responses for non-emergency conditions
            if re.search(r'headache|migraine', message_lower):
                detected_condition = "headache"
                if re.search(r'severe|worst|thunderclap', message_lower):
                    ai_response = "Severe headaches require medical evaluation, especially if sudden onset or 'worst headache ever.' Keep a headache diary and consult your doctor. Consider emergency care if accompanied by fever, neck stiffness, or neurological symptoms."
                else:
                    ai_response = "For mild to moderate headaches, try rest, hydration, and over-the-counter pain relief. Identify and avoid triggers. If headaches are frequent, severe, or changing pattern, consult a healthcare provider."
            elif re.search(r'fever|cold|flu', message_lower):
                detected_condition = "fever"
                if re.search(r'high|severe|over 101', message_lower):
                    ai_response = "For high fever (above 101.3°F/38.5°C), monitor closely and consider contacting your doctor. Stay hydrated, rest, and use fever-reducing medications as directed. If fever persists or worsens, seek medical care."
                else:
                    ai_response = "For mild fever, rest, stay hydrated, and monitor your temperature. Over-the-counter fever reducers can help. If symptoms persist beyond 3-5 days or worsen, consult a healthcare provider."
            elif re.search(r'anxious|anxiety|stress|stressed|worry|worried|panic|panic attack|overwhelmed|depression|sad|hopeless', message_lower):
                detected_condition = "anxiety"
                if re.search(r'severe|extreme|can\'t cope|suicidal|want to die|harm myself', message_lower):
                    ai_response = "🚨 URGENT: If you're having severe anxiety, panic attacks, or thoughts of self-harm, please seek immediate help. Call emergency services (911/112) or contact a crisis hotline. You don't have to go through this alone - help is available 24/7."
                else:
                    ai_response = "For mild to moderate anxiety and stress, consider these approaches: 1) Practice deep breathing and mindfulness exercises, 2) Maintain regular sleep schedule, 3) Exercise regularly (even 20-30 minutes daily helps), 4) Limit caffeine and alcohol, 5) Talk to friends, family, or a mental health professional. If symptoms persist or worsen, consult with a healthcare provider about potential treatment options including therapy or medication."
            elif re.search(r'medicine|medicines|medication|drugs|pills|prescription', message_lower):
                ai_response = "I understand you're asking about medicines. For proper medication recommendations, I need to know your specific symptoms or condition. Different conditions require different treatments - for example, headaches may respond to pain relievers, while anxiety might require different approaches. Please describe your symptoms so I can provide appropriate guidance. Always consult with a healthcare professional before starting any new medication."
            else:
                ai_response = f"I understand you mentioned: '{prompt}'. For a proper medical consultation, please consult with a healthcare professional."
            
            print(f"🎯 Simple rule-based AI Response: {ai_response[:100]}...")
            
            # Get medicine recommendations if condition detected
            if detected_condition:
                medicines = get_medicine_recommendations(detected_condition, severity="moderate")
                print(f"💊 Detected condition: {detected_condition}")
                
                # Generate medicine summary
                medicine_summary = generate_medicine_summary(detected_condition, medicines)
                
                # Check for drug interactions if multiple medicines
                interactions = []
                if medicines and len(medicines.get("medications", [])) > 1:
                    interactions = get_medicine_interactions(medicines["medications"])
            else:
                medicines = None
                medicine_summary = None
                interactions = []
            
            # Prepare response with medicine recommendations
            response_data = {
                "reply": ai_response,
                "detected_condition": detected_condition,
                "medicines": medicines,
                "medicine_summary": medicine_summary,
                "interactions": interactions,
                "urgency": "normal",
                "category": "general_health",
                "keywords": [],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return response_data

    except Exception as e:
        print(f"❌ Public chat error: {str(e)}")
        error_response = "I'm having trouble processing your request right now. Please try again later or consult with a healthcare professional for medical concerns."
        
        return {
            "reply": error_response,
            "detected_condition": None,
            "medicines": None,
            "medicine_summary": None,
            "interactions": [],
            "timestamp": datetime.utcnow().isoformat()
        }

@router.post("/chat")
async def chat_endpoint(data: dict, user: dict = Depends(get_current_user)):
    prompt = data.get("message", "")
    user_email = user.get("email")

    if not prompt:
        return {"reply": "Please provide a message."}

    try:
        # Detect medical condition from user prompt
        detected_condition = detect_medical_condition(prompt)
        medicines = None
        
        if USE_AI_CHAT:
            # Use enhanced AI model for response
            print(f"🤖 Processing AI chat for user: {user_email}")
            print(f"💬 User message: {prompt}")

            # Fetch user's recent chat history for context
            try:
                recent_chats = []
                async for doc in chat_col.find(
                    {"user_email": user_email, "type": "chat_interaction"}
                ).sort("timestamp", -1).limit(5):
                    recent_chats.append({
                        "user_message": doc.get("user_message", ""),
                        "ai_response": doc.get("ai_response", ""),
                        "timestamp": doc.get("timestamp")
                    })
                # Reverse to get chronological order
                recent_chats.reverse()
                print(f"📚 Loaded {len(recent_chats)} previous messages for context")
            except Exception as e:
                print(f"⚠️ Could not load chat history: {e}")
                recent_chats = []

            # Process the medical chat with enhanced features and context
            chat_result = process_medical_chat(prompt, user_email, recent_chats)
            ai_response = chat_result["response"]
            
            # Extract additional information
            urgency = chat_result.get("urgency", "normal")
            category = chat_result.get("category", "general_health")
            keywords = chat_result.get("keywords", [])

            print(f"🎯 AI Response: {ai_response[:100]}...")
            print(f"📊 Detected urgency: {urgency}, category: {category}")
            
            # Get medicine recommendations if condition detected
            # Adjust severity based on urgency level
            severity_map = {"emergency": "severe", "urgent": "urgent", "normal": "moderate"}
            severity = severity_map.get(urgency, "moderate")
            
            if detected_condition:
                medicines = get_medicine_recommendations(detected_condition, severity=severity)
                print(f"💊 Detected condition: {detected_condition} (severity: {severity})")
                
                # Generate medicine summary
                medicine_summary = generate_medicine_summary(detected_condition, medicines)
                
                # Check for drug interactions if multiple medicines
                interactions = []
                if medicines and len(medicines.get("medications", [])) > 1:
                    interactions = get_medicine_interactions(medicines["medications"])
            else:
                medicines = None
                medicine_summary = None
                interactions = []
            
            # Save chat history (medical AI chat is private to the user; no admin notification)
            await save_chat_history(
                user_email,
                prompt,
                ai_response,
                detected_condition,
                medicines,
                urgency=urgency,
                category=category,
                keywords=keywords,
                medicine_summary=medicine_summary,
                interactions=interactions,
            )
            
            # Prepare response with medicine recommendations
            response_data = {
                "reply": ai_response,
                "detected_condition": detected_condition,
                "medicines": medicines,
                "medicine_summary": medicine_summary,
                "interactions": interactions,
                "urgency": urgency,
                "category": category,
                "keywords": keywords,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return response_data
        else:
            # Fallback to simple rule-based system if AI not available
            message_lower = prompt.lower()
            
            # Emergency responses - CHECK FIRST
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
                    ai_response = "🚨 MEDICAL EMERGENCY: This requires immediate medical attention! Please call emergency services (911/112) right now or go to the nearest emergency room. Do not delay seeking help."
                    
                    # Still detect condition and provide basic info for emergency
                    if detected_condition:
                        medicines = get_medicine_recommendations(detected_condition, severity="severe")
                        medicine_summary = generate_medicine_summary(detected_condition, medicines)
                        interactions = get_medicine_interactions(medicines["medications"]) if medicines and len(medicines.get("medications", [])) > 1 else []
                    else:
                        medicines = None
                        medicine_summary = None
                        interactions = []
                    
                    # Save emergency response to history
                    await save_chat_history(
                        user_email,
                        prompt,
                        ai_response,
                        detected_condition,
                        medicines,
                        urgency="emergency",
                        category="emergency",
                        keywords=["emergency", "immediate care"],
                        medicine_summary=medicine_summary,
                        interactions=interactions,
                    )
                    
                    # Prepare emergency response
                    return {
                        "reply": ai_response,
                        "detected_condition": detected_condition,
                        "medicines": medicines,
                        "medicine_summary": medicine_summary,
                        "interactions": interactions,
                        "urgency": "emergency",
                        "category": "emergency",
                        "keywords": ["emergency", "immediate care"],
                        "timestamp": datetime.utcnow().isoformat()
                    }
            
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
                    ai_response = "⚠️ URGENT: This needs prompt medical attention. Please contact your doctor immediately or visit urgent care within the next few hours. Monitor your symptoms closely."
                    
                    # Still detect condition and provide basic info for urgent
                    if detected_condition:
                        medicines = get_medicine_recommendations(detected_condition, severity="urgent")
                        medicine_summary = generate_medicine_summary(detected_condition, medicines)
                        interactions = get_medicine_interactions(medicines["medications"]) if medicines and len(medicines.get("medications", [])) > 1 else []
                    else:
                        medicines = None
                        medicine_summary = None
                        interactions = []
                    
                    # Save urgent response to history
                    await save_chat_history(
                        user_email,
                        prompt,
                        ai_response,
                        detected_condition,
                        medicines,
                        urgency="urgent",
                        category="urgent_care",
                        keywords=["urgent", "prompt care"],
                        medicine_summary=medicine_summary,
                        interactions=interactions,
                    )
                    
                    # Prepare urgent response
                    return {
                        "reply": ai_response,
                        "detected_condition": detected_condition,
                        "medicines": medicines,
                        "medicine_summary": medicine_summary,
                        "interactions": interactions,
                        "urgency": "urgent",
                        "category": "urgent_care",
                        "keywords": ["urgent", "prompt care"],
                        "timestamp": datetime.utcnow().isoformat()
                    }
            
            # Simple rule-based responses for non-emergency conditions
            if re.search(r'headache|migraine', message_lower):
                detected_condition = "headache"
                if re.search(r'severe|worst|thunderclap', message_lower):
                    ai_response = "Severe headaches require medical evaluation, especially if sudden onset or 'worst headache ever.' Keep a headache diary and consult your doctor. Consider emergency care if accompanied by fever, neck stiffness, or neurological symptoms."
                else:
                    ai_response = "For mild to moderate headaches, try rest, hydration, and over-the-counter pain relief. Identify and avoid triggers. If headaches are frequent, severe, or changing pattern, consult a healthcare provider."
            elif re.search(r'fever|cold|flu', message_lower):
                detected_condition = "fever"
                if re.search(r'high|severe|over 101', message_lower):
                    ai_response = "For high fever (above 101.3°F/38.5°C), monitor closely and consider contacting your doctor. Stay hydrated, rest, and use fever-reducing medications as directed. If fever persists or worsens, seek medical care."
                else:
                    ai_response = "For mild fever, rest, stay hydrated, and monitor your temperature. Over-the-counter fever reducers can help. If symptoms persist beyond 3-5 days or worsen, consult a healthcare provider."
            elif re.search(r'anxious|anxiety|stress|stressed|worry|worried|panic|panic attack|overwhelmed|depression|sad|hopeless', message_lower):
                detected_condition = "anxiety"
                if re.search(r'severe|extreme|can\'t cope|suicidal|want to die|harm myself', message_lower):
                    ai_response = "🚨 URGENT: If you're having severe anxiety, panic attacks, or thoughts of self-harm, please seek immediate help. Call emergency services (911/112) or contact a crisis hotline. You don't have to go through this alone - help is available 24/7."
                else:
                    ai_response = "For mild to moderate anxiety and stress, consider these approaches: 1) Practice deep breathing and mindfulness exercises, 2) Maintain regular sleep schedule, 3) Exercise regularly (even 20-30 minutes daily helps), 4) Limit caffeine and alcohol, 5) Talk to friends, family, or a mental health professional. If symptoms persist or worsen, consult with a healthcare provider about potential treatment options including therapy or medication."
            elif re.search(r'medicine|medicines|medication|drugs|pills|prescription', message_lower):
                ai_response = "I understand you're asking about medicines. For proper medication recommendations, I need to know your specific symptoms or condition. Different conditions require different treatments - for example, headaches may respond to pain relievers, while anxiety might require different approaches. Please describe your symptoms so I can provide appropriate guidance. Always consult with a healthcare professional before starting any new medication."
            else:
                ai_response = f"I understand you mentioned: '{prompt}'. For a proper medical consultation, please consult with a healthcare professional."
            
            print(f"🎯 Rule-based AI Response: {ai_response[:100]}...")
            
            # Get medicine recommendations if condition detected
            if detected_condition:
                medicines = get_medicine_recommendations(detected_condition, severity="moderate")
                print(f"💊 Detected condition: {detected_condition}")
                
                # Generate medicine summary
                medicine_summary = generate_medicine_summary(detected_condition, medicines)
                
                # Check for drug interactions if multiple medicines
                interactions = []
                if medicines and len(medicines.get("medications", [])) > 1:
                    interactions = get_medicine_interactions(medicines["medications"])
            else:
                medicines = None
                medicine_summary = None
                interactions = []
            
            # Save fallback response to history
            await save_chat_history(
                user_email,
                prompt,
                ai_response,
                detected_condition,
                medicines,
                urgency="normal",
                category="general_health",
                keywords=[],
                medicine_summary=medicine_summary,
                interactions=interactions,
            )
            
            return {
                "reply": ai_response,
                "detected_condition": detected_condition,
                "medicines": medicines,
                "medicine_summary": medicine_summary,
                "interactions": interactions,
                "urgency": "normal",
                "category": "general_health",
                "keywords": [],
                "timestamp": datetime.utcnow().isoformat()
            }

    except Exception as e:
        print(f"❌ Chat error: {str(e)}")
        error_response = "I'm having trouble processing your request right now. Please try again later or consult with a healthcare professional for medical concerns."
        
        # Save error to history
        await save_chat_history(
            user_email,
            prompt,
            error_response,
            None,
            None,
            urgency="normal",
            category="error",
            keywords=[],
            medicine_summary=None,
            interactions=[],
        )
        
        return {
            "reply": error_response,
            "detected_condition": None,
            "medicines": None,
            "medicine_summary": None,
            "interactions": [],
            "timestamp": datetime.utcnow().isoformat()
        }
