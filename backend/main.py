import os
import requests
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import osmnx as ox
import geopandas as gpd
import pandas as pd
from pydantic import BaseModel, validator
from typing import List, Dict
from dotenv import load_dotenv
from cache_manager import CacheManager
from history_manager import HistoryManager

try:
    import google.genai as genai
    USING_NEW_GENAI = True
except ImportError:
    import google.generativeai as genai
    USING_NEW_GENAI = False

# --- 1. LOAD ENVIRONMENT VARIABLES ---
load_dotenv()

# --- 2. SETUP APP ---
app = FastAPI(title="Market Gap Hunter API V2")

# Initialize Cache Manager
cache = CacheManager(cache_dir="cache", ttl_hours=24)

# Initialize History Manager
history = HistoryManager(history_file="analysis_history.json")

# Security: Load API Key from environment
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("❌ GOOGLE_API_KEY not found in environment variables!")

# Configure Gemini API
if USING_NEW_GENAI:
    client = genai.Client(api_key=GOOGLE_API_KEY)
    print("✅ Using new google.genai package")
else:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    print("⚠️ Using deprecated google.generativeai package")

# Rate Limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 3. CONFIGURATION ---
BUSINESS_MAPPINGS = {
    "Cafe": {"tags": {"amenity": "cafe"}},
    "Restaurant": {"tags": {"amenity": "restaurant"}},
    "Bar/Pub": {"tags": {"amenity": ["bar", "pub"]}},
    "Convenience Store": {"tags": {"shop": "convenience"}},
    "Pharmacy": {"tags": {"amenity": "pharmacy"}},
    "Gym/Fitness": {"tags": {"leisure": "fitness_centre"}},
    "Coworking Space": {"tags": {"amenity": "coworking_space"}},
}

