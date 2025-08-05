from fastapi import Request, APIRouter, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import Table, MetaData, select, update
from sqlalchemy.orm import Session
from database import get_db, engine
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

config_metadata = MetaData(schema="institution_details")
config_table = Table("institution_configuration", config_metadata, autoload_with=engine)
institution_table = Table("institution", config_metadata, autoload_with=engine)

@router.get("/institution_configuration", response_class=HTMLResponse)
def show_configuration(request: Request, institution_id: int, username: str, db: Session = Depends(get_db)):
    stmt = select(config_table).where(config_table.c.institution_id == institution_id)
    result = db.execute(stmt).mappings().all()

    stmt1 = select(institution_table).where(institution_table.c.id == institution_id)
    result1 = db.execute(stmt1).mappings().first()

    if not result:
        raise HTTPException(status_code=404, detail="No configuration found for this institution.")

    # ✅ Add this sorting block
    desired_order = [
        "working_days",
        "day_start_time",
        "day_end_time",
        "lunch_start_time",
        "lunch_end_time",
        "half_day_enabled",
        "half_day_pattern",
        "half_day_start_time",
        "half_day_end_time"
    ]

    sorted_result = sorted(
        result,
        key=lambda x: desired_order.index(x["configuration_name"]) if x["configuration_name"] in desired_order else len(desired_order)
    )

    return templates.TemplateResponse("institution_configuration.html", {
        "request": request,
        "username": username,
        "institution_id": institution_id,
        "configurations": sorted_result,
        "institution": result1
    })

@router.post("/institution_configuration/update")
async def update_configuration(
    request: Request,
    db: Session = Depends(get_db)
):
    form = await request.form()
    institution_id = int(form.get("institution_id"))
    username = form.get("username")

    # Loop over form keys to update values
    for key in form:
        if key.startswith("config_"):  # name="config_{{ id }}"
            config_id = int(key.split("_")[1])
            new_value = form.get(key)

            stmt = (
                update(config_table)
                .where(config_table.c.configuration_id == config_id)
                .values(configuration_value=new_value, updated_by=username)
            )
            db.execute(stmt)

    db.commit()

    return RedirectResponse(
        url=f"/institution_configuration?institution_id={institution_id}&username={username}",
        status_code=303
    )

