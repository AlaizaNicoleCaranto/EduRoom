from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import User, Role
from system import EduRoomSystem, ValidationError
from datetime import date, time, timedelta, datetime
import os
import json

# Initialize Flask app with template and static folders
app = Flask(__name__, template_folder='flask_templates', static_folder='static')
app.secret_key = "supersecret!@#123"

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "select_role"

# Initialize EduRoom system
system = EduRoomSystem()

# Add initial rooms to the system
system.add_room("R204", "Modern Classroom", 40)
system.add_room("COMPLAB", "Computer Laboratory", 35)
system.add_room("R303", "Room 303", 30)
system.add_room("AVR", "Audio Visual Room", 100)
system.add_room("LAB101", "Science Lab", 25)
system.add_room("STUDIO", "Media Studio", 20)

# Add initial users to the system
system.add_user("S1", "ALAIZA NICOLE CARANTO", Role.STUDENT)
system.add_user("S2", "JIM DELANTAR", Role.STUDENT)
system.add_user("S3", "WODY LUSANTA", Role.STUDENT)
system.add_user("S4", "MARK BOLIGOR", Role.STUDENT)
system.add_user("T1", "MR. JOLLARD FLORES", Role.TEACHER)
system.add_user("T2", "MS. AGNES RECAÑA", Role.TEACHER)
system.add_user("T3", "MR. NEIL JOSE", Role.TEACHER)
system.add_user("T4", "MR. REYNAN BACCLE", Role.TEACHER)
system.add_user("T5", "MR. JED MALVEDA", Role.TEACHER)
system.add_user("A1", "ADMIN ALVARADO", Role.ADMIN)
system.add_user("A2", "ADMIN LANIP", Role.ADMIN)

# Setup weekly class schedules for current week
today = date.today()
# Find the Monday of the current week (so schedules apply to the current week)
# weekday(): Monday is 0. Subtract weekday days from today to get Monday.
monday = today - timedelta(days=today.weekday())
tuesday = monday + timedelta(days=1)
wednesday = monday + timedelta(days=2)
thursday = monday + timedelta(days=3)
friday = monday + timedelta(days=4)

# Add class schedules for the week
system.add_class_schedule("RESEARCH", "COMPLAB", "T3", monday, time(17,0), time(20,0), student_ids=["S1"])
system.add_class_schedule("DATA COMM", "COMPLAB", "T5", tuesday, time(8,0), time(10,0), student_ids=["S2", "S3", "S4"])
system.add_class_schedule("PATHFIT", "R204", "T3", tuesday, time(14,0), time(16,0), student_ids=["S1", "S2", "S3", "S4"])
system.add_class_schedule("DATA STRUCT", "R204", "T1", tuesday, time(16,0), time(19,30), student_ids=["S1","S2", "S3", "S4"])
system.add_class_schedule("OPERATING SYSTEM", "COMPLAB", "T2", wednesday, time(9,0), time(12,30), student_ids=["S1", "S2", "S3", "S4"])
system.add_class_schedule("MULTIMEDIA ARTS", "STUDIO", "T4", wednesday, time(17,0), time(20,0), student_ids=["S1"])
system.add_class_schedule("VISUAL ARTS", "R303", "MS. CHARLENE FLORES", wednesday, time(16,0), time(19,0), student_ids=["S2", "S3", "S4"])
system.add_class_schedule("COMP 03", "COMPLAB", "T4", thursday, time(9,0), time(12,30), student_ids=["S1", "S2", "S3", "S4"])
system.add_class_schedule("MULTIMEDIA ARTS", "LAB101", "T4", thursday, time(17,0), time(20,0), student_ids=["S1"])
system.add_class_schedule("DATA STRUCT", "COMPLAB", "T1", friday, time(16,0), time(19,30), student_ids=["S1", "S2", "S3", "S4"])

# Hardcoded user credentials for Flask-Login authentication
users = {
    "2024-00244-cl-1": {"user": User("S1", "ALAIZA NICOLE CARANTO", Role.STUDENT), "password": "studpass"},
    "2024-00244-cl-2": {"user": User("S2", "JIM DELANTAR", Role.STUDENT), "password": "studpass2"},
    "2024-00244-cl-3": {"user": User("S3", "WODY LUSANTA", Role.STUDENT), "password": "studpass3"},
    "2024-00244-cl-4": {"user": User("S4", "MARK BOLIGOR", Role.STUDENT), "password": "studpass4"},
    "2024-00245-tc-1": {"user": User("T1", "MR. JOLLARD FLORES", Role.TEACHER), "password": "teachpass"},
    "2024-00245-tc-2": {"user": User("T2", "MS. AGNES RECAÑA", Role.TEACHER), "password": "teachpass2"},
    "2024-00245-tc-3": {"user": User("T3", "MR. NEIL JOSE", Role.TEACHER), "password": "teachpass3"},
    "2024-00245-tc-4": {"user": User("T4", "MR. REYNAN BACCLE", Role.TEACHER), "password": "teachpass4"},
    "2024-00245-tc-5": {"user": User("T5", "MR. JED MALVEDA", Role.TEACHER), "password": "teachpass5"},
    "2024-00001-ad-1": {"user": User("A1", "ADMIN ALVARADO", Role.ADMIN), "password": "adminpass"},
    "2024-00001-ad-2": {"user": User("A2", "ADMIN LANIP", Role.ADMIN), "password": "adminpass2"},
}

