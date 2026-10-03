# EduRoom

>><><><><><><><><><><><><><><><><><><><><><><><><><><>

EduRoom is a Flask-based room scheduling and reservation system for students, teachers, and administrators. It helps manage room availability, class schedules, and room booking requests in a simple web application.

========================================

## Overview

This project allows users to:

- View class schedules
- Check room availability
- Submit room reservation requests
- Approve or reject room requests as an administrator
- Manage rooms, classes, and user roles

The system is designed to support three user roles:

- Student
- Teacher
- Admin


========================================

## Features

### Student Features
- View personal dashboard
- Check weekly class schedule
- See room availability
- Submit room request
- Track request status

### Teacher Features
- View own schedule
- Check room availability
- Submit room request with room suggestion logic
- Review request history
- View assigned students

### Admin Features
- View admin dashboard
- Review pending room requests
- Approve or reject requests
- Manage rooms
- Add, edit, or remove rooms
- Add class schedules
- Update room assignments
- View upcoming calendar


========================================

## Tech Stack

- Python
- Flask
- Flask-Login
- HTML templates
- CSS/Bootstrap-like frontend styling


========================================

## Project Structure

```text
EduRoom/
├── main.py                 # Application entry point and route logic
├── models.py               # User and role model definitions
├── system.py               # Core scheduling and room management logic
├── flask_templates/        # HTML pages for all user roles
├── static/                 # Static assets such as CSS, JS, images
├── .venv/                  # Virtual environment
├── venv/                   # Alternative virtual environment folder
├── README.md               # Project documentation
└── .git/                  # Git metadata
```


========================================

## Requirements

Make sure you have Python installed on your machine.

Recommended:
- Python 3.10 or later
- Virtual environment

Install required packages:

```bash
pip install flask flask-login
```


========================================

## Setup Instructions

### 1. Clone or open the project folder

```bash
cd EduRoom
```

### 2. Create a virtual environment

Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

Linux/Mac:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install flask flask-login
```

### 4. Run the app

```bash
python main.py
```

Then open in your browser:

```text
http://localhost:5001
```


========================================

## Default Login Accounts

The system already includes sample accounts for testing.

### Students
- S1 / ALAIZA NICOLE CARANTO / Password: `studpass`
- S2 / JIM DELANTAR / Password: `studpass2`
- S3 / WODY LUSANTA / Password: `studpass3`
- S4 / MARK BOLIGOR / Password: `studpass4`

### Teachers
- T1 / MR. JOLLARD FLORES / Password: `teachpass`
- T2 / MS. AGNES RECAÑA / Password: `teachpass2`
- T3 / MR. NEIL JOSE / Password: `teachpass3`
- T4 / MR. REYNAN BACCLE / Password: `teachpass4`
- T5 / MR. JED MALVEDA / Password: `teachpass5`

### Admins
- A1 / ADMIN ALVARADO / Password: `adminpass`
- A2 / ADMIN LANIP / Password: `adminpass2`

> Note: You must first choose a role before logging in.


========================================

## How the App Works

### Role Selection
When the app starts, the user is redirected to the role selection page. The user chooses either:

- Student
- Teacher
- Admin

The selected role determines which credentials can be used for login.

### Room Request Flow
1. A student or teacher chooses a room and time
2. The request is submitted to the system
3. Admin reviews the request
4. Admin approves or rejects it
5. Approved requests appear as room bookings

### Conflict Handling
The system prevents:
- overlapping room bookings for the same time slot
- room assignments that conflict with existing class schedules
- invalid time ranges where end time is before start time


========================================

## Main Files

### `main.py`
Contains all Flask routes and app initialization.

Includes:
- login and logout logic
- dashboard pages for each role
- room request handling
- admin approval/rejection actions
- API route for room availability

### `system.py`
Contains the core logic for:
- users
- rooms
- class schedules
- room requests
- validation and conflict checks
- room suggestion logic

### `models.py`
Defines the application models:
- `Role` enum
- `User` model
- Flask-Login compatibility


========================================

## Common Routes

```text
/                    -> redirects to role selection
/select-role         -> choose role
/login               -> login page
/logout              -> log out
/student/dashboard   -> student home
/student/schedule    -> weekly student schedule
/student/rooms       -> room availability for students
/student/request     -> submit room request
/teacher/dashboard   -> teacher home
/teacher/schedule    -> teacher schedule
/teacher/rooms       -> room availability for teachers
/teacher/request     -> teacher request form and room suggestions
/admin/dashboard      -> admin home
/admin/manage        -> manage users, rooms, classes
/admin/requests      -> pending requests
/admin/rooms         -> room management
/admin/calendar      -> weekly calendar view
```


========================================

## Usage Guide

### For Students
- Log in using a student account
- Check your dashboard for today's classes
- Go to the room request page to reserve a room
- Wait for admin approval

### For Teachers
- Log in as teacher
- View your teaching schedule
- Submit room requests based on date and time
- Use room suggestions to find suitable rooms faster

### For Admins
- Log in as admin
- Open pending requests
- Approve or reject each request with reason
- Manage room inventory and class schedule entries


========================================

## Notes

- The app currently uses a built-in in-memory data model, not a database.
- Data resets when the Flask app restarts.
- This is a prototype/demo system for educational room scheduling.


========================================

## Future Improvements

Possible enhancements:
- Use a real database like SQLite or PostgreSQL
- Add password hashing for security
- Add email notifications for request status
- Create a full reporting dashboard
- Improve validation and UI responsiveness
- Add audit logs for admin actions


========================================

## Running the App

```bash
python main.py
```

Then visit:

```text
http://localhost:5001
```


========================================

## License

This project is intended for educational and local development use.


========================================

## Developer Note

This project is a simple academic scheduling system and is best suited for learning Flask, route handling, role-based access, and scheduling logic.
