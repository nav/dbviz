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
        "bg": ColourModeValue(light="white", dark="#242424"),
    },
    "table": {
        "text": ColourModeValue(light="black", dark="#f4f6f6"),
        "bg_head": ColourModeValue(light="#f2f9ff", dark="#5a6369"),
        "bg_head_primary": ColourModeValue(light="#fdedec", dark="#887575"),
    },
    "column": {
        "text": ColourModeValue(light="", dark="#999999"),
        "subtext": ColourModeValue(light="#abb2b9", dark="#f4f6f6"),
        "bg_odd": ColourModeValue(light="white", dark="#242424"),
        "bg_even": ColourModeValue(light="#f5f7f7", dark="#414141"),
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
