from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import MetaData, Table, select
from sqlalchemy.orm import Session
from database import get_db, engine

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Reflect users table
metadata = MetaData(schema="user_management")
users_table = Table("users", metadata, autoload_with=engine)

@router.get("/login", response_class=HTMLResponse)
def show_login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    query = select(users_table).where(users_table.c.email == email)
    result = db.execute(query).mappings().first()

    if not result:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

    user = dict(result)

    if password != user["password"]:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    
    if user["role_id"] == 4:
        return RedirectResponse(
            url=f"/programs?username={user['username']}",
            status_code=303
        )

    if user["role_id"] not in [5]:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Access denied"})
    
    

    # ✅ Redirect with username in URL query string
    return RedirectResponse(
        url=f"/institution_dashboard?username={user['username']}",
        status_code=303
    )
