# Deployment Configuration for Replit

## Required Run Commands (TESTED & WORKING)

**Option 1 - Replit Standard (RECOMMENDED):**
```
python3 main.py
```

**Option 2 - Alternative Python:**
```
python main.py
```

**Option 3 - Gunicorn with WSGI:**
```
gunicorn wsgi:application --bind 0.0.0.0:5000
```

**Option 4 - Gunicorn with app module:**
```
gunicorn app:app --bind 0.0.0.0:5000
```

**Option 5 - Direct app run:**
```
python app.py
```

## Alternative Commands (if needed)
```
python3 app.py
```
or
```
python3 run.py
```
or
```
flask --app app run --host=0.0.0.0 --port=5000
```

## Health Check Endpoint
The app includes a `/health` endpoint that responds with:
```json
{
  "status": "healthy",
  "service": "booking-automation", 
  "timestamp": "2025-08-05T01:46:05.409482"
}
```

## Environment Variables for Deployment
Set these environment variables in your deployment:
- `FLASK_HOST=0.0.0.0` (for external access)
- `FLASK_PORT=5000` (standard port)
- `FLASK_DEBUG=false` (for production)

## Deployment Checklist
✅ Main application file: `app.py`
✅ Health check endpoint: `/health`
✅ Host configuration: `0.0.0.0` for external access
✅ Port configuration: `5000`
✅ All dependencies installed via pip
✅ Flask app properly configured

## Manual Deployment Setup
If using Replit's deployment interface:
1. Set run command to: `python app.py`
2. Ensure port 5000 is configured
3. Add any required environment variables
4. Deploy and test the `/health` endpoint

Your app is fully ready for deployment!