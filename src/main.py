import typing

from fastapi import FastAPI, Form, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse, JSONResponse

import database
import diagram
import colour

templates = Jinja2Templates(directory="templates")

app = FastAPI()
db: typing.Optional[database.Database] = None
colour_mode: typing.Optional[colour.ColourMode] = colour.ColourMode.LIGHT


@app.on_event("shutdown")
async def shutdown_event():
    if db is not None:
        db.backend.connection.close()


@app.get("/", response_class=HTMLResponse)
async def root(
    request: Request,
    table: str = Query(None),
):
    context = dict(request=request, db=db, colour_mode=colour_mode)

    if db is None:
        return templates.TemplateResponse("connect.html", context)

    columns = []
    if table:
        table = database.Table(name=table)
        table = db.backend.populate_columns_for_table(table)
        table = db.backend.populate_outbound_related_tables(table)
        table = db.backend.populate_inbound_related_tables(table)

        dot = diagram.generate_dot_diagram(table, colour_mode)
        context.update({"table": table, "dot": dot})
        return templates.TemplateResponse("viewer.html", context)

    return templates.TemplateResponse("viewer.html", context)


@app.post("/connect")
async def save_connection(connection: database.Connection):
    try:
        _db = database.Database.connect(database.MySQL, connection)
    except Exception as e:
        return JSONResponse(dict(error=str(e)), status_code=400)
    else:
        global db
        db = _db
    return dict(status="OK")


@app.post("/colour-mode")
async def save_colour_mode():
    global colour_mode

    if colour_mode == colour.ColourMode.LIGHT:
        colour_mode = colour.ColourMode.DARK
    else:
        colour_mode = colour.ColourMode.LIGHT

    return dict(status="OK")


app.mount("/static", StaticFiles(directory="static"), name="static")
