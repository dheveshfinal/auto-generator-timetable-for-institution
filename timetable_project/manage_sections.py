from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, Table, MetaData
from sqlalchemy.orm import Session
from database import engine, get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")

institution_schema = MetaData(schema="institution_details")
academic_schema = MetaData(schema="academic_terms")

institution_table = Table("semesters", academic_schema, autoload_with=engine)
rooms_table = Table("rooms", academic_schema, autoload_with=engine)
sections_table = Table("sections", academic_schema, autoload_with=engine)
sections_room_table = Table("section_room_assignments", academic_schema, autoload_with=engine)
specializations_table = Table("specializations", academic_schema, autoload_with=engine)

@router.api_route("/manage_sections", methods=["GET", "POST"], response_class=HTMLResponse)
async def manage_sections(request: Request, institution_id: int, semester_id: int, db: Session = Depends(get_db)):
    # Fetch room list
    rooms_query = select(rooms_table)
    rooms = db.execute(rooms_query).fetchall()

    # Fetch sections
    sections_query = (
        select(sections_table.c.id, sections_table.c.section_name, sections_room_table.c.room_id)
        .join(sections_room_table, sections_table.c.id == sections_room_table.c.section_id)
        .where(sections_table.c.semester_id == semester_id)
    )
    sections = db.execute(sections_query).fetchall()

    if request.method == "POST":
        form = await request.form()

        # 🔴 DELETE
        if "delete" in form:
            section_id = int(form["delete"])
            print("Deleting section:", section_id)
            db.execute(sections_room_table.delete().where(sections_room_table.c.section_id == section_id))
            db.execute(sections_table.delete().where(sections_table.c.id == section_id))
            db.commit()

        # ✅ SAVE
        elif "save" in form:
            section_id = int(form["save"])
            new_name = form.get(f"section_name_{section_id}")
            new_room_id = int(form.get(f"room_id_{section_id}"))

            db.execute(
                sections_table.update().where(sections_table.c.id == section_id).values(section_name=new_name)
            )
            db.execute(
                sections_room_table.update().where(sections_room_table.c.section_id == section_id).values(room_id=new_room_id)
            )
            db.commit()

        # ➕ ADD
        elif "add" in form:
            result = db.execute(
                sections_table.insert().values(
                    semester_id=semester_id,
                    section_name="NewSec",  # name must be <= length of DB column
                    created_by="system",
                    updated_by="system"
                ).returning(sections_table.c.id)
            )
            new_id = result.scalar()
            db.execute(
                sections_room_table.insert().values(
                    section_id=new_id,
                    room_id=rooms[0].id if rooms else 1,
                    institution_id=institution_id,
                    created_by="system",
                    updated_by="system"
                )
            )
            db.commit()

        return RedirectResponse(url=f"/manage_sections?institution_id={institution_id}&semester_id={semester_id}", status_code=303)

    semester_data = db.execute(
        select(institution_table).where(institution_table.c.id == semester_id)
    ).first()

    institution_name = f"Institution #{institution_id}"

    return templates.TemplateResponse("manage_sections.html", {
        "request": request,
        "institution_name": institution_name,
        "semester": semester_data,
        "rooms": rooms,
        "sections": sections
    })