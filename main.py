import os
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from gemini_service import analyze_image_with_gemini, chat_with_gemini
from plantid_service import analyze_image_with_plantid
from PIL import Image
import io
from supabase import create_client, Client
from auth_utils import get_password_hash, verify_password, create_access_token
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Plant Disease Detection AI")

# Safer Supabase Initialization
def get_supabase() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("CRITICAL: SUPABASE_URL or SUPABASE_KEY missing!")
        return None
    try:
        return create_client(url, key)
    except Exception as e:
        print(f"CRITICAL: Failed to init Supabase: {e}")
        return None

supabase = get_supabase()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/register")
async def register(request: dict):
    if not supabase:
        return JSONResponse(status_code=500, content={"error": "Database connection failed. Check your Vercel Environment Variables."})
    
    email = request.get("email")
    password = request.get("password")
    
    if not email or not password:
        return JSONResponse(status_code=400, content={"error": "Email and password are required"})
    
    try:
        # Check if user already exists
        response = supabase.table("users").select("*").eq("email", email).execute()
        if response.data:
            return JSONResponse(status_code=400, content={"error": "User already exists"})
        
        # Hash password and save to Supabase
        hashed_password = get_password_hash(password)
        new_user = {
            "email": email,
            "password": hashed_password
        }
        
        supabase.table("users").insert(new_user).execute()
        return {"message": "User registered successfully"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Database Error: {str(e)}"})

@app.post("/login")
async def login_route(request: dict):
    if not supabase:
        return JSONResponse(status_code=500, content={"error": "Database connection failed. Check your Vercel Environment Variables."})
    
    email = request.get("email")
    password = request.get("password")
    
    if not email or not password:
        return JSONResponse(status_code=400, content={"error": "Email and password are required"})
    
    try:
        # Fetch user from Supabase
        response = supabase.table("users").select("*").eq("email", email).execute()
        if not response.data:
            return JSONResponse(status_code=401, content={"error": "Invalid email or password"})
        
        user = response.data[0]
        if not verify_password(password, user["password"]):
            return JSONResponse(status_code=401, content={"error": "Invalid email or password"})
        
        # Create JWT token
        access_token = create_access_token(data={"sub": email})
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "email": email
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Database Error: {str(e)}"})

@app.get("/weather")
async def get_weather(city: str = "solapur"):
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        return JSONResponse(status_code=500, content={"error": "Weather API key not configured"})
    
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(url)
        return JSONResponse(content=response.json())
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/analyze")
async def analyze_plant(
    image: UploadFile = File(...),
    language: str = Form("english")
):
    try:
        contents = await image.read()
        
        # Use a unique filename to avoid conflicts
        import uuid
        temp_path = f"temp_{uuid.uuid4()}.jpg"
        with open(temp_path, "wb") as f:
            f.write(contents)
        
        # Perform analysis with Gemini
        result = analyze_image_with_gemini(temp_path, language=language)
        
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        if not result:
            return JSONResponse(status_code=500, content={"error": "AI analysis failed"})
            
        # Ensure result is returned with UTF-8 encoding
        return JSONResponse(
            content=result,
            media_type="application/json; charset=utf-8"
        )
    except Exception as e:
        print(f"Analyze Error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/chat")
async def chat_bot(request: dict):
    message = request.get("message")
    context = request.get("context", "")
    language = request.get("language", "english")
    
    if not message:
        return JSONResponse(status_code=400, content={"error": "Message is required"})
        
    response_text = chat_with_gemini(message, context=context, language=language)
    return JSONResponse(
        content={"response": response_text},
        media_type="application/json; charset=utf-8"
    )

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Backend is alive!", "db_connected": supabase is not None}

@app.get("/")
def read_root():
    return JSONResponse(
        content={"message": "Welcome to GreenMind AI API", "status": "running"},
        media_type="application/json; charset=utf-8"
    )
