import yaml

def get_default_columns(filename):
    conf = list(yaml.safe_load_all(open(filename)))[0]
    columns = []
    for element in conf:
        if isinstance(element,str):
            columns.append(element)
        else:
            columns.append(list(element)[0])
    return columns

