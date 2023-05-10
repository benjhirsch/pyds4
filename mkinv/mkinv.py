import xml.etree.ElementTree as et
import csv
import os
import sys
import re

## Command
## python mkinv.py <path to collection>
##
## Optional Parameters
## ===================
## 
## -l <collection LID>     Tool uses this LID instead of one from the collection
##                         file.
## 
## -f <inventory file>     Sets a custom name for the inventory file. Default is
##                         inventory.csv in the collection directory.
##
## -e <xml/lblx>           Finds labels of the given extension. Default is xml.
## 
## -v <IM major version>   Used to set the namespace for XML attribute searches.
##                         Default is 1, but for future-proofing can be set to 2.
## 
## -a                      Include to append new LIDVIDs to an already extant
##                         inventory file. Be sure to include the -i parameter as
##                         well, or this will append all LIDVIDs found rather than
##                         only new ones.
## 
## -i                      Include to perform integrity checking against the
##                         various product LIDs found by this tool.
## 
## -d <optional log file>  Include to print some basic debugging info to the
##                         console. If a file is included, writes the debugging to
##                         a log file instead.
## 
## -h, --help              Print this file to the console.

args = sys.argv

#methods

def file_list(path, ext='', excl=[]):
    fl = []
    for root, _, file in os.walk(path):
        fl.extend([os.path.normpath(os.path.join(root, fn)) for fn in file if fn.endswith(ext) and fn not in excl])
    return fl

def param_check(param, value_error, index_error, dash_error):
    try:
        return_value = args[args.index(param)+1].replace("'", "")
    except ValueError:
        return_value = value_error
    except IndexError:
        return_value = index_error
        
    if isinstance(return_value, str) and return_value.startswith('-'):
        return_value = dash_error
        
    if callable(return_value):
        return_value()
    else:
        return return_value

def get_arg(param, flag=False, default_value=None, opt_param=False):
    if flag and not opt_param:
        #returns true if flag is present in parameter list, false if not
        return param in args
    elif default_value:
        #for parameters that require some string value, returns that value when it's present, returns a default value if not present
        param_value = param_check(param, default_value, lambda: report('%s parameter value not found' % param, out=True), lambda: report('invalid %s parameter' % param, out=True))
        
        return param_value
    elif opt_param:
        #for flag parameters that can optionally take a string value, returns true and that value if it is present, false and nothing if not present
        param_value = param_check(param, False, True, True)
        
        if isinstance(param_value, str):
            return True, param_value
        else:
            return param_value, None
    else:
        report('%s parameter not found' % param, out=True)
        
#if a product LID does not match the collection LID, it's labeled as a secondary product in the inventory
def mem_check(lid):
    if lid.startswith(collection_lid):
        return 'P'
    else:
        return 'S'

def report(msg, out=False, integ=False):
    if (debug and not log_file) or out or integ:
        print(msg)
    if log_file:
        if os.path.isfile(log_file):
            woa = 'a'
        else:
            woa = 'w'
        with open(log_file, woa) as f:
            q = f.write(msg+'\n')

    if out:
        print('mkinv exited without finishing.')
        sys.exit()

#reading in command line arguments
debug, log_file = get_arg('-d', flag=True, opt_param=True)
ns = 'http://pds.nasa.gov/pds4/pds/v%s' % get_arg('-v', default_value='1')
lbl_ext = get_arg('-e', default_value='xml')
inventory_file = get_arg('-f', default_value='inventory.csv')
collection_lid = get_arg('-l', default_value='urn:nasa:pds:bundle_id:collection_id')

#if help command given, print readme and exit
if get_arg('-h', flag=True) or get_arg('--help', flag=True):
    with open('readme.txt') as f:
        readme = f.read()
        print()
        print(readme)
    sys.exit()

#check to make sure at least one argument is given, which should be the collection path
if len(args) > 1:
    collection_fp = args[1]
    if not os.path.isabs(collection_fp):
        #if collection path is relative, get current working directory
        collection_fp = os.path.normpath(os.path.join(os.getcwd(), collection_fp))
else:
    report('No path specified.', out=True)
    

if os.path.isdir(collection_fp):
    #if the path argument is to a directory, check to see if there happens to be a collection file in the usual place.
    collection_path = collection_fp
    test_collection = '%s/collection.%s' % (collection_fp, lbl_ext)
    collection_filename = os.path.basename(test_collection)
    
    report('No collection file specified. Checking for collection LID.')
    if not get_arg('-l', flag=True):
        report('No collection LID specified. Checking for %s' % collection_filename)
        if os.path.isfile(test_collection):
            #if user did not specify a collection LID, pull one from the collection file.
            collection_lid = et.parse(test_collection).getroot().find('.//{%s}logical_identifier' % ns).text
            report('%s pulled from %s' % (collection_lid, collection_filename))
        else:
            #if there is no collection file and no specified collection LID, compare LIDs against a dummy LID.
            report('%s not found. Collection LID not specified. Using %s for collection LID.' % (collection_filename, collection_lid))
            collection_filename = 'N/A'
