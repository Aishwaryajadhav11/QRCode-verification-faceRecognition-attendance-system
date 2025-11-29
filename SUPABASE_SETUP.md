# Supabase Setup Guide for Proxy-Scan

## 1. Create Supabase Project
1. Go to [supabase.com](https://supabase.com)
2. Sign up/login and create a new project
3. Note your project URL and anon key from Settings > API

## 2. Set Up Database Tables
1. Go to Supabase Dashboard > SQL Editor
2. Copy and run the contents of `supabase_schema.sql`
3. This will create all required tables (lectures, attendance, faculties, students)

## 3. Update Environment Variables
Edit your `.env` file and replace the placeholder values:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# QR Configuration  
QR_SIGNING_SECRET=your-secure-qr-signing-secret
SECRET_KEY=your-flask-secret-key

# Face Recognition
REQUIRE_FACE=false
FACE_SIGNING_SECRET=your-face-signing-secret
```

## 4. Install Dependencies
```bash
pip install -r requirements.txt
```

## 5. Run the Application
```bash
python app.py
```

## Key Changes Made:
- ✅ **Cross-device QR scanning**: Removed IP address restrictions
- ✅ **Increased location radius**: Extended from 5m to 50m for better accessibility
- ✅ **Supabase integration**: Full database connectivity configured
- ✅ **Face recognition optional**: Set to false by default

## Features:
- QR codes can now be scanned from any device (phone, tablet, etc.)
- No IP address restrictions - works from any network
- Attendance stored securely in Supabase database
- Real-time attendance tracking and reporting
- Export attendance data to Excel

## Test the System:
1. Access `http://localhost:5000`
2. Create faculty account or use admin credentials
3. Create a new lecture with location
4. Generate QR code
5. Scan QR with any phone camera
6. Mark attendance from any device
