"""
Medicine Recommendation Service
Provides comprehensive medicine recommendations based on medical conditions
"""

# Comprehensive medicine database
MEDICINE_DATABASE = {
    "diabetes": {
        "medications": [
            {
                "name": "Metformin",
                "dosage": "500mg twice daily",
                "type": "Oral",
                "description": "First-line treatment for type 2 diabetes",
                "side_effects": ["Nausea", "Diarrhea", "Stomach upset"],
                "contraindications": ["Kidney disease", "Liver disease"],
                "category": "Biguanide"
            },
            {
                "name": "Insulin",
                "dosage": "As prescribed by doctor",
                "type": "Injection",
                "description": "For type 1 and advanced type 2 diabetes",
                "side_effects": ["Hypoglycemia", "Weight gain"],
                "contraindications": ["Hypoglycemia"],
                "category": "Hormone"
            },
            {
                "name": "Glipizide",
                "dosage": "5-10mg daily",
                "type": "Oral",
                "description": "Stimulates insulin production",
                "side_effects": ["Hypoglycemia", "Weight gain"],
                "contraindications": ["Type 1 diabetes"],
                "category": "Sulfonylurea"
            },
            {
                "name": "Sitagliptin",
                "dosage": "100mg daily",
                "type": "Oral",
                "description": "DPP-4 inhibitor",
                "side_effects": ["Upper respiratory infection", "Headache"],
                "contraindications": ["Pancreatitis"],
                "category": "DPP-4 inhibitor"
            }
        ],
        "lifestyle": [
            "Regular exercise (30 minutes daily)",
            "Low-carb diet",
            "Blood sugar monitoring",
            "Regular check-ups",
            "Weight management",
            "Stress management"
        ],
        "monitoring": [
            "HbA1c every 3 months",
            "Blood pressure monitoring",
            "Foot examination",
            "Eye examination annually"
        ]
    },
    "heart_disease": {
        "medications": [
            {
                "name": "Aspirin",
                "dosage": "75-100mg daily",
                "type": "Oral",
                "description": "Prevents blood clots",
                "side_effects": ["Stomach irritation", "Bleeding risk"],
                "contraindications": ["Active bleeding", "Peptic ulcer"],
                "category": "Antiplatelet"
            },
            {
                "name": "Atorvastatin",
                "dosage": "20-80mg daily",
                "type": "Oral",
                "description": "Lowers cholesterol",
                "side_effects": ["Muscle pain", "Liver enzyme elevation"],
                "contraindications": ["Active liver disease"],
                "category": "Statin"
            },
            {
                "name": "Lisinopril",
                "dosage": "5-40mg daily",
                "type": "Oral",
                "description": "ACE inhibitor for blood pressure",
                "side_effects": ["Dry cough", "Dizziness"],
                "contraindications": ["Pregnancy", "Bilateral renal artery stenosis"],
                "category": "ACE inhibitor"
            },
            {
                "name": "Metoprolol",
                "dosage": "25-200mg daily",
                "type": "Oral",
                "description": "Beta-blocker for heart protection",
                "side_effects": ["Fatigue", "Cold hands/feet"],
                "contraindications": ["Severe asthma", "Heart block"],
                "category": "Beta-blocker"
            }
        ],
        "lifestyle": [
            "Heart-healthy diet (Mediterranean diet)",
            "Regular exercise",
            "Quit smoking",
            "Stress management",
            "Limit alcohol",
            "Maintain healthy weight"
        ],
        "monitoring": [
            "Regular blood pressure checks",
            "Cholesterol levels",
            "ECG monitoring",
            "Echocardiogram as needed"
        ]
    },
    "hypertension": {
        "medications": [
            {
                "name": "Amlodipine",
                "dosage": "5-10mg daily",
                "type": "Oral",
                "description": "Calcium channel blocker",
                "side_effects": ["Swelling of ankles", "Dizziness"],
                "contraindications": ["Severe hypotension"],
                "category": "Calcium channel blocker"
            },
            {
                "name": "Losartan",
                "dosage": "25-100mg daily",
                "type": "Oral",
                "description": "ARB for blood pressure control",
                "side_effects": ["Dizziness", "High potassium"],
                "contraindications": ["Pregnancy", "Bilateral renal artery stenosis"],
                "category": "ARB"
            },
            {
                "name": "Hydrochlorothiazide",
                "dosage": "12.5-25mg daily",
                "type": "Oral",
                "description": "Diuretic",
                "side_effects": ["Increased urination", "Low potassium"],
                "contraindications": ["Severe kidney disease"],
                "category": "Diuretic"
            },
            {
                "name": "Carvedilol",
                "dosage": "6.25-25mg twice daily",
                "type": "Oral",
                "description": "Alpha and beta blocker",
                "side_effects": ["Dizziness", "Fatigue"],
                "contraindications": ["Severe asthma", "Heart block"],
                "category": "Alpha-beta blocker"
            }
        ],
        "lifestyle": [
            "Low-sodium diet (<2g daily)",
            "Regular exercise",
            "Weight management",
            "Limit alcohol",
            "Stress reduction",
            "Adequate sleep"
        ],
        "monitoring": [
            "Daily blood pressure monitoring",
            "Regular doctor visits",
            "Kidney function tests",
            "Electrolyte monitoring"
        ]
    },
    "alzheimer": {
        "medications": [
            {
                "name": "Donepezil",
                "dosage": "5-10mg daily",
                "type": "Oral",
                "description": "Cholinesterase inhibitor",
                "side_effects": ["Nausea", "Diarrhea", "Insomnia"],
                "contraindications": ["Severe liver disease"],
                "category": "Cholinesterase inhibitor"
            },
            {
                "name": "Memantine",
                "dosage": "5-20mg daily",
                "type": "Oral",
                "description": "NMDA receptor antagonist",
                "side_effects": ["Dizziness", "Headache", "Confusion"],
                "contraindications": ["Severe kidney disease"],
                "category": "NMDA antagonist"
            },
            {
                "name": "Rivastigmine",
                "dosage": "1.5-6mg twice daily",
                "type": "Oral",
                "description": "Cholinesterase inhibitor",
                "side_effects": ["Nausea", "Vomiting", "Weight loss"],
                "contraindications": ["Severe liver disease"],
                "category": "Cholinesterase inhibitor"
            },
            {
                "name": "Galantamine",
                "dosage": "8-24mg daily",
                "type": "Oral",
                "description": "Cholinesterase inhibitor",
                "side_effects": ["Nausea", "Diarrhea", "Weight loss"],
                "contraindications": ["Severe liver disease"],
                "category": "Cholinesterase inhibitor"
            }
        ],
        "lifestyle": [
            "Mental stimulation (puzzles, reading)",
            "Physical exercise",
            "Social engagement",
            "Healthy diet (Mediterranean)",
            "Adequate sleep",
            "Stress management"
        ],
        "monitoring": [
            "Regular cognitive assessments",
            "Medication adherence monitoring",
            "Safety assessments",
            "Caregiver support"
        ]
    },
    "depression": {
        "medications": [
            {
                "name": "Sertraline",
                "dosage": "50-200mg daily",
                "type": "Oral",
                "description": "SSRI antidepressant",
                "side_effects": ["Nausea", "Insomnia", "Sexual dysfunction"],
                "contraindications": ["MAOI use", "Pimozide"],
                "category": "SSRI"
            },
            {
                "name": "Fluoxetine",
                "dosage": "20-80mg daily",
                "type": "Oral",
                "description": "SSRI antidepressant",
                "side_effects": ["Nausea", "Headache", "Insomnia"],
                "contraindications": ["MAOI use", "Thioridazine"],
                "category": "SSRI"
            },
            {
                "name": "Bupropion",
                "dosage": "150-300mg daily",
                "type": "Oral",
                "description": "NDRI antidepressant",
                "side_effects": ["Dry mouth", "Insomnia", "Headache"],
                "contraindications": ["Seizure disorder", "Eating disorders"],
                "category": "NDRI"
            },
            {
                "name": "Venlafaxine",
                "dosage": "75-225mg daily",
                "type": "Oral",
                "description": "SNRI antidepressant",
                "side_effects": ["Nausea", "Headache", "Sweating"],
                "contraindications": ["MAOI use", "Severe hypertension"],
                "category": "SNRI"
            }
        ],
        "lifestyle": [
            "Regular therapy sessions",
            "Exercise (30 minutes daily)",
            "Sleep hygiene",
            "Social support",
            "Stress management",
            "Healthy diet"
        ],
        "monitoring": [
            "Regular mood assessments",
            "Suicide risk screening",
            "Medication adherence",
            "Side effect monitoring"
        ]
    },
    "asthma": {
        "medications": [
            {
                "name": "Albuterol",
                "dosage": "2-4 puffs as needed",
                "type": "Inhaler",
                "description": "Short-acting beta-agonist for acute relief",
                "side_effects": ["Tremor", "Rapid heartbeat", "Nervousness"],
                "contraindications": ["Severe heart disease"],
                "category": "SABA"
            },
            {
                "name": "Fluticasone",
                "dosage": "1-2 puffs twice daily",
                "type": "Inhaler",
                "description": "Inhaled corticosteroid",
                "side_effects": ["Thrush", "Hoarseness"],
                "contraindications": ["Active infection"],
                "category": "ICS"
            },
            {
                "name": "Montelukast",
                "dosage": "10mg daily",
                "type": "Oral",
                "description": "Leukotriene receptor antagonist",
                "side_effects": ["Headache", "Stomach pain"],
                "contraindications": ["Phenylketonuria"],
                "category": "LTRA"
            }
        ],
        "lifestyle": [
            "Avoid triggers (allergens, smoke)",
            "Regular exercise",
            "Proper inhaler technique",
            "Action plan for attacks",
            "Regular monitoring"
        ],
        "monitoring": [
            "Peak flow monitoring",
            "Symptom tracking",
            "Regular doctor visits",
            "Medication review"
        ]
    },
    "fever": {
        "medications": [
            {
                "name": "Paracetamol (Acetaminophen)",
                "dosage": "500-1000mg every 4-6 hours",
                "type": "Oral",
                "description": "Antipyretic and analgesic for fever and pain relief",
                "side_effects": ["Rare liver damage with overdose", "Skin rash"],
                "contraindications": ["Liver disease", "Alcoholism"],
                "category": "Antipyretic"
            },
            {
                "name": "Ibuprofen",
                "dosage": "200-400mg every 6-8 hours",
                "type": "Oral",
                "description": "NSAID for fever, pain, and inflammation",
                "side_effects": ["Stomach upset", "Dizziness", "Headache"],
                "contraindications": ["Stomach ulcers", "Kidney disease", "Heart disease"],
                "category": "NSAID"
            }
        ],
        "lifestyle": [
            "Rest and stay hydrated", "Cool compresses", "Light clothing",
            "Monitor temperature", "Seek medical help if fever persists"
        ]
    },
    "cough_cold": {
        "medications": [
            {
                "name": "Dextromethorphan",
                "dosage": "15-30mg every 4-6 hours",
                "type": "Oral",
                "description": "Cough suppressant for dry cough",
                "side_effects": ["Drowsiness", "Dizziness", "Nausea"],
                "contraindications": ["MAOI use", "Pregnancy"],
                "category": "Antitussive"
            },
            {
                "name": "Guaifenesin",
                "dosage": "200-400mg every 4 hours",
                "type": "Oral",
                "description": "Expectorant to loosen mucus",
                "side_effects": ["Nausea", "Vomiting", "Dizziness"],
                "contraindications": ["Severe kidney disease"],
                "category": "Expectorant"
            }
        ],
        "lifestyle": [
            "Increase fluid intake", "Rest adequately", "Use humidifier",
            "Avoid smoking", "Wash hands frequently"
        ]
    },
    "headache": {
        "medications": [
            {
                "name": "Ibuprofen",
                "dosage": "200-400mg every 4-6 hours",
                "type": "Oral",
                "description": "NSAID for headache and inflammation",
                "side_effects": ["Stomach upset", "Dizziness"],
                "contraindications": ["Stomach ulcers", "Kidney disease"],
                "category": "NSAID"
            },
            {
                "name": "Acetaminophen",
                "dosage": "500-1000mg every 4-6 hours",
                "type": "Oral",
                "description": "Pain reliever for mild to moderate headache",
                "side_effects": ["Rare liver damage with overdose"],
                "contraindications": ["Liver disease"],
                "category": "Analgesic"
            }
        ],
        "lifestyle": [
            "Rest in dark, quiet room", "Apply cold compress", "Stay hydrated",
            "Avoid triggers", "Regular sleep schedule"
        ]
    }
}

