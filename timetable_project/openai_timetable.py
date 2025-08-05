# from fastapi import APIRouter, Request, Depends, HTTPException, Query
# from sqlalchemy import MetaData, Table, select, text, update
# from sqlalchemy.orm import Session
# from database import engine, get_db
# import openai
# import json
# from datetime import datetime,date,time
# from fastapi.responses import HTMLResponse, RedirectResponse

# router = APIRouter()
# client = openai.OpenAI()


# @router.get("/generate-timetable")
# async def generate_timetable(
#     institution_id: int,
#     db: Session = Depends(get_db)
# ):
#     try:
#         from datetime import datetime, date, time
#         import json
#         from fastapi import HTTPException
#         from sqlalchemy import MetaData, Table, select, text
#         from openai import OpenAI

#         # --- Step 1: Load Tables ---
#         academic_meta = MetaData(schema="academic_terms")
#         institution_meta = MetaData(schema="institution_details")
#         staff_meta = MetaData(schema="staff_details")

#         table_definitions = {
#             "staff": Table("staff", staff_meta, autoload_with=engine),
#             "preferences": Table("preferences", staff_meta, autoload_with=engine),
#             "institution_configuration": Table("institution_configuration", institution_meta, autoload_with=engine),
#             "subjects": Table("subjects", academic_meta, autoload_with=engine),
#             "rooms": Table("rooms", academic_meta, autoload_with=engine),
#             "sections": Table("sections", academic_meta, autoload_with=engine),
#             "semesters": Table("semesters", academic_meta, autoload_with=engine),
#             "programs": Table("programs", academic_meta, autoload_with=engine),
#             "academic_holidays": Table("academic_holidays", academic_meta, autoload_with=engine),
#             "semester_events": Table("semester_events", academic_meta, autoload_with=engine),
#             "specializations": Table("specializations", academic_meta, autoload_with=engine),
#             "semester_subjects": Table("semester_subjects", academic_meta, autoload_with=engine),
#             "section_room_assignments": Table("section_room_assignments", academic_meta, autoload_with=engine),
#             "lab_sessions": Table("lab_sessions", academic_meta, autoload_with=engine),
#         }

#         # --- Step 2: Data Collection ---
#         def get_filtered_rows(table_name, table):
#             try:
#                 if 'institution_id' in [col.name for col in table.c]:
#                     stmt = select(table).where(table.c.institution_id == institution_id)
#                 elif table_name == "section_room_assignments":
#                     sections = table_definitions["sections"]
#                     stmt = select(table).join(sections, table.c.section_id == sections.c.id)\
#                         .where(sections.c.institution_id == institution_id)
#                 else:
#                     stmt = select(table)
                
#                 return db.execute(stmt).mappings().all()
#             except Exception as e:
#                 print(f"❌ Error fetching {table_name}: {e}")
#                 return []

#         def filter_datetime_fields(row):
#             try:
#                 if hasattr(row, "_mapping"):
#                     row_dict = dict(row._mapping)
#                 else:
#                     row_dict = dict(row)
#                 result = {}
#                 for key, value in row_dict.items():
#                     if isinstance(value, (datetime, date)):
#                         continue
#                     elif isinstance(value, time):
#                         result[key] = value.strftime("%H:%M:%S")
#                     else:
#                         result[key] = value
#                 return result
#             except Exception:
#                 return {}

#         raw_data = {}
#         for name, table in table_definitions.items():
#             rows = get_filtered_rows(name, table)
#             raw_data[name] = [filter_datetime_fields(r) for r in rows if r]

#         # --- Step 3: Filter Snapshot ---
#         schema_snapshot = {}
#         for table_name, data in raw_data.items():
#             if data and isinstance(data, list):
#                 if 'institution_id' in data[0]:
#                     schema_snapshot[table_name] = [r for r in data if r.get("institution_id") == institution_id]
#                 else:
#                     schema_snapshot[table_name] = data

#         if "semester_subjects" in schema_snapshot and "semesters" in schema_snapshot:
#             semester_ids = {s['id'] for s in schema_snapshot["semesters"]}
#             schema_snapshot["semester_subjects"] = [
#                 ss for ss in schema_snapshot["semester_subjects"]
#                 if ss.get("semester_id") in semester_ids
#             ]

#         # --- Step 4: Prompt Construction (Full Data Used) ---
#         system_prompt = """
# You are an expert PostgreSQL assistant specialized in academic timetable generation.

# Your task is to generate valid and logically consistent SQL INSERT queries for the `time_table.time_table` table using the provided data from related tables.

# IMPORTANT Rules:
# - Generate INSERT statements for all rows matching the institution_id condition.
# - Each INSERT must be unique and valid.
# - Use only these columns in this exact order:
#   institution_id, configuration_id, semester_id, section_id, subject_id, room_id, staff_id, preference_id, event_id, program_id, holiday_id, lab_session_id
# - All foreign key values used in the query must exist in the provided data.
# - If a field has no matching value, use NULL (unquoted).
# - Return only the INSERT statements — no explanations or formatting.
# """.strip()


#         user_prompt = f"""
# Using the following filtered data (institution_id={institution_id}), generate 10 logically correct INSERT queries into `time_table.time_table`.

# Sample Table Sizes:
# {json.dumps({k: f"{len(v)} records" for k, v in schema_snapshot.items()}, indent=2)}

# Data:
# {json.dumps(schema_snapshot, indent=2)}

# Return only the INSERT statements in PostgreSQL syntax.
# """.strip()

#         # --- Step 5: Call OpenAI ---
#         response = client.chat.completions.create(
#             model="gpt-4o",
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": user_prompt}
#             ],
#             temperature=0.3
#         )

#         raw_response = response.choices[0].message.content.strip()

#         insert_statements = [
#             stmt.strip().rstrip(";") + ";" 
#             for stmt in raw_response.split(";") 
#             if stmt.strip().lower().startswith("insert into")
#         ]

#         if not insert_statements:
#             raise HTTPException(
#                 status_code=400,
#                 detail={"message": "OpenAI did not return any valid INSERT statements.", "raw_response": raw_response}
#             )

#         # --- Step 6: Execute All INSERTs ---
#         for stmt in insert_statements:
#             try:
#                 db.execute(text(f"EXPLAIN {stmt}"))  # Dry run
#                 db.execute(text(stmt))
#             except Exception as e:
#                 db.rollback()
#                 raise HTTPException(
#                     status_code=400,
#                     detail={"message": "Failed to execute query", "query": stmt, "error": str(e)}
#                 )

#         db.commit()

#         return {
#             "status": "success",
#             "executed_queries": insert_statements,
#             "inserted_rows": len(insert_statements),
#             "institution_id": institution_id
#         }

#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail={
#                 "message": "Internal server error during timetable generation",
#                 "error": str(e),
#                 "institution_id": institution_id
#             }
#         )
