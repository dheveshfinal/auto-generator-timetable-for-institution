from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import MetaData, Table, select
from sqlalchemy.orm import Session
from database import engine, get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Already defined
institution_schema = MetaData(schema="institution_details")
academic_schema = MetaData(schema="academic_terms")

institution_table = Table("semesters", academic_schema, autoload_with=engine)
rooms_table = Table("rooms", academic_schema, autoload_with=engine)
sections_room_table = Table("section_room_assignments", academic_schema, autoload_with=engine)
sections_table = Table("sections", academic_schema, autoload_with=engine)
specializations_table = Table("specializations", academic_schema, autoload_with=engine)

# 🔹 Declare the institutions table (not previously declared)
institutions_table = Table("institution", institution_schema, autoload_with=engine)


@router.get("/section_room", response_class=HTMLResponse)
def section_room(request: Request, institution_id: int, username: str, db: Session = Depends(get_db)):
    # ✅ Step 1: Get institution name
    inst_query = select(institutions_table.c.name).where(institutions_table.c.id == institution_id)
    inst_name = db.execute(inst_query).scalar()

    if not inst_name:
        raise HTTPException(status_code=404, detail="Institution not found")

    # ✅ Step 2: Get semesters for the institution
    sem_query = (
        select(institution_table)
        .distinct()
        .select_from(
            institution_table
            .join(sections_table, institution_table.c.id == sections_table.c.semester_id)
            .join(sections_room_table, sections_table.c.id == sections_room_table.c.section_id)
        )
        .where(sections_room_table.c.institution_id == institution_id)
        .order_by(institution_table.c.sem)
    )
    sem_results = db.execute(sem_query).fetchall()

    data = []

    # ✅ Step 3: Fetch sections + room + specialization for each semester
    for sem in sem_results:
        sections_query = (
        select(
            sections_table.c.id,
            sections_table.c.section_name,
            sections_room_table.c.room_id,
            specializations_table.c.specialization_name.label("specialization_name"),
            rooms_table.c.name.label("room_name"),
            rooms_table.c.location,
            rooms_table.c.capacity
        )
        .select_from(
            sections_table
            .join(sections_room_table, sections_table.c.id == sections_room_table.c.section_id)
            .join(institution_table, sections_table.c.semester_id == institution_table.c.id)  # Join to semesters
            .join(specializations_table, institution_table.c.specialization_id == specializations_table.c.id)  # Join to specializations
            .join(rooms_table, sections_room_table.c.room_id == rooms_table.c.id)
        )
        .where(
            sections_table.c.semester_id == sem.id,
            sections_room_table.c.institution_id == institution_id
        )
    )


        section_room_data = db.execute(sections_query).fetchall()

        data.append({
            "semester": sem,
            "sections": section_room_data
        })

    return templates.TemplateResponse("section_room.html", {
        "request": request,
        "institution_name": inst_name,
        "data": data,
        "username": username,
        "institution_id": institution_id
    })

