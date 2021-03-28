from pprint import pprint
from dataclasses import dataclass
from enum import Enum
import json
# used for serialising and deserialising yaml CRE documents

class Credoctypes(Enum):
    CRE = "CRE"
    Standard = "Standard"

@dataclass
class Metadata():
    labels: list

    def __init__(self, labels=[]):
        self.labels = labels

    def todict(self):
        return json.dump(self.labels)


@dataclass
class Document():
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
            self.doctype.value == other.doctype.value and \
            self.description == other.description and \
            self.links == other.links and \
            self.tags == other.tags and \
            self.metadata == other.metadata

    def todict(self):
        result = {
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

    def __init__(self, name, doctype=None, id="", description="", links=[], tags=[], metadata: Metadata = Metadata()):
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
