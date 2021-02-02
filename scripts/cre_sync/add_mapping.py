import gspread
import yaml
import tempfile
import jsonschema
import json
import os.path
import logging
import git

from pprint import pprint
from datetime import datetime
from github import Github

class Mapping:
    standard_name
    standard_value

    def __init__(self, name,value):
        self.standard_name = name
        self.standard_value = value

class MappingDoc:
    mappings

    def __init__(self, document):
        # doc is a list of dictionaries each with a k,v mapping a standard name to a value
        # transform each to a mapping and add it to mappings
        pass

class Match:
    # tupple of Mappings
        
    mapping_match

# TODO: THIS NEEDS TO BE OOP, class PartialMatch with confidence score and with Match subclass describing which fields of which mapping match to which cre and Disagreement describing which fields of the mapping partially disagree with which field of which CRE
#  then we can use the map of "file->cre" to load and update a specific cre
# (there is a case where a mapping might match one CRE 5 and another 15)
# For disputed standards/lines we should add them to a disputes workbook along with the disputes, score + what ended up happening to it
#
#
# Use case: there is a spreadsheet that maps
# a standard we know about and have mapped to cres to standards we don't know about
# workflow:
# parse spreadsheet to json, try to find at least one standard that we know about, add the mappings
# Cherry pick the "key/standard" columns we want to add only

# v2:
# * ability to define metadata columns
# * generate a new pull request

spreadsheet_link = "" # todo: argument
relevant_worksheets = ["output.yaml"] # todo: argument
relevant_columns = [] # todo: argument
script_path = os.path.dirname(os.path.realpath(__file__))
MIN_CONFIDENCE = 2 # todo: make into argument

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def load_all_standards()-> (dict,set):
    cres = {}
    cre_loc = os.path.join(script_path, "../../cres")
    for root, dirs, files in os.walk(cre_loc, topdown=False):
        for cref in files:
            if cref == ".gitkeep":
                continue
            cres[cref] = list(yaml.safe_load_all(open(os.path.join(root,cref))))

            stands = set([])
            for cre_maps in cres[cref]:
                for cmap in cre_maps:
                    # print(cmap)
                    if type(cmap) != dict:
                        # print(cmap)
                        # input()
                        continue
                    # input()
                    for key in cmap.keys():
                        # input(key)
                        stands.add(key)
    # pprint("============================")
    # pprint(stands)
    # pprint("============================")
    # input()
    return stands,cres

def find_existing_cre_mapping(mapping:dict,all_cres:dict,known_standards:set):
    """
    given a mapping of type
    {standard_name1:link_to_relevant_standard_section1,
    standard_name2:link_to_relevant_standard_section2,
    ....}
    find the most similar cre by matching the names with sections,
    calculate how many keys,values of the incoming mapping match to a particular CRE
    and return the cre along with the calculation
    """

    common_standards = mapping.keys() & known_standards
    max_confidence = len(common_standards)
    disputed_matches = []
    if len(common_standards) == 0:
        print("no commonalities")
        return 0, {}
    elif len(common_standards) == 1:
        print("1 common standard, will be a weak matching")

    best_cre = {}
    best_confidence = 0
    # for standard_name in common_standards:
    for file_name, cre_file in all_cres.items():
        for cre in cre_file[0]:
            confidence = 0
            for standard_name in common_standards:
                if cre[standard_name] != '' and cre[standard_name] == mapping[standard_name]:
                    print("match")
                    print(standard_name)
                    print(cre[standard_name])
                    print(mapping[standard_name])

                    confidence += 1 # if you find matching standards, it's more likely this is a valid mapping

                elif confidence >=1 and cre[standard_name] != '' and cre[standard_name] != mapping[standard_name]:
                    disputed_matches.append((mapping,cre))
                    # confidence -= 1 # if there are non-matching standards, we got a problem
            if confidence >= best_confidence:
                best_cre = cre
                best_confidence = confidence
            if confidence == max_confidence:
                return confidence, cre
    if len(disputed_matches) and confidence:
        pprint(disputed_matches)
        print(confidence)
        input(len(disputed_matches))
        #  TODO: return disputes i
    return best_confidence, best_cre

        # try to find a cre that references a matching standard

    # for standard_name, standard_value in mapping.items():

            # if standard_name in known_standards:
                # if we know about the standard
                # (e.g. CRE already maps NIST and the new mapping is NIST->X->ISO)
                # then try to find a CRE that references the standard value
                #  e.g. find the CRE that maps to NIST:1.2.3
                #  then try to reinforce the mapping by searching if the new link has more similarities with that particular CRE
                # e.g. if the new link maps NIST:1.2.3 AND ASVS:3.4.5 AND a couple other things to ISO:XYZ then we're probably safe to introduce the mapping
                # Will hardcode safety margins for now.

            #     print(standard_name)
            #     pprint(mapping)
            #     input()
            # print("name")
            # # pprint(standard_name)
            # print("index")

            # pprint(index)
        #  todo if interesting columns in known_standards continue
        # find column we know about, find where it's value is and map the rest of the interesting columns as extra standards



def explorashone(mappings):
    # pprint(mappings)
    # exit(1)
    known_standards,all_cres = load_all_standards()
    for mapping in mappings:
        confidence, cre = find_existing_cre_mapping(mapping,all_cres,known_standards)
        if confidence >= MIN_CONFIDENCE:
        #    pprint(cre)
        #    pprint(confidence)
        #    pprint(mapping)
        #    input()
            pass

def readSpreadsheet(url: str, cres_loc: str, alias:str):
    """given remote google spreadsheet url,
     reads each workbook into a yaml file"""
    try:
        gc = gspread.oauth()
        # gc = gspread.service_account()
        sh = gc.open_by_url(url)
        logger.debug("accessing spreadsheet \"%s\" : \"%s\""%(alias,url))
        print("reading")

        for wsh in sh.worksheets():
            if wsh.title in relevant_worksheets:
                logger.debug("handling worksheet %s " % wsh.title)
                records = wsh.get_all_records()
                toyaml = yaml.safe_load(yaml.dump(records))
                explorashone(toyaml)
    except gspread.exceptions.APIError as ae:
        logger.error("Error opening spreadsheet \"%s\" : \"%s\""%(alias,url))
        logger.error(ae)


def validateYaml(yamldoc: str, schema: str):
    jsonschema.validate(instance=yamldoc, schema=schema)



def main():
    spreadsheets_file = "working_spreadsheets.yaml"
    script_path = os.path.dirname(os.path.realpath(__file__))
    cre_loc = os.path.join(script_path, "../../cres")
    with open(os.path.join(script_path, spreadsheets_file)) as sfile:
        # create_branch(commit_msg_base)
        urls = yaml.safe_load(sfile)
        for spreadsheet_url in urls:
            logger.info("Dealing with spreadsheet '%s' "%spreadsheet_url['alias'])
            readSpreadsheet(spreadsheet_url['url'], cres_loc=cre_loc,alias=spreadsheet_url['alias'])
if __name__ == "__main__":
    main()
