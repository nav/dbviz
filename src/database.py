from __future__ import annotations

import re
import abc
import typing

import MySQLdb
from pydantic import BaseModel, validator
from colour import ColourMode, Colours


class Connection(BaseModel):
    host: str
    user: str
    password: str
    name: str


class DatabaseBackend(abc.ABC):
    def __init__(self, connection: Connection):
        self.connection = connection
        self.db_connection = None

    @abc.abstractmethod
    def connect(self, connection: Connection) -> bool:
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

    @classmethod
    def connect(cls, backend: DatabaseBackend, connection: Connection):
        _backend = backend(connection)
        is_connected = _backend.connect()

        tables = _backend.get_tables()
        database = Database(backend=_backend, tables=tables)
        return database


class MySQL(DatabaseBackend):
    def connect(self):
        db_connection = MySQLdb.connect(
            host=self.connection.host,
            user=self.connection.user,
            passwd=self.connection.password,
            db=self.connection.name,
        )
        self.db_connection = db_connection

    def get_tables(self) -> typing.List[Table]:
        try:
            cursor = self.db_connection.cursor()
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
        try:
            cursor = self.db_connection.cursor()
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
        try:
            cursor = self.db_connection.cursor()
            query = """
            SELECT column_name, referenced_table_name, referenced_column_name
            FROM  information_schema.key_column_usage
            WHERE referenced_table_name IS NOT NULL
              AND table_name = %s
              AND table_schema = %s
            ORDER BY referenced_table_name;
            """.strip()
            cursor.execute(query, [table.name, self.connection.name])
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
        try:
            cursor = self.db_connection.cursor()
            query = """
            SELECT column_name, table_name, referenced_column_name
            FROM information_schema.key_column_usage
            WHERE referenced_table_name = %s
                AND referenced_table_schema = %s
            ORDER BY referenced_table_name
            """.strip()
            cursor.execute(query, [table.name, self.connection.name])
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


Column.update_forward_refs()
