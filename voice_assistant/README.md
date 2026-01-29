# Multilingual Voice Assistant for Medical Prediction App

## Overview

This voice assistant module provides multilingual voice interaction capabilities for the medical prediction web app. It supports **Telugu**, **Hindi**, and **English** languages for both speech recognition and text-to-speech synthesis.

## Features

### 🎤 Speech Recognition
- **Google Speech Recognition API** integration
- **Auto-language detection** for Telugu, Hindi, and English
- **Medical entity extraction** (name, age, symptoms, intent)
- **Robust error handling** for unclear audio

### 🔊 Text-to-Speech
- **Multilingual TTS** using gTTS (Google Text-to-Speech)
- **Offline TTS** support with pyttsx3
- **Natural voice synthesis** in detected language
- **Medical response templates** in multiple languages

### 📱 WhatsApp Integration
- **Twilio WhatsApp API** integration
- **Prediction result notifications**
- **Appointment confirmations**
- **Doctor notifications**
- **Multilingual message templates**

### 🏥 Medical Integration
- **Heart disease prediction** via voice input
- **Alzheimer's disease prediction** via voice input
- **Appointment booking** through voice commands
- **Doctor contact** requests
- **Seamless integration** with existing backend routes

## Architecture

```
voice_assistant/
├── __init__.py              # Module initialization
├── speech_handler.py        # Speech-to-text processing
├── tts_handler.py          # Text-to-speech processing
├── whatsapp_service.py     # WhatsApp integration
└── voice_assistant.py      # Main integration module

routes/
└── voice_assistant.py      # FastAPI router endpoints
```

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file with the following variables:

```env
# Twilio WhatsApp Configuration
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

# Backend Configuration
BASE_URL=http://localhost:8000
```

### 3. Audio Dependencies (Windows)

For Windows users, you may need to install additional audio dependencies:

```bash
pip install pyaudio
```

If you encounter issues with PyAudio, try:

```bash
pip install pipwin
pipwin install pyaudio
```

## API Endpoints

### Voice Processing

#### POST `/voice-assistant/process`
Process voice input and return audio response.

**Parameters:**
- `file`: Audio file (wav, mp3, ogg)
- `user_whatsapp`: WhatsApp number (optional)
- `language_hint`: Language hint (en, hi, te) (optional)

**Response:**
- Audio file (MP3) with spoken response
- Headers with transcription and metadata

#### POST `/voice-assistant/process-text`
Process text input for testing purposes.

**Parameters:**
- `text`: Text input to process
- `language`: Language of the text
- `user_whatsapp`: WhatsApp number (optional)

### Status and Configuration

#### GET `/voice-assistant/status`
Get status of all voice assistant components.

#### GET `/voice-assistant/supported-languages`
Get list of supported languages.

#### GET `/voice-assistant/voices`
Get information about available TTS voices.

### Testing

#### POST `/voice-assistant/test-whatsapp`
Test WhatsApp service functionality.

#### POST `/voice-assistant/simulate-prediction`
Simulate a prediction for testing purposes.

## Usage Examples

### 1. Basic Voice Processing

```python
from voice_assistant import VoiceAssistant

# Initialize voice assistant
va = VoiceAssistant()

# Process voice input
with open('audio.wav', 'rb') as f:
    audio_data = f.read()

result = va.process_voice_input(
    audio_data=audio_data,
    user_whatsapp="+919876543210",
    language_hint="hi"
)

print(f"Transcription: {result['transcription']['text']}")
print(f"Detected Language: {result['transcription']['language']}")
print(f"Intent: {result['entities']['intent']}")
```

### 2. Heart Disease Prediction

**Voice Input:** "मेरा नाम राम है, मैं 45 साल का हूं, मुझे सीने में दर्द हो रहा है"

**Response:** 
- Transcribes to text
- Extracts: name="राम", age=45, symptoms=["सीने", "दर्द"]
- Detects intent: "heart"
- Calls heart prediction API
- Generates Hindi TTS response
- Sends WhatsApp notification

### 3. Alzheimer's Prediction

**Voice Input:** "I am John, 70 years old, I have memory problems"

**Response:**
- Transcribes to text
- Extracts: name="John", age=70, symptoms=["memory"]
- Detects intent: "alzheimer"
- Calls Alzheimer's prediction API
- Generates English TTS response
- Sends WhatsApp notification

### 4. Appointment Booking

**Voice Input:** "నేను రాజు, నాకు డాక్టర్‌ను కలవాలి"

**Response:**
- Transcribes to text
- Extracts: name="రాజు", intent="appointment"
- Books appointment
- Generates Telugu TTS response
- Sends WhatsApp confirmation

## Language Support

### Speech Recognition Languages
- **English (en)**: en-US
- **Hindi (hi)**: hi-IN
- **Telugu (te)**: te-IN
- **Tamil (ta)**: ta-IN
- **Kannada (kn)**: kn-IN
- **Malayalam (ml)**: ml-IN
- **Bengali (bn)**: bn-IN
- **Gujarati (gu)**: gu-IN
- **Marathi (mr)**: mr-IN
- **Punjabi (pa)**: pa-IN

### Text-to-Speech Languages
- **English (en)**: Native support
- **Hindi (hi)**: Native support
- **Telugu (te)**: Native support
- **Tamil (ta)**: Native support
- **Kannada (kn)**: Native support
- **Malayalam (ml)**: Native support
- **Bengali (bn)**: Native support
- **Gujarati (gu)**: Native support
- **Marathi (mr)**: Native support
- **Punjabi (pa)**: Native support

