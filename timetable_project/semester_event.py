from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import MetaData, Table, select, update, delete, join,insert
from sqlalchemy.orm import Session
from database import engine, get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Schemas and tables
institution_schema = MetaData(schema="institution_details")
semester_event_schema = MetaData(schema="academic_terms")

institution_table = Table("institution", institution_schema, autoload_with=engine)
semester_event_table = Table("semester_events", semester_event_schema, autoload_with=engine)
semesters_table = Table("semesters", semester_event_schema, autoload_with=engine)

# GET: Render semester events page
@router.get("/semester_event", response_class=HTMLResponse)
def semester_event(
    request: Request,
    institution_id: int,
    username: str,
    add_new: bool = False,
    db: Session = Depends(get_db)
):
    # Get institution name
    institution_stmt = select(institution_table.c.name).where(institution_table.c.id == institution_id)
    institution_name = db.scalar(institution_stmt)
    if not institution_name:
        raise HTTPException(status_code=404, detail="Institution not found")

    # Get all semesters (for dropdown)
    semester_stmt = select(semesters_table.c.id, semesters_table.c.sem).select_from(
        join(semesters_table, semester_event_table, semesters_table.c.id == semester_event_table.c.semester_id)
    ).where(semester_event_table.c.institution_id == institution_id)
    semesters = db.execute(semester_stmt).mappings().all()

    # Get all semester events joined with semester name
    j = join(semester_event_table, semesters_table, semester_event_table.c.semester_id == semesters_table.c.id)
    stmt = select(
        semester_event_table.c.id,
        semester_event_table.c.semester_id,
        semester_event_table.c.title,
        semester_event_table.c.event_type,
        semester_event_table.c.date,
        semester_event_table.c.start_time,
        semester_event_table.c.end_time,
        semesters_table.c.sem.label("semester_name")
    ).select_from(j).where(semester_event_table.c.institution_id == institution_id)

    event_list = db.execute(stmt).mappings().all()

    return templates.TemplateResponse("semester_event.html", {
        "request": request,
        "institution_name": institution_name,
        "institution_id": institution_id,
        "username": username,
        "event_list": event_list,
        "semesters": semesters,
        "add_new": add_new
    })


# POST: Update an existing event
@router.post("/semester_event/update")
def update_event(
    event_id: int = Form(...),
    title: str = Form(...),
    event_type: str = Form(...),
    date: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    institution_id: int = Form(...),
    username: str = Form(...),
    db: Session = Depends(get_db)
):
    stmt = update(semester_event_table).where(semester_event_table.c.id == event_id).values(
        title=title,
        event_type=event_type,
        date=date,
        start_time=start_time,
        end_time=end_time,
        updated_by=username
    )
    db.execute(stmt)
    db.commit()
    return RedirectResponse(url=f"/semester_event?institution_id={institution_id}&username={username}", status_code=303)


# POST: Delete an event
@router.post("/semester_event/delete")
def delete_event(
    event_id: int = Form(...),
    institution_id: int = Form(...),
    username: str = Form(...),
    db: Session = Depends(get_db)
):
    stmt = delete(semester_event_table).where(semester_event_table.c.id == event_id)
    db.execute(stmt)
    db.commit()
    return RedirectResponse(url=f"/semester_event?institution_id={institution_id}&username={username}", status_code=303)


@router.get("/semester_event/new", response_class=HTMLResponse)
def new_semester_event(
    request: Request,
    institution_id: int,
    username: str,
    db: Session = Depends(get_db)
):
    # Get all semesters for the institution to populate dropdown
    semester_stmt = select(semesters_table.c.id, semesters_table.c.sem).select_from(semesters_table)
    semesters = db.execute(semester_stmt).mappings().all()

    return templates.TemplateResponse("new_semester_event.html", {
        "request": request,
        "institution_id": institution_id,
        "username": username,
        "semesters": semesters
    })


# POST: Create new semester event
@router.post("/semester_event/new")
def create_semester_event(
    title: str = Form(...),
    event_type: str = Form(...),
    date: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    semester_id: int = Form(...),
    institution_id: int = Form(...),
    username: str = Form(...),
    db: Session = Depends(get_db)
):
    stmt = insert(semester_event_table).values(
        title=title,
        event_type=event_type,
        date=date,
        start_time=start_time,
        end_time=end_time,
        semester_id=semester_id,
        institution_id=institution_id,
        created_by=username  # If this column exists
    )
    db.execute(stmt)
    db.commit()
    return RedirectResponse(
        url=f"/semester_event?institution_id={institution_id}&username={username}", status_code=303
    )