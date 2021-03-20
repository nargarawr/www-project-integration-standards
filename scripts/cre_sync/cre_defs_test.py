
import unittest
import cre_defs as defs
from parsers import *
from pprint import pprint


class TestCreDefs(unittest.TestCase):

    def test_document_to_dict(self):
        standard = defs.Standard(version=defs.CreVersions.V0, doctype=defs.Credoctypes.Standard, name='ASVS',
                                 section='SESSION-MGT-TOKEN-DIRECTIVES-DISCRETE-HANDLING', subsection='3.1.1')
        standard_output = {'description': '','doctype': 'Standard','hyperlink': None,'id': '','links': [],'metadata': {},'name': 'ASVS','section': 'SESSION-MGT-TOKEN-DIRECTIVES-DISCRETE-HANDLING','subsection': '3.1.1','tags': [],'version': 0}

        cre = defs.CRE(
            version=CreVersions.V0, id="100", description="CREdesc", name="CREname", links=[standard], tags=['CREt1', 'CREt2'], metadata=defs.Metadata(labels=['CREl1', 'CREl2']))
        cre_output = {'description': 'CREdesc','doctype': 'CRE','id': '100',
                      'links': [
                          {'description': '','doctype': 'Standard','hyperlink': None,'id': '','links': [],'metadata': {},'name': 'ASVS','section': 'SESSION-MGT-TOKEN-DIRECTIVES-DISCRETE-HANDLING','subsection': '3.1.1','tags': [],'version': 0}],
                      'metadata': {}, 'name': 'CREname', 'tags': ['CREt1', 'CREt2'], 'version': 0}

        standard2 = defs.Standard(version=defs.CreVersions.V1, doctype=defs.Credoctypes.Standard, name='Standard',
                                  section='StandardSection', subsection='3.1.1')
        group = defs.CreGroup(version=CreVersions.V0, id="500", description="desc", name="name", links=[cre, standard2], tags=['tag1', 't2'],
                              metadata=defs.Metadata(labels=['l1', 'l2']))
        group_output = {'description': 'desc', 'doctype': 'Group', 'id': '500', 
                        'links': [
                                  {'description': 'CREdesc', 'doctype': 'CRE', 'id': '100', 
                                   'links': [
                                            {'description': '', 'doctype': 'Standard', 'hyperlink': None, 'id': '', 'links': [], 'metadata': {}, 'name': 'ASVS', 'section': 'SESSION-MGT-TOKEN-DIRECTIVES-DISCRETE-HANDLING', 'subsection': '3.1.1', 'tags': [], 'version': 0}],
                                   'metadata': {}, 'name': 'CREname', 'tags': ['CREt1', 'CREt2'], 'version': 0},
                                  {'description': '', 'doctype': 'Standard', 'hyperlink': None, 'id': '', 'links': [], 'metadata': {}, 'name': 'Standard', 'section': 'StandardSection', 'subsection': '3.1.1', 'tags': [], 'version': 1}],
                        'metadata': {},
                        'name': 'name',
                        'tags': ['tag1', 't2'],
                        'version': 0}

        self.assertEqual(standard.todict(),standard_output)
        self.assertEqual(cre.todict(),cre_output)
        self.assertEqual(group.todict(),group_output)

if __name__ == '__main__':
    unittest.main()
