from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import MetaData, Table, select
from sqlalchemy.orm import Session
from database import engine, get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Reflect schemas
user_metadata = MetaData(schema="user_management")
academic_metadata = MetaData(schema="academic_terms")
institution_metadata = MetaData(schema="institution_details")

users_table = Table("users", user_metadata, autoload_with=engine)
programs_table = Table("programs", academic_metadata, autoload_with=engine)
specializations_table = Table("specializations", academic_metadata, autoload_with=engine)
institution_table = Table("institution", institution_metadata, autoload_with=engine)

@router.get("/programs", response_class=HTMLResponse)
def view_programs(request: Request, username: str, db: Session = Depends(get_db)):
    # Fetch user by username
    user_query = select(users_table).where(users_table.c.username == username)
    user_result = db.execute(user_query).mappings().first()

    if not user_result:
        raise HTTPException(status_code=404, detail="User not found")

    institution_id = user_result["institution_id"]

    # Fetch institution info
    inst_query = select(institution_table).where(institution_table.c.id == institution_id)
    inst_result = db.execute(inst_query).mappings().first()
    if not inst_result:
        raise HTTPException(status_code=404, detail="Institution not found")

    # Fetch programs for that institution
    prog_query = select(programs_table).where(programs_table.c.institution_id == institution_id)
    prog_result = db.execute(prog_query).mappings().all()
    prog_dict_list = [dict(row) for row in prog_result]

    # Fetch specializations for that institution
    spec_query = select(specializations_table).where(specializations_table.c.institution_id == institution_id)
    spec_result = db.execute(spec_query).mappings().all()
    spec_dict_list = [dict(row) for row in spec_result]

    return templates.TemplateResponse("programs.html", {
        "request": request,
        "username": username,
        "institution": dict(inst_result),
        "programs": prog_dict_list,
        "specializations": spec_dict_list,
        "role_id": user_result["role_id"]  
    })
