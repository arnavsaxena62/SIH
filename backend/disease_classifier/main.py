import os
import base64
import requests
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from kindwise import CropHealthApi

# Load .env
load_dotenv()
KINDWISE_API_KEY = os.getenv("KINDWISE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not KINDWISE_API_KEY:
    raise Exception("Missing KINDWISE_API_KEY. Please add it to your .env file.")
if not GEMINI_API_KEY:
    raise Exception("Missing GEMINI_API_KEY. Please add it to your .env file.")

# Kindwise API client
kindwise_api = CropHealthApi(api_key=KINDWISE_API_KEY)

# Define FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper function to get cure and remedies from Gemini
def get_remedies_from_gemini(disease_name):
    """Calls the Gemini API to get information about cures and remedies."""
    try:
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent"
        headers = {
            "Content-Type": "application/json"
        }
        
        prompt = f"Act as a world-class plant health expert. Provide a concise, bulleted list of 2 or 3 professional cures and common local remedies for the plant disease: {disease_name}. Keep the total response between 45-50 words. Where applicable, mention companies like Flipkart and Amazon. Provide the response in both English and Malayalam, without using asterisks or any other special formatting characters."

        payload = {
            "contents": [{ "parts": [{ "text": prompt }] }],
            "tools": [{ "google_search": {} }]
        }
        
        # Make the POST request to the Gemini API
        response = requests.post(url, headers=headers, json=payload, params={"key": GEMINI_API_KEY})
        response.raise_for_status() # Raises an exception for bad responses (4xx or 5xx)
        
        data = response.json()
        
        # Check for a valid response structure and parse the text
        if data and 'candidates' in data and data['candidates'][0].get('content'):
            generated_text = data['candidates'][0]['content']['parts'][0]['text']
            # Remove asterisks and other unwanted formatting
            generated_text = generated_text.replace('*', '').replace('•', '').replace('●', '').replace('-', '')
            # Split the text by newlines and filter out empty strings
            remedies_list = [line.strip() for line in generated_text.split('\n') if line.strip()]
            return remedies_list
        return ["Remedy information not available.", "ചികിത്സാ വിവരങ്ങൾ ലഭ്യമല്ല."]
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return ["Remedy information not available.", "ചികിത്സാ വിവരങ്ങൾ ലഭ്യമല്ല."]

@app.get("/")
def read_root():
    return {
        "message": "Crop Disease Identification API is running!",
        "instructions": "Visit /docs to test the `/identify` endpoint by uploading an image."
    }

@app.post("/identify")
async def identify_disease(image: UploadFile = File(...)):
    """
    Identifies a plant disease using the Kindwise API and gets additional
    remedy information from the Gemini API.
    """
    try:
        # Read uploaded image and convert to base64
        image_bytes = await image.read()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        # Call Kindwise API
        kindwise_response = kindwise_api.identify(
            image=image_b64,
            details=["disease", "crop", "wiki_url"],
            language="en"
        )
        
        crop_name = None
        disease_name = None
        wiki_url = None

        if kindwise_response.result and kindwise_response.result.crop.suggestions:
            crop_name = kindwise_response.result.crop.suggestions[0].name

        if kindwise_response.result and kindwise_response.result.disease.suggestions:
            disease_name = kindwise_response.result.disease.suggestions[0].name
            wiki_url = kindwise_response.result.disease.suggestions[0].details.get("wiki_url")

        # Get cures and remedies using Gemini, if a disease was found
        remedies_text = ["Remedy information not available.", "ചികിത്സാ വിവരങ്ങൾ ലഭ്യമല്ല."]
        if disease_name:
            remedies_text = get_remedies_from_gemini(disease_name)

        return JSONResponse(content={
            "plant_name": crop_name,
            "disease_name": disease_name,
            "wiki_url": wiki_url,
            "remedies": remedies_text
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
