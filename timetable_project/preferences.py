from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, MetaData, Table
from sqlalchemy.orm import Session
from database import get_db, engine

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Define schemas
institution_schema = MetaData(schema="institution_details")
staff_schema = MetaData(schema="staff_details")

# Load tables
institution_table = Table("institution", institution_schema, autoload_with=engine)
staff_table = Table("staff", staff_schema, autoload_with=engine)
preferences_table = Table("preferences", staff_schema, autoload_with=engine)

@router.get("/preferences", response_class=HTMLResponse)
async def view_staff_preferences(
    request: Request,
    institution_id: int,
    staff_id: int,
    username:str,
    db: Session = Depends(get_db)
):
    stmt = (
        select(
            staff_table.c.id.label("staff_id"),
            staff_table.c.name.label("staff_name"),
            staff_table.c.role,
            preferences_table.c.preference_type,
            preferences_table.c.preference_value
        )
        .select_from(
            staff_table.join(preferences_table, staff_table.c.id == preferences_table.c.staff_id)
        )
        .where(
            staff_table.c.institution_id == institution_id,
            staff_table.c.id == staff_id
        )
        .order_by(staff_table.c.name)
    )

    results = db.execute(stmt).fetchall()

    return templates.TemplateResponse("staff_preferences.html", {
        "request": request,
        "preferences": results,
        "institution_id": institution_id,
        "staff_id": staff_id,
        "username":username
    })
