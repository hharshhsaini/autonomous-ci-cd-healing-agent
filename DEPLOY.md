# Render Deployment - Quick Guide

## Step 1: Backend Deployment

1. Go to https://dashboard.render.com
2. Click **New +** → **Web Service**
3. Connect GitHub repo
4. Settings:
   - Name: `rift-backend`
   - Root Directory: `backend`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt && pip install flake8 mypy pytest`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

5. Environment Variables (click Advanced):
   ```
   GROQ_API_KEY=your_groq_api_key_here
   GITHUB_CLIENT_ID=your_github_client_id_here
   GITHUB_CLIENT_SECRET=your_github_client_secret_here
   ```

6. Click **Create Web Service**
7. Copy backend URL (e.g., `https://rift-backend.onrender.com`)

## Step 2: Frontend Deployment

1. Click **New +** → **Static Site**
2. Connect same repo
3. Settings:
   - Name: `rift-frontend`
   - Root Directory: `frontend`
   - Build Command: `npm install && npm run build`
   - Publish Directory: `dist`

4. Environment Variable:
   ```
   VITE_API_URL=https://rift-backend.onrender.com
   ```
   (Use your actual backend URL)

5. Click **Create Static Site**
6. Copy frontend URL

## Step 3: Update GitHub OAuth

1. Go to https://github.com/settings/developers
2. Click your OAuth App
3. Update:
   - Homepage URL: `https://your-frontend-url.onrender.com`
   - Callback URL: `https://your-frontend-url.onrender.com`

## Done! 🎉

Open your frontend URL and test!

## Notes

- Free tier spins down after 15 min
- First request takes 30-60s after spin-down
- Upgrade to $7/month for always-on
