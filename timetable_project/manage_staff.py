from fastapi import APIRouter, Request, Depends, Query, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, update, delete, MetaData, Table
from sqlalchemy.orm import Session
from database import get_db, engine
from werkzeug.security import generate_password_hash
import hashlib

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Load tables from schema
staff_schema = MetaData(schema="staff_details")
staff_table = Table("staff", staff_schema, autoload_with=engine)
preferences_table = Table("preferences", staff_schema, autoload_with=engine)

# ✅ GET: Show the update form
@router.get("/update/", response_class=HTMLResponse)
def get_update_form(
    request: Request,
    staff_id: int = Query(...),
    institution_id: int = Query(...),
    username: str = Query(...),
    db: Session = Depends(get_db)
):
    stmt = select(staff_table).where(staff_table.c.id == staff_id)
    staff = db.execute(stmt).mappings().first()
    if not staff:
        return RedirectResponse("/staff_details", status_code=303)
    return templates.TemplateResponse("manage_staff.html", {
        "request": request,
        "staff": staff,
        "institution_id": institution_id,
        "username": username
    })


# ✅ POST: Submit updated staff form
@router.post("/update", response_class=HTMLResponse)
def update_staff(
    request: Request,
    staff_id: int = Form(...),
    institution_id: int = Form(...),
    username: str = Form(...),
    name: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db)
):
    stmt = (
        update(staff_table)
        .where(staff_table.c.id == staff_id)
        .values(name=name, email=email, role=role)
    )
    db.execute(stmt)
    db.commit()
    return RedirectResponse(
        url=f"/staff_details?institution_id={institution_id}&username={username}",
        status_code=303
    )


# ✅ GET: Delete staff and preferences
@router.get("/delete")
def delete_staff(
    request: Request,
    staff_id: int = Query(...),
    institution_id: int = Query(...),
    username: str = Query(...),
    db: Session = Depends(get_db)
):
    # Delete related preferences first
    db.execute(delete(preferences_table).where(preferences_table.c.staff_id == staff_id))
    # Then delete the staff member
    db.execute(delete(staff_table).where(staff_table.c.id == staff_id))
    db.commit()

    return RedirectResponse(
        url=f"/staff_details?institution_id={institution_id}&username={username}",
        status_code=303
    )


# ✅ GET: Show the add staff form
@router.get("/add_staff", response_class=HTMLResponse)
def get_add_staff_form(
    request: Request,
    institution_id: int = Query(...),
    username: str = Query(...),
    db: Session = Depends(get_db)
):
    return templates.TemplateResponse("add_staff.html", {
        "request": request,
        "institution_id": institution_id,
        "username": username
    })


# ✅ POST: Handle the submission of new staff
def get_short_hash(text, length=10):
    return hashlib.sha256(text.encode()).hexdigest()[:length]

@router.post("/add_staff", response_class=HTMLResponse)
def add_staff(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    institution_id: int = Form(...),
    username: str = Form(...),
    db: Session = Depends(get_db)
):
    # Check if email already exists
    existing = db.execute(select(staff_table).where(staff_table.c.email == email)).fetchone()
    
    if existing:
        # Email exists, return to the same form with an error message
        return templates.TemplateResponse("add_staff.html", {
            "request": request,
            "error": "Email already exists!",
            "name": name,
            "email": email,
            "role": role,
            "institution_id": institution_id,
            "username": username
        })

    # Short hash (not safe for real passwords)
    short_hash = get_short_hash(password, length=6)

    # Insert new staff
    insert_stmt = staff_table.insert().values(
        name=name,
        email=email,
        password=short_hash,
        role=role,
        institution_id=institution_id
    )

    db.execute(insert_stmt)
    db.commit()

    return RedirectResponse(
        url=f"/staff_details?institution_id={institution_id}&username={username}",
        status_code=303
    )
