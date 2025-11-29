from typing import Any, Dict, Optional
import threading

try:
    from supabase import create_client, Client  # type: ignore
except Exception:  # library not installed yet
    create_client = None  # type: ignore
    Client = None  # type: ignore


class SupabaseService:
    def __init__(self, url: str, key: str):
        self.enabled = False
        self._mem = {"lectures": {}, "attendance": {}, "faculties": {}, "students": {}}
        self._lock = threading.Lock()
        self._sb: Optional[Client] = None
        if url and key and create_client is not None:
            try:
                self._sb = create_client(url, key)
                self.enabled = True
            except Exception:
                self._sb = None
                self.enabled = False

    # Lectures
    def create_lecture(self, lecture_id: str, data: Dict[str, Any]) -> None:
        if self.enabled and self._sb is not None:
            try:
                self._sb.table("lectures").upsert({**data, "lectureId": lecture_id}).execute()
                return
            except Exception:
                pass
        with self._lock:
            self._mem["lectures"][lecture_id] = data

    def get_lecture(self, lecture_id: str) -> Optional[Dict[str, Any]]:
        if self.enabled and self._sb is not None:
            try:
                res = self._sb.table("lectures").select("*").eq("lectureId", lecture_id).limit(1).execute()
                data = getattr(res, "data", None) or []
                if data:
                    return data[0]
            except Exception:
                pass
        with self._lock:
            return self._mem["lectures"].get(lecture_id)

    def list_lectures(self) -> Dict[str, Dict[str, Any]]:
        if self.enabled and self._sb is not None:
            try:
                res = self._sb.table("lectures").select("*").execute()
                items = getattr(res, "data", None) or []
                return {it.get("lectureId"): it for it in items if it.get("lectureId")}
            except Exception:
                pass
        with self._lock:
            return dict(self._mem["lectures"])

    def delete_lecture(self, lecture_id: str) -> None:
        if self.enabled and self._sb is not None:
            try:
                self._sb.table("lectures").delete().eq("lectureId", lecture_id).execute()
                self._sb.table("attendance").delete().eq("lectureId", lecture_id).execute()
                return
            except Exception:
                pass
        with self._lock:
            self._mem["lectures"].pop(lecture_id, None)
            self._mem["attendance"].pop(lecture_id, None)

    # Attendance
    def write_attendance(self, lecture_id: str, roll_no: str, data: Dict[str, Any]) -> None:
        if self.enabled and self._sb is not None:
            try:
                payload = {**data, "lectureId": lecture_id, "rollNo": roll_no}
                self._sb.table("attendance").upsert(payload).execute()
                return
            except Exception:
                pass
        with self._lock:
            self._mem["attendance"].setdefault(lecture_id, {})
            self._mem["attendance"][lecture_id][roll_no] = data

    def list_attendance(self, lecture_id: str) -> Dict[str, Dict[str, Any]]:
        if self.enabled and self._sb is not None:
            try:
                res = self._sb.table("attendance").select("*").eq("lectureId", lecture_id).execute()
                items = getattr(res, "data", None) or []
                out: Dict[str, Dict[str, Any]] = {}
                for it in items:
                    rn = it.get("rollNo")
                    if rn:
                        # ensure compatibility with templates expecting fields
                        rec = dict(it)
                        out[rn] = rec
                return out
            except Exception:
                pass
        with self._lock:
            return dict(self._mem["attendance"].get(lecture_id, {}))

    def delete_attendance(self, lecture_id: str, roll_no: str) -> None:
        if self.enabled and self._sb is not None:
            try:
                self._sb.table("attendance").delete().eq("lectureId", lecture_id).eq("rollNo", roll_no).execute()
                return
            except Exception:
                pass
        with self._lock:
            if lecture_id in self._mem["attendance"]:
                self._mem["attendance"][lecture_id].pop(roll_no, None)

    # Faculties
    def _email_key(self, email: str) -> str:
        return (email or "").strip().lower()

    def create_faculty(self, email: str, data: Dict[str, Any]) -> None:
        key = self._email_key(email)
        if self.enabled and self._sb is not None:
            try:
                payload = {**data, "email": key}
                self._sb.table("faculties").upsert(payload).execute()
                return
            except Exception:
                pass
        with self._lock:
            self._mem["faculties"][key] = data

    def get_faculty(self, email: str) -> Optional[Dict[str, Any]]:
        key = self._email_key(email)
        if self.enabled and self._sb is not None:
            try:
                res = self._sb.table("faculties").select("*").eq("email", key).limit(1).execute()
                data = getattr(res, "data", None) or []
                if data:
                    return data[0]
            except Exception:
                pass
        with self._lock:
            return self._mem["faculties"].get(key)

    def list_faculties(self) -> Dict[str, Dict[str, Any]]:
        if self.enabled and self._sb is not None:
            try:
                res = self._sb.table("faculties").select("*").execute()
                items = getattr(res, "data", None) or []
                return {self._email_key(it.get("email", "")): it for it in items if it.get("email")}
            except Exception:
                pass
        with self._lock:
            return dict(self._mem["faculties"])  # shallow copy

    def delete_faculty(self, email: str) -> None:
        key = self._email_key(email)
        if self.enabled and self._sb is not None:
            try:
                self._sb.table("faculties").delete().eq("email", key).execute()
                return
            except Exception:
                pass
        with self._lock:
            self._mem["faculties"].pop(key, None)

    # Students
    def create_student(self, roll_no: str, data: Dict[str, Any]) -> None:
        roll = (roll_no or "").strip()
        if self.enabled and self._sb is not None:
            try:
                payload = {**data, "rollNo": roll}
                self._sb.table("students").upsert(payload).execute()
                return
            except Exception:
                pass
        with self._lock:
            self._mem["students"][roll] = data

    def get_student(self, roll_no: str) -> Optional[Dict[str, Any]]:
        roll = (roll_no or "").strip()
        if self.enabled and self._sb is not None:
            try:
                res = self._sb.table("students").select("*").eq("rollNo", roll).limit(1).execute()
                data = getattr(res, "data", None) or []
                if data:
                    return data[0]
            except Exception:
                pass
        with self._lock:
            return self._mem["students"].get(roll)

    def list_students(self) -> Dict[str, Dict[str, Any]]:
        if self.enabled and self._sb is not None:
            try:
                res = self._sb.table("students").select("*").execute()
                items = getattr(res, "data", None) or []
                return {it.get("rollNo"): it for it in items if it.get("rollNo")}
            except Exception:
                pass
        with self._lock:
            return dict(self._mem["students"])  # shallow copy

    def delete_student(self, roll_no: str) -> None:
        roll = (roll_no or "").strip()
        if self.enabled and self._sb is not None:
            try:
                self._sb.table("students").delete().eq("rollNo", roll).execute()
                return
            except Exception:
                pass
        with self._lock:
            self._mem["students"].pop(roll, None)
