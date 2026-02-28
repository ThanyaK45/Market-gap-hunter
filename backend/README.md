# Market Gap Hunter - Backend API

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Setup Environment Variables

Copy `.env.example` to `.env` and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` file:
```env
GOOGLE_API_KEY=your_actual_google_api_key_here
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
HOST=127.0.0.1
PORT=8000
```

### 3. Run the Server

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Or use environment variables:
```bash
python -m uvicorn main:app --reload
```

## 🔑 Getting Google API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key and paste it in `.env` file

## 📡 API Endpoints

### Health Check
```
GET /
```

### Search Location
```
GET /search?query=Siam
```

### Autocomplete
```
GET /autocomplete?query=Siam&country=th
```

### Analyze Market
```
POST /analyze
Body: {
  "lat": 13.7465,
  "lon": 100.5348,
  "business_type": "Cafe",
  "radius": 1000
}
```

### Ask AI Consultant
```
POST /ask-ai
Body: {
  "business_type": "Cafe",
  "score": 4.39,
  "supply_count": 18,
  "demand_count": 79,
  "demand_breakdown": {...},
  "growth_status": "Growing"
}
```

## 🔒 Security Features

- ✅ Environment variables for sensitive data
- ✅ Rate limiting (prevents API abuse)
- ✅ Input validation with Pydantic
- ✅ CORS configuration
- ✅ `.gitignore` to prevent committing secrets

## 📊 Rate Limits

- `/search`: 20 requests/minute
- `/autocomplete`: 30 requests/minute
- `/analyze`: 10 requests/minute
- `/ask-ai`: 5 requests/minute

## 🛠️ Tech Stack

- FastAPI - Web framework
- Google Gemini AI - AI analysis
- OSMnx - OpenStreetMap data
- GeoPandas - Geospatial analysis
- SlowAPI - Rate limiting
- python-dotenv - Environment management
