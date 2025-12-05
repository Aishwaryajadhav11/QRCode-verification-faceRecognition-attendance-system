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
```
## ✳️ 3. Create Virtual Environment
```bash
python -m venv venv

---

### Activate:

**Windows**

```bash
venv\Scripts\activate
```

**Mac/Linux**

```bash
source venv/bin/activate
```

---

## ✅ 4. Install Dependencies

```bash
pip install -r requirements.txt
pip install opencv-python
pip install face-recognition
pip install numpy
pip install pillow
pip install pyzbar
pip install qrcode
```

---

## ✅ 5. Database Setup (MySQL)

1. Open **phpMyAdmin**
2. Create Database:

```sql
CREATE DATABASE attendance_system;
```

3. Import your `.sql` file in phpMyAdmin
4. Update DB config in **config.py**:

```python
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = ""
DB_NAME = "attendance_system"
```

---

## ✅ 6. Run the Application

```bash
python app.py
```

Visit:

```
http://127.0.0.1:5000
```

---

## ✅ 7. Using the System

### 📸 Face Recognition

* Register student faces
* System encodes & stores
* Webcam auto-detects
* Attendance marked automatically

### 📱 QR Code Scanning

* Generate QR for each student
* Scan QR through webcam
* Attendance stored instantly

---
## ✅ Output & Results

Below are the results generated by the **Smart Attendance System using QR + Face Recognition**:

- ✔️ Scans QR Code from Student ID  
- ✔️ Detects & Recognizes Face in Real-Time  
- ✔️ Marks Attendance Automatically  
- ✔️ Stores Attendance in Database  
- ✔️ Displays Success Message on Validation  

### 📸 Screenshot (Replace with your image)
<img width="938" height="478" alt="front" src="https://github.com/user-attachments/assets/7c735c79-eb0c-4106-9923-854c705cac54" />


<img width="953" height="446" alt="image" src="https://github.com/user-attachments/assets/ddfb341b-dd72-498f-be73-6db3cc389f81" />



<img width="960" height="540" alt="create lec" src="https://github.com/user-attachments/assets/2c351466-9201-4fc1-9ce9-d1a7bbac54ba" />



<img width="837" height="476" alt="qr1" src="https://github.com/user-attachments/assets/ba2a49a2-d950-4af5-b1c7-f2f3f9dd4a8e" />



<img width="943" height="472" alt="view" src="https://github.com/user-attachments/assets/123443ae-4f96-4063-a904-710a7d05d690" />



<img width="960" height="457" alt="MARK" src="https://github.com/user-attachments/assets/ceb3d041-4c74-4a77-a411-7ff10a8fd712" />




<img width="716" height="366" alt="image" src="https://github.com/user-attachments/assets/3223a5e6-e281-47ea-90e1-e6b680415368" />

---
---

## 📞 Contact & Collaboration

If you want to **collaborate** or **reach out**:

- **Email:** aishwaryajadhav56952@gmail.com  
- **GitHub Issues:** Open an issue in this repo  
- **LinkedIn:**  www.linkedin.com/in/
aishwarya-jadhav-081344289

  

Feel free to fork, contribute, or report issues!

---

##  🤝 Collaborators
- [Aishwarya Jadhav](https://github.com/Aishwaryajadhav11) 
- [Bhagyshree Ahirrao](https://github.com/bhagyshri-int) 
- [Ruchita Chaudhari](https://github.com/Ruchit1205) 
- [Gayatri Patil](https://github.com/Gayatrip-26)







