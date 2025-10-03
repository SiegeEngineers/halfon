#! /usr/bin/env python3
import argparse
import dataclasses
import json
import re
from pathlib import Path

from genieutils.datfile import DatFile
from genieutils.tech import Tech
from genieutils.unit import Unit

RES_FOOD = 0
RES_WOOD = 1
RES_STONE = 2
RES_GOLD = 3
ARM_PIERCE = 3


def cpp_round(value: float) -> int | float:
    rounded_int = round(value)
    if abs(rounded_int - value) < 0.0000001:
        return rounded_int
    return round(value, 6)


def read_strings(path: Path) -> dict[int, str]:
    values = {}
    for line in path.read_text().splitlines():
        if line and line[0].isnumeric():
            items = line.strip().split(maxsplit=1)
            values[int(items[0])] = items[1][1:-1]
    return values


def read_rms_consts(path: Path) -> dict[int, str]:
    values = {}
    pattern = re.compile(r'#const\s+([A-Z_]+)\s+(\d+)')
    active = False
    for line in path.read_text().splitlines():
        if 'OBJECT TYPES' in line or 'DLC_AUTUMNTREE ' in line or 'DLC_BOULDER_A ' in line:
            active = True
        if 'Effect Constants' in line or 'DLC_BAOBABFOREST ' in line or 'DLC_ROCK ' in line:
            active = False
        if active:
            m = pattern.match(line)
            if m:
                if m.group(2) not in values:
                    values[m.group(2)] = m.group(1)
    return values


def get_pierce_armor(unit: Unit) -> int:
    if unit.type_50:
        for a in unit.type_50.armours:
            if a.class_ == ARM_PIERCE:
                return a.amount
    return 0


def unit_data(unit: Unit) -> dict:
    cost = {
        "wood": 0,
        "food": 0,
        "gold": 0,
        "stone": 0,
    }
    if unit.creatable:
        cost = {
            "wood": next((c.amount for c in unit.creatable.resource_costs if c.type == RES_WOOD), 0),
            "food": next((c.amount for c in unit.creatable.resource_costs if c.type == RES_FOOD), 0),
            "gold": next((c.amount for c in unit.creatable.resource_costs if c.type == RES_GOLD), 0),
            "stone": next((c.amount for c in unit.creatable.resource_costs if c.type == RES_STONE), 0),
        }
    return {
        "cost": cost,
        "attack": unit.type_50.displayed_attack if unit.type_50 else 0,
        "melee_armor": unit.type_50.displayed_melee_armour if unit.type_50 else 0,
        "pierce_armor": get_pierce_armor(unit),
        "base_id": unit.base_id,
        "help_converter": unit.language_dll_help - 79000,
        "language_file_name": unit.language_dll_name,
        "language_file_help": unit.language_dll_help,
        "name": unit.name,
        "hit_points": unit.hit_points,
        "line_of_sight": cpp_round(unit.line_of_sight),
        "garrison_capacity": unit.garrison_capacity,
        "type": unit.type,
        "class": unit.class_,
        "localised_name": '',
        "rms_const": None,
    }


def tech_data(tech: Tech) -> dict:
    return {
        "cost": {
            "wood": next((c.amount for c in tech.resource_costs if c.type == RES_WOOD), 0),
            "food": next((c.amount for c in tech.resource_costs if c.type == RES_FOOD), 0),
            "gold": next((c.amount for c in tech.resource_costs if c.type == RES_GOLD), 0),
            "stone": next((c.amount for c in tech.resource_costs if c.type == RES_STONE), 0),
        },
        "help_converter": tech.language_dll_help - 79000,
        "language_file_name": tech.language_dll_name,
        "language_file_help": tech.language_dll_help,
        "name": tech.name,
        "localised_name": '',
    }


def process(dat_file: Path, strings_file: Path, rms_file: Path | None, target: Path) -> None:
    data = {'units_buildings': {}, 'techs': {}}
    strings = read_strings(strings_file)
    rms = read_rms_consts(rms_file) if rms_file else {}
    dat = DatFile.parse(dat_file)
    for unit in dat.civs[0].units:
        if unit:
            data['units_buildings'][str(unit.base_id)] = unit_data(unit)
    for tid, tech in enumerate(dat.techs):
        data['techs'][str(tid)] = tech_data(tech)

    for objtype in ('units_buildings', 'techs'):
        for key in data[objtype]:
            strings_key = data[objtype][key]['language_file_name']
            data[objtype][key]['localised_name'] = strings.get(strings_key, '')
            if objtype == 'units_buildings':
                data[objtype][key]['rms_const'] = rms.get(key, None)

    target.write_text(json.dumps(data, indent='\t', ensure_ascii=False, sort_keys=False))


def main():
    parser = argparse.ArgumentParser(
        prog='update-de-data.py',
        description='Update data files for DE and RoR',
    )
    parser.add_argument('aoe2_dir', type=Path)
    args = parser.parse_args()

    de_dat = args.aoe2_dir / 'resources' / '_common' / 'dat' / 'empires2_x2_p1.dat'
    de_strings = args.aoe2_dir / 'resources' / 'en' / 'strings' / 'key-value' / 'key-value-strings-utf8.txt'
    de_rms = args.aoe2_dir / 'resources' / '_common' / 'drs' / 'gamedata_x2' / 'random_map.def'
    de_target = Path(__file__).parent.resolve().parent / 'data' / 'units_buildings_techs.de.json'

    ror_dat = args.aoe2_dir / 'modes' / 'Pompeii' / 'resources' / '_common' / 'dat' / 'empires2_x2_p1.dat'
    ror_strings = args.aoe2_dir / 'modes' / 'Pompeii' / 'resources' / 'en' / 'strings' / 'key-value' / 'key-value-pompeii-strings-utf8.txt'
    ror_target = Path(__file__).parent.resolve().parent / 'data' / 'units_buildings_techs.ror.json'

    process(de_dat, de_strings, de_rms, de_target)
    process(ror_dat, ror_strings, None, ror_target)


if __name__ == '__main__':
    main()
