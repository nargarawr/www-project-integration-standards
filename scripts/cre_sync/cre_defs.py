from pprint import pprint
from dataclasses import dataclass
from enum import Enum
import json
# used for serialising and deserialising yaml CRE documents

class Credoctypes(Enum):
    Group = "Group"
    CRE = "CRE"
    Standard = "Standard"


class CreVersions(Enum):
    V0 = 0  # initial experiments, no groups, list of flat mappings
    V1 = 1  # group introduction, still requires manual parsing
    V2 = 2  # future


@dataclass
class Metadata():
    labels: list

    def __init__(self, labels=[]):
        self.labels = labels

    def todict(self):
        return json.dump(self.labels)


@dataclass
class Document():
    version: CreVersions
    doctype: Credoctypes
    id: str
    description: str
    name: str
    links: list
    tags: list
    metadata: Metadata

    def __eq__(self, other):
        return self.id == other.id and \
            self.name == other.name and \
            self.version.value == other.version.value and \
            self.doctype.value == other.doctype.value and \
            self.description == other.description and \
            self.links == other.links and \
            self.tags == other.tags and \
            self.metadata == other.metadata

    def todict(self):
        result = {'version': self.version.value,
                  'doctype': self.doctype.value,
                  'id': self.id,
                  'description': self.description,
                  'name': self.name,
                  'links': [],
                  'tags': [],
                  'metadata': {}
                  }
        if self.links:
            for link in self.links:
                result['links'].append(link.todict())
        if self.tags:
            for tag in self.tags:
                result['tags'].append(str(tag))
        return result

    def add_link(self, document):
        if not self.links:
            self.links = []
        self.links.append(document)

    def __init__(self, version, name, doctype=None, id="", description="", links=[], tags=[], metadata: Metadata = Metadata()):
        self.version = version or raise_MandatoryFieldException(
            "Document version not defined for document %s" % name)
        self.description = str(description)
        self.name = str(name) or raise_MandatoryFieldException(
            "Document name not defined for document of doctype %s" % doctype)
        self.links = links
        self.tags = tags
        self.id = id
        self.metadata = metadata
        if not doctype and not self.doctype:
            raise_MandatoryFieldException("You need to set doctype")


@dataclass
class CreGroup(Document):
    def __init__(self, *args, **kwargs):
        self.doctype = Credoctypes.Group
        super().__init__(*args, **kwargs)

    # def toflatdict(self):
    #     # flat dictionary
    #     baseline = {'version': self.version.value,
    #               'doctype': self.doctype.value,
    #               'id': self.id,
    #               'description': self.description,
    #               'name': self.name,
    #               'tags': ":".join(self.tags), # : join tags
    #               'existing_links' : [] # hack so we know which keys exist in this row
    #               }
    #     row = baseline.copy()
    #     rows = [row]
    #     if self.links:
    #         for link in self.links:
    #             # 'links': [], # instead of links we get link.name_section/subsection/hyperlink
    #             #  if link exists
    #                     # iterate over existing dict list, find subdict where link doesn't exist
    #                     # if not found, duplicate base line and add
    #             # if link no exists
    #             #   add link

    #             # if the specific dict does not already have a mapping of this group to this standard/cre
    #             if link.
    #             elif link.name in row['existing_links']:
    #                 added = False
    #                 for row in rows: # search for a row that has a gap
    #                     if link.doctype == Credoctypes.CRE and "CRE" not in row.keys():
    #                         added = True
    #                         self.add_cre(link,row)
    #                     elif link.doctype == Credoctypes.Standard and link.name+"_section" not in row.keys():
    #                         added = True
    #                         self.add_standard(link,row)
    #                     if not added: # duplicate row and add
    #                         newrow = baseline.copy()

    #                         rows.append(newrow)

    #     def __add_link_to_flat_dict(self,link:Document,row:dict):
    #         if link.doctype == Credoctypes.CRE:
    #             row['existing_links'].append("CRE")
    #             row["CRE"] = link.name
    #             row["CRE_description"] = link.description
    #             row["CRE_tags"] = ":".join(link.tags)
    #         elif link.doctype == Credoctypes.Standard:
    #             row['existing_links'].append(link.name)
    #             row[link.name+"_section"] = link.section
    #             row[link.name+"_subsection"] = link.subsection
    #             row[link.name+"_hyperlink"] = link.hyperlink
    #         return row

    # def tocsv(self):
    #     # TODO: need a custom serialiser to CSV, and a custom parser from that specific csv format
    #     # e.g. for every link in every top level cre or group: add a line with the CRE and all the standard key/val/subval pairs if there are
    #     # duplicate standard names add another line
    #     # this requires for each csv to find all the standard names so we can build the initial heading
    #     result_header = []
    #     cre_csvheader = ['document-version', 'document-type',
    #                      'description', 'CRE/Group-name', 'tags']
    #     standards_csvheader = []
    #     rows = []
    #     if self.links:
    #         result_row = []
    #         cre_row = [self.version, self.doctype, self.description,
    #                    self.name, ":".join(self.tags)]
    #         standards_row = []
    #         for link in self.links:
    #             if link.name not in result_header:
    #                 if link.doctype == Credoctypes.Standard:
    #                     standards_csvheader.extend([link.name+"_section",
    #                                                 link.name+"_subsection",
    #                                                 link.name+"_hyperlink",
    #                                                 link.name+"_tags"])
    #                     standards_row.extend([link.section,
    #                                           link.subsection,
    #                                           link.hyperlink,
    #                                           ":".join(link.tags)])
    #                     result_header.extend(standards_csvheader)
    #                     result_row.extend(standards_row)
    #                 elif link.doctype == Credoctypes.CRE:
    #                     result_row.extend([EMPTY_VAL]*(len(standards_csvheader)+len(cre_csvheader)))
    #                     cre_csvheader.extend(["CRE","CRE_description","CRE_tags"])
    #                     cre_row.extend([link.name,link.description,":".join(link.tags)])
    #                     result_header.extend(cre_csvheader)
    #                     result_row.extend(cre_row)
    #             else:  # cre_row.append
    #                 if link.doctype == Credoctypes.Standard:
    #                     offset = standards_csvheader.index(link.name+"_section")
    #                     padding = [EMPTY_VAL]*(offset-1)
    #                     standards_row.


@dataclass
class CRE(Document):
    def __init__(self, *args, **kwargs):
        self.doctype = Credoctypes.CRE
        super().__init__(*args, **kwargs)


@dataclass
class Standard(Document):
    doctype = Credoctypes.Standard
    section: str
    subsection: str
    hyperlink: str

    def todict(self):
        result = super().todict()
        result['section'] = self.section
        result['subsection'] = self.subsection
        result['hyperlink'] = self.hyperlink
        return result

    def __eq__(self, other):
        return super().__eq__(other) and \
            self.section == other.section and \
            self.subsection == other.subsection and \
            self.hyperlink == other.hyperlink

    def __init__(self, *args, **kwargs):
        self.doctype = Credoctypes.Standard
        self.section = str(kwargs.pop('section'))
        if 'subsection' in kwargs.keys():
            self.subsection = str(kwargs.pop('subsection'))
        else:
            self.subsection = None
        if 'hyperlink' in kwargs.keys():
            self.hyperlink = str(kwargs.pop('hyperlink'))
        else:
            self.hyperlink = None
        super().__init__(*args, **kwargs)


class MandatoryFieldException(Exception):
    pass


def raise_MandatoryFieldException(msg=''): raise MandatoryFieldException(msg)
