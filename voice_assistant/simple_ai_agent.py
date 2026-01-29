"""
Simple AI Agent for Messages and Calls
Replaces Twilio with a simple notification system for illiterate users
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleAIAgent:
    def __init__(self):
        """
        Initialize Simple AI Agent for messages and calls
        Designed for illiterate users with voice-based interactions
        """
        self.notifications = []
        self.call_logs = []
        
        # Simple message templates in multiple languages
        self.message_templates = {
            'en': {
                'heart_result': """
🏥 *Medical Prediction Result*

*Heart Health Analysis:*
• Prediction: {prediction}
• Risk Level: {risk_level}
• Risk Percentage: {risk_percentage}%
• Confidence: {confidence}%

*Recommendations:*
• Consult a cardiologist for detailed examination
• Follow a heart-healthy diet
• Regular exercise and stress management
• Monitor blood pressure regularly

*Next Steps:*
• Schedule an appointment with our cardiologist
• Get additional tests if recommended
• Follow up in 3 months

For emergency: Call 108 or visit nearest hospital
                """,
                'alzheimer_result': """
🧠 *Medical Prediction Result*

*Cognitive Health Analysis:*
• Prediction: {prediction}
• Severity Level: {severity_level}
• Risk Level: {risk_level}
• Risk Percentage: {risk_percentage}%
• Confidence: {confidence}%

*Recommendations:*
• Consult a neurologist for detailed assessment
• Engage in cognitive exercises
• Maintain social connections
• Regular mental stimulation activities

*Next Steps:*
• Schedule an appointment with our neurologist
• Consider cognitive assessment tests
• Family support and monitoring

For urgent concerns: Contact our emergency line
                """,
                'appointment_confirmed': """
📅 *Appointment Confirmed*

*Appointment Details:*
• Date: {appointment_date}
• Time: {appointment_time}
• Doctor: {doctor_name}
• Department: {department}
• Location: {location}

*Preparation:*
• Bring your medical records
• Arrive 15 minutes early
• Bring a list of current medications
• Prepare questions for the doctor

*Contact:* {clinic_phone}
*Address:* {clinic_address}

We look forward to seeing you!
                """,
                'doctor_notification': """
🚨 *Patient Alert*

*Patient Information:*
• Name: {patient_name}
• Age: {patient_age}
• Contact: {patient_contact}
• Symptoms: {symptoms}

*Request Type:* {request_type}
*Priority:* {priority}

*Action Required:*
• Review patient information
• Schedule consultation if needed
• Contact patient within 24 hours

Patient is waiting for your response.
                """,
                'general_message': """
🏥 *Medical Assistant Response*

{message}

*Need Help?*
• Call our helpline: {helpline_number}
• Visit our website: {website_url}
• Emergency: Call 108

Thank you for using our medical assistant!
                """
            },
            'hi': {
                'heart_result': """
🏥 *चिकित्सा भविष्यवाणी परिणाम*

*हृदय स्वास्थ्य विश्लेषण:*
• भविष्यवाणी: {prediction}
• जोखिम स्तर: {risk_level}
• जोखिम प्रतिशत: {risk_percentage}%
• आत्मविश्वास: {confidence}%

*सिफारिशें:*
• विस्तृत जांच के लिए हृदय रोग विशेषज्ञ से सलाह लें
• हृदय-स्वस्थ आहार का पालन करें
• नियमित व्यायाम और तनाव प्रबंधन
• रक्तचाप की नियमित निगरानी

*अगले कदम:*
• हमारे हृदय रोग विशेषज्ञ के साथ अपॉइंटमेंट शेड्यूल करें
• सिफारिश की गई अतिरिक्त जांच कराएं
• 3 महीने में फॉलो-अप करें

आपातकाल के लिए: 108 पर कॉल करें या निकटतम अस्पताल जाएं
                """,
                'alzheimer_result': """
🧠 *चिकित्सा भविष्यवाणी परिणाम*

