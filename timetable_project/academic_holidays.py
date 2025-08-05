from fastapi import APIRouter, Request, Depends, Form, HTTPException, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import MetaData, Table, select, insert, update, delete
from sqlalchemy.orm import Session
from database import engine, get_db
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="templates")

academic_schema = MetaData(schema="academic_terms")
institution_schema = MetaData(schema="institution_details")

academic_holidays_table = Table("academic_holidays", academic_schema, autoload_with=engine)
institution_table = Table("institution", institution_schema, autoload_with=engine)


# View Holidays
@router.get("/academic_holiday", response_class=HTMLResponse)
def get_academic_holidays(
    request: Request,
    db: Session = Depends(get_db),
    institution_id: int = Query(...),
    username: str = Query(...),
):
    # Fetch holidays
    stmt = select(academic_holidays_table).where(
        academic_holidays_table.c.institution_id == institution_id
    )
    results = db.execute(stmt).fetchall()

    # Fetch institution name
    inst_stmt = select(institution_table.c.name).where(institution_table.c.id == institution_id)
    inst_result = db.execute(inst_stmt).fetchone()

    institution_name = inst_result.name if inst_result else "Unknown"

    return templates.TemplateResponse(
        "academic_holidays.html",
        {
            "request": request,
            "holidays": results,
            "institution_id": institution_id,
            "institution_name": institution_name,
            "username": username
        }
    )
# Add Holiday
@router.post("/academic_holidays/add")
def add_academic_holiday(
    institution_id: int = Form(...),
    name: str = Form(...),
    date: str = Form(...),
    is_national: bool = Form(...),
    created_by: str = Form(...),
    username: str = Form(...),  # required for redirect
    db: Session = Depends(get_db)
):
    new_holiday = {
        "institution_id": institution_id,
        "name": name,
        "date": date,
        "is_national": is_national,
        "created_by": created_by,
        "created_timestamp": datetime.now(),
        "updated_by": created_by,
        "updated_timestamp": datetime.now()
    }
    db.execute(insert(academic_holidays_table).values(**new_holiday))
    db.commit()
    return RedirectResponse(
        f"/academic_holiday?institution_id={institution_id}&username={username}",
        status_code=303
    )

# Update Holiday
@router.post("/academic_holidays/update/{holiday_id}")
def update_academic_holiday(
    holiday_id: int,
    institution_id: int = Form(...),
    name: str = Form(...),
    date: str = Form(...),
    is_national: bool = Form(...),
    updated_by: str = Form(...),
    username: str = Form(...),
    db: Session = Depends(get_db)
):
    stmt = (
        update(academic_holidays_table)
        .where(academic_holidays_table.c.id == holiday_id)
        .values(
            name=name,
            date=date,
            is_national=is_national,
            updated_by=updated_by,
            updated_timestamp=datetime.now()
        )
    )
    db.execute(stmt)
    db.commit()
    return RedirectResponse(
        f"/academic_holiday?institution_id={institution_id}&username={username}",
        status_code=303
    )

# Delete Holiday
@router.get("/academic_holidays/delete/{holiday_id}")
def delete_academic_holiday(
    holiday_id: int,
    institution_id: int = Query(...),
    username: str = Query(...),
    db: Session = Depends(get_db)
):
    db.execute(
        delete(academic_holidays_table).where(academic_holidays_table.c.id == holiday_id)
    )
    db.commit()
    return RedirectResponse(
        f"/academic_holiday?institution_id={institution_id}&username={username}",
        status_code=303
    )
