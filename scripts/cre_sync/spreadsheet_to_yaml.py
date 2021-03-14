# make spreadsheets a frontend for the cre api
# export from spreadsheet to yaml
# yaml to github as a pull request
# import from rest api to spreadsheet

# given: a spreadsheet url
#   export to yaml
#   pull latest yaml from github
#   git merge
#   push to merge branch

# Qs:
# * do i have fs access with a spreadsheet app?
# * can i run git commands?
# * how do we make users setup a github account? maybe get them to create a GH api token?
# if i provide a GO/pex binary
#   can i compile for mac and windows?
#   is there a github client for go?
#   spreadsheets?

# A:
# i can sync s3 and google sheets
# i miss on merging
# i miss on who did what
#

import json
import os.path
import yaml

from spreadsheet_utils import readSpreadsheet
from pprint import pprint

from cre_defs import *
import parsers
import db


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.basicConfig()

spreadsheets_file = "working_spreadsheets.yaml"

# gspread_creds_file = " ~/.config/gspread/credentials.json" # OAUTH default credentials location
# gspread_creds_file = "~/.config/gspread/service_account.json" # Service Account default creds location



cache = "file::memory:?cache=shared"

def parse(workbook:list, result : db.Standard_collection)->db.Standard_collection:
    """ parses custom cre docs into cre_defs classes the opposite of db.py Export"""
    if workbook[0].get("CRE-ID-lookup-from-taxonomy-table"):
        cres = parsers.parse_v0_standards(workbook)
        for cre_name, cre in cres.items():
            dbcre = db.CRE(description=cre.description,
                            name=cre.name)
            result.add_cre(dbcre)
            for link in cre.links:
                linked_standard = db.Standard(
                    name=link.name,
                    section=link.section,
                    subsection=link.subsection)
                result.add_standard(linked_standard)
                result.add_link(dbcre, linked_standard)
    return result
    # todo: add support for v1 (groups)


def main():
    script_path = os.path.dirname(os.path.realpath(__file__))
    cre_loc = os.path.join(script_path, "../../cres")
    with open(os.path.join(script_path, spreadsheets_file)) as sfile:
        # create_branch(commit_msg_base)
        urls = yaml.safe_load(sfile)
        standards = db.Standard_collection(cache=True, cache_file=cache)
        for spreadsheet_url in urls:
            logger.info("Dealing with spreadsheet %s"%spreadsheet_url['alias'])
            workbooks = readSpreadsheet(spreadsheet_url['url'], cres_loc=cre_loc,alias=spreadsheet_url['alias'])
            for workbook in workbooks:
                standards = parse(workbook,standards)
        standards.export(cre_loc)

            # if  # todo: make this optional
            #     add_to_github(cre_loc, spreadsheet_url['alias'],os.getenv("GITHUB_API_KEY"))
            # else:
            #     logger.info("Spreadsheet \"%s\" didn't produce any changes, no pull request needed"%spreadsheet_url['alias'])
if __name__ == "__main__":
    main()


#  todo : split into spreadsheet utilities, git utilities
#  allow "parse spreadsheet" to write CRE docs instead of Yaml.dump