# ========== HELPER FUNCTIONS ==========
def format_time_12hr(t):
    """Convert datetime.time to 12-hour format with AM/PM"""
    hour = t.hour
    minute = t.minute
    am_pm = "AM" if hour < 12 else "PM"
    hour = hour % 12
    hour = 12 if hour == 0 else hour
    return f"{hour}:{minute:02d} {am_pm}"

def get_teacher_name(teacher_id):
    # Get teacher name by ID
    teacher_names = {
        "T1": "MR. JOLLARD FLORES",
        "T2": "MS. AGNES RECAÑA", 
        "T3": "MR. NEIL JOSE",
        "T4": "MR. REYNAN BACCLE",
        "T5": "MR. JED MALVEDA"
    }
    return teacher_names.get(teacher_id, "Unknown Teacher")

def get_day_name(class_date):
    # Convert date to day name
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    return days[class_date.weekday()]

def get_fun_message():
    # Return random motivational message
    messages = [
        "🌟 YOUR SCHEDULE IS LOOKING GREAT TODAY!",
        "🚀 READY TO CONQUER YOUR CLASSES?",
        "📚 LEARNING IS AN ADVENTURE!",
        "💡 BRIGHT MINDS NEED BRIGHT ROOMS!",
        "🎯 STAY FOCUSED, YOU'VE GOT THIS!",
        "🌈 MAKE TODAY COLORFUL WITH LEARNING!",
        "⚡ ENERGY + EDUCATION = EXCELLENCE!",
        "🎉 ANOTHER DAY TO SHINE BRIGHT!",
        "🧠 FEED YOUR BRAIN WITH KNOWLEDGE!",
        "✨ YOU'RE DOING AMAZING!"
    ]
    import random
    return random.choice(messages)

@login_manager.user_loader
def load_user(user_id):
    # Load user by ID for Flask-Login
    for u in users.values():
        if u["user"].id == user_id:
            return u["user"]
    return None

# ========== ROLE SELECTION ==========
@app.route("/")
def index():
    # Redirect to role selection
    return redirect(url_for("select_role"))

@app.route("/select-role", methods=["GET", "POST"])
def select_role():
    # Handle role selection and redirect to login
    if current_user.is_authenticated:
        return redirect_to_dashboard()
    
    if request.method == "POST":
        selected_role = request.form.get("role")
        if selected_role in ["student", "teacher", "admin"]:
            session['selected_role'] = selected_role
            flash(f"WELCOME TO {selected_role.title()} mode! 🎉", "info")
            return redirect(url_for("login"))
        else:
            flash("Please select a valid role!", "danger")
    
    return render_template("select_role.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    # Handle user authentication
    if current_user.is_authenticated:
        return redirect_to_dashboard()
    
    if 'selected_role' not in session:
        return redirect(url_for("select_role"))
    
    selected_role = session['selected_role']
    
    if request.method == "POST":
        school_id = request.form["school_id"]
        password = request.form["password"]
        
        if school_id in users and users[school_id]["password"] == password:
            user = users[school_id]["user"]
            
            role_match = (
                (selected_role == "student" and user.role == Role.STUDENT) or
                (selected_role == "teacher" and user.role == Role.TEACHER) or
                (selected_role == "admin" and user.role == Role.ADMIN)
            )
            
            if not role_match:
                flash(f"Oops! This Account Is For A {user.role.name.title()}, Not A {selected_role.title()}. 😅", "warning")
                return render_template("login.html", selected_role=selected_role)
            
            login_user(user)
            session.pop('selected_role', None)
            
            flash(f"Welcome back, {user.name}! {get_fun_message()}", "success")
            return redirect_to_dashboard()
        else:
            flash("Hmm, Those Credentials Do Not Match Our Records. Try Again! 🔍", "danger")
    
    return render_template("login.html", selected_role=selected_role)

def redirect_to_dashboard():
    # Redirect user to appropriate dashboard based on role
    if current_user.role == Role.STUDENT:
        return redirect(url_for("student_dashboard"))
    elif current_user.role == Role.TEACHER:
        return redirect(url_for("teacher_dashboard"))
    elif current_user.role == Role.ADMIN:
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("select_role"))

