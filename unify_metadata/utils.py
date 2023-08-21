import os
import json
from .questions import question

data_dir = os.path.expanduser('~')+"/.unify-metadata/"


def sanitize_location(location):
    lookup = json.load(open(data_dir+"country_lookup.json"))
    if location in lookup:
        return lookup[location]
    else:
        country_code = question(f"Location not found: {location}. Please enter manually")
        country_code = country_code.lower()
        lookup[location] = country_code
        json.dump(lookup,open(data_dir+"country_lookup.json","w"),indent=4)
        return country_code

def sanitize_date(date):
    pass

def left_join_rows(target_rows,source_rows,source_key,target_key):
    fields = list(source_rows[0])
    new_target_rows = target_rows.copy()
    source_rows_dict = { row[source_key]:row for row in source_rows }
    for row in new_target_rows:
        if row[target_key] in source_rows_dict:
            row.update(source_rows_dict[row[target_key]])
        else:
            row.update({ field:None for field in fields })

    return new_target_rows