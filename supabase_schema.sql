-- Supabase Database Schema for Proxy-Scan Attendance System

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Lectures table
CREATE TABLE IF NOT EXISTS lectures (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    lectureId TEXT UNIQUE NOT NULL,
    lectureName TEXT NOT NULL,
    roomNo TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    lat DECIMAL(10, 8) NOT NULL,
    lng DECIMAL(11, 8) NOT NULL,
    qrNonce TEXT NOT NULL,
    qrIssuedAt BIGINT NOT NULL,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Attendance table
CREATE TABLE IF NOT EXISTS attendance (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    lectureId TEXT NOT NULL REFERENCES lectures(lectureId) ON DELETE CASCADE,
    rollNo TEXT NOT NULL,
    name TEXT NOT NULL,
    lat DECIMAL(10, 8) NOT NULL,
    lng DECIMAL(11, 8) NOT NULL,
    accuracy DECIMAL(8, 2) NOT NULL,
    distanceMeters DECIMAL(8, 2) NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('Present', 'Rejected')),
    timestamp TEXT NOT NULL,
    userAgent TEXT,
    faceVerified BOOLEAN DEFAULT false,
    faceConfidence DECIMAL(5, 4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(lectureId, rollNo)
);

-- Faculties table
CREATE TABLE IF NOT EXISTS faculties (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    passwordHash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Students table
CREATE TABLE IF NOT EXISTS students (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    rollNo TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    email TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_lectures_lectureId ON lectures(lectureId);
CREATE INDEX IF NOT EXISTS idx_attendance_lectureId ON attendance(lectureId);
CREATE INDEX IF NOT EXISTS idx_attendance_rollNo ON attendance(rollNo);
CREATE INDEX IF NOT EXISTS idx_faculties_email ON faculties(email);
CREATE INDEX IF NOT EXISTS idx_students_rollNo ON students(rollNo);

-- Row Level Security (RLS) policies
ALTER TABLE lectures ENABLE ROW LEVEL SECURITY;
ALTER TABLE attendance ENABLE ROW LEVEL SECURITY;
ALTER TABLE faculties ENABLE ROW LEVEL SECURITY;
ALTER TABLE students ENABLE ROW LEVEL SECURITY;

-- Allow all operations (for demo purposes - adjust for production)
CREATE POLICY "Enable all operations for lectures" ON lectures
    FOR ALL USING (true);

CREATE POLICY "Enable all operations for attendance" ON attendance
    FOR ALL USING (true);

CREATE POLICY "Enable all operations for faculties" ON faculties
    FOR ALL USING (true);

CREATE POLICY "Enable all operations for students" ON students
    FOR ALL USING (true);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_lectures_updated_at BEFORE UPDATE ON lectures
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_faculties_updated_at BEFORE UPDATE ON faculties
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_students_updated_at BEFORE UPDATE ON students
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