@app.route("/logout")
@login_required
def logout():
    # Handle user logout
    flash(f"See you soon, {current_user.name}! 👋 Have a great day!", "info")
    logout_user()
    session.pop('selected_role', None)
    return redirect(url_for("select_role"))

# ========== STUDENT ROUTES ==========
@app.route("/student/dashboard")
@login_required
def student_dashboard():
    # Check student access
    if current_user.role != Role.STUDENT:
        flash("Oops — this page is for Students only. Please sign in as a Student to continue. 📚", "warning")
        return redirect(url_for("select_role"))
    
    today_date = date.today()
    fun_message = get_fun_message()
    
    # Get today's classes for current student
    todays_classes = []
    for c in system.class_schedules:
        # Only include classes that are scheduled for today and the current student is enrolled
        if c.class_date == today_date and current_user.id in getattr(c, 'student_ids', []):
            todays_classes.append({
                'course_code': c.course_code,
                'room_id': c.room_id,
                'teacher': get_teacher_name(c.teacher_id),
                'time_range': f"{format_time_12hr(c.start_time)} - {format_time_12hr(c.end_time)}",
                'start_time': c.start_time,
                'end_time': c.end_time
            })
    
    # Sort by start time
    todays_classes.sort(key=lambda x: x['start_time'])
    
    my_requests = [r for r in system.requests if r.user_id == current_user.id]
    rooms_list = list(system.rooms.values())
    
    # Next class
    next_class = None
    current_time = datetime.now().time()
    for cls in todays_classes:
        if cls['start_time'] > current_time:
            next_class = cls
            break
    
    return render_template("student_dashboard.html", 
                         name=current_user.name,
                         fun_message=fun_message,
                         today_date=today_date.strftime("%B %d, %Y"),
                         todays_classes=todays_classes[:3],  # Only show 3
                         rooms=rooms_list[:4],  # Only show 4
                         my_requests=my_requests[-3:],  # Last 3 requests
                         next_class=next_class,
                         total_rooms=len(rooms_list),
                         total_requests=len(my_requests))

@app.route("/student/schedule")
@login_required
def student_schedule():
    # Show student's weekly class schedule
    if current_user.role != Role.STUDENT:
        flash("Oops — Students only allowed here. Sign in as a Student to continue. 👨‍🎓", "warning")
        return redirect(url_for("select_role"))
    
    weekly_classes = []
    for c in system.class_schedules:
        # Only include classes that the current student is enrolled in
        if current_user.id not in getattr(c, 'student_ids', []):
            continue
        weekly_classes.append({
            'course_code': c.course_code,
            'room_id': c.room_id,
            'teacher': get_teacher_name(c.teacher_id),
            'day': get_day_name(c.class_date),
            'date': c.class_date.strftime("%Y-%m-%d"),
            'start_time': c.start_time,
            'end_time': c.end_time,
            'formatted_start': format_time_12hr(c.start_time),
            'formatted_end': format_time_12hr(c.end_time),
            'time_range': f"{format_time_12hr(c.start_time)} - {format_time_12hr(c.end_time)}"
        })
    
    # Sort by date then time
    weekly_classes.sort(key=lambda x: (x['date'], x['start_time']))
    
    return render_template("student_schedule.html", 
                         name=current_user.name, 
                         classes=weekly_classes,
                         fun_message=get_fun_message())

@app.route("/student/rooms")
@login_required
def student_rooms():
    # Show room availability for students
    if current_user.role != Role.STUDENT:
        flash("Oops — you don't have permission to view that page. 🚫", "warning")
        return redirect(url_for("select_role"))
    
    rooms_list = list(system.rooms.values())
    today_date = date.today()
    
    # Add availability status for each room
    for room in rooms_list:
        room.busy_today = []
        
        # Check class schedules for conflicts
        for c in system.class_schedules:
            if c.room_id == room.room_id and c.class_date == today_date:
                room.busy_today.append({
                    'time': f"{format_time_12hr(c.start_time)}-{format_time_12hr(c.end_time)}",
                    'course': c.course_code
                })
        
        # Check approved room requests for conflicts
        for req in system.requests:
            if (req.room_id == room.room_id and 
                req.usage_date == today_date and 
                req.status == "Accepted"):
                room.busy_today.append({
                    'time': f"{format_time_12hr(req.start_time)}-{format_time_12hr(req.end_time)}",
                    'course': f"Reserved ({req.purpose[:20]}...)"  # Truncate long purposes
                })
    
    return render_template("student_rooms.html", 
                         name=current_user.name, 
                         rooms=rooms_list,
                         today_date=today_date.strftime("%B %d, %Y"))

