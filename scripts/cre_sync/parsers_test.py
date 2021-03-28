
import unittest
import cre_defs as defs
from parsers import *
from pprint import pprint
import collections


class TestParsers(unittest.TestCase):

    def test_parse_uknown_key_val_spreadsheet(self):
        # OrderedDict only necessary for testing  so we can predict the root Standard, normally it wouldn't matter
        input = [collections.OrderedDict({'CS': 'Session Management', 'CWE': 598,
                                          'ASVS': 'SESSION-MGT-TOKEN-DIRECTIVES-DISCRETE-HANDLING',
                                          'OPC': '',
                                          'Top10': 'https://owasp.org/www-project-top-ten/2017/A5_2017-Broken_Access_Control',
                                          'WSTG': 'WSTG-SESS-04'}),
                 collections.OrderedDict({'CS': 'Session Management', 'CWE': 384,
                                          'ASVS': 'SESSION-MGT-TOKEN-DIRECTIVES-GENERATION',
                                          'OPC': 'C6',
                                          'Top10': 'https://owasp.org/www-project-top-ten/2017/A5_2017-Broken_Access_Control',
                                          'WSTG': 'WSTG-SESS-03'})]
        expected = {'CS-Session Management': defs.Standard(doctype=defs.Credoctypes.Standard,
                                                           name='CS', links=[defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='CWE', section=598)),
                                                                             defs.Link(document=defs.Standard(
                                                                                 doctype=defs.Credoctypes.Standard, name='ASVS', section='SESSION-MGT-TOKEN-DIRECTIVES-DISCRETE-HANDLING')),
                                                                             defs.Link(document=defs.Standard(
                                                                                 doctype=defs.Credoctypes.Standard, name='Top10', section='https://owasp.org/www-project-top-ten/2017/A5_2017-Broken_Access_Control')),
                                                                             defs.Link(document=defs.Standard(
                                                                                 doctype=defs.Credoctypes.Standard, name='WSTG', section='WSTG-SESS-04'))
                                                                             ], section='Session Management')}
        self.maxDiff = None
        actual = parse_uknown_key_val_spreadsheet(input)
        for key, val in actual.items():
            self.assertEqual(expected[key], val)

    def test_parse_v0_standards(self):
        input = [{'CRE-ID-lookup-from-taxonomy-table': '011-040-026', 'CS': 'Session Management', 'CWE': 598,
                  'Description': 'Verify the application never reveals session tokens in URL parameters or error messages.',
                  'Development guide (does not exist for SessionManagement)': '',
                  'ID-taxonomy-lookup-from-ASVS-mapping': 'SESSION-MGT-TOKEN-DIRECTIVES-DISCRETE-HANDLING',
                  'Item': '3.1.1', 'Name': 'Session', 'OPC': '',
                  'Top10 (lookup)': 'https://owasp.org/www-project-top-ten/2017/A5_2017-Broken_Access_Control',
                  'WSTG': 'WSTG-SESS-04'},
                 {'CRE-ID-lookup-from-taxonomy-table': '011-040-033', 'CS': 'Session Management', 'CWE': 384,
                  'Description': 'Verify the application generates a new session token on user '
                  'authentication.', 'Development guide (does not exist for SessionManagement)': '',
                  'ID-taxonomy-lookup-from-ASVS-mapping': 'SESSION-MGT-TOKEN-DIRECTIVES-GENERATION',
                  'Item': '3.2.1', 'Name': 'Session', 'OPC': 'C6',
                  'Top10 (lookup)': 'https://owasp.org/www-project-top-ten/2017/A5_2017-Broken_Access_Control',
                  'WSTG': 'WSTG-SESS-03'}]
        expected = {'011-040-026': defs.CRE(doctype=defs.Credoctypes.CRE, name='011-040-026',
                                            description='Verify the application never reveals session tokens in URL parameters or error messages.',
                                            links=[
                                                defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='ASVS',
                                                                                 section='SESSION-MGT-TOKEN-DIRECTIVES-DISCRETE-HANDLING', subsection='3.1.1')),
                                                defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='CS',
                                                                                 section='Session Management')),
                                                defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='CWE',
                                                                                 section=598)),
                                                defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='Name',
                                                                                 section='Session')),
                                                defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='Top10 (lookup)',
                                                                                 section='https://owasp.org/www-project-top-ten/2017/A5_2017-Broken_Access_Control')),
                                                defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='WSTG', section='WSTG-SESS-04'))]),
                    '011-040-033': defs.CRE(doctype=defs.Credoctypes.CRE,   name='011-040-033',
                                            description='Verify the application generates a new session token on user authentication.',
                                            links=[
                                                defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard,   name='ASVS',
                                                                                 section='SESSION-MGT-TOKEN-DIRECTIVES-GENERATION', subsection='3.2.1')),
                                                defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='CS',
                                                                                 section='Session Management')),
                                                defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='CWE',
                                                                                 section=384)),
                                                defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='Name',
                                                                                 section='Session')),
                                                defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='OPC',
                                                                                 section='C6')),
                                                defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='Top10 (lookup)',
                                                                                 section='https://owasp.org/www-project-top-ten/2017/A5_2017-Broken_Access_Control')),
                                                defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='WSTG',
                                                                                 section='WSTG-SESS-03'))])}
        self.maxDiff = None
        output = parse_v0_standards(input)
        for key, value in output.items():
            self.assertEqual(expected[key], value)

    def test_parse_v1_standards(self):
        input = [{'ASVS Item': 'V9.9.9', 'ASVS-L1': 'X', 'ASVS-L2': '', 'ASVS-L3': '',
                  'CORE-CRE-ID': '999-999',
                  'CRE Group 1': '', 'CRE Group 1 Lookup': '',
                  'CRE Group 2': '', 'CRE Group 2 Lookup': '',
                  'CRE Group 3': '', 'CRE Group 3 Lookup': '',
                  'CRE Group 4': '', 'CRE Group 4 Lookup': '',
                  'CRE Group 5': '', 'CRE Group 5 Lookup': '',
                  'CRE Group 6': '', 'CRE Group 6 Lookup': '',
                  'CRE Group 7': '', 'CRE Group 7 Lookup': '',
                  'CWE': '',
                  'Cheat Sheet': '',
                  'Core-CRE (high-level description/summary)': 'GROUPLESS',
                  'Description': 'groupless desc',
                  'ID-taxonomy-lookup-from-ASVS-mapping': '',
                  'NIST 800-53 - IS RELATED TO': 'RA-3 RISK ASSESSMENT'},
                 {'ASVS Item': 'V1.1.2', 'ASVS-L1': 'X', 'ASVS-L2': 'X', 'ASVS-L3': 'X', 'CORE-CRE-ID': '000-001',
                 # group 1 maps to 2 cres
                  'CRE Group 1': 'SDLC_GUIDELINES_JUSTIFICATION', 'CRE Group 1 Lookup': '925-827',
                  # group 2 is invalid as it's imissing a lookup
                  'CRE Group 2': '', 'CRE Group 2 Lookup': '',
                  'CRE Group 3': '', 'CRE Group 3 Lookup': '',
                  'CRE Group 4': '', 'CRE Group 4 Lookup': '',
                  'CRE Group 5': '', 'CRE Group 5 Lookup': '',
                  'CRE Group 6': '', 'CRE Group 6 Lookup': '',
                  'CRE Group 7': '', 'CRE Group 7 Lookup': '',
                  'CWE': '0',  # both CREs map to CWE 0
                  # and they both map to the same cheatsheet
                  'Cheat Sheet': 'Architecture, Design and Threat Modeling Requirements',
                  'Core-CRE (high-level description/summary)': 'OTHER_CRE',
                  'Description': 'desc',
                  'ID-taxonomy-lookup-from-ASVS-mapping': 'SDLC_GUIDELINES_JUSTIFICATION-REQUIREMENTS-RISK_ANALYSIS-THREAT_MODEL',
                  'NIST 800-53 - IS RELATED TO': 'RA-3 RISK ASSESSMENT\n'},
                 {'ASVS Item': 'V1.1.1', 'ASVS-L1': '', 'ASVS-L2': 'X', 'ASVS-L3': 'X', 'CORE-CRE-ID': '002-036',
                  'CRE Group 1': 'SDLC_GUIDELINES_JUSTIFICATION', 'CRE Group 1 Lookup': '925-827',
                  'CRE Group 2': 'REQUIREMENTS', 'CRE Group 2 Lookup': '654-390',
                  'CRE Group 3': 'RISK_ANALYSIS', 'CRE Group 3 Lookup': '533-658',
                  'CRE Group 4': 'THREAT_MODEL', 'CRE Group 4 Lookup': '635-846',
                  'CRE Group 5': '', 'CRE Group 5 Lookup': '',
                  'CRE Group 6': '', 'CRE Group 6 Lookup': '',
                  'CRE Group 7': '', 'CRE Group 7 Lookup': '',
                  'CWE': '0', 'Cheat Sheet': 'Architecture, Design and Threat Modeling Requirements',
                  'Core-CRE (high-level description/summary)': 'SDLC_APPLY_CONSISTENTLY',
                  'Description': 'Verify the use of a secure software development lifecycle that addresses security in all stages of development. (C1)',
                  'ID-taxonomy-lookup-from-ASVS-mapping': 'SDLC_GUIDELINES_JUSTIFICATION-REQUIREMENTS-RISK_ANALYSIS-THREAT_MODEL',
                  'NIST 800-53 - IS RELATED TO': 'RA-3 RISK ASSESSMENT\nPL-8 SECURITY AND PRIVACY ARCHITECTURES',
                  'NIST 800-63': 'None', 'OPC': 'C1', 'SIG ISO 25010': '@SDLC', 'Top10 2017': '', 'WSTG': '',
                  'cheat_sheets': 'https: // cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html, https: // cheatsheetseries.owasp.org/cheatsheets/Abuse_Case_Cheat_Sheet.html, https: // cheatsheetseries.owasp.org/cheatsheets/Attack_Surface_Analysis_Cheat_Sheet.html'}]

        groupless = {'GROUPLESS': defs.CRE(
            doctype=defs.Credoctypes.CRE, id='999-999', description='groupless desc', name='GROUPLESS',links=[
              defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='NIST 800-53', tags='is related to', section='RA-3 RISK ASSESSMENT'))])}
        expected = {'REQUIREMENTS': defs.CRE(doctype=defs.Credoctypes.CRE, id='654-390', name='REQUIREMENTS',
                                             links=[
                                                 defs.Link(document=defs.CRE(doctype=defs.Credoctypes.CRE, id='002-036', description='Verify the use of a secure software development lifecycle that addresses security in all stages of development. (C1)', name='SDLC_APPLY_CONSISTENTLY',
                                                                             links=[
                                                                                 defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='ASVS', tags=[
                                                                                     'L2', 'L3'], section='V1.1.1', subsection='SDLC_GUIDELINES_JUSTIFICATION-REQUIREMENTS-RISK_ANALYSIS-THREAT_MODEL')),
                                                                                 defs.Link(document=defs.Standard(
                                                                                     doctype=defs.Credoctypes.Standard, name='CWE', section='0')),
                                                                                 defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='Cheatsheet', section='Architecture, Design and Threat Modeling Requirements',
                                                                                                                  hyperlink='https: // cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html, https: // cheatsheetseries.owasp.org/cheatsheets/Abuse_Case_Cheat_Sheet.html, https: // cheatsheetseries.owasp.org/cheatsheets/Attack_Surface_Analysis_Cheat_Sheet.html')),
                                                                                 defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='NIST 800-53', links=[
                                                                                 ], tags='is related to', section='RA-3 RISK ASSESSMENT')),
                                                                                 defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='NIST 800-53', links=[
                                                                                 ], tags='is related to', section='PL-8 SECURITY AND PRIVACY ARCHITECTURES')),
                                                                                 defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='OPC', links=[
                                                                                 ], section='C1')),
                                                                                 defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='SIG ISO 25010', section='@SDLC'))],
                                                                             ))], ),
                    'RISK_ANALYSIS': defs.CRE(doctype=defs.Credoctypes.CRE, id='533-658', name='RISK_ANALYSIS',
                                              links=[
                                                  defs.Link(document=defs.CRE(doctype=defs.Credoctypes.CRE, id='002-036', description='Verify the use of a secure software development lifecycle that addresses security in all stages of development. (C1)', name='SDLC_APPLY_CONSISTENTLY',
                                                                               links=[
                                                                                   defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='ASVS', tags=[
                                                                                       'L2', 'L3'], section='V1.1.1', subsection='SDLC_GUIDELINES_JUSTIFICATION-REQUIREMENTS-RISK_ANALYSIS-THREAT_MODEL')),
                                                                                   defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='CWE', links=[
                                                                                   ], section='0')),
                                                                                   defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='Cheatsheet', section='Architecture, Design and Threat Modeling Requirements',
                                                                                                                    hyperlink='https: // cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html, https: // cheatsheetseries.owasp.org/cheatsheets/Abuse_Case_Cheat_Sheet.html, https: // cheatsheetseries.owasp.org/cheatsheets/Attack_Surface_Analysis_Cheat_Sheet.html')),
                                                                                   defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='NIST 800-53', links=[
                                                                                   ], tags='is related to', section='RA-3 RISK ASSESSMENT')),
                                                                                   defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='NIST 800-53', links=[
                                                                                   ], tags='is related to', section='PL-8 SECURITY AND PRIVACY ARCHITECTURES')),
                                                                                   defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='OPC', links=[
                                                                                   ], section='C1')),
                                                                                   defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='SIG ISO 25010', section='@SDLC'))],
                                                                              ))], ),
                    'SDLC_GUIDELINES_JUSTIFICATION': defs.CRE(doctype=defs.Credoctypes.CRE, id='925-827', name='SDLC_GUIDELINES_JUSTIFICATION',
                                                              links=[
                                                                  defs.Link(document=defs.CRE(doctype=defs.Credoctypes.CRE, id='000-001', description='desc', name='OTHER_CRE',
                                                                                              links=[
                                                                                                  defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='ASVS', tags=[
                                                                                                            'L1', 'L2', 'L3'], section='V1.1.2', subsection='SDLC_GUIDELINES_JUSTIFICATION-REQUIREMENTS-RISK_ANALYSIS-THREAT_MODEL')),
                                                                                                  defs.Link(document=defs.Standard(
                                                                                                      doctype=defs.Credoctypes.Standard, name='CWE', section='0')),
                                                                                                  defs.Link(document=defs.Standard(
                                                                                                      doctype=defs.Credoctypes.Standard, name='NIST 800-53', tags='is related to', section='RA-3 RISK ASSESSMENT')),
                                                                                              ])),
                                                                  defs.Link(document=defs.CRE(doctype=defs.Credoctypes.CRE, id='002-036', description='Verify the use of a secure software development lifecycle that addresses security in all stages of development. (C1)', name='SDLC_APPLY_CONSISTENTLY',
                                                                                              links=[
                                                                                                  defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='ASVS', tags=[
                                                                                                            'L2', 'L3'], section='V1.1.1', subsection='SDLC_GUIDELINES_JUSTIFICATION-REQUIREMENTS-RISK_ANALYSIS-THREAT_MODEL')),
                                                                                                  defs.Link(document=defs.Standard(
                                                                                                      doctype=defs.Credoctypes.Standard, name='CWE', section='0')),
                                                                                                  defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='Cheatsheet', section='Architecture, Design and Threat Modeling Requirements',
                                                                                                            hyperlink='https: // cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html, https: // cheatsheetseries.owasp.org/cheatsheets/Abuse_Case_Cheat_Sheet.html, https: // cheatsheetseries.owasp.org/cheatsheets/Attack_Surface_Analysis_Cheat_Sheet.html')),
                                                                                                  defs.Link(document=defs.Standard(
                                                                                                      doctype=defs.Credoctypes.Standard, name='NIST 800-53', tags='is related to', section='RA-3 RISK ASSESSMENT')),
                                                                                                  defs.Link(document=defs.Standard(
                                                                                                      doctype=defs.Credoctypes.Standard, name='NIST 800-53', tags='is related to', section='PL-8 SECURITY AND PRIVACY ARCHITECTURES')),
                                                                                                  defs.Link(document=defs.Standard(
                                                                                                      doctype=defs.Credoctypes.Standard, name='OPC', section='C1')),
                                                                                                  defs.Link(document=defs.Standard(
                                                                                                      doctype=defs.Credoctypes.Standard, name='SIG ISO 25010', section='@SDLC'))
                                                                                              ], ))
                                                              ], ),
                    'THREAT_MODEL': defs.CRE(doctype=defs.Credoctypes.CRE, id='635-846', name='THREAT_MODEL',
                                             links=[
                                                 defs.Link(document=defs.CRE(doctype=defs.Credoctypes.CRE, id='002-036', description='Verify the use of a secure software development lifecycle that addresses security in all stages of development. (C1)', name='SDLC_APPLY_CONSISTENTLY',
                                                                              links=[
                                                                                  defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='ASVS', tags=[
                                                                                      'L2', 'L3'], section='V1.1.1', subsection='SDLC_GUIDELINES_JUSTIFICATION-REQUIREMENTS-RISK_ANALYSIS-THREAT_MODEL')),
                                                                                  defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard,
                                                                                                                   name='CWE', section='0')),
                                                                                  defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='Cheatsheet', section='Architecture, Design and Threat Modeling Requirements',
                                                                                                                   hyperlink='https: // cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html, https: // cheatsheetseries.owasp.org/cheatsheets/Abuse_Case_Cheat_Sheet.html, https: // cheatsheetseries.owasp.org/cheatsheets/Attack_Surface_Analysis_Cheat_Sheet.html')),
                                                                                  defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard,
                                                                                                                   name='NIST 800-53', tags='is related to', section='RA-3 RISK ASSESSMENT')),
                                                                                  defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='NIST 800-53', links=[
                                                                                  ], tags='is related to', section='PL-8 SECURITY AND PRIVACY ARCHITECTURES')),
                                                                                  defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard,
                                                                                                                   name='OPC', section='C1')),
                                                                                  defs.Link(document=defs.Standard(doctype=defs.Credoctypes.Standard, name='SIG ISO 25010', section='@SDLC'))],
                                                                             ))], )}

        self.maxDiff = None
        output = parse_v1_standards(input)
        for key, value in output[0].items():
            self.assertEqual(expected[key], value)
        for key, value in output[1].items():
            self.assertEqual(groupless[key], value)


if __name__ == '__main__':
    unittest.main()