# --- 4. PYDANTIC MODELS WITH VALIDATION ---
class AnalyzeRequest(BaseModel):
    lat: float
    lon: float
    business_type: str
    radius: int = 1000

    @validator('lat')
    def validate_lat(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Latitude must be between -90 and 90')
        return v
    
    @validator('lon')
    def validate_lon(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Longitude must be between -180 and 180')
        return v
    
    @validator('radius')
    def validate_radius(cls, v):
        if not 100 <= v <= 5000:
            raise ValueError('Radius must be between 100 and 5000 meters')
        return v
    
    @validator('business_type')
    def validate_business_type(cls, v):
        if v not in BUSINESS_MAPPINGS:
            raise ValueError(f'Business type must be one of: {list(BUSINESS_MAPPINGS.keys())}')
        return v

class AIRequest(BaseModel):
    business_type: str
    score: float
    supply_count: int
    demand_count: int
    demand_breakdown: dict
    growth_status: str

# --- 4. HELPER FUNCTIONS ---
def create_ai_prompt(data: AIRequest) -> str:
    """สร้าง prompt สำหรับ AI"""
    return f"""คุณคือผู้เชี่ยวชาญด้านการวางแผนกลยุทธ์ธุรกิจและการเลือกทำเลที่ตั้ง (Business Consultant)
กรุณาวิเคราะห์ศักยภาพของทำเลนี้สำหรับการเปิด "{data.business_type}" โดยอ้างอิงจากข้อมูลสถิติดังนี้:

- Opportunity Score: {data.score} (คะแนนยิ่งสูงแปลว่ามีความต้องการตลาดมาก คู่แข่งน้อย)
- จำนวนร้านคู่แข่งในรัศมี 1 กม.: {data.supply_count} ร้าน
- จำนวนสถานที่ดึงดูดลูกค้า (Demand): {data.demand_count} แห่ง
- สัดส่วนกลุ่มลูกค้าเป้าหมาย: {data.demand_breakdown}
- แนวโน้มการเติบโตของพื้นที่ (ก่อสร้างใหม่): {data.growth_status}

รูปแบบการตอบกลับ (ขอสั้นๆ กระชับ อ่านง่าย เป็นภาษาไทย สไตล์มืออาชีพ):

🎯 **คำตัดสิน:** (เช่น น่าลงทุนมาก / ควรระวัง / ตลาดอิ่มตัว) พร้อมเหตุผล 1 บรรทัด

💪 **จุดแข็งของทำเลนี้:** (1 ข้อ)

⚠️ **ความเสี่ยงที่ต้องระวัง:** (1 ข้อ)

💡 **กลยุทธ์แนะนำ:** (แนะนำ 1 กลยุทธ์การตลาด หรือ รูปแบบร้านที่เหมาะกับลูกค้ากลุ่มนี้)

สำคัญ: ใส่บรรทัดว่างระหว่างแต่ละหัวข้อ และใช้ ** สำหรับหัวข้อ"""

# --- 5. API ENDPOINTS ---

@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Market Gap Hunter API V2",
        "version": "2.0.0"
    }

@app.get("/cache/stats")
def cache_stats():
    """Get cache statistics"""
    cache_files = list(cache.cache_dir.glob("*.json"))
    return {
        "total_cached_items": len(cache_files),
        "cache_dir": str(cache.cache_dir),
        "ttl_hours": cache.ttl.total_seconds() / 3600
    }

@app.post("/cache/clear")
def clear_cache(expired_only: bool = True):
    """Clear cache (expired only by default)"""
    if expired_only:
        cleared = cache.clear_expired()
        return {"message": f"Cleared {cleared} expired cache files"}
    else:
        cleared = cache.clear_all()
        return {"message": f"Cleared all {cleared} cache files"}

@app.get("/history")
def get_history(limit: int = 10, business_type: str = None):
    """Get analysis history"""
    return history.get_history(limit=limit, business_type=business_type)

@app.get("/history/location")
def get_location_history(lat: float, lon: float, tolerance: float = 0.01):
    """Get history for specific location"""
    return history.get_location_history(lat=lat, lon=lon, tolerance=tolerance)

@app.get("/history/stats")
def get_history_stats():
    """Get history statistics"""
    return history.get_statistics()

@app.delete("/history")
def clear_history():
    """Clear all history"""
    cleared = history.clear_history()
    return {"message": f"Cleared {cleared} history entries"}

@app.get("/search")
@limiter.limit("20/minute")
def search_place(request: Request, query: str):
    print(f"🔎 Searching for: {query}")
    try:
        # ใช้ OSMnx หาพิกัดจากชื่อ
        lat, lon = ox.geocode(query)
        return {"lat": lat, "lon": lon, "name": query}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Location not found: {e}")

@app.get("/autocomplete")
@limiter.limit("30/minute")
def autocomplete(request: Request, query: str, country: str = ""):
    print(f"🔎 Autocomplete: {query} in {country}")
    
    url = "https://nominatim.openstreetmap.org/search"
    
    params = {
        "q": query,
        "format": "json",
        "limit": 20,  # เพิ่มจำนวนเพื่อกรองภายหลัง
        "addressdetails": 1,
        "extratags": 1,  # ดึงข้อมูลเพิ่มเติม
    }
    
    if country:
        params["countrycodes"] = country

    headers = {
        "User-Agent": "MarketGapHunter_StudentProject_V2/1.0 (thanyatle2004@gmail.com)",
        "Referer": "http://127.0.0.1:8000"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Nominatim Error! Status: {response.status_code}")
            return []

        data = response.json()
        
        # ระบบให้คะแนนความเกี่ยวข้อง (Relevance Scoring)
        scored_results = []
        
        for item in data:
            score = 0
            place_type = item.get("type", "")
            place_class = item.get("class", "")
            importance = float(item.get("importance", 0))
            
            # กรองผลลัพธ์ที่ไม่ต้องการออกทันที
            # 1. ข้ามประเทศทั้งประเทศ
            if place_class == "boundary" and place_type == "administrative":
                admin_level = item.get("address", {}).get("country")
                if admin_level and len(item["display_name"].split(",")) <= 1:
                    continue  # ข้ามถ้าเป็นแค่ชื่อประเทศเดียว
            
            # 2. ข้ามทวีป/มหาสมุทร
            if place_class in ["natural", "waterway"] and place_type in ["sea", "ocean", "continent"]:
                continue
            
            # ให้คะแนนตามประเภทสถานที่ (ยิ่งเฉพาะเจาะจงยิ่งดี)
            priority_map = {
                # POI และสถานที่เฉพาะเจาะจง (คะแนนสูงสุด)
                "amenity": 100,
                "shop": 95,
                "tourism": 90,
                "leisure": 85,
                "building": 80,
                
                # ถนน/ซอย (ค่อนข้างเฉพาะเจาะจง)
                "highway": 70,
                
                # ย่าน/เขต (กลางๆ)
                "place": {
                    "neighbourhood": 60,
                    "suburb": 55,
                    "quarter": 58,
                    "city_block": 62,
                    "hamlet": 50,
                    "village": 45,
                    "town": 40,
                    "city": 35,
                    "state": 10,
                    "country": 5
                },
                
                # เขตการปกครอง (คะแนนต่ำ)
                "boundary": 20,
            }
            
            # คำนวณคะแนน
            if place_class in priority_map:
                if isinstance(priority_map[place_class], dict):
                    score = priority_map[place_class].get(place_type, 30)
                else:
                    score = priority_map[place_class]
            else:
                score = 40  # คะแนนเริ่มต้น
            
            # โบนัสจาก importance (ค่าที่ Nominatim คำนวณให้)
            score += importance * 20
            
            # โบนัสถ้าชื่อตรงกับคำค้นหา (case-insensitive)
            display_name_lower = item["display_name"].lower()
            query_lower = query.lower()
            
            if display_name_lower.startswith(query_lower):
                score += 30  # ขึ้นต้นด้วยคำค้นหา
            elif query_lower in display_name_lower.split(",")[0].lower():
                score += 20  # อยู่ในส่วนแรกของชื่อ
            elif query_lower in display_name_lower:
                score += 10  # อยู่ที่ไหนสักแห่งในชื่อ
            
            scored_results.append({
                "display_name": item["display_name"],
                "lat": float(item["lat"]),
                "lon": float(item["lon"]),
                "score": score,
                "type": place_type,
                "class": place_class
            })
        
        # เรียงตามคะแนนจากมากไปน้อย
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        
        # ส่งกลับแค่ 8 อันดับแรก (ไม่ต้องส่ง score ไปให้ frontend)
        suggestions = [
            {
                "display_name": r["display_name"],
                "lat": r["lat"],
                "lon": r["lon"]
            }
            for r in scored_results[:8]
        ]
        
        return suggestions
        
    except Exception as e:
        print(f"Error autocomplete: {e}")
        return []

@app.post("/analyze")
@limiter.limit("10/minute")
async def analyze_market(request: Request, req: AnalyzeRequest):
    print(f"🌍 Received Request: {req.business_type} at ({req.lat}, {req.lon})")
    
    # Check cache first
    cache_key_params = {
        "lat": round(req.lat, 4),  # Round to reduce cache misses
        "lon": round(req.lon, 4),
        "business_type": req.business_type,
        "radius": req.radius
    }
    
    cached_result = cache.get(**cache_key_params)
    if cached_result:
        print("✅ Returning cached result")
        return cached_result
    
    if req.business_type not in BUSINESS_MAPPINGS:
        raise HTTPException(status_code=400, detail="Business type not supported")
    
    center_point = (req.lat, req.lon)
    supply_tags = BUSINESS_MAPPINGS[req.business_type]["tags"]
    
    # A. Fetch Supply
    supply_points = []
    num_supply = 0
    try:
        supply_gdf = ox.features_from_point(center_point, tags=supply_tags, dist=req.radius)
        if not supply_gdf.empty:
            supply_gdf['centroid'] = supply_gdf.geometry.centroid
            for p, row in zip(supply_gdf['centroid'], supply_gdf.to_dict('records')):
                name = row.get('name', 'Unknown')
                if pd.isna(name): name = "Unknown"
                if pd.notna(p.y) and pd.notna(p.x):
                    supply_points.append({"lat": p.y, "lon": p.x, "name": name})
            num_supply = len(supply_points)
    except Exception as e:
        print(f"Error supply: {e}")

    # B. Fetch Demand & Breakdown
    demand_tags_map = {
        'office': 'Office',
        'school': 'Students',
        'university': 'Students',
        'college': 'Students',
        'apartments': 'Residential',
        'condominium': 'Residential',
        'residential': 'Residential',
        'station': 'Transport'
    }
    
    query_tags = {
        'office': True,
        'amenity': ['school', 'university', 'college'],
        'building': ['apartments', 'condominium', 'residential'],
        'public_transport': ['station']
    }

    demand_points = []
    demand_breakdown = {"Office": 0, "Students": 0, "Residential": 0, "Transport": 0}
    
    try:
        demand_gdf = ox.features_from_point(center_point, tags=query_tags, dist=req.radius)
        if not demand_gdf.empty:
            # Loop เพื่อจัดกลุ่ม (Segmentation)
            for _, row in demand_gdf.iterrows():
                assigned = False
                # เช็คว่าแถวนี้ตรงกับ tag ไหนใน map
                for col in demand_gdf.columns:
                    val = str(row.get(col))
                    if val in demand_tags_map:
                        group = demand_tags_map[val]
                        demand_breakdown[group] += 1
                        assigned = True
                        break
                if not assigned: # ถ้าหาไม่เจอ ให้โยนลง Residential (ค่า Default)
                    demand_breakdown["Residential"] += 1
            
            # เตรียมพิกัด
            demand_gdf['centroid'] = demand_gdf.geometry.centroid
            if len(demand_gdf) > 1000: demand_gdf = demand_gdf.sample(1000)
            demand_points = [{"lat": p.y, "lon": p.x} for p in demand_gdf['centroid']]
            
    except Exception as e:
        print(f"Error demand: {e}")

    # C. Future Growth (Construction Sites)
    growth_status = "ทรงตัว 🏙️"
    cons_count = 0
    try:
        cons_gdf = ox.features_from_point(center_point, tags={'landuse': 'construction'}, dist=req.radius)
        cons_count = len(cons_gdf)
        if cons_count > 5: growth_status = "กำลังบูมสุดๆ 🚀"
        elif cons_count > 2: growth_status = "กำลังเติบโต 📈"
    except:
        pass

    # D. Calculate Score & Prepare Result
    num_demand = len(demand_points)
    divisor = num_supply if num_supply > 0 else 1
    score = round(num_demand / divisor, 2)

    if num_supply == 0 and num_demand > 0:
        verdict = "ตลาดไร้คู่แข่ง (โอกาสสูงมาก)"
        color = "#2980b9" # Blue
    elif score > 5.0:
        verdict = "ศักยภาพสูง (น่าลงทุน)"
        color = "#27ae60" # Green
    elif score > 2.0:
        verdict = "ตลาดสมดุล (พอแข่งขันได้)"
        color = "#f39c12" # Orange
    else:
        verdict = "ตลาดอิ่มตัว (Red Ocean)"
        color = "#c0392b" # Red

    result = {
        "score": score,
        "verdict": verdict,
        "verdict_color": color,
        "supply_count": num_supply,
        "demand_count": num_demand,
        "demand_breakdown": demand_breakdown,
        "growth_status": growth_status,
        "construction_count": cons_count,
        "supply_points": supply_points,
        "demand_points": demand_points
    }
    
    # Save to cache before returning
    cache.set(result, **cache_key_params)
    
    # Save to history
    history.add_analysis(
        lat=req.lat,
        lon=req.lon,
        business_type=req.business_type,
        radius=req.radius,
        result=result
    )
    
    return result

@app.post("/ask-ai")
@limiter.limit("5/minute")
async def ask_ai_consultant(request: Request, data: AIRequest):
    print("🤖 AI is analyzing...")
    
    prompt = create_ai_prompt(data)
    
    try:
        if USING_NEW_GENAI:
            response = client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=prompt
            )
            analysis_text = response.text
        else:
            response = model.generate_content(prompt)
            analysis_text = response.text
            
        return {"analysis": analysis_text}
    except Exception as e:
        print(f"AI Error: {e}")
        raise HTTPException(status_code=500, detail=f"AI Service Error: {str(e)}")

# Streaming AI endpoint
from fastapi.responses import StreamingResponse

@app.post("/ask-ai-stream")
@limiter.limit("5/minute")
async def ask_ai_stream(request: Request, data: AIRequest):
    print("🤖 AI is analyzing (streaming)...")
    
    prompt = create_ai_prompt(data)
    
    async def generate():
        try:
            if USING_NEW_GENAI:
                response = client.models.generate_content(
                    model='gemini-2.0-flash-exp',
                    contents=prompt,
                    config={'response_modalities': ['TEXT']}
                )
                yield response.text
            else:
                response = model.generate_content(prompt, stream=True)
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
        except Exception as e:
            print(f"AI Streaming Error: {e}")
            yield f"Error: {str(e)}"
    
    return StreamingResponse(generate(), media_type="text/plain")
