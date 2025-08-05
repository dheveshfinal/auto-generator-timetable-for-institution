from fastapi import APIRouter, Request, Form,Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import MetaData, Table, select, insert, update, delete
from database import get_db, engine
from sqlalchemy.orm import Session

templates = Jinja2Templates(directory="templates")
router = APIRouter()

# Schemas
academic_schema = MetaData(schema="academic_terms")
staff_schema = MetaData(schema="staff_details")

# Tables
lab_sessions = Table("lab_sessions", academic_schema, autoload_with=engine)
subjects = Table("subjects", academic_schema, autoload_with=engine)
rooms = Table("rooms", academic_schema, autoload_with=engine)
staff = Table("staff", staff_schema, autoload_with=engine)

# 1. View all lab sessions
@router.get("/lab_session")
def lab_session_home(
    request: Request,
    institution_id: int,
    username: str,
    db: Session = Depends(get_db)
):
    # Join lab_sessions with subjects, staff, and rooms
    stmt = (
        select(
            lab_sessions.c.id,
            subjects.c.name.label("subject_name"),
            staff.c.name.label("staff_name"),
            rooms.c.name.label("room_name"),
            lab_sessions.c.day,
            lab_sessions.c.start_time,
            lab_sessions.c.end_time,
        )
        .select_from(
            lab_sessions
            .join(subjects, lab_sessions.c.subject_id == subjects.c.id)
            .join(staff, lab_sessions.c.staff_id == staff.c.id)
            .join(rooms, lab_sessions.c.room_id == rooms.c.id)
        )
        .where(lab_sessions.c.institution_id == institution_id)  # ✅ Filter here
    )

    lab_data = db.execute(stmt).mappings().all()

    return templates.TemplateResponse("lab_sessions.html", {
        "request": request,
        "lab_sessions": lab_data,
        "institution_id": institution_id,
        "username": username
    })

# 2. Add a lab session - GET form
@router.get("/lab_session/add")
def add_lab_session_form(
    request: Request,
    institution: int,
    username: str,
    db: Session = Depends(get_db)
):
    subj = db.execute(select(subjects.c.id, subjects.c.name)).fetchall()
    stf = db.execute(select(staff.c.id, staff.c.name)).fetchall()
    rms = db.execute(select(rooms.c.id, rooms.c.name)).fetchall()

    return templates.TemplateResponse("add_lab_session.html", {
        "request": request,
        "subjects": subj,
        "staff": stf,
        "rooms": rms,
        "institution_id": institution,
        "username": username
    })


# 3. Add a lab session - POST
@router.post("/lab_session/add")
def add_lab_session(
    request: Request,
    subject_id: int = Form(...),
    staff_id: int = Form(...),
    room_id: int = Form(...),
    day: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    institution: int = Form(...),
    username: str = Form(...)
):
    with engine.connect() as conn:
        stmt = insert(lab_sessions).values(
            subject_id=subject_id,
            staff_id=staff_id,
            room_id=room_id,
            institution_id=institution,
            day=day,
            start_time=start_time,
            end_time=end_time,
            created_by=username
        )
        conn.execute(stmt)
        conn.commit()

    return RedirectResponse(url=f"/lab_session?institution_id={institution}&username={username}", status_code=303)


# 4. Edit lab session - GET form
@router.get("/lab_session/edit/{session_id}")
def edit_lab_session_form(request: Request, session_id: int, institution: int, username: str):
    with engine.connect() as conn:
        session = conn.execute(select(lab_sessions).where(lab_sessions.c.id == session_id)).first()
        subj = conn.execute(select(subjects.c.id, subjects.c.name)).fetchall()
        stf = conn.execute(select(staff.c.id, staff.c.name)).fetchall()
        rms = conn.execute(select(rooms.c.id, rooms.c.name)).fetchall()

    return templates.TemplateResponse("edit_lab_session.html", {
        "request": request,
        "session": session,
        "subjects": subj,
        "staff": stf,
        "rooms": rms,
        "institution_id": institution,
        "username": username
    })


# 5. Edit lab session - POST
@router.post("/lab_session/edit/{session_id}")
def edit_lab_session(
    session_id: int,
    subject_id: int = Form(...),
    staff_id: int = Form(...),
    room_id: int = Form(...),
    day: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    institution: int = Form(...),
    username: str = Form(...)
):
    with engine.connect() as conn:
        stmt = update(lab_sessions).where(lab_sessions.c.id == session_id).values(
            subject_id=subject_id,
            staff_id=staff_id,
            room_id=room_id,
            day=day,
            start_time=start_time,
            end_time=end_time,
            updated_by=username
        )
        conn.execute(stmt)
        conn.commit()

    return RedirectResponse(url=f"/lab_session?institution_id={institution}&username={username}", status_code=303)


# 6. Delete lab session
@router.get("/lab_session/delete/{session_id}")
def delete_lab_session(session_id: int, institution: int, username: str):
    with engine.connect() as conn:
        conn.execute(delete(lab_sessions).where(lab_sessions.c.id == session_id))
        conn.commit()

    return RedirectResponse(url=f"/lab_session?institution_id={institution}&username={username}", status_code=303)