@app.route("/student/request", methods=["GET", "POST"])
@login_required
def student_request():
    # Handle room booking requests from students
    if current_user.role != Role.STUDENT:
        flash("Oops — Students only. Log in as a student to submit requests. 📝", "warning")
        return redirect(url_for("select_role"))
    
    if request.method == "POST":
        try:
            usage_date_str = request.form.get("usage_date", date.today().strftime("%Y-%m-%d"))
            usage_date = datetime.strptime(usage_date_str, "%Y-%m-%d").date()
            
            start_time_str = request.form.get("start_time", "13:00")
            end_time_str = request.form.get("end_time", "14:00")
            
            start_time_obj = datetime.strptime(start_time_str, "%H:%M").time()
            end_time_obj = datetime.strptime(end_time_str, "%H:%M").time()
            
            system.request_room(current_user.id, 
                               request.form["room_id"], 
                               usage_date, 
                               start_time_obj, 
                               end_time_obj, 
                               request.form["purpose"])
            flash("🎉 Request submitted successfully! We'll notify you when it's reviewed!", "success")
        except ValidationError as e:
            flash(f"Oops! {str(e)} 🛑", "danger")
        except Exception as e:
            flash(f"Oh no — something went wrong. {str(e)} 😬", "danger")
    
    my_requests = [r for r in system.requests if r.user_id == current_user.id]
    rooms_list = list(system.rooms.values())
    
    # Format request data for display
    for req in my_requests:
        req.formatted_start = format_time_12hr(req.start_time)
        req.formatted_end = format_time_12hr(req.end_time)
        req.formatted_date = req.usage_date.strftime("%B %d, %Y")
        req.status_color = {
            "Pending": "warning",
            "Accepted": "success",
            "Rejected": "danger"
        }.get(req.status, "secondary")
    
    return render_template("student_request.html", 
                         name=current_user.name, 
                         requests=my_requests[::-1],  # Reverse to show newest first
                         rooms=rooms_list,
                         today_date=date.today().strftime("%Y-%m-%d"))

# ========== TEACHER ROUTES ==========
@app.route("/teacher/dashboard")
@login_required
def teacher_dashboard():
    # Show teacher's dashboard with today's classes
    if current_user.role != Role.TEACHER:
        flash("Oops — this area is for Teachers only. Please sign in as a Teacher. 👨‍🏫", "warning")
        return redirect(url_for("select_role"))
    
    today_date = date.today()
    fun_message = get_fun_message()
    
    todays_classes = []
    for c in system.class_schedules:
        if c.class_date == today_date and c.teacher_id == current_user.id:
            todays_classes.append({
                'course_code': c.course_code,
                'room_id': c.room_id,
                'time_range': f"{format_time_12hr(c.start_time)} - {format_time_12hr(c.end_time)}",
                'start_time': c.start_time,
                'end_time': c.end_time
            })
    
    todays_classes.sort(key=lambda x: x['start_time'])
    
    my_requests = [r for r in system.requests if r.user_id == current_user.id]
    rooms_list = list(system.rooms.values())
    
    # Next class
    next_class = None
    current_time = datetime.now().time()
    for cls in todays_classes:
        if cls['start_time'] > current_time:
            next_class = cls
            break
    
    return render_template("teacher_dashboard.html", 
                         name=current_user.name,
                         fun_message=fun_message,
                         today_date=today_date.strftime("%B %d, %Y"),
                         todays_classes=todays_classes[:3],
                         rooms=rooms_list[:4],
                         my_requests=my_requests[-3:],
                         next_class=next_class,
                         total_rooms=len(rooms_list))

@app.route("/teacher/schedule")
@login_required
def teacher_schedule():
    if current_user.role != Role.TEACHER:
        flash("Oops — Teachers only. Please use a Teacher account to view schedules. 📅", "warning")
        return redirect(url_for("select_role"))
    
    my_classes = []
    for c in system.class_schedules:
        if c.teacher_id == current_user.id:
            my_classes.append({
                'course_code': c.course_code,
                'room_id': c.room_id,
                'day': get_day_name(c.class_date),
                'date': c.class_date.strftime("%Y-%m-%d"),
                'start_time': c.start_time,
                'end_time': c.end_time,
                'formatted_start': format_time_12hr(c.start_time),
                'formatted_end': format_time_12hr(c.end_time),
                'time_range': f"{format_time_12hr(c.start_time)} - {format_time_12hr(c.end_time)}"
            })
    
    my_classes.sort(key=lambda x: (x['date'], x['start_time']))
    
    return render_template("teacher_schedule.html", 
                         name=current_user.name, 
                         classes=my_classes,
                         fun_message=get_fun_message())


