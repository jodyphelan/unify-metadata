from .ena import *
from .cli import *
from .utils import *
import pandas as pd

homologous_columns = {
    'collection_date':['date_of_collection','collection_date'], 
}

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
            for key in sample_info:
                if sample_info[key] is None:
                    continue
                if key not in new_row:
                    new_row[key] = sample_info[key]
                else:
                    if new_row[key] is None:
                        new_row[key] = sample_info[key]
                    elif new_row[key] != sample_info[key]:
                        print(f"WARNING: {key} for {row['id']} is different between runs and samples: {new_row[key]} != {sample_info[key]}")


        for key in conf:
            if isinstance(conf[key],str):
                new_row[key] = conf[key]
            elif isinstance(conf[key],dict):
                if conf[key]['column'] is None:
                    if key not in new_row:
                        new_row[key] = None
                elif "mapping" in conf[key]:
                    new_row[key] = conf[key]['mapping'][row[conf[key]['column']]]
                else:
                    new_row[key] = row[conf[key]['column']]
        rows.append(new_row)

    df = pd.DataFrame(rows)

    for key in homologous_columns:
        # check there are more than one of the values in the data frame
        print([column in df.columns for column in homologous_columns[key]])
        if sum([column in df.columns for column in homologous_columns[key]]) < 2:
            continue

        def get_value_if_only_one_value(x):
            x = x.dropna()
            sx = set(x)
            if len(sx) == 1:
                return sx.pop()
            else:
                return None
            
        only_one_values = df[homologous_columns[key]].apply(get_value_if_only_one_value, axis=1)
        for col in homologous_columns[key]:
            missing_i = df[col].isna()
            df.loc[missing_i, col] = only_one_values[missing_i] 
        notequal_i = df[['date_of_collection','collection_date']].apply(lambda x: len(set(x))!=1,axis=1)

        if True in notequal_i > 0:
            print(df.loc[notequal_i,['id']+['date_of_collection','collection_date']])
            column_to_use = input(f"\nDifferent values present for {key}. Which column to use for {key}? ")
            chosen_values = df[column_to_use]
            df.drop(columns=homologous_columns[key],inplace=True)
            df[key] = chosen_values
            print(df[['id',key]])
    
    print("Number of resolved IDs:")
    print(pd.notna(df['wgs_id']).value_counts())
    if args.find_wgs_id:
        if args.debug:
            df.to_csv(args.outfile,na_rep="NA",index=False)
        else:
            df[pd.notna(df['wgs_id'])].to_csv(args.outfile,na_rep="NA",index=False)
    else:
        df.to_csv(args.outfile,na_rep="NA",index=False)