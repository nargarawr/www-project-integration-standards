import cre_defs as defs
from enum import Enum
from pprint import pprint
# collection of methods to parse different versions of spreadsheet standards
# each method returns a list of cre_defs documents


def is_empty(value: str):
    value = str(value)
    return value is None or value == 'None' or value == "" or "N/A" in value.upper() or value == 'nan'


def parse_review_standards(cre_file: list) -> dict:
    raise NotImplementedError


def parse_uknown_key_val_spreadsheet(link_file: list) -> dict:
    """ parses a cre-less spreadsheet into a list of Standards documents"""
    standards = {}
    # get the first Key of the first row, pretty much, choose a standard at random to be the main one
    main_standard_name = None
    for stand in list(link_file[0]):
        if not is_empty(stand):
            main_standard_name = stand
            break

    for mapping in link_file:
        primary_standard = None
        linked_standard = None
        if not is_empty(mapping.get(main_standard_name)):
            primary_standard = standards.get(
                main_standard_name+"-"+str(mapping.get(main_standard_name)))
            if not primary_standard:
                # pop is important here, if the primary standard is not removed, it will end up linking to itself
                primary_standard = defs.Standard(name=main_standard_name,
                                                 section=mapping.pop(
                                                     main_standard_name))

        for key, value in mapping.items():
            if not is_empty(value) and not is_empty(key):
                linked_standard = defs.Standard(
                    name=key, section=mapping.get(key))
                primary_standard.add_link(defs.Link(document=linked_standard))
        if primary_standard:
            standards[primary_standard.name+"-" +
                      primary_standard.section] = primary_standard
        return standards


def parse_v1_standards(cre_file: list) -> dict:
    cre = None
    linked_standard = None
    cres = {}
    groupless_cres = {}
    groups = {}
    for cre_mapping in cre_file:
        name = cre_mapping.pop("Core-CRE (high-level description/summary)")
        id = cre_mapping.pop('CORE-CRE-ID').strip()
        if name in cres.keys():
            cre = cres[name]
            # if name is not None and id != cre.id:
            #     raise EnvironmentError(
            #         "same cre name %s different id? %s %s" % (cre.name, cre.id, id))
        else:
            cre = defs.CRE(description=cre_mapping.pop("Description"),
                           name=name,
                           id=id)
        asvs_tags = []
        if cre_mapping.pop('ASVS-L1') == 'X':
            asvs_tags.append("L1")
        if cre_mapping.pop('ASVS-L2') == 'X':
            asvs_tags.append("L2")
        if cre_mapping.pop('ASVS-L3') == 'X':
            asvs_tags.append("L3")

        if not is_empty(cre_mapping.get("ID-taxonomy-lookup-from-ASVS-mapping")):
            cre.add_link(defs.Link(document=defs.Standard(name='ASVS',
                                                          section=cre_mapping.pop(
                                                              'ASVS Item'),
                                                          subsection=cre_mapping.pop(
                                                              "ID-taxonomy-lookup-from-ASVS-mapping"),
                                                          tags=asvs_tags)))
        if not is_empty(cre_mapping.get('CWE')):
            cre.add_link(defs.Link(document=defs.Standard(
                name='CWE', section=cre_mapping.pop('CWE'))))

        if not is_empty(cre_mapping.get('Cheat Sheet')) and not is_empty(cre_mapping.get('cheat_sheets')):
            cre.add_link(defs.Link(document=defs.Standard(name='Cheatsheet',
                                                          section=cre_mapping.pop(
                                                              'Cheat Sheet'),
                                                          hyperlink=cre_mapping.pop(
                                                              'cheat_sheets'))))

        nist_items = cre_mapping.pop('NIST 800-53 - IS RELATED TO')
        if not is_empty(nist_items):
            if '\n' in nist_items:
                for element in nist_items.split('\n'):
                    if element:
                        cre.add_link(defs.Link(document=defs.Standard(name='NIST 800-53',
                                                                      section=element,
                                                                      tags="is related to")))
            else:
                cre.add_link(defs.Link(document=defs.Standard(name='NIST 800-53',
                                                              section=nist_items,
                                                              tags="is related to")))
        if not is_empty(cre_mapping.get('NIST 800-63')):
            cre.add_link(defs.Link(document=defs.Standard(name='NIST 800-63',
                                                          section=cre_mapping.pop('NIST 800-63'))))

        if not is_empty(cre_mapping.get('OPC')):
            cre.add_link(defs.Link(document=defs.Standard(name='OPC',
                                                          section=cre_mapping.pop('OPC'))))

        if not is_empty(cre_mapping.get('Top10 2017')):
            cre.add_link(defs.Link(document=defs.Standard(name='TOP10',
                                                          section=cre_mapping.pop('Top10 2017'))))
        if not is_empty(cre_mapping.get('WSTG')):
            cre.add_link(defs.Link(document=defs.Standard(name='WSTG',
                                                          section=cre_mapping.pop('WSTG'))))
        if not is_empty(cre_mapping.get('SIG ISO 25010')):
            cre.add_link(defs.Link(document=defs.Standard(name='SIG ISO 25010',
                                                          section=cre_mapping.pop('SIG ISO 25010'))))
        cres[cre.name] = cre
        # group mapping
        is_in_group = False
        for i in range(1, 8):
            group = None
            gname = cre_mapping.pop("CRE Group %s" % i)
            gid = cre_mapping.pop("CRE Group %s Lookup" % i)
            if not is_empty(gname):

                if gname not in groups.keys():
                    group = defs.CRE(name=gname, id=gid)
                elif groups.get(name) and id != groups.get(name).id and not is_empty(groups.get('name')):
                    raise Exception("Group %s has two different ids %s and %s" % (
                        name, id, groups.get('name')))
                else:
                    group = groups.get(gname)

                is_in_group = True
                group.add_link(defs.Link(document=cre))
                groups[group.name] = group
        if not is_in_group:
            groupless_cres[cre.name] = cre
    return (groups, groupless_cres)


def parse_v0_standards(cre_file: list) -> dict:
    """ given a yaml with standards, build a list of standards
    """
    cres = {}
    for cre_mapping in cre_file:
        cre = None
        linked_standard = None
        if cre_mapping.get("CRE-ID-lookup-from-taxonomy-table"):
            existing = cres.get(cre_mapping.get(
                "CRE-ID-lookup-from-taxonomy-table"))
            if existing:
                cre = existing
                name = cre_mapping.get("name")
                if name is not None and name != cre.name:
                    raise EnvironmentError(
                        "same cre different name? %s %s" % (cre.name, name))
            else:
                cre = defs.CRE(description=cre_mapping.pop("Description"),
                               name=cre_mapping.pop("CRE-ID-lookup-from-taxonomy-table"))

        # parse ASVS, the v0 docs have a human-friendly but non-standard way of doing asvs
        if cre_mapping.get("ID-taxonomy-lookup-from-ASVS-mapping"):
            linked_standard = defs.Standard(name="ASVS",
                                            section=cre_mapping.pop(
                                                "ID-taxonomy-lookup-from-ASVS-mapping"),
                                            subsection=cre_mapping.pop("Item")
                                            )

            cre.add_link(defs.Link(document=linked_standard))

        for key, value in cre_mapping.items():
            if not is_empty(value) and not is_empty(key):
                linked_standard = defs.Standard(name=key,
                                                section=value
                                                )
                cre.add_link(defs.Link(document=linked_standard))
        if cre:
            cres[cre.name] = cre
    return cres
