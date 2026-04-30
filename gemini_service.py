import os
import google.generativeai as genai
from PIL import Image
import time
import json
from dotenv import load_dotenv

load_dotenv()

# List of API Keys for rotation - dynamically loaded from environment
def load_api_keys():
    keys = []
    # Check for GEMINI_API_KEY and GEMINI_API_KEY_1, _2, etc.
    if os.getenv("GEMINI_API_KEY"):
        keys.append(os.getenv("GEMINI_API_KEY"))
    
    for i in range(1, 21): # Support up to 20 keys
        k = os.getenv(f"GEMINI_API_KEY_{i}")
        if k and k not in keys:
            keys.append(k)
    return keys

API_KEYS = load_api_keys()
print(f"DEBUG: Loaded {len(API_KEYS)} Gemini API keys for rotation.")

def analyze_image_with_gemini(image_path, language="english"):
    if not API_KEYS:
        print("ERROR: No Gemini API keys found!")
        return None

    prompt = f"""
    Analyze this plant leaf image and provide a detailed report in JSON format.
    The response must be in {language}.
    
    JSON structure:
    {{
        "is_plant": boolean,
        "plant": "name of the plant",
        "disease": "name of the disease or 'Healthy'",
        "confidence": "95%", 
        "description": "brief description",
        "cause": "what caused this",
        "solution": "how to fix it"
    }}
    
    If it is NOT a plant leaf, set is_plant to false.
    """

    all_errors = []
    for i, key in enumerate(API_KEYS):
        try:
            print(f"DEBUG: Using Gemini Key #{i+1}...")
            genai.configure(api_key=key)
            
            # Try primary model
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                img = Image.open(image_path)
                response = model.generate_content([prompt, img])
            except Exception as e:
                error_str = str(e).lower()
                if "429" in error_str or "quota" in error_str:
                    print(f"WARNING: Key #{i+1} quota exceeded. Rotating...")
                    continue # Skip to next key
                
                print(f"DEBUG: 1.5-flash failed, trying fallback 2.0-flash... ({e})")
                model = genai.GenerativeModel('gemini-2.0-flash')
                img = Image.open(image_path)
                response = model.generate_content([prompt, img])
            
            if not response or not response.text:
                continue
                
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:-3].strip()
            elif text.startswith("```"):
                text = text[3:-3].strip()
                
            return json.loads(text)
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                print(f"WARNING: Key #{i+1} exhausted. Rotating...")
                continue
            all_errors.append(error_msg)
            print(f"ERROR: Gemini Key #{i+1} failed: {error_msg}")
            continue
                
    if any("429" in err or "quota" in err.lower() for err in all_errors):
        return {"error": "QUOTA_EXCEEDED"}
    
    return None

def chat_with_gemini(message, context="", language="english"):
    if not API_KEYS:
        return "Gemini API key not configured."

    full_prompt = f"System: You are an agricultural expert AI. Language: {language}. Context: {context}\nUser: {message}"

    for i, key in enumerate(API_KEYS):
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                print(f"WARNING: Chat Key #{i+1} quota exceeded. Rotating...")
                continue
            return f"Error: {str(e)}"
            
    return "All API keys are exhausted. Please try again later."
