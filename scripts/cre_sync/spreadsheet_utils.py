      
import os
import yaml
import logging
import gspread

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.basicConfig()

def readSpreadsheet(url: str, cres_loc: str, alias:str,validate=True):
    """given remote google spreadsheet url,
     reads each workbook into a collection of documents"""
    changes_present = False
    try:
        gc = gspread.oauth() # oauth config, TODO (northdpole): make this configurable
        # gc = gspread.service_account()
        sh = gc.open_by_url(url)
        logger.info("accessing spreadsheet \"%s\" : \"%s\""%(alias,url))
        result = {}
        for wsh in sh.worksheets():
            if wsh.title[0].isdigit():
                logger.info(
                    "handling worksheet %s  (remember, only numbered worksheets will be processed by convention)" % wsh.title)
                records = wsh.get_all_records()
                toyaml = yaml.safe_load(yaml.dump(records))
                result[wsh.title] = toyaml
    except gspread.exceptions.APIError as ae:
        logger.error("Error opening spreadsheet \"%s\" : \"%s\""%(alias,url))
        logger.error(ae)
    return result



def createSpreadsheet(docs:list,title:str, share_with:list) -> str:
    """ Given a list of cre_defs.Document will create a new spreadsheet and dump each document into a new worksheet
        will share spreadsheet with the emails identified in the "share_with" list
        returns: the url of the new spreadsheet
    """
    gc = gspread.oauth() # oauth config, TODO (northdpole): make this configurable
    sh = gc.create(title)
    for doc in docs:
        worksheet = sh.add_worksheet(title=doc.name, rows="100", cols="20")
        worksheet.update(yaml.dump(doc))

    for email in share_with:
        sh.share(email, perm_type='user', role='writer')
    return sh.url

def writeSpreadsheet(local, url):
    pass