@app.route("/teacher/rooms")
@login_required
def teacher_rooms():
    if current_user.role != Role.TEACHER:
        flash("Oops — Teachers only. Please use a Teacher account to view room availability. 📅", "warning")
        return redirect(url_for("select_role"))

    rooms_list = list(system.rooms.values())
    today_date = date.today()

    # Add availability status
    for room in rooms_list:
        room.busy_today = []
        
        # Check class schedules
        for c in system.class_schedules:
            if c.room_id == room.room_id and c.class_date == today_date:
                room.busy_today.append({
                    'time': f"{format_time_12hr(c.start_time)}-{format_time_12hr(c.end_time)}",
                    'course': c.course_code
                })
        
        # Check approved room requests
        for req in system.requests:
            if (req.room_id == room.room_id and 
                req.usage_date == today_date and 
                req.status == "Accepted"):
                room.busy_today.append({
                    'time': f"{format_time_12hr(req.start_time)}-{format_time_12hr(req.end_time)}",
                    'course': f"Reserved ({req.purpose[:20]}...)"  # Truncate long purposes
                })

    return render_template("teacher_rooms.html", 
                         name=current_user.name, 
                         rooms=rooms_list,
                         today_date=today_date.strftime("%B %d, %Y"))

@app.route("/teacher/request", methods=["GET", "POST"])
@login_required
def teacher_request():
    # Handle room requests with suggestion feature
    if current_user.role != Role.TEACHER:
        flash("Oops — you don't have permission to access that page. 👨‍🏫", "warning")
        return redirect(url_for("select_role"))
    
    suggestions = []
    form_values = {}

    if request.method == "POST":
        try:
            action = request.form.get('action', 'submit')
            usage_date_str = request.form.get("usage_date", date.today().strftime("%Y-%m-%d"))
            usage_date = datetime.strptime(usage_date_str, "%Y-%m-%d").date()
            
            start_time_str = request.form.get("start_time", "14:00")
            end_time_str = request.form.get("end_time", "15:00")
            
            start_time_obj = datetime.strptime(start_time_str, "%H:%M").time()
            end_time_obj = datetime.strptime(end_time_str, "%H:%M").time()
            
            # capture common form values (to re-render when suggesting)
            form_values = {
                'usage_date': usage_date_str,
                'start_time': start_time_str,
                'end_time': end_time_str,
                'purpose': request.form.get('purpose',''),
                'min_capacity': request.form.get('min_capacity',''),
                'features': request.form.get('features','')
            }

            if action == 'suggest':
                # gather optional filters
                min_capacity = int(request.form.get('min_capacity', '0') or 0)
                features = [f.strip() for f in request.form.get('features','').split(',') if f.strip()]
                suggestions = system.find_best_rooms(usage_date, start_time_obj, end_time_obj, min_capacity, features)
                if not suggestions:
                    flash("No suitable rooms were found for your criteria — try relaxing features or capacity.", "info")
            else:
                # final submit -> create request
                room_id = request.form.get('room_id')
                system.request_room(current_user.id, 
                                   room_id, 
                                   usage_date, 
                                   start_time_obj, 
                                   end_time_obj, 
                                   request.form["purpose"])
                flash("🎯 Request sent successfully! Awaiting admin approval.", "success")
        except ValidationError as e:
            flash(f"Whoops! {str(e)} 🤔", "danger")
        except Exception as e:
            flash(f"Oh no — something went wrong. {str(e)} 😅", "danger")
    
    my_requests = [r for r in system.requests if r.user_id == current_user.id]
    rooms_list = list(system.rooms.values())
    
    for req in my_requests:
        req.formatted_start = format_time_12hr(req.start_time)
        req.formatted_end = format_time_12hr(req.end_time)
        req.formatted_date = req.usage_date.strftime("%B %d, %Y")
        req.status_color = {
            "Pending": "warning",
            "Accepted": "success",
            "Rejected": "danger"
        }.get(req.status, "secondary")
    
    return render_template("teacher_request.html", 
                         name=current_user.name, 
                         requests=my_requests[::-1],
                         rooms=rooms_list,
                         today_date=date.today().strftime("%Y-%m-%d"),
                         suggestions=suggestions,
                         form_values=form_values)

