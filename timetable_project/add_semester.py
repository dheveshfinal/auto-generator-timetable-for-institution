from fastapi import APIRouter, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from sqlalchemy.orm import Session
from sqlalchemy import MetaData, Table, select
from database import get_db, engine
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Reflect academic_terms schema
academic_schema = MetaData(schema="academic_terms")

semester_table = Table("semesters", academic_schema, autoload_with=engine)
specialization_table = Table("specializations", academic_schema, autoload_with=engine)
subject_table = Table("subjects", academic_schema, autoload_with=engine)
semester_subject_table = Table("semester_subjects", academic_schema, autoload_with=engine)

# GET route to show the semester form
@router.get("/add_semester_form")
def add_semester_form(institution_id: int, username: str, request: Request, db: Session = Depends(get_db)):
    # Fetch specializations
    specializations = db.execute(
        select(specialization_table).where(specialization_table.c.institution_id == institution_id)
    ).fetchall()

    # Get subject IDs from semester_subjects for this institution
    subject_ids_stmt = select(semester_subject_table.c.subject_id).where(
        semester_subject_table.c.institution_id == institution_id
    )
    subject_ids = [row[0] for row in db.execute(subject_ids_stmt).fetchall()]

    # Fetch subjects using those IDs
    subjects = []
    if subject_ids:
        subjects_stmt = select(subject_table).where(subject_table.c.id.in_(subject_ids))
        subjects = db.execute(subjects_stmt).fetchall()

    return templates.TemplateResponse("add_semester_form.html", {
        "request": request,
        "institution_id": institution_id,
        "username": username,
        "specializations": specializations,
        "subjects": subjects
    })

# POST route to insert semester data
@router.post("/add_semester")
def add_semester(
    specialization_id: int = Form(...),
    sem: int = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    working_days: int = Form(...),
    institution_id: int = Form(...),
    username: str = Form(...),
    subject_inputs: list[str] = Form(...),
    db: Session = Depends(get_db)
):
    from sqlalchemy import func

    # Insert semester
    insert_stmt = semester_table.insert().values(
        specialization_id=specialization_id,
        sem=sem,
        start_date=start_date,
        end_date=end_date,
        working_days=working_days,
        created_by=username,
        created_timestamp=datetime.now(),
        updated_by=username,
        updated_timestamp=datetime.now()
    )
    result = db.execute(insert_stmt)
    db.commit()
    semester_id = result.inserted_primary_key[0]

    for item in subject_inputs:
        # Try to parse as subject_id
        try:
            subject_id = int(item)
        except ValueError:
            # If it's a name, check if it already exists (case-insensitive match)
            existing_subject = db.execute(
                select(subject_table.c.id).where(
                    func.lower(subject_table.c.name) == item.lower()
                )
            ).fetchone()

            if existing_subject:
                subject_id = existing_subject[0]
            else:
                # Insert new subject with default values
                insert_subject = subject_table.insert().values(
                    name=item,
                    code='',           # default
                    is_lab=False,      # default
                    created_by=username,
                    created_timestamp=datetime.now(),
                    updated_by=username,
                    updated_timestamp=datetime.now()
                )
                result_subject = db.execute(insert_subject)
                db.commit()
                subject_id = result_subject.inserted_primary_key[0]

        # Insert into semester_subjects
        db.execute(
            semester_subject_table.insert().values(
                semester_id=semester_id,
                subject_id=subject_id,
                institution_id=institution_id  # this goes in semester_subjects only
            )
        )

    db.commit()

    return RedirectResponse(
        url=f"/subject_semester?institution_id={institution_id}&username={username}",
        status_code=303
    )
