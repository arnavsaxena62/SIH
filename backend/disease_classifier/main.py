# main.py

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from kindwise import CropHealthApi
from dotenv import load_dotenv
import base64
import os

# Load API Key from .env
load_dotenv()
API_KEY = os.getenv("KINDWISE_API_KEY")

# Check API key
if not API_KEY:
    raise Exception("Missing KINDWISE_API_KEY. Set it in .env file or hardcode for testing.")

# Initialize Kindwise SDK
api = CropHealthApi(api_key=API_KEY)

# Create FastAPI app
app = FastAPI()

@app.post("/identify")
async def identify_disease(image: UploadFile = File(...)):
    try:
        # Read and encode the uploaded image
        image_bytes = await image.read()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        # Call Kindwise API
        response = api.identify(
            image=image_b64,
            details=["disease", "crop", "wiki_url"],  # Add more as needed
            language="en"
        )

        # Return the full JSON result
        return JSONResponse(content=response.__dict__)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
