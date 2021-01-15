from __future__ import annotations

import re
import abc
import typing

import MySQLdb
from graphviz import Digraph
from pydantic import BaseModel, validator

from colours import ColourMode, Colours


class Config(BaseModel):
    host: str
    user: str
    password: str
    name: str
    colour_mode: ColourMode = ColourMode.LIGHT

    def connect(self, Backend: DatabaseBackend) -> typing.Optional[Database]:
        backend = Backend(self)
        is_connected = backend.connect()

        if not is_connected:
            return None

        tables = backend.get_tables()
        database = Database(backend=backend, tables=tables)

        return database


class DatabaseBackend(abc.ABC):
    def __init__(self, config: Config):
        self.config = config
        self.connection = None

    @abc.abstractmethod
    def connect(self, config: Config) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_tables(self) -> typing.List[Table]:
        raise NotImplementedError()

    @abc.abstractmethod
    def populate_columns_for_table(self, table_name: str) -> Table:
        raise NotImplementedError()

    @abc.abstractmethod
    def populate_outbound_related_tables(self, table: Table) -> Table:
        raise NotImplementedError()

    @abc.abstractmethod
    def populate_inbound_related_tables(self, table: Table) -> Table:
        raise NotImplementedError()


class Column(BaseModel):
    name: str
    type: str
    is_primary: bool
    is_foreign: bool

    outbound_related_table: typing.Optional[Table] = None
    inbound_related_tables: typing.List[Table] = []


class Table(BaseModel):
    name: str
    columns: typing.List[Column] = []

    @validator("name")
    def name_must_be_sort_of_alphanumeric(cls, value):
        if re.match(r"^[\w\s]+$", value):
            return value
        raise ValueError("Table name is invalid.")


class Database(BaseModel):
    backend: DatabaseBackend
    tables: typing.List[Table]

    class Config:
        arbitrary_types_allowed = True


class MySQL(DatabaseBackend):
    def connect(self) -> bool:
        try:
            connection = MySQLdb.connect(
                host=self.config.host,
                user=self.config.user,
                passwd=self.config.password,
                db=self.config.name,
            )
        except MySQLdb.Error as e:
            return False
        else:
            self.connection = connection
            return True

    def get_tables(self) -> typing.List[Table]:
        if self.connection is None:
            raise ValueError("Not connected to database.")

        try:
            cursor = self.connection.cursor()
            query = "SHOW TABLES"
            cursor.execute(query)
            rows = cursor.fetchall()
        finally:
            cursor.close()

        tables = []
        for row in rows:
            tables.append(Table(name=row[0]))
        return tables

    def populate_columns_for_table(self, table: Table) -> Table:
        if self.connection is None:
            raise ValueError("Not connected to database.")

        try:
            cursor = self.connection.cursor()
            query = f"DESCRIBE {table.name}"
            cursor.execute(query)
            rows = cursor.fetchall()
        finally:
            cursor.close()

        columns = []
        for row in rows:
            columns.append(
                Column(
                    name=row[0],
                    type=row[1],
                    is_primary=row[3] == "PRI",
                    is_foreign=row[3] in ("UNI", "MUL"),
                )
            )
        table.columns = columns
        return table

    def populate_outbound_related_tables(self, table: Table) -> Table:
        if self.connection is None:
            raise ValueError("Not connected to database.")

        try:
            cursor = self.connection.cursor()
            query = """
            SELECT column_name, referenced_table_name, referenced_column_name
            FROM  information_schema.key_column_usage
            WHERE referenced_table_name IS NOT NULL
              AND table_name = %s
              AND table_schema = %s
            ORDER BY referenced_table_name;
            """.strip()
            cursor.execute(query, [table.name, self.config.name])
            rows = cursor.fetchall()
        finally:
            cursor.close()

        column_relation_map = {}
        for row in rows:
            column_relation_map[row[0]] = row

        for column in table.columns:
            if column.is_foreign and column.name in column_relation_map:
                related_table = Table(name=column_relation_map[column.name][1])
                related_table = self.populate_columns_for_table(related_table)
                column.outbound_related_table = related_table
        return table

    def populate_inbound_related_tables(self, table):
        if self.connection is None:
            raise ValueError("Not connected to database.")

        try:
            cursor = self.connection.cursor()
            query = """
            SELECT column_name, table_name, referenced_column_name
            FROM information_schema.key_column_usage
            WHERE referenced_table_name = %s
                AND referenced_table_schema = %s
            ORDER BY referenced_table_name
            """.strip()
            cursor.execute(query, [table.name, self.config.name])
            rows = cursor.fetchall()
        finally:
            cursor.close()

        column_map = {}
        for column in table.columns:
            column_map[column.name] = column

        for row in rows:
            inbound_column_name, inbound_table_name, column_name = row
            related_table = Table(name=inbound_table_name)
            related_table = self.populate_columns_for_table(related_table)
            column = column_map[column_name]
            column.inbound_related_tables.append(related_table)

        return table


def generate_dot_diagram(table: Table, colour_mode: ColourMode):
    colours = Colours(colour_mode)
    spc = "&nbsp;&nbsp;&nbsp;"

    def render_columns(columns):
        output = ""
        for index, column in enumerate(columns):
            bgcolour = "#f4f6f6"
            bgcolour = colours("column", "bg_odd")
            if index % 2 == 0:
                bgcolour = "white"
                bgcolour = colours("column", "bg_even")

            text_colour = colours("column", "text")
            subtext_colour = colours("column", "subtext")

            output += (
                f"""<tr><td port="{column.name}" align="left" bgcolor="{bgcolour}">"""
                f"""<font color="{text_colour}">{column.name}{spc}</font>"""
                f"""<font color="{subtext_colour}">{column.type}</font>{spc}</td></tr>"""
            )
        return output

    def render_table(table, *, is_primary=False):
        bgcolour = colours("table", "bg_head")
        if is_primary:
            bgcolour = colours("table", "bg_head_primary")

        return f"""<<table cellspacing="0" cellborder="0">
        <tr><td bgcolor="{bgcolour}">{spc}{table.name}{spc}</td></tr>
        {render_columns(table.columns)}{spc}
        </table>>"""

    dot = Digraph(
        name=f"Visualize {table.name}",
        graph_attr=dict(ranksep="1.5", bgcolor=colours("graph", "bg")),
        node_attr=dict(shape="plaintext", fontname="sans-serif", margin="0"),
    )
    inbound_tables = []
    outbound_tables = []

    dot.node(table.name, label=render_table(table, is_primary=True))

    for column in table.columns:
        if column.inbound_related_tables:
            inbound_tables.extend(
                [(column, table) for table in column.inbound_related_tables]
            )

        if column.outbound_related_table:
            outbound_tables.append((column, column.outbound_related_table))

    for column, related_table in inbound_tables:
        dot.node(
            related_table.name,
            render_table(related_table),
            href=f"/?table={related_table.name}",
        )
        dot.edge(related_table.name, f"{table.name}:{column.name}")

    for column, related_table in outbound_tables:
        dot.node(
            related_table.name,
            render_table(related_table),
            href=f"/?table={related_table.name}",
        )
        dot.edge(f"{table.name}:{column.name}", f"{related_table.name}")

    return dot


Column.update_forward_refs()
