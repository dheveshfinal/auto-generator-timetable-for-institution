from fastapi import APIRouter, Request, Form, Depends, HTTPException,Query
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, update, delete, insert, MetaData, Table
from sqlalchemy.orm import Session
from database import engine, get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Schema reflection
academic_metadata = MetaData(schema="academic_terms")
programs_table = Table("programs", academic_metadata, autoload_with=engine)
specializations_table = Table("specializations", academic_metadata, autoload_with=engine)

institution_metadata = MetaData(schema="institution_details")
institution_table = Table("institution", institution_metadata, autoload_with=engine)

# GET: Render the Manage Program Page
@router.get("/programs/manage/{program_id}", response_class=HTMLResponse)
def manage_program_page(request: Request, program_id: int, username: str, institution_id: int, db: Session = Depends(get_db)):
    # Get program
    prog_query = select(programs_table).where(programs_table.c.id == program_id)
    prog_result = db.execute(prog_query).mappings().first()
    if not prog_result:
        raise HTTPException(status_code=404, detail="Program not found")

    # Get specializations
    spec_query = select(specializations_table).where(specializations_table.c.program_id == program_id)
    spec_result = db.execute(spec_query).mappings().all()

    # Get institution name
    inst_query = select(institution_table.c.name).where(institution_table.c.id == institution_id)
    inst_result = db.execute(inst_query).mappings().first()
    if not inst_result:
        raise HTTPException(status_code=404, detail="Institution not found")

    return templates.TemplateResponse("manage_program.html", {
        "request": request,
        "username": username,
        "institution_id": institution_id,
        "institution_name": inst_result["name"],
        "program": dict(prog_result),
        "specializations": [dict(row) for row in spec_result]
    })


# POST: Update Program Details
@router.post("/programs/manage/{program_id}/update")
def update_program(program_id: int, institution_id: int = Form(...), username: str = Form(...),
                   program_name: str = Form(...), duration_years: int = Form(...), db: Session = Depends(get_db)):

    upd_query = (
        update(programs_table)
        .where(programs_table.c.id == program_id)
        .values(name=program_name, duration_years=duration_years, updated_by=username)
    )
    db.execute(upd_query)
    db.commit()

    return RedirectResponse(
        url=f"/programs/manage/{program_id}?institution_id={institution_id}&username={username}",
        status_code=303
    )

# POST: Add Specialization
@router.post("/specializations/add/{program_id}")
def add_specialization(program_id: int, new_specialization: str = Form(...), institution_id: int = Form(...),
                       username: str = Form(...), db: Session = Depends(get_db)):

    if new_specialization.strip():
        ins_query = insert(specializations_table).values(
            institution_id=institution_id,
            program_id=program_id,
            specialization_name=new_specialization,
            created_by=username,
            updated_by=username
        )
        db.execute(ins_query)
        db.commit()

    return RedirectResponse(
        url=f"/programs/manage/{program_id}?institution_id={institution_id}&username={username}",
        status_code=303
    )

# POST: Delete Specialization
@router.post("/specializations/delete/{spec_id}")
def delete_specialization(spec_id: int, institution_id: int = Form(...), username: str = Form(...),
                          program_id: int = Form(...), db: Session = Depends(get_db)):

    del_query = delete(specializations_table).where(specializations_table.c.id == spec_id)
    db.execute(del_query)
    db.commit()

    return RedirectResponse(
        url=f"/programs/manage/{program_id}?institution_id={institution_id}&username={username}",
        status_code=303
    )

@router.get("/programs/specializations", response_class=HTMLResponse)
def show_specialization_form(
    request: Request,
    program_id: int = Query(...),
    institution_id: int = Query(...),
    username: str = Query(...)
):
    return templates.TemplateResponse("add_programe_specializations.html", {
        "request": request,
        "program_id": program_id,
        "institution_id": institution_id,
        "username": username
    })


# ✅ POST: Handle form submission
@router.post("/programs/specializations/add")
def add_specialization(
    request: Request,
    program_id: int = Form(...),
    institution_id: int = Form(...),
    username: str = Form(...),
    name: str = Form(...),
    description: str = Form(None),
    db: Session = Depends(get_db)
):
    db.execute(insert(specializations_table).values(
        program_id=program_id,
        name=name,
        description=description
    ))
    db.commit()
    return RedirectResponse(
        url=f"/programs/view?program_id={program_id}&institution_id={institution_id}&username={username}",
        status_code=303
    )