*संज्ञानात्मक स्वास्थ्य विश्लेषण:*
• भविष्यवाणी: {prediction}
• गंभीरता स्तर: {severity_level}
• जोखिम स्तर: {risk_level}
• जोखिम प्रतिशत: {risk_percentage}%
• आत्मविश्वास: {confidence}%

*सिफारिशें:*
• विस्तृत मूल्यांकन के लिए न्यूरोलॉजिस्ट से सलाह लें
• संज्ञानात्मक अभ्यास में संलग्न रहें
• सामाजिक संबंध बनाए रखें
• नियमित मानसिक उत्तेजना गतिविधियां

*अगले कदम:*
• हमारे न्यूरोलॉजिस्ट के साथ अपॉइंटमेंट शेड्यूल करें
• संज्ञानात्मक मूल्यांकन परीक्षण पर विचार करें
• पारिवारिक सहायता और निगरानी

तत्काल चिंताओं के लिए: हमारी आपातकालीन लाइन से संपर्क करें
                """,
                'appointment_confirmed': """
📅 *अपॉइंटमेंट पुष्टि*

*अपॉइंटमेंट विवरण:*
• तारीख: {appointment_date}
• समय: {appointment_time}
• डॉक्टर: {doctor_name}
• विभाग: {department}
• स्थान: {location}

*तैयारी:*
• अपने मेडिकल रिकॉर्ड लाएं
• 15 मिनट पहले पहुंचें
• वर्तमान दवाओं की सूची लाएं
• डॉक्टर के लिए प्रश्न तैयार करें

*संपर्क:* {clinic_phone}
*पता:* {clinic_address}

हम आपसे मिलने की प्रतीक्षा कर रहे हैं!
                """,
                'doctor_notification': """
🚨 *रोगी अलर्ट*

*रोगी जानकारी:*
• नाम: {patient_name}
• आयु: {patient_age}
• संपर्क: {patient_contact}
• लक्षण: {symptoms}

*अनुरोध प्रकार:* {request_type}
• प्राथमिकता: {priority}

*आवश्यक कार्रवाई:*
• रोगी जानकारी की समीक्षा करें
• आवश्यकता होने पर परामर्श शेड्यूल करें
• 24 घंटे के भीतर रोगी से संपर्क करें

रोगी आपकी प्रतिक्रिया की प्रतीक्षा कर रहा है।
                """,
                'general_message': """
🏥 *चिकित्सा सहायक प्रतिक्रिया*

{message}

*सहायता चाहिए?*
• हमारी हेल्पलाइन पर कॉल करें: {helpline_number}
• हमारी वेबसाइट देखें: {website_url}
• आपातकाल: 108 पर कॉल करें

हमारे चिकित्सा सहायक का उपयोग करने के लिए धन्यवाद!
                """
            },
            'te': {
                'heart_result': """
🏥 *వైద్య ఊహాఫలితం*

*గుండె ఆరోగ్య విశ్లేషణ:*
• ఊహాఫలితం: {prediction}
• ప్రమాద స్థాయి: {risk_level}
• ప్రమాద శాతం: {risk_percentage}%
• నమ్మకం: {confidence}%

*సిఫార్సులు:*
• వివరణాత్మక పరీక్ష కోసం కార్డియాలజిస్ట్‌ను సంప్రదించండి
• గుండె-ఆరోగ్యకర ఆహారాన్ని అనుసరించండి
• క్రమమైన వ్యాయామం మరియు ఒత్తిడి నిర్వహణ
• రక్తపోటును క్రమమైనంగా పర్యవేక్షించండి

*తదుపరి దశలు:*
• మా కార్డియాలజిస్ట్‌తో అపాయింట్మెంట్ షెడ్యూల్ చేయండి
• సిఫార్సు చేసిన అదనపు పరీక్షలు చేయించుకోండి
• 3 నెలలలో ఫాలో-అప్ చేయండి

అత్యవసర పరిస్థితులకు: 108 కి కాల్ చేయండి లేదా దగ్గరి ఆసుపత్రికి వెళ్లండి
                """,
                'alzheimer_result': """
🧠 *వైద్య ఊహాఫలితం*

