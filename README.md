# Instagram Scraper - MERN Stack Application

A full-stack Instagram scraper application with real-time streaming capabilities, built with MongoDB, Express, React, and Node.js.

## Features

- 🔐 User authentication (JWT-based)
- 📊 Real-time data streaming from backend to frontend
- 🗄️ MongoDB database for storing user data and scraping results
- 🎨 Modern React UI with Material-UI
- 📈 Real-time statistics and progress tracking
- 💾 Persistent storage of scraping results

## Project Structure

```
.
├── backend/              # Node.js/Express backend
│   ├── models/          # MongoDB models
│   ├── routes/          # API routes
│   ├── middleware/      # Authentication middleware
│   └── server.js        # Express server
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── context/    # React context (Auth)
│   │   └── App.js      # Main app component
│   └── public/
├── main.py              # Python scraping script
├── comments.py
├── likes.py
├── followers.py
└── ... (other Python scripts)
```

## Prerequisites

- Node.js (v14 or higher)
- MongoDB (running locally or connection string)
- Python 3 (for scraping scripts)
- npm or yarn

## Installation

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env` file:
```bash
cp .env.example .env
```

4. Edit `.env` file with your configuration:
```env
PORT=5000
MONGODB_URI=mongodb://localhost:27017/instagram_scraper
JWT_SECRET=your_secret_key_here_change_in_production
JWT_EXPIRE=7d
NODE_ENV=development
```

5. Start MongoDB (if running locally):
```bash
# On macOS with Homebrew
brew services start mongodb-community

# On Linux
sudo systemctl start mongod

# Or use MongoDB Atlas cloud connection string
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

## Running the Application

### Start Backend

```bash
cd backend
npm start
# or for development with auto-reload
npm run dev
```

Backend will run on `http://localhost:5000`

### Start Frontend

```bash
cd frontend
npm start
```

Frontend will run on `http://localhost:3000`

## Usage

1. **Register/Login**: Create an account or login to access the application
2. **Start Scraping**: Enter an Instagram username and start scraping
3. **View Results**: Watch data stream in real-time as it's collected
4. **Review History**: View all your previous scraping results in the Results page

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user (protected)

### Scraping
- `POST /api/scrape/start` - Start scraping (streams results via SSE)

### Results
- `GET /api/results` - Get all results (protected)
- `GET /api/results/:id` - Get single result (protected)
- `DELETE /api/results/:id` - Delete result (protected)

## Streaming Architecture

The application uses Server-Sent Events (SSE) to stream data from the backend to frontend:

1. Frontend sends POST request to `/api/scrape/start`
2. Backend starts Python scraping script
3. Backend monitors output files and streams data as it's written
4. Frontend receives streamed data in real-time
5. UI updates automatically as data arrives

## Environment Variables

### Backend (.env)
- `PORT` - Server port (default: 5000)
- `MONGODB_URI` - MongoDB connection string
- `JWT_SECRET` - Secret key for JWT tokens
- `JWT_EXPIRE` - JWT expiration time
- `NODE_ENV` - Environment (development/production)

## Notes

- Make sure MongoDB is running before starting the backend
- The Python scraping scripts must be in the project root directory
- Ensure you have valid Instagram cookies/headers in `cookies_headers.py`
- The streaming feature requires the Python scripts to output data incrementally

## Troubleshooting

1. **MongoDB Connection Error**: 
   - Check if MongoDB is running
   - Verify connection string in `.env`

2. **Streaming Not Working**:
   - Check browser console for errors
   - Verify Python script is outputting data incrementally
   - Check backend logs for errors

3. **Authentication Issues**:
   - Clear browser localStorage
   - Check JWT_SECRET in `.env`
   - Verify token in Authorization header

## License

ISC