## Medical Entity Extraction

The system automatically extracts:

### Personal Information
- **Name**: "मेरा नाम राम है" → name="राम"
- **Age**: "मैं 45 साल का हूं" → age=45

### Symptoms
- **Heart symptoms**: chest pain, shortness of breath, heart attack
- **Memory symptoms**: memory loss, forgetfulness, dementia
- **General symptoms**: fever, headache, fatigue

### Intent Detection
- **heart**: Heart disease prediction
- **alzheimer**: Alzheimer's prediction
- **appointment**: Book appointment
- **contact**: Contact doctor
- **general**: General medical query

## WhatsApp Integration

### Message Types

#### Prediction Results
- Heart disease prediction results
- Alzheimer's prediction results
- Risk levels and recommendations
- Next steps and follow-up instructions

#### Appointment Confirmations
- Appointment date and time
- Doctor and department information
- Preparation instructions
- Contact information

#### Doctor Notifications
- Patient information and symptoms
- Request type and priority
- Action required
- Contact details

### Message Templates

Messages are automatically formatted in the detected language with:
- **Professional formatting**
- **Medical terminology**
- **Clear instructions**
- **Contact information**
- **Emergency procedures**

## Error Handling

### Speech Recognition Errors
- **UnknownValueError**: Audio not understood
- **RequestError**: Service unavailable
- **Fallback**: Retry with different language

### TTS Errors
- **Online TTS failure**: Fallback to offline TTS
- **Offline TTS failure**: Return text response
- **Language not supported**: Fallback to English

### WhatsApp Errors
- **Service unavailable**: Log error, continue processing
- **Invalid number**: Return error message
- **Rate limiting**: Queue message for retry

## Testing

### 1. Test Voice Processing

```bash
curl -X POST "http://localhost:8000/voice-assistant/process" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test_audio.wav" \
  -F "user_whatsapp=+919876543210" \
  -F "language_hint=hi"
```

### 2. Test Text Processing

```bash
curl -X POST "http://localhost:8000/voice-assistant/process-text" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "text=I have chest pain" \
  -F "language=en" \
  -F "user_whatsapp=+919876543210"
```

### 3. Test WhatsApp Service

```bash
curl -X POST "http://localhost:8000/voice-assistant/test-whatsapp" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "phone_number=+919876543210" \
  -F "message=Test message" \
  -F "language=en"
```

## Configuration

### Twilio Setup

1. **Create Twilio Account**: Sign up at [twilio.com](https://twilio.com)
2. **Get Credentials**: Account SID and Auth Token
3. **Enable WhatsApp**: Use Twilio Sandbox for testing
4. **Set Environment Variables**: Add to `.env` file

### Audio Configuration

#### Microphone Setup
- **Sample Rate**: 16kHz recommended
- **Channels**: Mono
- **Format**: WAV, MP3, or OGG
- **Duration**: 1-30 seconds

#### TTS Configuration
- **Rate**: 150 words per minute
- **Volume**: 0.9 (90%)
- **Voice**: Auto-select based on language

## Troubleshooting

### Common Issues

#### 1. Speech Recognition Not Working
- Check internet connection
- Verify audio file format
- Try different language hints
- Check microphone permissions

#### 2. TTS Not Generating Audio
- Check internet connection for gTTS
- Verify language code support
- Try offline TTS fallback
- Check audio drivers

#### 3. WhatsApp Not Sending
- Verify Twilio credentials
- Check phone number format
- Ensure WhatsApp number is valid
- Check Twilio account balance

#### 4. Backend Integration Issues
- Verify API endpoints are accessible
- Check authentication tokens
- Ensure prediction models are loaded
- Verify database connections

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Optimization

### Speech Recognition
- **Audio preprocessing**: Noise reduction
- **Language hints**: Improve accuracy
- **Chunk processing**: Handle long audio
- **Caching**: Store common phrases

### TTS Optimization
- **Voice caching**: Cache common responses
- **Batch processing**: Process multiple requests
- **Compression**: Optimize audio file sizes
- **CDN**: Serve audio files from CDN

### WhatsApp Optimization
- **Message queuing**: Handle high volume
- **Template caching**: Cache message templates
- **Rate limiting**: Respect API limits
- **Error retry**: Implement retry logic

## Security Considerations

### Data Privacy
- **Audio data**: Not stored permanently
- **Transcriptions**: Logged for debugging only
- **Personal information**: Encrypted in transit
- **WhatsApp messages**: Secure delivery

### Authentication
- **API tokens**: Required for all endpoints
- **User validation**: Verify user permissions
- **Rate limiting**: Prevent abuse
- **Input validation**: Sanitize all inputs

## Future Enhancements

### Planned Features
- **OpenAI Whisper**: Better multilingual recognition
- **Custom voice models**: Personalized TTS
- **Real-time processing**: WebSocket support
- **Mobile app**: Native mobile integration
- **Analytics**: Usage tracking and insights

### Integration Opportunities
- **Electronic Health Records**: EHR integration
- **Telemedicine**: Video call integration
- **IoT devices**: Wearable device data
- **AI chatbots**: Enhanced conversation flow

## Support

For technical support or questions:

- **Documentation**: Check this README
- **Issues**: Report on GitHub
- **Email**: support@yourclinic.com
- **Phone**: +91-XXXX-XXXXXX

## License

This voice assistant module is part of the Medical Prediction App and follows the same licensing terms.