*అభిజ్ఞా ఆరోగ్య విశ్లేషణ:*
• ఊహాఫలితం: {prediction}
• తీవ్రత స్థాయి: {severity_level}
• ప్రమాద స్థాయి: {risk_level}
• ప్రమాద శాతం: {risk_percentage}%
• నమ్మకం: {confidence}%

*సిఫార్సులు:*
• వివరణాత్మక అంచనా కోసం న్యూరాలజిస్ట్‌ను సంప్రదించండి
• అభిజ్ఞా వ్యాయామాలలో నిమగ్నమవండి
• సామాజిక సంబంధాలను నిర్వహించండి
• క్రమమైన మానసిక ఉద్దీపన కార్యకలాపాలు

*తదుపరి దశలు:*
• మా న్యూరాలజిస్ట్‌తో అపాయింట్మెంట్ షెడ్యూల్ చేయండి
• అభిజ్ఞా అంచనా పరీక్షలను పరిగణించండి
• కుటుంబ మద్దతు మరియు పర్యవేక్షణ

తక్షణ ఆందోళనలకు: మా అత్యవసర లైన్‌ను సంప్రదించండి
                """,
                'appointment_confirmed': """
📅 *అపాయింట్మెంట్ నిర్ధారణ*

*అపాయింట్మెంట్ వివరాలు:*
• తేదీ: {appointment_date}
• సమయం: {appointment_time}
• వైద్యుడు: {doctor_name}
• విభాగం: {department}
• స్థానం: {location}

*తయారీ:*
• మీ వైద్య రికార్డులను తీసుకురండి
• 15 నిమిషాల ముందు వచ్చండి
• ప్రస్తుత మందుల జాబితాను తీసుకురండి
• వైద్యుడి కోసం ప్రశ్నలను సిద్ధం చేయండి

*సంప్రదింపు:* {clinic_phone}
*చిరునామా:* {clinic_address}

మేము మిమ్మల్ని చూడటానికి ఎదురుచూస్తున్నాము!
                """,
                'doctor_notification': """
🚨 *రోగి హెచ్చరిక*

*రోగి సమాచారం:*
• పేరు: {patient_name}
• వయస్సు: {patient_age}
• సంప్రదింపు: {patient_contact}
• లక్షణాలు: {symptoms}

*అభ్యర్థన రకం:* {request_type}
• ప్రాధాన్యత: {priority}

*అవసరమైన చర్య:*
• రోగి సమాచారాన్ని సమీక్షించండి
• అవసరమైతే సంప్రదింపును షెడ్యూల్ చేయండి
• 24 గంటలలోపు రోగిని సంప్రదించండి

రోగి మీ ప్రతిస్పందన కోసం వేచి ఉన్నారు।
                """,
                'general_message': """
🏥 *వైద్య సహాయక ప్రతిస్పందన*

{message}

*సహాయం కావాలా?*
• మా హెల్ప్‌లైన్‌కి కాల్ చేయండి: {helpline_number}
• మా వెబ్‌సైట్‌ను చూడండి: {website_url}
• అత్యవసర: 108 కి కాల్ చేయండి