def detect_medical_condition(prompt: str) -> str:
    """Enhanced condition detection with more keywords"""
    prompt_lower = prompt.lower()
    
    # Enhanced keywords for different conditions
    conditions = {
        "diabetes": [
            "diabetes", "diabetic", "blood sugar", "glucose", "insulin", 
            "hyperglycemia", "hypoglycemia", "a1c", "hba1c", "type 1", "type 2",
            "diabetic ketoacidosis", "diabetic neuropathy"
        ],
        "heart_disease": [
            "heart", "cardiac", "chest pain", "angina", "heart attack", 
            "cardiovascular", "myocardial infarction", "coronary", "arrhythmia",
            "atrial fibrillation", "heart failure", "cardiac arrest"
        ],
        "hypertension": [
            "blood pressure", "hypertension", "high bp", "hypertensive",
            "elevated blood pressure", "systolic", "diastolic"
        ],
        "alzheimer": [
            "alzheimer", "dementia", "memory loss", "cognitive", "forgetfulness",
            "confusion", "cognitive decline", "memory problems", "alzheimer's"
        ],
        "depression": [
            "depression", "depressed", "sad", "anxiety", "mental health", 
            "mood", "suicidal", "hopeless", "worthless", "guilt", "fatigue",
            "concentration problems", "sleep problems"
        ],
        "asthma": [
            "asthma", "wheezing", "shortness of breath", "chest tightness",
            "coughing", "breathing problems", "respiratory", "bronchospasm"
        ],
        "fever": [
            "fever", "high temperature", "pyrexia", "hot", "burning", "chills",
            "sweating", "body temperature", "febrile"
        ],
        "cough_cold": [
            "cough", "cold", "flu", "influenza", "sore throat", "runny nose",
            "congestion", "nasal", "sneezing", "phlegm", "mucus", "chest congestion",
            "upper respiratory", "viral infection", "common cold"
        ],
        "headache": [
            "headache", "head pain", "migraine", "tension", "throbbing",
            "pounding", "head ache", "cephalgia"
        ],
        "stomach_issues": [
            "stomach", "stomachache", "stomach pain", "abdominal pain", "belly pain",
            "indigestion", "upset stomach", "nausea", "vomiting", "diarrhea",
            "constipation", "gastric", "gastrointestinal"
        ]
    }
    
    # Score each condition based on keyword matches
    condition_scores = {}
    for condition, keywords in conditions.items():
        score = sum(1 for keyword in keywords if keyword in prompt_lower)
        if score > 0:
            condition_scores[condition] = score
    
    # Return the condition with the highest score
    if condition_scores:
        return max(condition_scores, key=condition_scores.get)
    
    return None

