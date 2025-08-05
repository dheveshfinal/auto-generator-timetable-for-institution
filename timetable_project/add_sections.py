from fastapi import APIRouter, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from sqlalchemy.orm import Session
from sqlalchemy import select, insert, MetaData, Table
from database import get_db, engine
from datetime import datetime

template = Jinja2Templates(directory="templates")

academic_schema = MetaData(schema="academic_terms")
institution_schema = MetaData(schema="institution_details")

# Reflect tables
semester_table = Table("semesters", academic_schema, autoload_with=engine)
section_table = Table("sections", academic_schema, autoload_with=engine)
specialization_table = Table("specializations", academic_schema, autoload_with=engine)
room_table = Table("rooms", academic_schema, autoload_with=engine)
section_room_table = Table("section_room_assignments", academic_schema, autoload_with=engine)
institution_table = Table("institution", institution_schema, autoload_with=engine)

router = APIRouter()

@router.get("/add_section_room")
def section_room_open(
    request: Request,
    institution_id: int,
    username: str,
    db: Session = Depends(get_db)
):
    # Load specializations specific to the institution
    specs = db.execute(
    select(specialization_table).where(specialization_table.c.institution_id == institution_id)
).mappings().fetchall()


    return template.TemplateResponse("add_section.html", {
        "request": request,
        "username": username,
        "institution_id": institution_id,
        "specializations": specs
    })


@router.post("/add_section_room", response_class=HTMLResponse)
def section_room(request: Request,
                 institution_id: int,
                 username: str,
                 section_name: str = Form(...),
                 Room_name: str = Form(...),
                 Location: str = Form(...),
                 Capacity: int = Form(...),
                 specializations: str = Form(...),
                 sem: str = Form(...),
                 db: Session = Depends(get_db)):

    try:
        specialization_id = int(specializations)  # Cast to int
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid specialization ID")

    # Validate specialization
    spec_stmt = select(specialization_table).where(
        specialization_table.c.id == specialization_id,
        specialization_table.c.institution_id == institution_id
    )
    spec = db.execute(spec_stmt).mappings().fetchone()

    if not spec:
        raise HTTPException(
            status_code=404,
            detail=f"Specialization not found for institution. Searched for specialization_id={specialization_id}, institution_id={institution_id}"
        )

    # Validate semester
    sem_stmt = select(semester_table).where(
        semester_table.c.specialization_id == specialization_id,
        semester_table.c.sem == int(sem)
    )
    semester = db.execute(sem_stmt).fetchone()
    if not semester:
        raise HTTPException(status_code=404, detail="Semester not found. Please add semester before continuing.")

    # Insert Section
    insert_section = insert(section_table).values(
        semester_id=semester.id,
        section_name=section_name,
        created_by=username,
        created_timestamp=datetime.utcnow(),
        updated_by=username,
        updated_timestamp=datetime.utcnow()
    ).returning(section_table.c.id)
    section_id = db.execute(insert_section).scalar()
    db.commit()

    # Insert Room
    insert_room = insert(room_table).values(
        name=Room_name,
        room_type="Classroom",
        location=Location,
        capacity=Capacity,
        created_by=username,
        created_timestamp=datetime.utcnow(),
        updated_by=username,
        updated_timestamp=datetime.utcnow()
    ).returning(room_table.c.id)
    room_id = db.execute(insert_room).scalar()
    db.commit()

    # Insert Section Room Assignment
    insert_section_room = insert(section_room_table).values(
        section_id=section_id,
        room_id=room_id,
        institution_id=institution_id,
        created_by=username,
        created_timestamp=datetime.utcnow(),
        updated_by=username,
        updated_timestamp=datetime.utcnow()
    )
    db.execute(insert_section_room)
    db.commit()

    return template.TemplateResponse("add_section.html", {
        "request": request,
        "message": "✅ Section and room successfully created!",
        "username": username,
        "institution_id": institution_id,
        "specializations": db.execute(
            select(specialization_table).where(specialization_table.c.institution_id == institution_id)
        ).fetchall()
    })
