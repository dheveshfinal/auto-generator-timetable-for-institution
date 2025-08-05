from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import MetaData, Table, select
from sqlalchemy.orm import Session
from database import engine, get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")

institution_schema = MetaData(schema="institution_details")
staff_schema = MetaData(schema="staff_details")

institution_table = Table("institution", institution_schema, autoload_with=engine)
staff_table = Table("staff", staff_schema, autoload_with=engine)

@router.get("/staff_details", response_class=HTMLResponse)
def staff_details(request: Request, institution_id: int, username: str, db: Session = Depends(get_db)):
    # Check if institution exists
    inst_query = select(institution_table).where(institution_table.c.id == institution_id)
    inst_result = db.execute(inst_query).mappings().first()
    if not inst_result:
        raise HTTPException(status_code=404, detail="Institution not found")

    # Fetch staff for that institution
    staff_query = select(
        staff_table.c.id,
        staff_table.c.name,
        staff_table.c.email,
        staff_table.c.role
    ).where(staff_table.c.institution_id == institution_id)
    staff_result = db.execute(staff_query).mappings().all()

    return templates.TemplateResponse("staff_details.html", {
        "request": request,
        "staff_list": staff_result,
        "institution_name": inst_result["name"],
        "username": username,
        "institution_id":institution_id
    })
