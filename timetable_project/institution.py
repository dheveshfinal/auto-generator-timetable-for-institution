from fastapi import APIRouter, Depends, Request, HTTPException,Form
from fastapi.responses import HTMLResponse,RedirectResponse
from sqlalchemy import MetaData, Table, select
from sqlalchemy.orm import Session
from database import get_db, engine
from fastapi.templating import Jinja2Templates
from datetime import datetime
from sqlalchemy import update


router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Reflect the tables
user_metadata = MetaData(schema="user_management")
institution_metadata = MetaData(schema="institution_details")

users_table = Table("users", user_metadata, autoload_with=engine)
institution_table = Table("institution", institution_metadata, autoload_with=engine)

@router.get("/institution_dashboard", response_class=HTMLResponse)
def dashboard(request: Request, username: str, db: Session = Depends(get_db)):
    # Step 1: Find the user
    user_query = select(users_table).where(users_table.c.username == username)
    user_result = db.execute(user_query).mappings().first()

    if not user_result:
        raise HTTPException(status_code=404, detail="User not found")

    institution_id = user_result["institution_id"]

    # Step 2: Fetch institution by ID
    inst_query = select(institution_table).where(institution_table.c.id == institution_id)
    inst_result = db.execute(inst_query).mappings().first()

    if not inst_result:
        raise HTTPException(status_code=404, detail="Institution not found")

    institution = dict(inst_result)

    return templates.TemplateResponse("institution_dashboard.html", {
        "request": request,
        "username": username,
        "institution": institution
    })

@router.post("/institution/update")
async def update_institution(
    id: int = Form(...),
    username: str = Form(...),
    name: str = Form(...),
    principal_name: str = Form(...),
    address: str = Form(...),
    contact_email: str = Form(...),
    phone_number: str = Form(...),
    website: str = Form(...),
    db: Session = Depends(get_db)
):
    # Prepare update statement
    stmt = (
        update(institution_table)
        .where(institution_table.c.id == id)
        .values(
            name=name,
            principal_name=principal_name,
            address=address,
            contact_email=contact_email,
            phone_number=phone_number,
            website=website,
            updated_by=username,
            updated_timestamp=datetime.now()
        )
    )

    result = db.execute(stmt)
    db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"Institution with ID {id} not found.")

    return RedirectResponse(url=f"/institution_dashboard?username={username}", status_code=303)