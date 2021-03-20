CRE Spreadhsheet to Github Sync
===============================

This script can be run either manually or via Github Actions.
The Github Action is run on a cron schedule defined in .github/ .
It syncs the contents of the spreadsheets with links between CREs and other external entities to CRE yaml files on Github.
There is a different Github Action which syncs those Yaml files to a CRE REST API for querying.


Assumptions
-----------
* The URLs of the auto-synced spreadsheets are defined in the ```spreadsheets.txt ``` file. One URL per line.
* All spreadsheets need to follow the template defined by ```CRE_LINK_schema```, the script will ignore any workbooks that do not follow the schema
* Only workbooks whose names start with a number will be synced, this is on purpose to allow pivot tables or other miscelaneous/WiP workbooks.
* You _need_ to share the spreadsheet to be synced with the following email: ```project-integratio-sync-servic@project-integration-standards.iam.gserviceaccount.com``` (this script's service account)
* This script creates Pull Requests, this is important so CRE elements can be manually reviewed.

Running
-------
This script runs automatically, if you want to run it yourself against your own spreadsheet you need the following:
* Setup gspread for you, if you want to run this script as a user you are looking for an OAUTH token, otherwise you need a Service Account: https://gspread.readthedocs.io/en/latest/oauth2.html#enable-api-access
* Setup a github api token with access to your repository: https://github.com/settings/tokens
* From within this repository and with the ability to push to github with an SSH key run:
``` GITHUB_API_KEY="<your github api key>" python ./spreadsheet_to_yaml.py```







TODO: 
add more edge cases in spreadsheet

add tests
    defs ~
    db 2 tests remaining
    parsers ~
    mapping_add
    git_utils
    spreadsheet_utils

add parse from export format

add parse from export format where the root doc is a standard and it links to cres or groups
add parse from spreadsheet with unknown standards (for key,val in items add_standard)

merge spreadsheet to yaml and mapping add, they do the same thing

add git integration in the root script

make library out of ????

add sparse_spreadsheet_export functionality one leve of mapping per row, either everything that maps to standard X or everything that maps to CRE x

add the ability for standards to link other standards, then you can handle assigning CREs yourself  <-- this is what mapping add was supposed to be initially

add the ability for a mapping document to have multiple yamls in it
add dockerfile????
