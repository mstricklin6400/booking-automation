# DEPLOY NOW - Simple Instructions

## EXACT STEPS:

1. **Go to Deploy tab** in your Replit workspace
2. **Click "Create Deployment"**
3. **Choose "Autoscale"** 
4. **In the Run Command field, enter EXACTLY:**

```
python3 server.py
```

5. **Click Deploy**

## Alternative if that doesn't work:

```
python server.py
```

## If still not working, try:

```
gunicorn server:app --bind 0.0.0.0:$PORT
```

The `server.py` file is the simplest possible entry point I can create.