from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import date, time
from typing import List, Dict
import itertools

class EduRoomError(Exception): pass
class ValidationError(EduRoomError): pass
class ConflictError(EduRoomError): pass
class PermissionError_(EduRoomError): pass

class Role(Enum):
    STUDENT = auto()
    TEACHER = auto()
    ADMIN = auto()

@dataclass
class User:
    user_id: str
    name: str
    role: Role

@dataclass
class Room:
    room_id: str
    name: str
    capacity: int
    tags: List[str] = field(default_factory=list)
    features: List[str] = field(default_factory=list)  # e.g., projector, computers
    zone: str = ""  # eg 'North Wing', '2nd Floor'
    maintenance: bool = False

@dataclass
class ClassSchedule:
    schedule_id: str
    course_code: str
    room_id: str
    teacher_id: str
    class_date: date
    start_time: time
    end_time: time
    student_ids: List[str] = field(default_factory=list)

@dataclass
class RoomRequest:
    request_id: str
    room_id: str
    user_id: str
    usage_date: date
    start_time: time
    end_time: time
    purpose: str
    status: str = "Pending"       # Pending, Accepted, Rejected
    rejection_reason: str = ""

class EduRoomSystem:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self.users: Dict[str, User] = {}
        self.class_schedules: List[ClassSchedule] = []
        self.requests: List[RoomRequest] = []
        self._req_seq = itertools.count(1)
        self._schedule_seq = itertools.count(1)

    def add_room(self, room_id, name, capacity, tags=None, features=None, zone=None, maintenance=False):
        if room_id in self.rooms:
            raise ValidationError("Room already exists.")
        if capacity <= 0:
            raise ValidationError("Capacity must be positive.")
        r = Room(room_id, name, capacity, tags or [], features or [], zone or "", bool(maintenance))
        self.rooms[room_id] = r
        return r

    def add_user(self, user_id, name, role: Role):
        if user_id in self.users:
            raise ValidationError("User already exists.")
        u = User(user_id, name, role)
        self.users[user_id] = u
        return u

    def add_class_schedule(self, course_code, room_id, teacher_id, class_date, start_time, end_time, student_ids=None):
        if room_id not in self.rooms:
            raise ValidationError("Room does not exist.")
        schedule_id = f"S{next(self._schedule_seq)}"
        cs = ClassSchedule(schedule_id, course_code, room_id, teacher_id, class_date, start_time, end_time, student_ids or [])
        self.class_schedules.append(cs)
        return cs

    def request_room(self, user_id, room_id, usage_date, start_time, end_time, purpose):
        if room_id not in self.rooms:
            raise ValidationError("Room does not exist.")
        if end_time <= start_time:
            raise ValidationError("End time must be after start time.")
        
        # Check for conflicts with class schedules
        for c in self.class_schedules:
            if (c.room_id == room_id and 
                c.class_date == usage_date and 
                self._times_overlap(c.start_time, c.end_time, start_time, end_time)):
                raise ConflictError(f"Room {room_id} is already scheduled for class '{c.course_code}' at {self._format_time_range(c.start_time, c.end_time)}")
        
        # Check for conflicts with approved requests
        for r in self.requests:
            if (r.room_id == room_id and 
                r.usage_date == usage_date and 
                r.status == "Accepted" and
                self._times_overlap(r.start_time, r.end_time, start_time, end_time)):
                raise ConflictError(f"Room {room_id} is already booked for another approved request at {self._format_time_range(r.start_time, r.end_time)}")
        
        request_id = f"REQ{next(self._req_seq)}"
        req = RoomRequest(request_id, room_id, user_id, usage_date, start_time, end_time, purpose)
        self.requests.append(req)
        return req

    def approve_request(self, request_id, admin_id):
        req = next((r for r in self.requests if r.request_id == request_id), None)
        if not req: raise ValidationError("Request not found.")
        
        # Check for conflicts with class schedules
        for c in self.class_schedules:
            if (c.room_id == req.room_id and 
                c.class_date == req.usage_date and 
                self._times_overlap(c.start_time, c.end_time, req.start_time, req.end_time)):
                raise ConflictError(f"Room {req.room_id} is already scheduled for class '{c.course_code}' at {self._format_time_range(c.start_time, c.end_time)}")
        
        # Check for conflicts with other accepted requests
        for r in self.requests:
            if (r.request_id != request_id and 
                r.room_id == req.room_id and 
                r.usage_date == req.usage_date and 
                r.status == "Accepted" and
                self._times_overlap(r.start_time, r.end_time, req.start_time, req.end_time)):
                raise ConflictError(f"Room {req.room_id} is already booked for another request at {self._format_time_range(r.start_time, r.end_time)}")
        
        req.status = "Accepted"
        return req

    def reject_request(self, request_id, admin_id, reason):
        req = next((r for r in self.requests if r.request_id == request_id), None)
        if not req: raise ValidationError("Request not found.")
        req.status = "Rejected"
        req.rejection_reason = reason
        return req

    def cancel_class(self, schedule_id):
        before = len(self.class_schedules)
        self.class_schedules = [s for s in self.class_schedules if s.schedule_id != schedule_id]
        if len(self.class_schedules) == before:
            raise ValidationError("Schedule not found.")

    def update_class_room(self, schedule_id, new_room_id):
        if new_room_id not in self.rooms:
            raise ValidationError("New room does not exist.")
        for s in self.class_schedules:
            if s.schedule_id == schedule_id:
                s.room_id = new_room_id
                return s
        raise ValidationError("Schedule not found.")

    def update_room(self, room_id, name=None, capacity=None, tags=None, features=None, zone=None, maintenance=None):
        if room_id not in self.rooms:
            raise ValidationError("Room not found.")
        r = self.rooms[room_id]
        if name is not None:
            r.name = name
        if capacity is not None:
            if capacity <= 0:
                raise ValidationError("Capacity must be positive.")
            r.capacity = capacity
        if tags is not None:
            r.tags = tags
        if features is not None:
            r.features = features
        if zone is not None:
            r.zone = zone
        if maintenance is not None:
            r.maintenance = bool(maintenance)
        return r

    def remove_room(self, room_id):
        if room_id not in self.rooms:
            raise ValidationError("Room not found.")
        # check schedules or requests that reference this room (prevent accidental deletion)
        for s in self.class_schedules:
            if s.room_id == room_id:
                raise ValidationError("Cannot remove room with scheduled classes.")
        for r in self.requests:
            if r.room_id == room_id:
                raise ValidationError("Cannot remove room with existing requests.")
        del self.rooms[room_id]

    def get_day_calendar(self, target_date: date):
        cal: Dict[str, Dict[str, List[str]]] = {}
        for room in self.rooms.values():
            cal[room.room_id] = {"classes": [], "requests": []}
        for sch in self.class_schedules:
            if sch.class_date == target_date:
                cal[sch.room_id]["classes"].append(f"{sch.course_code} {sch.start_time}-{sch.end_time}")
        for r in self.requests:
            if r.usage_date == target_date:
                cal[r.room_id]["requests"].append(f"{r.purpose} {r.start_time}-{r.end_time} ({r.status})")
        return cal

    def find_best_rooms(self, target_date: date, start_time: time, end_time: time, min_capacity: int = 0, required_features: List[str] = None):
        """Return a list of available rooms for the requested time/date, sorted by best fit.

        Criteria:
        - Not under maintenance
        - No class scheduled at overlapping time on target_date
        - No accepted request overlapping time on target_date
        - Capacity >= min_capacity
        - Ranks rooms by smallest sufficient capacity and number of matching features
        """
        req_feats = set([f.strip().lower() for f in (required_features or []) if f and f.strip()])

        def overlaps(s1, e1, s2, e2):
            return (s1 < e2) and (s2 < e1)

        candidates = []
        for room in self.rooms.values():
            if room.maintenance:
                continue
            if room.capacity < min_capacity:
                continue

            # check class schedule conflicts
            conflict = False
            for sch in self.class_schedules:
                if sch.room_id != room.room_id:
                    continue
                if sch.class_date != target_date:
                    continue
                if overlaps(start_time, end_time, sch.start_time, sch.end_time):
                    conflict = True
                    break
            if conflict:
                continue

            # check accepted requests
            for r in self.requests:
                if r.room_id != room.room_id:
                    continue
                if r.usage_date != target_date:
                    continue
                if r.status != 'Accepted':
                    continue
                if overlaps(start_time, end_time, r.start_time, r.end_time):
                    conflict = True
                    break
            if conflict:
                continue

            feats = set([f.lower() for f in (room.features or [])])
            matches = len(req_feats & feats) if req_feats else 0
            capacity_diff = room.capacity - min_capacity

            candidates.append((capacity_diff, -matches, room))

        # sort by capacity closeness then by feature matches
        candidates.sort(key=lambda x: (x[0], x[1]))
        return [c[2] for c in candidates]

    def _times_overlap(self, start1, end1, start2, end2):
        """Check if two time ranges overlap"""
        return (start1 < end2) and (start2 < end1)

    def _format_time_range(self, start_time, end_time):
        """Format time range for error messages"""
        from datetime import datetime
        start_12hr = datetime.strptime(str(start_time), '%H:%M:%S').strftime('%I:%M %p')
        end_12hr = datetime.strptime(str(end_time), '%H:%M:%S').strftime('%I:%M %p')
        return f"{start_12hr}-{end_12hr}"
