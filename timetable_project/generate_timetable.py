from fastapi import APIRouter, Request, Depends, Form, HTTPException
from sqlalchemy import MetaData, Table, select, insert,delete,and_
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from database import get_db, engine
import logging
from fastapi.responses  import HTMLResponse
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define metadata per schema
academic_meta = MetaData(schema="academic_terms")
institution_meta = MetaData(schema="institution_details")
staff_meta = MetaData(schema="staff_details")
time_table_meta = MetaData(schema="time_table")

# Reflect tables
staff = Table("staff", staff_meta, autoload_with=engine)
preferences = Table("preferences", staff_meta, autoload_with=engine)
institution_configuration = Table("institution_configuration", institution_meta, autoload_with=engine)
institution_table = Table("institution", institution_meta, autoload_with=engine)
subjects = Table("subjects", academic_meta, autoload_with=engine)
rooms = Table("rooms", academic_meta, autoload_with=engine)
sections = Table("sections", academic_meta, autoload_with=engine)
semesters = Table("semesters", academic_meta, autoload_with=engine)
programs = Table("programs", academic_meta, autoload_with=engine)
specializations = Table("specializations", academic_meta, autoload_with=engine)
academic_holidays = Table("academic_holidays", academic_meta, autoload_with=engine)
semester_events = Table("semester_events", academic_meta, autoload_with=engine)
lab_sessions = Table("lab_sessions", academic_meta, autoload_with=engine)
semester_subjects = Table("semester_subjects", academic_meta, autoload_with=engine)
section_room_assignments = Table("section_room_assignments", academic_meta, autoload_with=engine)
time_table = Table("time_table", time_table_meta, autoload_with=engine)


    # Query all necessary IDs for insertion into time_table
@router.post("/generate-timetable")
def generate_timetable(request: Request, institution_id: int = Form(...), db: Session = Depends(get_db)):

    stmt = select(
        semesters.c.id.label("semester_id"),
        subjects.c.id.label("subject_id"),
        sections.c.id.label("section_id"),
        rooms.c.id.label("room_id"),
        semesters.c.specialization_id.label("specialization_id"),
        specializations.c.program_id.label("program_id"),
        lab_sessions.c.id.label("lab_session_id"),
        lab_sessions.c.staff_id.label("staff_id"),  # ← NEW
        academic_holidays.c.id.label("holiday_id"),
        institution_configuration.c.configuration_id.label("configuration_id")
    ).select_from(
        semester_subjects
        .join(semesters, semester_subjects.c.semester_id == semesters.c.id)
        .join(subjects, semester_subjects.c.subject_id == subjects.c.id)
        .join(sections, sections.c.semester_id == semesters.c.id)
        .join(section_room_assignments, section_room_assignments.c.section_id == sections.c.id)
        .join(rooms, section_room_assignments.c.room_id == rooms.c.id)
        .join(specializations, semesters.c.specialization_id == specializations.c.id)
        .outerjoin(lab_sessions, lab_sessions.c.subject_id == subjects.c.id)  # ← LEFT JOIN
        .outerjoin(academic_holidays, academic_holidays.c.institution_id == institution_id)
        .outerjoin(institution_configuration,institution_configuration.c.institution_id==institution_id)
    ).where(
        section_room_assignments.c.institution_id == institution_id
    ).distinct()

    results = db.execute(stmt).fetchall()

    if not results:
        raise HTTPException(status_code=404, detail="No valid data found for timetable generation.")

    inserted_count = 0
    for row in results:
        db.execute(insert(time_table).values(
            institution_id=institution_id,
            semester_id=row.semester_id,
            subject_id=row.subject_id,
            section_id=row.section_id,
            room_id=row.room_id,
            specialization_id=row.specialization_id,
            program_id=row.program_id,
            lab_session_id=row.lab_session_id,
            staff_id=row.staff_id,  # ← NEW
            holiday_id=row.holiday_id,
            configuration_id=row.configuration_id,
            created_by="devesha",
            updated_by="devesha"
        ))
        inserted_count += 1

    db.commit()

    return {
        "message": f"Timetable generated successfully. {inserted_count} entries inserted.",
        "institution_id": institution_id
    }







@router.get("/get-related-semesters")
def get_related_semesters(
    request: Request,
    institution_id: int,
    db: Session = Depends(get_db)
):
    # Get related semesters
    semester_query = (
        select(
            semesters.c.id.label("semester_id"),
            semesters.c.sem.label("semester_name")
        )
        .select_from(
            semester_subjects.join(
                semesters, semesters.c.id == semester_subjects.c.semester_id
            )
        )
        .where(semester_subjects.c.institution_id == institution_id)
        .distinct()
    )
    semester_results = db.execute(semester_query).all()
    semesters_list = [
        {"semester_id": row.semester_id, "semester_name": row.semester_name}
        for row in semester_results
    ]

    # Fetch all programs for the institution
    program_query = (
        select(programs.c.id, programs.c.name)
        .where(programs.c.institution_id == institution_id)
    )
    program_results = db.execute(program_query).all()
    programs_list = [{"id": row.id, "name": row.name} for row in program_results]

    # Safely fetch all specializations if there are programs
    specializations_list = []
    subject_list = []
    if programs_list:
        program_ids = [p["id"] for p in programs_list]

        # Specializations
        specialization_query = (
            select(
                specializations.c.id,
                specializations.c.specialization_name,
                specializations.c.program_id
            )
            .where(specializations.c.program_id.in_(program_ids))
        )
        specialization_results = db.execute(specialization_query).all()
        specializations_list = [
            {
                "id": row.id,
                "name": row.specialization_name,
                "program_id": row.program_id
            }
            for row in specialization_results
        ]
    return templates.TemplateResponse(
        "generate.html",
        {
            "request": request,
            "institution_id": institution_id,
            "semesters": semesters_list,
            "programs": programs_list,
            "specializations": specializations_list,
           
        }
    )
