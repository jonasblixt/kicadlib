# Field-definition styles

Both styles produce the `fields` array inside the single `libraries[0]`
entry of the `.kicad_dbl` file, i.e. the return value of
`build_field_defs()` in the importer script. Every field dict has the same
four keys: `column` (must match a column name in the SQLite table),
`name` (label shown in KiCad), `visible_on_add`, `visible_in_chooser`, and
`show_name` (whether the label prefixes the value in the schematic — omit
this key entirely to get KiCad's default of `true`, as the `Value` field
does in the ceramic style below).

## Ceramic / MLCC style

Used for non-polarized ceramic capacitors: plain MLCCs, RF-grade MLCCs,
and safety-rated (X1/X2/Y1/Y2) MLCCs. Symbol is `Device:C`.

```python
def build_field_defs():
    return [
        {"column": "Capacitance", "name": "Capacitance",
         "visible_on_add": False, "visible_in_chooser": False, "show_name": True},
        {"column": "Voltage", "name": "Voltage",
         "visible_on_add": True, "visible_in_chooser": False, "show_name": False},
        {"column": "Dielectric", "name": "Dielectric",
         "visible_on_add": True, "visible_in_chooser": False, "show_name": False},
        {"column": "Manufacturer", "name": "Manufacturer",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Part Number", "name": "Part Number",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Value", "name": "Value",
         "visible_on_add": True, "visible_in_chooser": True},
    ]
```

If the part family is safety-rated (carries an X1/X2/Y1/Y2 classification,
as with `cap_xy_vishay_vj` and `cap_xy_murata_ga3`), append a
`"Safety Rating"` field:

```python
        {"column": "Safety Rating", "name": "Safety Rating",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
```

Corresponding `CREATE TABLE` columns (adjust the last 1-2 columns for
whatever extra field the family needs):

```sql
CREATE TABLE {table} (
    id TEXT PRIMARY KEY,
    Value TEXT,
    Footprints TEXT,
    Symbol TEXT,
    Capacitance TEXT,
    Voltage TEXT,
    Dielectric TEXT,
    Description TEXT,
    "Part Number" TEXT,
    Manufacturer TEXT,
    "Safety Rating" TEXT  -- omit if not a safety-rated family
)
```

## Polarized-electrolytic style

Used for polarized/electrolytic-type parts: aluminum electrolytic,
aluminum polymer, tantalum polymer, and film chip capacitors whose
datasheets carry ESR/endurance-style data. Symbol is
`Device:C_Polarized_US`.

```python
def build_field_defs():
    return [
        {"column": "Capacitance", "name": "Capacitance",
         "visible_on_add": False, "visible_in_chooser": False, "show_name": True},
        {"column": "Voltage", "name": "Voltage",
         "visible_on_add": True, "visible_in_chooser": False, "show_name": False},
        {"column": "Series", "name": "Series",
         "visible_on_add": False, "visible_in_chooser": False, "show_name": False},
        {"column": "Dielectric", "name": "Dielectric",
         "visible_on_add": False, "visible_in_chooser": False, "show_name": False},
        {"column": "Manufacturer", "name": "Manufacturer",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Part Number", "name": "Part Number",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Value", "name": "Value",
         "visible_on_add": True, "visible_in_chooser": True, "show_name": False},
        {"column": "ESR", "name": "ESR",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Leakage Current", "name": "Leakage Current",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Endurance", "name": "Endurance",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Temp Range", "name": "Temp Range",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
        {"column": "Ripple Current", "name": "Ripple Current",
         "visible_on_add": False, "visible_in_chooser": True, "show_name": True},
    ]
```

The `Value` column itself should be populated with just the resolved
capacitance string (e.g. `"100uF"`), not a "Value: 100uF"-style string —
`show_name: False` on that field is what suppresses the "Value:" label in
the schematic, so the column content and the display convention have to
match.

Corresponding `CREATE TABLE` columns:

```sql
CREATE TABLE {table} (
    id TEXT PRIMARY KEY,
    Value TEXT,
    Footprints TEXT,
    Symbol TEXT,
    Capacitance TEXT,
    Voltage TEXT,
    Series TEXT,
    Dielectric TEXT,
    Description TEXT,
    "Part Number" TEXT,
    Manufacturer TEXT,
    ESR TEXT,
    "Leakage Current" TEXT,
    Endurance TEXT,
    "Temp Range" TEXT,
    "Ripple Current" TEXT
)
```

If the vendor datasheet simply doesn't publish one of ESR / Leakage
Current / Endurance / Temp Range / Ripple Current for this family, keep
the column and field definition anyway and leave it empty for every row —
that's intentional schema parity across sibling libraries, not a mistake
to "clean up" by dropping the column.

## `.kicad_dbl` file skeleton

Both styles share the same wrapper — only `name`, `description`,
`connection_string`'s db filename, the `libraries[0].name` nickname,
`table`, and `fields` change:

```json
{
    "meta": { "version": 0 },
    "name": "<Human-readable library name>",
    "description": "<Human-readable description>",
    "source": {
        "type": "odbc",
        "dsn": "",
        "username": "",
        "password": "",
        "timeout_seconds": 2,
        "connection_string": "Driver={SQLite3 ODBC Driver};Database=${CWD}/<library_name>.db"
    },
    "libraries": [
        {
            "name": "<SHORT library nickname shown in KiCad's chooser - e.g. \"VJ\", \"GA3\", \"OSCON\", \"ECHU(X)\" - a few characters pulled from the series name, NOT the full table name>",
            "table": "<library_name>",
            "key": "id",
            "symbols": "Symbol",
            "footprints": "Footprints",
            "fields": [ /* build_field_defs() output */ ],
            "properties": { "description": "Description" }
        }
    ]
}
```
