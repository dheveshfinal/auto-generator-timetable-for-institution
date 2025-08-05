from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import MetaData, Table, select, insert
from sqlalchemy.orm import Session
from database import get_db, engine

router = APIRouter()
template = Jinja2Templates(directory="templates")

# Reflect schemas
user_schema = MetaData(schema="user_management")
institution_schema = MetaData(schema="institution_details")

# Reflect tables
user_table = Table("users", user_schema, autoload_with=engine)
institution_table = Table("institution", institution_schema, autoload_with=engine)

@router.get("/signup", response_class=HTMLResponse)
def signup(request: Request):
    return template.TemplateResponse("signup.html", {"request": request})


@router.post("/signup/user_details", response_class=HTMLResponse)
def signup_details(
    request: Request,
    institution: str = Form(...),
    address: str = Form(...),
    email: str = Form(...),
    contact: str = Form(...),
    website: str = Form(...),
    principal_name: str = Form(...),
    name: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    email2: str = Form(...),
    db: Session = Depends(get_db)
):
    # Check if institution already exists
    inst_check = select(institution_table).where(institution_table.c.name == institution)
    inst_final = db.execute(inst_check).mappings().first()

    if inst_final:
        raise HTTPException(status_code=400, detail="Institution already exists.")

    # Insert institution
    institution_insert = insert(institution_table).returning(institution_table.c.id).values(
        name=institution,
        address=address,
        contact_email=email,
        phone_number=contact,
        website=website,
        principal_name=principal_name,
        created_by=name,
        updated_by=name
    )
    result = db.execute(institution_insert)
    institution_id = result.scalar_one()  # Get the newly inserted institution_id

    # Insert user
    user_insert = insert(user_table).values(
        username=name,
        password=password,
        full_name=full_name,
        email=email2,
        institution_id=institution_id,
        role_id=5,
        created_by=name,
        updated_by=name
    )
    db.execute(user_insert)
    db.commit()

    return template.TemplateResponse("signup.html", {"request": request, "message": "Signup successful!"})