@app.route("/teacher/my-students")
@login_required
def teacher_students():
    if current_user.role != Role.TEACHER:
        flash("Oops — you don't have permission to do that. 👨‍🏫", "warning")
        return redirect(url_for("select_role"))
    
    # Get teacher's classes
    my_classes = {}
    for c in system.class_schedules:
        if c.teacher_id == current_user.id:
            if c.course_code not in my_classes:
                my_classes[c.course_code] = {
                    'room': c.room_id,
                    'time': f"{format_time_12hr(c.start_time)}-{format_time_12hr(c.end_time)}",
                    'students': []
                }
    
    # Add students (simulated - in real system, you'd have student enrollment)
    students_in_system = [
        {"id": "S1", "name": "ALAIZA NICOLE CARANTO"},
        {"id": "S2", "name": "JIM DELANTAR"},
        {"id": "S3", "name": "WODY LUSANTA"},
        {"id": "S4", "name": "MARK BOLIGOR"},
    ]
    
    for course in my_classes:
        my_classes[course]['students'] = students_in_system[:2]  # Simulate 2 students per class
    
    return render_template("teacher_Slists.html",
                         name=current_user.name,
                         my_classes=my_classes,
                         total_students=len(students_in_system))

# ========== ADMIN ROUTES ==========
@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    if current_user.role != Role.ADMIN:
        flash("Oops — admins only. Please sign in with an Admin account. 🔒", "danger")
        return redirect(url_for("select_role"))
    
    today_date = date.today()
    
    todays_classes = []
    for c in system.class_schedules:
        if c.class_date == today_date:
            todays_classes.append({
                'course_code': c.course_code,
                'room_id': c.room_id,
                'teacher': get_teacher_name(c.teacher_id),
                'time_range': f"{format_time_12hr(c.start_time)} - {format_time_12hr(c.end_time)}",
                'start_time': c.start_time,
                'end_time': c.end_time
            })
    
    todays_classes.sort(key=lambda x: x['start_time'])
    
    pending_count = sum(1 for req in system.requests if req.status == "Pending")
    total_requests = len(system.requests)
    rooms_list = list(system.rooms.values())
    
    # System statistics
    # `todays_classes` is a list of dicts (built above), so use dict key access here
    occupied_rooms_today = len(set(c['room_id'] for c in todays_classes))
    acceptance_rate = (total_requests - pending_count) / total_requests if total_requests > 0 else 0
    
    return render_template("admin_dashboard.html", 
                         name=current_user.name,
                         today_date=today_date.strftime("%B %d, %Y"),
                         todays_classes=todays_classes[:4],
                         rooms=rooms_list[:4],
                         requests=system.requests[-5:],  # Last 5 requests
                         classes=system.class_schedules[-3:],  # Last 3 classes
                         pending_requests=pending_count,
                         total_requests=total_requests,
                         total_rooms=len(rooms_list),
                         total_users=len(system.users),
                         occupied_rooms=occupied_rooms_today,
                         acceptance_rate=f"{acceptance_rate*100:.1f}%",
                         system_health="Excellent")

@app.route("/admin/manage")
@login_required
def admin_manage():
    if current_user.role != Role.ADMIN:
        flash("Oops — you don't have access to that admin section. 🚫", "danger")
        return redirect(url_for("select_role"))
    
    return render_template("admin_manage.html",
                         name=current_user.name,
                         users=system.users.values(),
                         rooms=system.rooms.values(),
                         classes=system.class_schedules)

@app.route("/admin/requests")
@login_required
def admin_requests():
    if current_user.role != Role.ADMIN:
        flash("Oops — permission required. 🔒", "danger")
        return redirect(url_for("select_role"))
    
    pending_requests = [r for r in system.requests if r.status == "Pending"]
    
    for req in pending_requests:
        req.formatted_start = format_time_12hr(req.start_time)
        req.formatted_end = format_time_12hr(req.end_time)
        req.formatted_date = req.usage_date.strftime("%B %d, %Y")
        req.user_name = system.users.get(req.user_id, User(req.user_id, "Unknown", Role.STUDENT)).name
    
    return render_template("admin_requests.html",
                         name=current_user.name,
                         requests=pending_requests,
                         total_pending=len(pending_requests))

@app.route("/admin/rooms")
@login_required
def admin_rooms():
    if current_user.role != Role.ADMIN:
        flash("Oops — you can't view this admin page right now. 🚧", "danger")
        return redirect(url_for("select_role"))
    
    rooms_list = list(system.rooms.values())
    
    # Add usage stats
    today = date.today()
    for room in rooms_list:
        # Count class schedules for today
        class_bookings = sum(1 for c in system.class_schedules 
                           if c.room_id == room.room_id and c.class_date == today)
        
        # Count approved requests for today
        request_bookings = sum(1 for r in system.requests 
                             if r.room_id == room.room_id and r.usage_date == today and r.status == "Accepted")
        
        room.today_bookings = class_bookings + request_bookings
        room.total_requests = sum(1 for r in system.requests 
                                 if r.room_id == room.room_id)
    
    return render_template("admin_rooms.html",
                         name=current_user.name,
                         rooms=rooms_list,
                         total_rooms=len(rooms_list))

