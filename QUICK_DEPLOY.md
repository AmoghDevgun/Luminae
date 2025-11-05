# Quick Deployment Guide

## 🚀 Backend Deployment (Render)

### Step 1: Prepare GitHub Repository
```bash
git init
git add .
git commit -m "Ready for deployment"
git remote add origin https://github.com/yourusername/instagram-scraper.git
git push -u origin main
```

### Step 2: Deploy to Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect GitHub and select your repository
4. Configure:
   - **Name**: `instagram-scraper-backend`
   - **Root Directory**: `backend`
   - **Environment**: `Node`
   - **Build Command**: `npm install`
   - **Start Command**: `npm start`
   - **Plan**: Free

5. Add Environment Variables:
   ```
   NODE_ENV=production
   PORT=10000
   MONGODB_URI=your_mongodb_connection_string
   JWT_SECRET=generate_a_random_secret_key_here
   JWT_EXPIRE=7d
   FRONTEND_URL=https://your-vercel-app.vercel.app
   ```

6. Click **"Create Web Service"**
7. Copy your Render URL: `https://your-service.onrender.com`

---

## 🎨 Frontend Deployment (Vercel)

### Step 1: Install Vercel CLI (Optional)
```bash
npm i -g vercel
```

### Step 2: Deploy via Vercel Dashboard

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Create React App
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`

5. Add Environment Variable:
   ```
   REACT_APP_API_URL=https://your-service.onrender.com
   ```
   (Use your Render backend URL from Step 2)

6. Click **"Deploy"**
7. Copy your Vercel URL: `https://your-app.vercel.app`

### Step 3: Update Backend CORS

1. Go back to Render dashboard
2. Update Environment Variable:
   ```
   FRONTEND_URL=https://your-app.vercel.app
   ```
3. Restart the service

---

## ✅ Testing

1. Visit your Vercel URL
2. Register a new account
3. Try scraping an Instagram username
4. Check if data streams correctly

---

## 🔧 Troubleshooting

### CORS Errors
- Make sure `FRONTEND_URL` in Render matches your Vercel URL exactly
- Check that backend CORS configuration allows your Vercel domain

### API Not Working
- Verify `REACT_APP_API_URL` is set correctly in Vercel
- Check browser console for errors
- Verify backend is running (check Render logs)

### MongoDB Connection
- Ensure MongoDB Atlas IP whitelist includes `0.0.0.0/0` (all IPs)
- Verify connection string is correct
- Check MongoDB Atlas logs

---

## 📝 Environment Variables Summary

### Backend (Render)
- `NODE_ENV=production`
- `MONGODB_URI=your_connection_string`
- `JWT_SECRET=your_secret_key`
- `JWT_EXPIRE=7d`
- `FRONTEND_URL=https://your-app.vercel.app`

### Frontend (Vercel)
- `REACT_APP_API_URL=https://your-service.onrender.com`

---

## 🎉 Done!

Your app should now be live at:
- Frontend: `https://your-app.vercel.app`
- Backend: `https://your-service.onrender.com`

