from .ena import *
from .cli import *
from .utils import *


def standardise_raw_data(args):
    conf = json.load(open(args.conf))

    if args.find_wgs_id:
        rundb = RunDB(get_taxid_files(args.taxid)[0])
        sampledb = BiosampleDB(get_taxid_files(args.taxid)[1])
    rows = []
    for row in csv.DictReader(open(conf['raw_data'],"r",encoding="utf-8-sig")):
        if row[conf['id']['column']]=="NA":continue
        new_row = {'id':row[conf['id']["column"]]}
        if args.find_wgs_id:
            run_info = rundb.get_sample_info(new_row['id'])
            new_row.update(run_info)
            sample_info = sampledb.get_sample_info(new_row['sample_accession'])
            print(sample_info)
            for key in sample_info:
                if sample_info[key] is None:
                    continue
                if key not in new_row:
                    new_row[key] = sample_info[key]
                else:
                    if new_row[key] is None:
                        new_row[key] = sample_info[key]
                    elif new_row[key] != sample_info[key]:
                        print(f"WARNING: {key} is different between runs and samples: {new_row[key]} != {sample_info[key]}")


        for key in conf:
            if isinstance(conf[key],str):
                new_row[key] = conf[key]
            elif isinstance(conf[key],dict):
                if conf[key]['column'] is None:
                    if key not in new_row:
                        new_row[key] = "NA"
                elif "mapping" in conf[key]:
                    new_row[key] = conf[key]['mapping'][row[conf[key]['column']]]
                else:
                    new_row[key] = row[conf[key]['column']]
        rows.append(new_row)

    write_csv(rows,args.outfile)