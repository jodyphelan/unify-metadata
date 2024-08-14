from .ena import update_ena_db
from .mappings import get_mapping_skeleton
from .standardise import standardise_raw_data
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