
import os
import yaml
import logging
import gspread
import cre_defs as defs
from pprint import pprint
import db
from copy import deepcopy
import io
import csv

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.basicConfig()


def readSpreadsheet(url: str, cres_loc: str, alias: str, validate=True):
    """given remote google spreadsheet url,
     reads each workbook into a collection of documents"""
    changes_present = False
    try:
        gc = gspread.oauth()  # oauth config, TODO (northdpole): make this configurable
        # gc = gspread.service_account()
        sh = gc.open_by_url(url)
        logger.info("accessing spreadsheet \"%s\" : \"%s\"" % (alias, url))
        result = {}
        for wsh in sh.worksheets():
            if wsh.title[0].isdigit():
                logger.info(
                    "handling worksheet %s  (remember, only numbered worksheets will be processed by convention)" % wsh.title)
                records = wsh.get_all_records()
                toyaml = yaml.safe_load(yaml.safe_dump(records))
                result[wsh.title] = toyaml
    except gspread.exceptions.APIError as ae:
        logger.error("Error opening spreadsheet \"%s\" : \"%s\"" %
                     (alias, url))
        logger.error(ae)
    return result


def __add_cre_to_spreadsheet(document: defs.Document, header: dict, cresheet: list, maxgroups: int):
    cresheet.append(header.copy())
    working_array = cresheet[-1]
    conflicts = []
    if document.doctype == defs.Credoctypes.CRE:
        working_array['CRE:name'] = document.name
        working_array['CRE:id'] = document.id
        working_array['CRE:description'] = document.description
    elif document.doctype == defs.Credoctypes.Standard: # case where a lone standard is displayed without any CRE links
        working_array[document.name+':section'] = document.section
        working_array[document.name+':subsection'] = document.subsection
        working_array[document.name+':hyperlink'] = document.hyperlink

    for link in document.links:
        if link.document.doctype == defs.Credoctypes.Standard:  # linking to normal standard
            # a single CRE can link to multiple standards hence we can have conflicts
            if working_array[link.document.name+":section"]:
                conflicts.append(link)
            else:
                working_array[link.document.name +
                              ":section"] = link.document.section
                working_array[link.document.name +
                              ":subsection"] = link.document.subsection
                working_array[link.document.name +
                              ":hyperlink"] = link.document.hyperlink
                working_array[link.document.name +
                              ":link_type"] = link.ltype.value
        elif link.document.doctype == defs.Credoctypes.CRE:  # linking to another CRE
            grp_added = False
            for i in range(0, maxgroups):
                if not working_array['Linked_CRE_%s:id' % i]:
                    grp_added = True
                    working_array['Linked_CRE_%s:id' % i] = link.document.id
                    working_array['Linked_CRE_%s:name' % i] = link.document.name
                    working_array['Linked_CRE_%s:link_type' % i] = link.ltype.value
                    break
            if not grp_added:
                logger.fatal("Tried to add Group %s but all of the %s group slots are filled. This must be a bug" % (
                    link.document.name, maxgroups))

    # conflicts handling
    if len(conflicts):
        new_cre = deepcopy(document)
        new_cre.links = conflicts
        cresheet = __add_cre_to_spreadsheet(new_cre, header, cresheet, maxgroups)
    return cresheet


def prepare_spreadsheet(collection: db.Standard_collection, docs: list) -> str:
    """ 
        Given a list of cre_defs.Document will create a list of key,value dict representing the mappings
    """
    standard_names = collection.get_standards_names()  # get header from db (cheap enough)
    header = {'CRE:name': None, 'CRE:id': None, 'CRE:description': None}
    groups = {}
    for name in standard_names:
        header["%s:section" % name] = None
        header["%s:subsection" % name] = None
        header["%s:hyperlink" % name] = None
        header["%s:link_type" % name] = None
    maxgroups = collection.get_max_internal_connections()
    for i in range(0, maxgroups):
        header["Linked_CRE_%s:id" % i] = None
        header["Linked_CRE_%s:name" % i] = None
        header["Linked_CRE_%s:link_type" % i] = None

    logger.debug(header)

    flatdict = {}
    result = []
    for cre in docs:
        flatdict[cre.name] = __add_cre_to_spreadsheet(
            document=cre, header=header, cresheet=[], maxgroups=maxgroups)
        result.extend(flatdict[cre.name])
    return result


def write_spreadsheet(title:str, docs:list, emails:list):
    """ upload local array of flat yamls to url, share with email list"""
    gc = gspread.oauth() # oauth config, TODO (northdpole): make this configurable
    sh = gc.create(title)
    worksheet = sh.add_worksheet(title="0."+title, rows="1000", cols="200")
    data = io.StringIO()
    fieldnames = docs[0].keys()
    writer = csv.DictWriter(data,fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(docs)
    pprint(data.getvalue())
    input()
    gc.import_csv(sh.id, data.getvalue().encode('utf-8'))
    for email in emails:
        sh.share(email, perm_type='user', role='writer')
    return "https://docs.google.com/spreadsheets/d/%s" % sh.id


