from fastapi import APIRouter, Request, Form, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse,RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, insert, MetaData, Table
from sqlalchemy.orm import Session
from database import engine, get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Schema reflection
user_metadata = MetaData(schema="user_management")
academic_metadata = MetaData(schema="academic_terms")
institution_metadata = MetaData(schema="institution_details")

users_table = Table("users", user_metadata, autoload_with=engine)
institution_table = Table("institution", institution_metadata, autoload_with=engine)
programs_table = Table("programs", academic_metadata, autoload_with=engine)
specializations_table = Table("specializations", academic_metadata, autoload_with=engine)

# Show form to add a new program
@router.get("/programs/specializations/form", response_class=HTMLResponse)
def new_program_form(request: Request,
                     institution_id: int,
                     username: str,
                     db: Session = Depends(get_db)):
    inst_query = select(institution_table).where(institution_table.c.id == institution_id)
    inst_result = db.execute(inst_query).mappings().first()
    if not inst_result:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    return templates.TemplateResponse("add_program.html", {
        "request": request,
        "institution": inst_result,
        "username": username
    })

# Handle form submission to add program and specialization
@router.post("/programs/new", response_class=HTMLResponse)
def create_program(request: Request,
                   institution_id: int = Form(...),
                   username: str = Form(...),
                   name: str = Form(...),
                   duration_years: int = Form(...),
                   specialization_name: str = Form(...),
                   db: Session = Depends(get_db)):

    # Validate user
    user_query = select(users_table).where(users_table.c.username == username)
    user_result = db.execute(user_query).mappings().first()
    if not user_result:
        raise HTTPException(status_code=404, detail="User not found")

    # Insert program
    program_insert_stmt = insert(programs_table).returning(programs_table.c.id).values(
        institution_id=institution_id,
        name=name,
        duration_years=duration_years,
        created_by=username,
        updated_by=username
    )
    program_result = db.execute(program_insert_stmt)
    program_id = program_result.scalar_one()
    
    # Insert specialization
    db.execute(insert(specializations_table).values(
        institution_id=institution_id,
        program_id=program_id,
        specialization_name=specialization_name,
        created_by=username,
        updated_by=username
    ))

    db.commit()

    # Fetch updated institution
    inst_query = select(institution_table).where(institution_table.c.id == institution_id)
    institution = db.execute(inst_query).mappings().first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    # Fetch all programs for this institution
    prog_query = select(programs_table).where(programs_table.c.institution_id == institution_id)
    programs = db.execute(prog_query).mappings().all()

    # Fetch all specializations for this institution
    spec_query = select(specializations_table).where(specializations_table.c.institution_id == institution_id)
    specializations = db.execute(spec_query).mappings().all()

    return templates.TemplateResponse("programs.html", {
        "request": request,
        "username": username,
        "institution": institution,
        "programs": programs,
        "specializations": specializations,
        "role_id": user_result["role_id"]
    })