@app.route("/admin/calendar")
@login_required
def admin_calendar():
    if current_user.role != Role.ADMIN:
        flash("Oops — admins only. Please sign in to view the calendar. 📅", "danger")
        return redirect(url_for("select_role"))
    
    # Get calendar for next 7 days
    calendar_data = {}
    for i in range(7):
        day = date.today() + timedelta(days=i)
        calendar_data[day.strftime("%Y-%m-%d")] = {
            'day_name': get_day_name(day),
            'date_str': day.strftime("%B %d"),
            'classes': [],
            'requests': []
        }
        
        for c in system.class_schedules:
            if c.class_date == day:
                calendar_data[day.strftime("%Y-%m-%d")]['classes'].append({
                    'course': c.course_code,
                    'room': c.room_id,
                    'teacher': get_teacher_name(c.teacher_id),
                    'time': f"{format_time_12hr(c.start_time)}-{format_time_12hr(c.end_time)}"
                })
        
        for r in system.requests:
            if r.usage_date == day:
                calendar_data[day.strftime("%Y-%m-%d")]['requests'].append({
                    'room': r.room_id,
                    'purpose': r.purpose,
                    'user': system.users.get(r.user_id, User(r.user_id, "Unknown", Role.STUDENT)).name,
                    'status': r.status,
                    'time': f"{format_time_12hr(r.start_time)}-{format_time_12hr(r.end_time)}"
                })
    
    return render_template("admin_calendar.html",
                         name=current_user.name,
                         calendar=calendar_data)

@app.route("/admin/approve/<req_id>")
@login_required
def approve_request(req_id):
    if current_user.role != Role.ADMIN:
        flash("Sorry — you don't have permission to approve requests. 👮‍♂️", "danger")
        return redirect(url_for("select_role"))
    
    try:
        system.approve_request(req_id, current_user.id)
        flash("✅ Request approved successfully! The user has been notified.", "success")
    except ValidationError as e:
        flash(f"❌ {str(e)}", "danger")
    
    return redirect(url_for("admin_requests"))

@app.route("/admin/reject/<req_id>", methods=["POST"])
@login_required
def reject_request(req_id):
    if current_user.role != Role.ADMIN:
        flash("Sorry — you don't have permission to reject requests. 🛑", "danger")
        return redirect(url_for("select_role"))
    
    reason = request.form["reason"]
    try:
        system.reject_request(req_id, current_user.id, reason)
        flash(f"🚫 Request rejected. Reason: {reason}", "warning")
    except ValidationError as e:
        flash(f"❌ {str(e)}", "danger")
    
    return redirect(url_for("admin_requests"))

@app.route("/admin/cancel_class/<schedule_id>")
@login_required
def cancel_class(schedule_id):
    if current_user.role != Role.ADMIN:
        flash("Sorry — you don't have permission to cancel classes. ⚠️", "danger")
        return redirect(url_for("select_role"))
    
    try:
        system.cancel_class(schedule_id)
        flash("🗑️ Class cancelled successfully! Students will be notified.", "info")
    except ValidationError as e:
        flash(f"❌ {str(e)}", "danger")
    
    return redirect(url_for("admin_manage"))

@app.route("/admin/change_room/<schedule_id>", methods=["POST"])
@login_required
def change_room(schedule_id):
    if current_user.role != Role.ADMIN:
        flash("Sorry — you don't have permission to change class rooms. 🔄", "danger")
        return redirect(url_for("select_role"))
    
    new_room_id = request.form["new_room_id"]
    try:
        system.update_class_room(schedule_id, new_room_id)
        flash(f"🔄 Class moved to {new_room_id} successfully!", "success")
    except ValidationError as e:
        flash(f"❌ {str(e)}", "danger")
    
    return redirect(url_for("admin_manage"))

