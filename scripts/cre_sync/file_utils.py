import os
import yaml


def writeToDisk(file_title:str, cres_loc:str, file_content:str):
        with open(os.path.join(cres_loc, file_title + ".yaml"), "w",encoding='utf8') as fp:
            fp.write(file_content)
