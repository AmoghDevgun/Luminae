# Deployment Guide

This guide will help you deploy:
- **Frontend** (React) → Vercel
- **Backend** (Node.js/Express) → Render

## Prerequisites

1. GitHub account (for connecting to Vercel/Render)
2. MongoDB Atlas account (or your MongoDB connection string)
3. Vercel account (free tier available)
4. Render account (free tier available)

---

## Step 1: Prepare Backend for Render

### 1.1 Update Backend Environment Variables

Create a `.env` file in the `backend` folder with these variables (you'll also add these to Render):

```env
PORT=10000
MONGODB_URI=your_mongodb_connection_string
JWT_SECRET=your_super_secret_jwt_key_change_this
JWT_EXPIRE=7d
NODE_ENV=production
```

### 1.2 Update CORS Configuration

The backend already has CORS enabled, but we need to ensure it allows your Vercel domain.

Update `backend/server.js` to allow Vercel domain:

```javascript
const cors = require('cors');

const corsOptions = {
  origin: process.env.FRONTEND_URL || 'http://localhost:3000',
  credentials: true
};

app.use(cors(corsOptions));
```

### 1.3 Create Render Configuration

Create `render.yaml` in the project root (optional, but helpful):

```yaml
services:
  - type: web
    name: instagram-scraper-backend
    env: node
    plan: free
    buildCommand: cd backend && npm install
    startCommand: cd backend && npm start
    envVars:
      - key: NODE_ENV
        value: production
      - key: MONGODB_URI
        sync: false
      - key: JWT_SECRET
        sync: false
      - key: JWT_EXPIRE
        value: 7d
      - key: PORT
        value: 10000
```

---

## Step 2: Deploy Backend to Render

### 2.1 Push Code to GitHub

1. Initialize git (if not already done):
```bash
git init
git add .
git commit -m "Initial commit"
```

2. Create a new repository on GitHub
3. Push your code:
```bash
git remote add origin https://github.com/yourusername/instagram-scraper.git
git branch -M main
git push -u origin main
```

### 2.2 Create Render Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Select your repository
5. Configure the service:
   - **Name**: `instagram-scraper-backend` (or your choice)
   - **Environment**: `Node`
   - **Build Command**: `cd backend && npm install`
   - **Start Command**: `cd backend && npm start`
   - **Plan**: Free (or choose paid)

6. Add Environment Variables:
   - `NODE_ENV` = `production`
   - `PORT` = `10000` (Render sets this automatically, but good to have)
   - `MONGODB_URI` = Your MongoDB connection string
   - `JWT_SECRET` = A random secret string (generate one)
   - `JWT_EXPIRE` = `7d`
   - `FRONTEND_URL` = Your Vercel URL (add this after deploying frontend)

7. Click **"Create Web Service"**

8. Wait for deployment to complete. You'll get a URL like:
   `https://instagram-scraper-backend.onrender.com`

### 2.3 Note Render's Free Tier Limitations

- Services spin down after 15 minutes of inactivity
- First request after spin-down takes ~30 seconds
- Consider upgrading to paid plan for production

---

## Step 3: Prepare Frontend for Vercel

### 3.1 Update API Base URL

Create a `.env` file in the `frontend` folder:

```env
REACT_APP_API_URL=https://your-backend-url.onrender.com
```

### 3.2 Update Frontend API Calls

Update `frontend/src/context/AuthContext.js` to use the environment variable:

```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || '';

// Update axios calls to use API_BASE_URL
axios.post(`${API_BASE_URL}/api/auth/login`, ...)
```

Actually, better approach - update the proxy in `package.json` won't work on Vercel. Instead, we'll use environment variables.

### 3.3 Create API Configuration

Create `frontend/src/config/api.js`:

```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export default API_BASE_URL;
```

Then update all axios calls to use this base URL.

### 3.4 Create Vercel Configuration

Create `vercel.json` in the project root:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "frontend/package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "build"
      }
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "frontend/$1"
    }
  ]
}
```

Or better, set the root directory in Vercel dashboard.

---

## Step 4: Deploy Frontend to Vercel

### 4.1 Install Vercel CLI (Optional)

```bash
npm i -g vercel
```

### 4.2 Deploy via Vercel Dashboard

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository
4. Configure the project:
   - **Framework Preset**: Create React App (or auto-detected)
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (or `npm run build` if in root)
   - **Output Directory**: `build`

5. Add Environment Variables:
   - `REACT_APP_API_URL` = `https://your-backend-url.onrender.com`

6. Click **"Deploy"**

7. Wait for deployment. You'll get a URL like:
   `https://instagram-scraper.vercel.app`

### 4.3 Update Backend CORS

After getting your Vercel URL, go back to Render and update:
- `FRONTEND_URL` = Your Vercel URL
- Restart the service

Also update `backend/server.js` to allow your Vercel domain.

---

## Step 5: Update Code for Production

### 5.1 Update Backend CORS

Update `backend/server.js`:

```javascript
const corsOptions = {
  origin: [
    'http://localhost:3000',
    process.env.FRONTEND_URL,
    'https://your-app.vercel.app'
  ].filter(Boolean),
  credentials: true
};

app.use(cors(corsOptions));
```

### 5.2 Update Frontend API Calls

Update all axios calls to use the environment variable. I'll create a helper file.

---

## Step 6: MongoDB Atlas Setup (if using cloud)

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a free cluster
3. Get connection string
4. Add your IP address (0.0.0.0/0 for Render, or specific IPs)
5. Create database user
6. Update `MONGODB_URI` in Render with your connection string

---

## Troubleshooting

### Backend Issues

- **Timeout errors**: Render free tier has cold starts. Consider upgrading.
- **CORS errors**: Make sure `FRONTEND_URL` is set correctly in backend
- **MongoDB connection**: Ensure IP is whitelisted in MongoDB Atlas

### Frontend Issues

- **API calls failing**: Check `REACT_APP_API_URL` is set correctly
- **Build errors**: Check Node.js version compatibility
- **Environment variables**: Must start with `REACT_APP_` for Create React App

---

## Quick Reference

### Render Backend URL Format
```
https://your-service-name.onrender.com
```

### Vercel Frontend URL Format
```
https://your-project-name.vercel.app
```

### Environment Variables Needed

**Backend (Render):**
- `MONGODB_URI`
- `JWT_SECRET`
- `JWT_EXPIRE`
- `NODE_ENV`
- `FRONTEND_URL`

**Frontend (Vercel):**
- `REACT_APP_API_URL`

---

## Next Steps

1. Test the deployed application
2. Set up custom domains (optional)
3. Monitor logs in both platforms
4. Set up error tracking (e.g., Sentry)
5. Consider upgrading plans for production use

