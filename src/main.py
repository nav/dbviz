import typing
from pydantic import BaseModel
from starlette.responses import RedirectResponse
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import database


templates = Jinja2Templates(directory="templates")

app = FastAPI()
config: typing.Optional[database.Config] = None
db: typing.Optional[database.Database] = None


@app.on_event("shutdown")
async def shutdown_event():
    if db is not None:
        db.backend.connection.close()


@app.get("/", response_class=HTMLResponse)
async def root(request: Request, table: str = ""):
    if config is None:
        return RedirectResponse(url="/connect")

    columns = []
    if table:
        table = database.Table(name=table)
        table = db.backend.populate_columns_for_table(table)
        table = db.backend.populate_outbound_related_tables(table)
        table = db.backend.populate_inbound_related_tables(table)
        dot = database.generate_dot_diagram(table)
        return templates.TemplateResponse(
            "viewer.html", {"request": request, "table": table, "dot": dot}
        )

    return templates.TemplateResponse("index.html", {"request": request, "db": db})


@app.get("/connect", response_class=HTMLResponse)
async def connect(request: Request):
    global config
    config = None
    return templates.TemplateResponse("connect.html", {"request": request})


@app.post("/connect")
async def save_connection(
    request: Request,
    host: str = Form(...),
    user: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
):

    _config = database.Config(host=host, user=user, password=password, name=name)
    _db = _config.connect(database.MySQL)

    if _db is not None:
        global config
        global db
        config = _config
        db = _db
        return RedirectResponse(url="/", status_code=301)
    return dict(error="Could not connect")
