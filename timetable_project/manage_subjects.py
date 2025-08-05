from fastapi import APIRouter, Request, Depends, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import MetaData, Table, select, update, delete
from sqlalchemy.orm import Session
from database import engine, get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Define metadata and tables
academic_schema = MetaData(schema="academic_terms")
staff_schema = MetaData(schema="staff_details")



subject_table = Table("subjects", academic_schema, autoload_with=engine)
semester_subject_table = Table("semester_subjects", academic_schema, autoload_with=engine)
semester_table = Table("semesters", academic_schema, autoload_with=engine)
lab_sessions_table = Table("lab_sessions", academic_schema, autoload_with=engine)


# 🚪 GET: Show Manage Subjects Page
@router.get("/manage_subjects", response_class=HTMLResponse)
def manage_subjects(
    request: Request,
    semester_id: int,
    institution_id: int,
    username: str,
    db: Session = Depends(get_db)
):
    # Fetch semester number
    semester_stmt = select(semester_table.c.sem).where(semester_table.c.id == semester_id)
    semester_number = db.execute(semester_stmt).scalar()

    # Get subject IDs mapped to the semester
    sem_sub_stmt = select(semester_subject_table).where(
        semester_subject_table.c.semester_id == semester_id
    )
    sem_sub_result = db.execute(sem_sub_stmt).mappings().all()
    subject_ids = [row["subject_id"] for row in sem_sub_result]

    # Fetch subjects
    subjects = []
    if subject_ids:
        subj_stmt = select(subject_table).where(subject_table.c.id.in_(subject_ids))
        subjects = db.execute(subj_stmt).mappings().all()

    # Fetch all semesters
    semesters_stmt = select(semester_table)
    semesters_result = db.execute(semesters_stmt).mappings().all()

    return templates.TemplateResponse("manage_subjects.html", {
        "request": request,
        "semester_id": semester_id,
        "semester_number": semester_number,
        "subjects": subjects,
        "all_semesters": semesters_result,
        "institution_id": institution_id,
        "username": username
    })


# 📝 POST: Update Subjects
@router.post("/update_subjects")
async def update_subjects(
    request: Request,
    semester_id: int = Form(...),
    institution_id: int = Form(...),
    username: str = Form(...),
    db: Session = Depends(get_db)
):
    form_data = await request.form()
    for key in form_data:
        if key.startswith("name_"):
            subject_id = int(key.split("_")[1])
            name = form_data.get(f"name_{subject_id}")
            code = form_data.get(f"code_{subject_id}")
            is_lab = form_data.get(f"is_lab_{subject_id}") == "true"

            # Update subject table
            upd_stmt = update(subject_table).where(subject_table.c.id == subject_id).values(
                name=name,
                code=code,
                is_lab=is_lab
            )
            db.execute(upd_stmt)

    db.commit()
    return RedirectResponse(
        url=f"/manage_subjects?semester_id={semester_id}&institution_id={institution_id}&username={username}",
        status_code=303
    )


# ❌ GET: Delete Subject
@router.get("/delete_subject/{subject_id}")
def delete_subject(
    subject_id: int,
    semester_id: int = Query(...),
    institution_id: int = Query(...),
    username: str = Query(...),
    db: Session = Depends(get_db)
):
    # ✅ Step 1: Delete references in lab_sessions (or any dependent tables)
    db.execute(
        delete(lab_sessions_table).where(lab_sessions_table.c.subject_id == subject_id)
    )

    # ✅ Step 2: Delete subject-semester mapping
    db.execute(
        delete(semester_subject_table).where(semester_subject_table.c.subject_id == subject_id)
    )

    # ✅ Step 3: Delete the subject itself
    db.execute(
        delete(subject_table).where(subject_table.c.id == subject_id)
    )

    db.commit()

    # ✅ Step 4: Redirect
    return RedirectResponse(
        url=f"/manage_subjects?semester_id={semester_id}&institution_id={institution_id}&username={username}",
        status_code=303
    )

# ➕ GET: Show Add Subject Form (Optional)
@router.get("/add_subject_form", response_class=HTMLResponse)
def add_subject_form(
    request: Request,
    semester_id: int = Query(...),
    institution_id: int = Query(...),
    username: str = Query(...)
):
    return templates.TemplateResponse("add_subject_form.html", {
        "request": request,
        "semester_id": semester_id,
        "institution_id": institution_id,
        "username": username
    })

@router.post("/add_subject")
def add_subject(
    name: str = Form(...),
    code: str = Form(...),
    is_lab: bool = Form(...),
    semester_id: int = Form(...),
    institution_id: int = Form(...),
    username: str = Form(...),
    db: Session = Depends(get_db)
):
    from datetime import datetime

    now = datetime.now()

    # Insert into subjects table
    insert_stmt = subject_table.insert().values(
        name=name,
        code=code,
        is_lab=is_lab,
        created_by=username,
        created_timestamp=now,
        updated_by=username,
        updated_timestamp=now
    ).returning(subject_table.c.id)

    subject_id = db.execute(insert_stmt).scalar()

    # Insert into semester_subject table with new fields
    db.execute(
        semester_subject_table.insert().values(
            institution_id=institution_id,
            subject_id=subject_id,
            semester_id=semester_id,
            created_by=username,
            created_timestamp=now,
            updated_by=username,
            updated_timestamp=now
        )
    )

    db.commit()

    return RedirectResponse(
        url=f"/manage_subjects?semester_id={semester_id}&institution_id={institution_id}&username={username}",
        status_code=303
    )



