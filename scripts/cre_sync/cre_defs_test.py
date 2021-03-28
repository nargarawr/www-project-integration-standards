
import unittest
import cre_defs as defs
from parsers import *
from pprint import pprint


class TestCreDefs(unittest.TestCase):

    def test_document_to_dict(self):
        standard = defs.Standard( doctype=defs.Credoctypes.Standard, name='ASVS',
                                 section='SESSION-MGT-TOKEN-DIRECTIVES-DISCRETE-HANDLING', subsection='3.1.1')
        standard_output = {'description': '','doctype': 'Standard','hyperlink': None,'id': '','links': [],'metadata': {},'name': 'ASVS','section': 'SESSION-MGT-TOKEN-DIRECTIVES-DISCRETE-HANDLING','subsection': '3.1.1',
        'tags': []}

        cre = defs.CRE(
             id="100", description="CREdesc", name="CREname", links=[standard], tags=['CREt1', 'CREt2'], metadata=defs.Metadata(labels=['CREl1', 'CREl2']))
        cre_output = {'description': 'CREdesc','doctype': 'CRE','id': '100',
                      'links': [
                          {'description': '','doctype': 'Standard','hyperlink': None,'id': '','links': [],'metadata': {},'name': 'ASVS','section': 'SESSION-MGT-TOKEN-DIRECTIVES-DISCRETE-HANDLING','subsection': '3.1.1','tags': []}],
                      'metadata': {}, 'name': 'CREname', 'tags': ['CREt1', 'CREt2']}

        standard2 = defs.Standard( doctype=defs.Credoctypes.Standard, name='Standard',
                                  section='StandardSection', subsection='3.1.1')
        group = defs.CreGroup(id="500", description="desc", name="name", links=[cre, standard2], tags=['tag1', 't2'],
                              metadata=defs.Metadata(labels=['l1', 'l2']))
        group_output = {'description': 'desc', 'doctype': 'Group', 'id': '500', 
                        'links': [
                                  {'description': 'CREdesc', 'doctype': 'CRE', 'id': '100', 
                                   'links': [
                                            {'description': '', 'doctype': 'Standard', 'hyperlink': None, 'id': '', 'links': [], 'metadata': {}, 'name': 'ASVS', 'section': 'SESSION-MGT-TOKEN-DIRECTIVES-DISCRETE-HANDLING', 'subsection': '3.1.1', 'tags': []}],
                                   'metadata': {}, 'name': 'CREname', 'tags': ['CREt1', 'CREt2'], },
                                  {'description': '', 'doctype': 'Standard', 'hyperlink': None, 'id': '', 'links': [], 'metadata': {}, 'name': 'Standard', 'section': 'StandardSection', 'subsection': '3.1.1', 'tags': []}],
                        'metadata': {},
                        'name': 'name',
                        'tags': ['tag1', 't2']}

        self.assertEqual(standard.todict(),standard_output)
        self.assertEqual(cre.todict(),cre_output)
        self.assertEqual(group.todict(),group_output)

if __name__ == '__main__':
    unittest.main()
