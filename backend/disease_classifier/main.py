# main.py

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from kindwise import CropHealthApi
from dotenv import load_dotenv
import base64
import os

# Load API Key from .env
load_dotenv()
API_KEY = os.getenv("KINDWISE_API_KEY")

if not API_KEY:
    raise Exception("Missing KINDWISE_API_KEY.")

api = CropHealthApi(api_key=API_KEY)
app = FastAPI()


@app.post("/identify")
async def identify_disease(image: UploadFile = File(...)):
    try:
        image_bytes = await image.read()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        response = api.identify(
            image=image_b64,
            details=["disease", "crop", "wiki_url"],
            language="en"
        )

        return JSONResponse(content=jsonable_encoder(response))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