మా వైద్య సహాయకుని ఉపయోగించినందుకు ధన్యవాదాలు!
                """
            }
        }
    
    def send_message(self, message_type: str, language: str = 'en', **kwargs) -> Dict[str, Any]:
        """
        Send a message (simulated - stores in local notifications)
        """
        try:
            message_text = self._get_message_template(message_type, language, **kwargs)
            
            notification = {
                'id': f"msg_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'type': 'message',
                'message_type': message_type,
                'language': language,
                'content': message_text,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'sent'
            }
            
            self.notifications.append(notification)
            logger.info(f"Message sent: {message_type} in {language}")
            
            return {
                'success': True,
                'message_id': notification['id'],
                'message_type': message_type,
                'language': language,
                'content': message_text
            }
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def make_call(self, phone_number: str, message_type: str, language: str = 'en', **kwargs) -> Dict[str, Any]:
        """
        Simulate a call (stores in call logs)
        """
        try:
            message_text = self._get_message_template(message_type, language, **kwargs)
            
            call_log = {
                'id': f"call_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'type': 'call',
                'phone_number': phone_number,
                'message_type': message_type,
                'language': language,
                'content': message_text,
                'timestamp': datetime.utcnow().isoformat(),
                'status': 'completed',
                'duration': '2-3 minutes (simulated)'
            }
            
            self.call_logs.append(call_log)
            logger.info(f"Call made to {phone_number}: {message_type} in {language}")
            
            return {
                'success': True,
                'call_id': call_log['id'],
                'phone_number': phone_number,
                'message_type': message_type,
                'language': language,
                'content': message_text
            }
            
        except Exception as e:
            logger.error(f"Error making call: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_prediction_result(self, prediction_type: str, result_data: Dict[str, Any], language: str = 'en') -> Dict[str, Any]:
        """
        Send prediction result via message
        """
        message_type = f'{prediction_type}_result'
        
        kwargs = {
            'prediction': result_data.get('prediction', 'Unknown'),
            'risk_level': result_data.get('risk_level', 'Unknown'),
            'risk_percentage': result_data.get('risk_percentage', 0),
            'confidence': result_data.get('confidence', 0),
            'severity_level': result_data.get('severity_level', 'Unknown')
        }
        
        return self.send_message(message_type, language, **kwargs)
    
    def send_appointment_confirmation(self, appointment_data: Dict[str, Any], language: str = 'en') -> Dict[str, Any]:
        """
        Send appointment confirmation via message
        """
        kwargs = {
            'appointment_date': appointment_data.get('date', 'TBD'),
            'appointment_time': appointment_data.get('time', 'TBD'),
            'doctor_name': appointment_data.get('doctor', 'Dr. Smith'),
            'department': appointment_data.get('department', 'General Medicine'),
            'location': appointment_data.get('location', 'Main Clinic'),
            'clinic_phone': appointment_data.get('phone', '+91-XXXX-XXXXXX'),
            'clinic_address': appointment_data.get('address', 'Clinic Address')
        }
        
        return self.send_message('appointment_confirmed', language, **kwargs)
    
    def notify_doctor(self, patient_data: Dict[str, Any], request_type: str, language: str = 'en') -> Dict[str, Any]:
        """
        Notify doctor about patient request
        """
        kwargs = {
            'patient_name': patient_data.get('name', 'Unknown'),
            'patient_age': patient_data.get('age', 'Unknown'),
            'patient_contact': patient_data.get('contact', 'Not provided'),
            'symptoms': ', '.join(patient_data.get('symptoms', [])),
            'request_type': request_type,
            'priority': 'High' if 'emergency' in request_type.lower() else 'Normal'
        }
        
        return self.send_message('doctor_notification', language, **kwargs)
    
    def get_notifications(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent notifications
        """
        return self.notifications[-limit:] if self.notifications else []
    
    def get_call_logs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent call logs
        """
        return self.call_logs[-limit:] if self.call_logs else []
    
    def _get_message_template(self, message_type: str, language: str, **kwargs) -> str:
        """
        Get formatted message template
        """
        if language not in self.message_templates:
            language = 'en'
        
        templates = self.message_templates[language]
        
        if message_type in templates:
            try:
                return templates[message_type].format(**kwargs)
            except KeyError as e:
                logger.warning(f"Missing template parameter: {e}")
                return templates[message_type]
        else:
            # Fallback to general message
            return templates['general_message'].format(
                message=f"Message type '{message_type}' not found. Data: {kwargs}",
                helpline_number='+91-XXXX-XXXXXX',
                website_url='https://yourclinic.com'
            )
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get agent status and statistics
        """
        return {
            'agent_type': 'Simple AI Agent',
            'notifications_sent': len(self.notifications),
            'calls_made': len(self.call_logs),
            'supported_languages': list(self.message_templates.keys()),
            'last_activity': self.notifications[-1]['timestamp'] if self.notifications else None,
            'status': 'active'
        }
