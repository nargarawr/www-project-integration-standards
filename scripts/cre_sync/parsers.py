from pprint import pprint
import cre_defs as defs
from enum import Enum
from cre_defs import CreVersions

# collection of methods to parse different versions of spreadsheet standards
# each method returns a list of cre_defs documents

def not_empty(value: str):
    value = str(value)
    return value != None and value != "" and "N/A" not in value


def parse_v0_standards(cre_file: list) -> dict:
    """ given a yaml with standards, build a list of standards
    """
    cres = {}
    for cre_mapping in cre_file:

        # temporary workaround, the CRE team is the only one adding mappings so everything is official for now
        # when we accept proposed mappings and other links, uncomment:
        # if status == Proposed:
        #   link_status = proposed
        #   cre_status = proposed
        # and change db to have a "proposed status" and change visualisation to paint proposed mappings somehow else

        # so far CRE-ID-lookup-from-taxonomy-table has been used to map CREs
        # so this means that the yaml is "official" and definitely has CRE mapping
        cre = None
        linked_standard = None
        if cre_mapping.get("CRE-ID-lookup-from-taxonomy-table"):
            existing = cres.get(cre_mapping.get("CRE-ID-lookup-from-taxonomy-table"))
            if existing:
                cre = existing
            else:
                cre = defs.CRE(version=CreVersions.V0,
                               description=cre_mapping.pop("Description"),
                               name=cre_mapping.pop("CRE-ID-lookup-from-taxonomy-table"))

        # parse ASVS, the v0 docs have a human-friendly but non-standard way of doing asvs
        if cre_mapping.get("ID-taxonomy-lookup-from-ASVS-mapping"):
            linked_standard = defs.Standard(
                version=CreVersions.V0,
                name="ASVS",
                section=cre_mapping.pop(
                    "ID-taxonomy-lookup-from-ASVS-mapping"),
                subsection=cre_mapping.pop("Item")
            )
            
            cre.add_link(linked_standard)

        for key, value in cre_mapping.items():
            if not_empty(value) and not_empty(key):
                linked_standard = defs.Standard(
                    version= CreVersions.V0,
                    name=key,
                    section=value
                )
                cre.add_link(linked_standard)
        if cre:
            cres[cre.name] = cre
    return cres