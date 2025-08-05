from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import MetaData, Table, select
from sqlalchemy.orm import Session
from database import engine, get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")

academic_schema = MetaData(schema="academic_terms")
institution_schema = MetaData(schema="institution_details")

# Tables
subject_table = Table("subjects", academic_schema, autoload_with=engine)
semester_table = Table("semesters", academic_schema, autoload_with=engine)
semester_subject_table = Table("semester_subjects", academic_schema, autoload_with=engine)
institution_table = Table("institution", institution_schema, autoload_with=engine)
specialization_table = Table("specializations", academic_schema, autoload_with=engine)


@router.get("/subject_semester", response_class=HTMLResponse)
def subject_sem(request: Request, institution_id: int, username: str, db: Session = Depends(get_db)):
    # Fetch semester_subject rows for institution


    inst_check=select(institution_table).where(institution_table.c.id==institution_id)
    inst_final=db.execute(inst_check).mappings().first()

    if not inst_final:
        raise HTTPException(status_code=404, detail="institution not found")
   
   
    sem_sub_stmt = select(semester_subject_table).where(
    semester_subject_table.c.institution_id == institution_id
)

    sem_sub_result = db.execute(sem_sub_stmt).mappings().all()


    # Extract semester_ids and subject_ids
    semester_ids = list(set(row["semester_id"] for row in sem_sub_result))
    subject_ids = list(set(row["subject_id"] for row in sem_sub_result))

    # Fetch semesters
    semesters_stmt = select(semester_table).where(semester_table.c.id.in_(semester_ids))
    semesters_result = db.execute(semesters_stmt).mappings().all()
    semester_map = {row["id"]: row for row in semesters_result}

    # Fetch specialization ids from semesters
    specialization_ids = list(set(row["specialization_id"] for row in semesters_result))

    # Fetch specializations
    specializations_stmt = select(specialization_table).where(
        specialization_table.c.id.in_(specialization_ids)
    )
    specializations_result = db.execute(specializations_stmt).mappings().all()
    specialization_map = {row["id"]: row["specialization_name"] for row in specializations_result}

    # Fetch subjects
    subjects_stmt = select(subject_table).where(subject_table.c.id.in_(subject_ids))
    subjects_result = db.execute(subjects_stmt).mappings().all()
    subject_map = {
        row["id"]: {
            "name": row["name"],
            "code": row["code"],
            "is_lab": row["is_lab"]
        }
        for row in subjects_result
    }

    # Build semester → subjects dictionary with specialization
    semester_subjects = {}
    for row in sem_sub_result:
        sem_id = row["semester_id"]
        subj_id = row["subject_id"]

        sem_obj = semester_map.get(sem_id)
        specialization_id = sem_obj["specialization_id"]
        specialization_name = specialization_map.get(specialization_id, "N/A")

        if sem_id not in semester_subjects:
            semester_subjects[sem_id] = {
            "sem": sem_obj["sem"],
            "specialization": specialization_name,
            "start_date": sem_obj["start_date"].strftime("%Y-%m-%d") if sem_obj["start_date"] else None,
            "end_date": sem_obj["end_date"].strftime("%Y-%m-%d") if sem_obj["end_date"] else None,
            "working_days": sem_obj["working_days"],
            "subjects": []
            }

        semester_subjects[sem_id]["subjects"].append(subject_map[subj_id])

    # Fetch institution name
    institution_stmt = select(institution_table.c.name).where(
        institution_table.c.id == institution_id
    )
    institution_result = db.execute(institution_stmt).scalar()

    if not institution_result:
        raise HTTPException(status_code=404, detail="Institution not found")

    institution_name = institution_result

    return templates.TemplateResponse("subject_semester.html", {
        "request": request,
        "username": username,
        "institution_id": institution_id,
        "semester_subjects": semester_subjects,
        "institution_name": institution_name
    })