@app.route("/admin/add_room", methods=["POST"])
@login_required
def add_room():
    if current_user.role != Role.ADMIN:
        flash("Sorry — you don't have permission to add rooms. 🏗️", "danger")
        return redirect(url_for("select_role"))
    
    try:
        tags = [t.strip() for t in request.form.get("tags", "").split(",") if t.strip()]
        features = [f.strip() for f in request.form.get("features", "").split(",") if f.strip()]
        zone = request.form.get("zone", "")
        maintenance = True if request.form.get("maintenance") == "on" else False

        system.add_room(
            request.form["room_id"], 
            request.form["name"], 
            int(request.form["capacity"]),
            tags,
            features,
            zone,
            maintenance
        )
        flash(f"🏢 Room {request.form['room_id']} added successfully! 🎉", "success")
    except ValidationError as e:
        flash(f"Oops — {str(e)}", "danger")
    
    return redirect(url_for("admin_rooms"))


@app.route("/admin/edit_room/<room_id>", methods=["GET", "POST"])
@login_required
def edit_room(room_id):
    if current_user.role != Role.ADMIN:
        flash("Oops — you don't have access to that admin section. 🚫", "danger")
        return redirect(url_for("select_role"))

    room = system.rooms.get(room_id)
    if not room:
        flash("Room not found.", "danger")
        return redirect(url_for("admin_rooms"))

    if request.method == "POST":
        try:
            tags = [t.strip() for t in request.form.get("tags", "").split(",") if t.strip()]
            features = [f.strip() for f in request.form.get("features", "").split(",") if f.strip()]
            zone = request.form.get("zone", "")
            maintenance = True if request.form.get("maintenance") == "on" else False

            system.update_room(
                room_id,
                name=request.form.get("name"),
                capacity=int(request.form.get("capacity")),
                tags=tags,
                features=features,
                zone=zone,
                maintenance=maintenance
            )
            flash(f"Room {room_id} updated successfully! ✅", "success")
        except ValidationError as e:
            flash(f"Oops — {str(e)}", "danger")
        except Exception as e:
            flash(f"Oh no — {str(e)}", "danger")

        return redirect(url_for("admin_rooms"))

    # GET -> render pre-filled form
    return render_template("admin_edit_room.html", room=room)


@app.route("/admin/delete_room/<room_id>", methods=["POST"])
@login_required
def delete_room(room_id):
    if current_user.role != Role.ADMIN:
        flash("Oops — you don't have access to that admin section. 🚫", "danger")
        return redirect(url_for("select_role"))

    try:
        system.remove_room(room_id)
        flash(f"Room {room_id} removed successfully.", "info")
    except ValidationError as e:
        flash(f"Oops — {str(e)}", "danger")
    except Exception as e:
        flash(f"Oh no — {str(e)}", "danger")

    return redirect(url_for("admin_rooms"))

@app.route("/admin/add_class", methods=["POST"])
@login_required
def add_class():
    if current_user.role != Role.ADMIN:
        flash("Sorry — you don't have permission to add classes. 📚", "danger")
        return redirect(url_for("select_role"))
    
    try:
        class_date = datetime.strptime(request.form["class_date"], "%Y-%m-%d").date()
        start_time = datetime.strptime(request.form["start_time"], "%H:%M").time()
        end_time = datetime.strptime(request.form["end_time"], "%H:%M").time()
        
        system.add_class_schedule(
            request.form["course_code"],
            request.form["room_id"],
            request.form["teacher_id"],
            class_date,
            start_time,
            end_time
        )
        flash(f"📚 Class {request.form['course_code']} scheduled successfully! 🗓️", "success")
    except ValidationError as e:
        flash(f"Oops — {str(e)}", "danger")
    except Exception as e:
        flash(f"Oh no — error: {str(e)}", "danger")
    
    return redirect(url_for("admin_manage"))

# ========== API ENDPOINTS ==========
@app.route("/api/room-availability/<room_id>/<date_str>")
@login_required
def room_availability(room_id, date_str):
    """Check room availability for a specific date"""
    try:
        check_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        bookings = []
        
        for c in system.class_schedules:
            if c.room_id == room_id and c.class_date == check_date:
                bookings.append({
                    'start': c.start_time.strftime("%H:%M"),
                    'end': c.end_time.strftime("%H:%M"),
                    'type': 'class',
                    'course': c.course_code
                })
        
        for r in system.requests:
            if r.room_id == room_id and r.usage_date == check_date and r.status == "Accepted":
                bookings.append({
                    'start': r.start_time.strftime("%H:%M"),
                    'end': r.end_time.strftime("%H:%M"),
                    'type': 'request',
                    'purpose': r.purpose
                })
        
        return jsonify({
            'room_id': room_id,
            'date': date_str,
            'bookings': bookings,
            'available_slots': []  # You could calculate available slots here
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == "__main__":
    # Create static folder if it doesn't exist
    if not os.path.exists('static'):
        os.makedirs('static')
    
    app.run(debug=True, host='0.0.0.0', port=5000)