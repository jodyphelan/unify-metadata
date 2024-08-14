import argparse
import unify_metadata
import sys
from .ena import update_ena_db, generate_data_from_bioprojects
from .mappings import get_mapping_skeleton
from .standardise import standardise_raw_data
from .utils import combine_csv_files
import os


def cli_update_ena_db(args):
    print(args)
    taxid = args.taxid
    update_ena_db(taxid)


def pipeline(args):
    # get current folder name
    current_folder = os.path.basename(os.getcwd())
    args.project_name = current_folder
    args.conf = "mappings.conf.json"
    get_mapping_skeleton(args)
    standardise_raw_data(args)



def main():
    parser = argparse.ArgumentParser(description='TBProfiler pipeline',formatter_class=argparse.ArgumentDefaultsHelpFormatter,add_help=False)
    subparsers = parser.add_subparsers(help="Task to perform")

    parser_sub = subparsers.add_parser('pipeline', help='Run whole profiling pipeline', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_sub.add_argument("--raw-data",type=str,help="Raw data file",required=True)
    parser_sub.add_argument("--outfile",default="data.clean.csv",type=str,help="Output file")
    parser_sub.add_argument("--defaults",type=str,help="Comma separated list of drugs",required=True)
    parser_sub.add_argument("--find-wgs-id",action="store_true",help="Raw data file")
    parser_sub.add_argument("--taxid",type=str,help="Raw data file",required='--find-wgs-id' in sys.argv)
    parser_sub.add_argument("--project-name",type=str,help="Raw data file")
    parser_sub.set_defaults(func=pipeline)


    # Profile #
    parser_sub = subparsers.add_parser('mappings', help='Run whole profiling pipeline', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_sub.add_argument("--raw-data",type=str,help="Raw data file",required=True)
    parser_sub.add_argument("--conf",default="mappings.conf.json",type=str,help="Output file")
    parser_sub.add_argument("--defaults",type=str,help="Comma separated list of drugs",required=True)
    parser_sub.set_defaults(func=get_mapping_skeleton)


    # Profile #
    parser_sub = subparsers.add_parser('standardise', help='Run whole profiling pipeline', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_sub.add_argument("--conf",type=str,default="mappings.conf.json",help="Raw data file")
    parser_sub.add_argument("--outfile",type=str,default="data.clean.csv",help="Raw data file")
    parser_sub.add_argument("--raw-data",type=str,help="Raw data file",required=True)
    parser_sub.add_argument("--find-wgs-id",action="store_true",help="Raw data file")
    parser_sub.add_argument("--taxid",type=str,help="Raw data file",required='--find-wgs-id' in sys.argv)
    parser_sub.set_defaults(func=standardise_raw_data)

    parser_sub = subparsers.add_parser('combine', help='Combine multiple csv files together', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_sub.add_argument("--id",type=str,help="Raw data file",required=True)
    parser_sub.add_argument("--additional-data",type=str,help="Raw data file")
    parser_sub.add_argument("--additional-data-id",type=str,help="Raw data file")
    parser_sub.add_argument("--missing-value",default="NA",type=str,help="Raw data file")
    parser_sub.add_argument("--outfile",type=str,help="Raw data file",required=True)
    parser_sub.add_argument("files",type=str,nargs="+",help="Raw data file")
    parser_sub.set_defaults(func=combine_csv_files)

    parser_sub = subparsers.add_parser('bioproject-csv', help='Combine multiple csv files together', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_sub.add_argument("--taxid",type=str,help="Raw data file",required=True)
    parser_sub.add_argument("--bioprojects",type=str,nargs="+",help="Raw data file",required=True)
    parser_sub.add_argument("--defaults",type=str,help="Raw data file",required=True)
    parser_sub.add_argument("--country",type=str,help="Raw data file")
    parser_sub.add_argument("--outfile",type=str,default="data.clean.csv",help="Raw data file")

    parser_sub.set_defaults(func=generate_data_from_bioprojects)

    parser_sub = subparsers.add_parser('udpate-ena', help='Combine multiple csv files together', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser_sub.add_argument("--taxid",type=str,help="Raw data file",required=True)
    parser_sub.set_defaults(func=cli_update_ena_db)


    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help(sys.stderr)