def get_medicine_recommendations(condition: str, severity: str = "moderate") -> dict:
    """Get comprehensive medicine recommendations for a specific condition"""
    if condition not in MEDICINE_DATABASE:
        return None
    
    base_recommendations = MEDICINE_DATABASE[condition].copy()
    
    # Adjust recommendations based on severity
    if severity == "mild":
        # For mild cases, recommend fewer medications
        base_recommendations["medications"] = base_recommendations["medications"][:2]
    elif severity == "severe":
        # For severe cases, include all medications
        pass
    
    return base_recommendations

def get_medicine_interactions(medicines: list) -> list:
    """Check for potential drug interactions"""
    # This is a simplified interaction checker
    # In a real system, you'd use a comprehensive drug interaction database
    
    interactions = []
    
    # Check for common interactions
    medicine_names = [med["name"].lower() for med in medicines]
    
    # Common interaction patterns
    if "warfarin" in medicine_names and "aspirin" in medicine_names:
        interactions.append({
            "medicines": ["Warfarin", "Aspirin"],
            "severity": "High",
            "description": "Increased bleeding risk",
            "recommendation": "Monitor INR closely"
        })
    
    if "metformin" in medicine_names and "insulin" in medicine_names:
        interactions.append({
            "medicines": ["Metformin", "Insulin"],
            "severity": "Moderate",
            "description": "Increased risk of hypoglycemia",
            "recommendation": "Monitor blood glucose closely"
        })
    
    return interactions

def generate_medicine_summary(condition: str, medicines: dict) -> str:
    """Generate a human-readable summary of medicine recommendations"""
    if not medicines:
        return "No specific medicine recommendations available for this condition."
    
    summary = f"**Medicine Recommendations for {condition.replace('_', ' ').title()}:**\n\n"
    
    # Add medications
    summary += "**Medications:**\n"
    for med in medicines.get("medications", []):
        summary += f"• {med['name']} ({med['dosage']}) - {med['description']}\n"
        if med.get("side_effects"):
            summary += f"  Side effects: {', '.join(med['side_effects'])}\n"
        summary += "\n"
    
    # Add lifestyle recommendations
    if medicines.get("lifestyle"):
        summary += "**Lifestyle Recommendations:**\n"
        for item in medicines["lifestyle"]:
            summary += f"• {item}\n"
        summary += "\n"
    
    # Add monitoring recommendations
    if medicines.get("monitoring"):
        summary += "**Monitoring Requirements:**\n"
        for item in medicines["monitoring"]:
            summary += f"• {item}\n"
    
    summary += "\n**⚠️ Important:** Always consult with a healthcare professional before starting any new medication."
    
    return summary
