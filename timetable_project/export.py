# from fastapi import APIRouter, Request
# from fastapi.responses import FileResponse
# import pandas as pd
# from pathlib import Path
 

# router = APIRouter()

# @router.get("/export-timetable")
# async def export_timetable(request: Request):
#     institution_id = request.query_params.get("institution_id")
#     program_id = request.query_params.get("program_id")
#     specialization_id = request.query_params.get("specialization_id")
#     semester_id = request.query_params.get("semester_id")

#     timetable_schedule, day_time_slot_map, section_room_map, header_info = generate_section_wise_schedule(
#         institution_id, program_id, specialization_id, semester_id
#     )

#     output_path = Path("section_timetables.xlsx")
#     with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
#         for section, day_schedule in timetable_schedule.items():
#             df_data = []
#             days = list(day_schedule.keys())
#             slots = day_time_slot_map[days[0]]

#             for day in days:
#                 row = [day] + day_schedule[day]
#                 df_data.append(row)

#             df = pd.DataFrame(df_data, columns=["Day / Time"] + slots)
#             sheet_name = section[:31]
#             df.to_excel(writer, sheet_name=sheet_name, index=False)

#     return FileResponse(path=output_path, filename=output_path.name, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
