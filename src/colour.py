#!/usr/bin/env python3
import typing
import enum
from pydantic import BaseModel


class ColourMode(str, enum.Enum):
    LIGHT = "light"
    DARK = "dark"


class ColourModeValue(BaseModel):
    light: str
    dark: str


COLOURS = {
    "graph": {
        "bg": ColourModeValue(light="#F5F5F5", dark="#242424"),
        "edge": ColourModeValue(light="", dark="#DDDDDD"),
    },
    "table": {
        "border": ColourModeValue(light="#000000", dark="#DDDDDD"),
        "bg_head": ColourModeValue(light="#DDF0FF", dark="#DDF0FF"),
        "bg_head_primary": ColourModeValue(light="#FDEDEC", dark="#FDEDEC"),
        "text": ColourModeValue(light="", dark=""),
    },
    "column": {
        "text": ColourModeValue(light="", dark="#DDDDDD"),
        "subtext": ColourModeValue(light="#ABB2B9", dark="#666666"),
        "bg_odd": ColourModeValue(light="#F2F6F8", dark="#333333"),
        "bg_even": ColourModeValue(light="#FFFFFF", dark="#444444"),
    },
}


class Colours:
    def __init__(self, mode: ColourMode):
        self.mode = mode

    def __call__(self, *args):
        region, name = args
        colour = COLOURS.get(region, {}).get(name)
        if colour is not None:
            return getattr(colour, self.mode.value)
        raise Exception("Colour not found.")
