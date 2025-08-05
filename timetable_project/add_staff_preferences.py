from fastapi import APIRouter, Request, Depends,Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, MetaData, Table,insert
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

@router.get("/add_staff_preferences",response_class=HTMLResponse)
def add_preferences(request:Request,institution_id:int,staff_id:int,username:str,db:Session=Depends(get_db)):
    return templates.TemplateResponse("add_preferences.html",{"request":request,"institution_id":institution_id,"staff_id":staff_id,"username":username})


@router.post("/adding_preferences",response_class=HTMLResponse,)
def add_staff_preferences(request:Request,
                          institution_id:int=Form(...),
                          staff_id:int=Form(...),
                          preference_type:str=Form(...),
                          preference_value:str=Form(...),
                          username:str=Form(...),
                          db:Session=Depends(get_db)):
    storing_preferences=insert(preferences_table).values(
        institution_id=institution_id,
        staff_id=staff_id,
        preference_type=preference_type,
        preference_value=preference_value,
        created_by=username,
        updated_by=username
    )
    db.execute(storing_preferences)
    db.commit()
    return templates.TemplateResponse("add_preferences.html",{"request":request,"institution_id":institution_id,"staff_id":staff_id})

    