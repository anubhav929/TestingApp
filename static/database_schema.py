import os
import sys
import copy
import subprocess


"""
SETTING VARIABLES
"""
WEB2PY_PATH = "/home/web2py"
if not 'WEB2PY_PATH' in os.environ:
    os.environ['WEB2PY_PATH'] = WEB2PY_PATH

NEW_APP = "new_databasemigrationTest"
OLD_APP = "old_databasemigrationTest"
NEW_PATH = "%s/applications/%s" % (WEB2PY_PATH, NEW_APP)
OLD_PATH = "%s/applications/%s" % (WEB2PY_PATH, OLD_APP)


"""
WE ARE LOADING THE 2 ENVIRONMENTS WITH ALL THERE MODELS
"""

os.chdir(os.environ['WEB2PY_PATH'])
sys.path.append(os.environ['WEB2PY_PATH'])

from gluon.custom_import import custom_import_install
custom_import_install(os.environ['WEB2PY_PATH'])
from gluon.shell import env
from gluon import DAL, Field

new_database_folder = "%s/databases" % (NEW_PATH)
new_env = env(NEW_APP, c=None, import_models=True)
database_string = "sqlite://storage.sqlite"
new_db = DAL( database_string, folder = new_database_folder,
 auto_import = True, migrate = False ,fake_migrate = True)

old_database_folder = "%s/databases" % (OLD_PATH)
old_env = env(OLD_APP, c=None, import_models=True)
old_db = DAL( database_string, folder = old_database_folder,\
 auto_import=True, migrate = False ,fake_migrate = True)

"""
this is specific to eden thus commented
"""
#subprocess.call("python web2py.py -S %s -M -R applications/eden2/static/scripts/tools/noop.py" % (NEW_APP),shell=True)
#subprocess.call("python web2py.py -S %s -M -R applications/eden2/static/scripts/tools/noop.py" % (OLD_APP),shell=True)

"""
*****************************************************

Gets The Table and fileds and their constraints which are
stored the above dict . It gets the following properties of the fields
1.not null
2.unique
3.length
4.type
5.foreign key constarints

******************************************************
"""
old_database = {}
new_database = {}
database = {}  #buffer

def GetTablesAndFields(db):
    tables = db.tables
    for table in tables:
        database[table] = {}
        database[table]['id'] = str(db[table]['_id']).split('.')[-1]
        fields = db[table]['_fields']
        for field in fields:
            database[table]['field_'+field]= {}
            database[table]['field_'+field]['type'] = db[table][field].type
            database[table]['field_'+field]['notnull'] = db[table][field].notnull
            database[table]['field_'+field]['unique'] = db[table][field].unique
            database[table]['field_'+field]['length'] = db[table][field].length
        for table in database.keys():
            database[table]['refrences'] = []
            database[table]['referenced_by'] = []

def GetForiegnKey(db):
    tables = db.tables
    for table in tables:
        database[table]['referenced_by'] = db[table]['_referenced_by'] #needed for ondelete action
        tables_referenced = db[table]['_referenced_by']
        for table_referenced in tables_referenced:
            database[table_referenced[0]]['refrences'].append(str(table))   

traversed = []


GetTablesAndFields(old_db)
GetForiegnKey(old_db)
old_database = copy.deepcopy(database)

database = {}

GetTablesAndFields(new_db)
GetForiegnKey(new_db)
new_database = copy.deepcopy(database)

"""
Get the topological order in traversed
"""
def intersect(a, b):
    return list(set(a) & set(b))

def union(a, b):
    return list(set(a) | set(b))

def TopoSort():
    while len(set(traversed)) != len(union(old_database.keys(),new_database)):
        for table in old_database.keys():
            if table not in traversed and len(intersect(old_database[table]['referenced_by'],traversed)) == 0:
                traversed.append(table)
        for table in new_database.keys():
            if table not in traversed and len(intersect(new_database[table]['referenced_by'],traversed)) == 0:
                traversed.append(table)

TopoSort()
#print traversed
print "TOPO Order = ",traversed

"""
CHANGES SCIPT
"""

change = {}

change["appeared"] = []
change["disappeared"] = []
TablesDisappeared = []
TablesAppeared = []

"""
DETECTING THE CHANGE IN TABLES , RENAMING , ADDING OR DELETING FIELDS
"""
for table in traversed:
    old_field = []
    change[table] = {}
    change[table]["appeared"] = []
    change[table]["disappeared"] = []
    if table in old_database.keys():
        for field in old_database[table].keys():
            if field.find("field_") >= 0:
                old_field.append(field)
        if table in new_database.keys():
            for field in new_database[table].keys():
                if field.find("field_") < 0:
                    continue
                else:
                    if field not in old_field:
                        change[table]["appeared"].append(field)
                    else:
                        old_field.remove(field)
            change[table]["disappeared"].extend(old_field)
        else: 
            TablesDisappeared.append(table)
    else:
        TablesAppeared.append(table)
        

"""
GENERATING REPORTS OF THE CHANGES
"""



print "\nTables Appeared =",TablesAppeared
print "\nTables Disappeared =",TablesDisappeared

for table in traversed:
	if len(change[table]["appeared"]) > 0:
		print "table =", table , "changes appeared = ",change[table]["appeared"] 
	if len(change[table]["disappeared"]) > 0:
		print "table =", table , "changes disappeared = ",change[table]["disappeared"]
