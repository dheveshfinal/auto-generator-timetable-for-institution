from fastapi import FastAPI
from login import router as login_router
from fastapi.staticfiles import StaticFiles
from institution import router as institution_router
from institution_configuration import router as config_router
from programs import router as programs_router 
from programs_manage import router as manage_program_router
from subject_semester import router as subject_semester_router
from manage_subjects import router as manage_subjects_router
from add_semester import router as add_semester_router
from section_room import router as section_room_router
from manage_sections import router as manage_sections_router
from add_sections import router as add_section_router
from staff_details import router as staff_details_router
from manage_staff import router as manage_staff_router
from preferences import router as preferences_router
from semester_event import router as semester_event_router
from academic_holidays import router as academic_holidays_router
from add_programe_specializations import router as add_programe_specializations_router
from signup import router as signup_router
from add_staff_preferences import router as add_staff_preferences_router
from lab_session_router import router as lab_session_router_router 
from generate_timetable import router as timetable_router
from student_view import router as student_view_router




app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(login_router)
app.include_router(institution_router)
app.include_router(config_router)
app.include_router(programs_router)
app.include_router(manage_program_router)
app.include_router(subject_semester_router)
app.include_router(manage_subjects_router)
app.include_router(add_semester_router)
app.include_router(section_room_router)
app.include_router(manage_sections_router)
app.include_router(add_section_router)
app.include_router(staff_details_router)
app.include_router(manage_staff_router)
app.include_router(preferences_router)
app.include_router(semester_event_router)
app.include_router(academic_holidays_router)
app.include_router(add_programe_specializations_router)
app.include_router(signup_router)
app.include_router(add_staff_preferences_router)
app.include_router(lab_session_router_router )
app.include_router(timetable_router)
app.include_router(student_view_router)

