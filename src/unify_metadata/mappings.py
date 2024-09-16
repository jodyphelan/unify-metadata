from .utils import *
import yaml
from .questions import multiple_choice
import sys

def get_mapping_skeleton(args):
    standard_columns = list(yaml.safe_load_all(open(args.defaults)))[0]

    csv_data = get_csv_data(args.raw_data)

    csv_columns = list(csv_data)
    
    conf = {
        'raw_data':args.raw_data,
    }
    
    tag_values = defaultdict(dict)


    if args.project_name:
        conf["study_name"] = args.project_name
    else:
        study_name = input(Cyan("What is the study name?\n"))
        conf["study_name"] = study_name

    for element in standard_columns:
        print("------ " + Green(str(element)) + " ------")
        happy = False
        while not happy:
            if isinstance(element,str):
                c = element
            else:
                c = list(element)[0]

            tmp_c = find_column(c,csv_columns)
            if tmp_c:
                sys.stderr.write(f"Found column {tmp_c} for {c}\n")
                data_column = tmp_c
            else:
                i = input(Cyan(f"What is the mapping for {c}? (leave blank to skip)\n") + "\n".join([f"{i+1}) {x}" for i,x in enumerate(csv_columns)]) + "\n")
                if i=="":
                    data_column = None
                else:
                    data_column = csv_columns[int(i)-1]


            tmp_conf = {"column":data_column}
            
            if data_column is None:
                break

            mapping =  {}


            
            

            if "values" in element:
                values = element["values"]
                for v in sorted(csv_data[data_column]):
                    if 'tag' in element:
                        if v in tag_values[element['tag']]:
                            mapping[v] = tag_values[element['tag']][v]
                            continue
                    question = f"What is the mapping for {v}?"
                    mapping[v] = multiple_choice(question,values)
                    if 'tag' in element:
                        tag_values[element['tag']][v] = mapping[v]
                tmp_conf["mapping"] = mapping

            if "date" in element:
                regex = input(Cyan("What is the regex for the date? (leave empty to enable guessing)\n"))
                if regex=="":
                    regex = None
                for v in csv_data[data_column]:
                    try:
                        tmpdate = sanitize_date(v,regex)
                        mapping[v] = tmpdate
                    except:
                        userdate = input(f"Could not parse |{v}| as a date. Press manually enter to value continue\n")
                        if userdate.lower() in ("null","none","","n/a","na"):
                            userdate = None
                        mapping[v] = userdate
                tmp_conf["mapping"] = mapping
            
            if "country_iso3" in element:
                for v in csv_data[data_column]:
                    mapping[v] = sanitize_location(v)
                tmp_conf["mapping"] = mapping

            qhappy = input(f"Are you happy with this mapping for {data_column}? {Green(str(tmp_conf))} (Y/n)\n")
            if qhappy=="y" or  qhappy=="":
                happy = True  

        conf[c] = tmp_conf
        print("\n#####################\n")

    with open(args.conf,"w") as fh:
        json.dump(conf,fh,indent=4)
