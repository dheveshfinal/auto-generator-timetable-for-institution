from fastapi import APIRouter, Request, Depends, Form, HTTPException
from sqlalchemy import MetaData, Table, select, insert,func,and_
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from database import get_db, engine
import logging
import random
from datetime import datetime,timedelta

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

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/student-view")
def student_view(
    request: Request,
    institution_id: int,
    program_id: int,
    specialization_id: int,
    semester_id: int,
    db: Session = Depends(get_db)
):
    try:
        # Header info
        header_query = (
            select(
                programs.c.name.label("program_name"),
                specializations.c.specialization_name,
                semesters.c.sem.label("semester_name")
            )
            .select_from(
                semester_subjects
                .join(semesters, semesters.c.id == semester_subjects.c.semester_id)
                .join(specializations, specializations.c.id == semesters.c.specialization_id)
                .join(programs, programs.c.id == specializations.c.program_id)
            )
            .where(
                semester_subjects.c.institution_id == institution_id,
                programs.c.id == program_id,
                specializations.c.id == specialization_id,
                semesters.c.id == semester_id
            ).limit(1)
        )
        header_result = db.execute(header_query).mappings().first()
        if not header_result:
            raise HTTPException(status_code=404, detail="Header info not found.")

        # Subjects
        subject_query = (
            select(subjects.c.name.label("subject_name"))
            .select_from(time_table.join(subjects, subjects.c.id == time_table.c.subject_id))
            .where(
                time_table.c.institution_id == institution_id,
                time_table.c.semester_id == semester_id,
                time_table.c.specialization_id == specialization_id,
                time_table.c.program_id == program_id
            )
            .distinct()
        )
        subject_results = db.execute(subject_query).mappings().all()
        subject_names = [row["subject_name"] for row in subject_results]

        # Sections
        section_query = (
            select(sections.c.section_name.label("section_name"))
            .select_from(time_table.join(sections, sections.c.id == time_table.c.section_id))
            .where(
                time_table.c.institution_id == institution_id,
                time_table.c.semester_id == semester_id
            )
            .distinct()
        )
        section_results = db.execute(section_query).mappings().all()
        section_names = [row["section_name"] for row in section_results]

        room_query = select(
            sections.c.section_name.label("section_name"),
            rooms.c.name.label("room_name")
        ).select_from(
            time_table
            .join(rooms, rooms.c.id == time_table.c.room_id)
            .join(sections, sections.c.id == time_table.c.section_id)
        ).where(
            time_table.c.institution_id == institution_id,
            time_table.c.semester_id == semester_id
        ).distinct()

        room_results = db.execute(room_query).mappings().all()
        section_room_map = {row["section_name"]: row["room_name"] for row in room_results}

        # Randomly assign subjects to each section
        # Ensure all sections get the same randomly shuffled subjects
        if len(subject_names) == 0 or len(section_names) == 0:
            raise HTTPException(status_code=404, detail="No subjects or sections found.")

        # Shuffle subjects once and assign same list to all sections
        # Shuffle subjects differently for each section
        section_subject_map = {
            section: random.sample(subject_names, k=len(subject_names))
            for section in section_names
        }


        confing=select(institution_configuration.c.configuration_value
        ).where(institution_configuration.c.institution_id==institution_id)





        # Config
        # Config
        config_query = select(
            institution_configuration.c.configuration_name,
            institution_configuration.c.configuration_value
        ).where(institution_configuration.c.institution_id == institution_id)
        config_results = db.execute(config_query).all()
        configurations = {row.configuration_name: row.configuration_value for row in config_results}

        # Required configuration values
        working_days = configurations.get("working_days", "").split(",")
        day_start_time = configurations.get("day_start_time", "09:00:00")
        day_end_time = configurations.get("day_end_time", "17:00:00")

        half_day_enabled = configurations.get("half_day_enabled", "FALSE") == "TRUE"
        half_day_pattern = configurations.get("half_day_pattern", "")
        half_day_start = configurations.get("half_day_start_time", "09:00:00")
        half_day_end = configurations.get("half_day_end_time", "13:00:00")

        # Construct time slots per day
        day_time_slot_map = {}
        for day in working_days:
            if half_day_enabled and day.strip() == half_day_pattern.strip():
                start = datetime.strptime(half_day_start, "%H:%M:%S")
                end = datetime.strptime(half_day_end, "%H:%M:%S")
            else:
                start = datetime.strptime(day_start_time, "%H:%M:%S")
                end = datetime.strptime(day_end_time, "%H:%M:%S")

            current = start
            slots = []
            while current < end:
                slot_str = current.strftime("%H:%M") + " - " + (current + timedelta(hours=1)).strftime("%H:%M")
                slots.append(slot_str)
                current += timedelta(hours=1)
            day_time_slot_map[day] = slots

        # Assign subjects randomly to time slots per section per day
        timetable_schedule = {}
        for section in section_names:
            timetable_schedule[section] = {}
            for day in working_days:
                slots_for_day = day_time_slot_map[day]
                # Repeat subject list if needed to fill all slots
                repeated_subjects = subject_names * ((len(slots_for_day) // len(subject_names)) + 1)
                daily_subjects = random.sample(repeated_subjects, len(slots_for_day))
                timetable_schedule[section][day] = daily_subjects

        if not subject_names or not section_names:
            raise HTTPException(status_code=404, detail="No subjects or sections found."
            )
        
        staff_query = select(
            staff.c.name.label("staff_name"),
            subjects.c.name.label("subject")
        ).select_from(
            time_table
            .join(staff, staff.c.id == time_table.c.staff_id)
            .join(subjects, subjects.c.id == time_table.c.subject_id)
        ).where(
            time_table.c.institution_id == institution_id,
            time_table.c.semester_id==semester_id


        ).distinct()

        staff_data = db.execute(staff_query).all()
        staff_final_data = {row[0]: row[1] for row in staff_data}

        inst_name=select(
            institution_table.c.name
        ).where(institution_table.c.id==institution_id)
        inst_final_name = db.execute(inst_name).scalar()



        # Render template
        return templates.TemplateResponse("student_view.html", {
            "request": request,
            "header_info": header_result,
            "institution_id":inst_final_name ,
            "program_id": program_id,
            "specialization_id": specialization_id,
            "semester_id": semester_id,
            "configurations": configurations,
            "day_time_slot_map": day_time_slot_map,
            "timetable_schedule": timetable_schedule,
            "section_subject_map": section_subject_map,
            "section_room_map": section_room_map,
            "staff_data": staff_final_data,
            "inst_final_name":inst_final_name
        })

    except Exception as e:
        logging.exception("Error in student_view")  # will show full stacktrace
        raise HTTPException(status_code=500, detail=str(e))