elif os.path.isfile(collection_fp):
    #if the path argument is to a file, pull the collection LID from that file
    manual_lid = collection_lid
    try:
        collection_lid = et.parse(collection_fp).getroot().find('.//{%s}logical_identifier' % ns).text
    except AttributeError:
        report('Attribute {%s}logical_identifier not found in %s.' % (ns, collection_fp), out=True)
    if get_arg('-l', flag=True) and not (manual_lid == collection_lid):
        #if for some reason the user has pointed to a file and also manually specified a collection lid, use the user-specified one
        report('Overriding extracted "%s" with explicit "%s"' % (collection_lid, manual_lid))
        collection_lid = manual_lid

    collection_path = os.path.dirname(collection_fp)
    collection_filename = os.path.basename(collection_fp)
else:
    report('No valid collection file or directory.', out=True)

#if given inventory and log file names are relative, put them in the collection path.
if not os.path.isabs(inventory_file):
    inventory_file = os.path.normpath(os.path.join(collection_path, inventory_file))

if log_file and not os.path.isabs(log_file):
    log_file = os.path.normpath(os.path.join(collection_path, log_file))

report('collection path: %s' % collection_path)
report('collection lid: %s' % collection_lid)
report('collection filename: %s' % collection_filename)
report('inventory file: %s' % inventory_file)

#crawl through the subdirs in the given path and find all files that match the given label extension
fl = file_list(collection_path, lbl_ext)
if len(fl) == 0:
    report('No label files found with extension %s in any subdirectories of %s' % (lbl_ext, collection_path))
    
inv_list = []

for file in fl:
    #go through each file, but ignore the collection file
    if not os.path.basename(file) == collection_filename:
        #iteratively parse each label rather than loading the entire thing, and stop once LID and VID have been identified
        for _, elem in et.iterparse(file):
            if elem.tag == '{%s}logical_identifier' % ns:
                lid = elem.text
            elif elem.tag == '{%s}version_id' % ns:
                vid = elem.text
                break
        elem.clear()

        inv_list.append({'mem': mem_check(lid), 'lid': lid, 'vid': vid, 'file': file})
        report('LIDVID %s::%s found in %s' % (lid, vid, file))
        
report('%s product LIDVIDs found' % len(inv_list))

#check for extant inventory file if user wants to append
if get_arg('-a', flag=True):
    if os.path.isfile(inventory_file):
        woa = 'a'
    else:
        report('No inventory file to append to.', out=True)
else:
    woa = 'w'

#integrity check looks for duplicate LIDVIDs from those extracted checks to make sure a product hasn't already been added to the inventory if the user is appending
if get_arg('-i', flag=True):
    #create a set of the harvested LIDVIDs to remove duplicates
    lidvid_list = ['%s::%s' % (i['lid'], i['vid']) for i in inv_list]
    lidvid_set = set(lidvid_list)
    new_inv = []

    if woa == 'a':
        #get LIDVIDs from the inventory file if appending
        with open(inventory_file, 'r', newline='') as f:
            csv_list = [lv for mem, lv in csv.reader(f, delimiter=',')]
            
    for lv in sorted(lidvid_set):
        #check for multiple instances of each LIDVID
        lv_count = lidvid_list.count(lv)
        if lv_count > 1:
            report('%s products with LIDVID %s found' % (lv_count, lv), integ=True)
            for i in inv_list:
                if '%s::%s' % (i['lid'], i['vid']) == lv:
                    report('product: %s' % i['file'], integ=True)

        if mem_check(lv) == 'S':
            report('Product LID %s does not match collection LID %s' % (lv, collection_lid))

        if woa == 'a' and lv in csv_list:
            report('LIDVID %s already in %s' % (lv, os.path.basename(inventory_file)), integ=True)
        else:
            #create a new LIDVID list with no duplicates and no already present LIDVIDs
            new_inv.append({'mem': mem_check(lv), 'lid': lv.split('::')[0], 'vid': lv.split('::')[-1]})

    inv_list = new_inv
    report('%s product LIDVIDs added' % len(inv_list))

with open(inventory_file, woa, newline='') as f:
    cw = csv.writer(f)
    for i in inv_list:
        q = cw.writerow([i['mem'], '%s::%s' % (i['lid'], i['vid'])])
