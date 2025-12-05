# 🎯 Smart attendence monitoring system using face recognition and Qr verification 

<p align="center">
<img src="https://img.shields.io/badge/Project-AI%20Attendance%20System-blue?style=for-the-badge&logo=appveyor&logoColor=white" alt="Project Badge">
<img src="https://img.shields.io/badge/Face-Recognition-success?style=for-the-badge&logo=opencv&logoColor=white" alt="Face Recognition Badge">
<img src="https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge&logo=github&logoColor=white" alt="Status Badge">
</p

---
## 📜 Overview

A smart, AI-powered attendance monitoring system that combines Face Recognition and QR Code Verification to automate student/faculty attendance with high accuracy, speed, and security.Automatically Generate Excel report 
This system eliminates proxy attendance and provides real-time monitoring.

## 🚀 Features 

✔ Face Recognition–based authentication

✔ QR code scanning for double verification

✔ Real-time attendance marking

✔ GPS-based location tracking

✔ Secure database storage

✔ Web dashboard for admin & faculty

✔ Automatic report generation

✔ Anti-proxy protection

✔ Multi-user support (Admin, Faculty, Student)

---

## 📁 **Project Structure**

```Smart-Attendance-System/
│
├── assets/                 
│   ├── banner.png              # GitHub project banner  
│   ├── screenshots/            # Output images & demo UI
│   └── qr_samples/             # Sample QR codes
│
├── src/
│   ├── face_recognition/       # Face recognition module  
│   │   ├── model.py
│   │   ├── train_model.py
│   │   └── detect_face.py
│   │
│   ├── qr_scanner/             # QR scanning module  
│   │   ├── qr_reader.py
│   │   └── qr_generator.py
│   │
│   ├── database/               # Database connection + queries
│   │   ├── db_config.py
│   │   └── attendance_db.py
│   │
│   ├── utils/                  # Helper utilities
│   │   ├── logger.py
│   │   ├── validation.py
│   │   └── config.py
│   │
│   └── main.py                 # Project entry point
│
├── requirements.txt            # Python dependencies  
├── .gitignore                  # Git ignore rules  
├── LICENSE                     # Project license  
└── README.md                   # Documentation```
```
---

## Tech Stack

| Category          | Technologies Used                                     |
|------------------|--------------------------------------------------------|
| Programming Lang | Python, JavaScript                                     |
| Frontend         | HTML, CSS, JavaScript                                  |
| Backend / API    | Python (Flask optional), Supabase REST API             |
| AI/ML Models     | Face Recognition (OpenCV, Haar Cascade), CNN Model     |
| Databases        | Supabase PostgreSQL, SQLite (local testing)            |
| QR Handling      | qrcode, pyzbar                                         |
| Cloud / Hosting  | Supabase, Cloudflare Tunnel, Ngrok                     |
| Tools            | Git, GitHub, VS Code                                   |
| Environment      | Virtualenv, Python 3.10+                               |

---

# 🛠️ Installation & Setup Guide – Smart Attendance System (QR + Face Recognition)

## ✅ 1. Prerequisites
Make sure the following are installed:
- Python 3.8+
- Git
- XAMPP / MySQL (if database used)
- Webcam

## 📌 Install Required Software
- Python: https://www.python.org/downloads/
- Git: https://git-scm.com/
- XAMPP: https://www.apachefriends.org/

---

## ✅ 2. Clone the Project
```bash
git clone https://github.com/your-username/smart-attendance-system.git
cd smart-attendance-system

---

## ✅ 3. Create Virtual Environment
