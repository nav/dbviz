#!/usr/bin/env python3
from graphviz import Digraph
from colour import ColourMode, Colours
from database import Table


def generate_dot_diagram(table: Table, colour_mode: ColourMode):
    colours = Colours(colour_mode)
    spc = "&nbsp;&nbsp;&nbsp;"

    def render_table(table, *, is_primary=False):
        bordercolour = colours("table", "border")
        bgcolour = colours("table", "bg_head")
        if is_primary:
            bgcolour = colours("table", "bg_head_primary")

        return f"""<<table cellpadding="0" cellspacing="0" cellborder="0" color="{bordercolour}">
        <tr>
        <td bgcolor="{bgcolour}" cellpadding="2">
            <b>{table.name}</b>{spc}
        </td>
        </tr>
        {render_columns(table.columns)}
        </table>>"""

    def render_columns(columns):
        output = ""
        for index, column in enumerate(columns):
            bgcolour = colours("column", "bg_odd")
            if index % 2 == 0:
                bgcolour = colours("column", "bg_even")

            text_colour = colours("column", "text")
            subtext_colour = colours("column", "subtext")

            output += f"""
                <tr>
                <td port="{column.name}" align="left"
                    bgcolor="{bgcolour}" cellpadding="2"><font
                    color="{text_colour}">{column.name}</font>{spc}<font
                    color="{subtext_colour}">{column.type}</font>  </td>
                </tr>
                """.strip()
        return output

    dot = Digraph(
        name=f"Visualize {table.name}",
        graph_attr=dict(ranksep="1.5", bgcolor="transparent"),
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
        dot.edge(
            related_table.name,
            f"{table.name}:{column.name}",
            color=colours("graph", "edge"),
        )

    for column, related_table in outbound_tables:
        dot.node(
            related_table.name,
            render_table(related_table),
            href=f"/?table={related_table.name}",
        )
        dot.edge(
            f"{table.name}:{column.name}",
            f"{related_table.name}",
            color=colours("graph", "edge"),
        )

    return dot
