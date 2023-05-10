from astropy.io import fits
import sys
import re
import csv
from collections import defaultdict
import os

## Command
## python kwex -f <path to fits file> -k <path to csv file>
##
## Optional Parameters
## ===================
##
## -l <path to lbl file>       Specifies a different name for the PDS3 label file.
##
## -o <path to output file>    Specifies a different name for the output file.
##
## -d                          Prints some minimal debugging to the console.
##							
## -h, --help                  Print this file to the console.

args = sys.argv

#methods

def get_arg(param, else_name='', flag=False, req=False):
    if flag:
        #true if flag is present, false otherwise
        return param in args
    else:
        if param in args:
            try:
                #gets string that appears after parameter
                return args[args.index(param)+1].replace("'", "")
            except:
                report('%s parameter value not found' % param, out=req)
        elif not else_name == '':
            #default parameter if not present
            return else_name
        else:
            report('%s parameter not found' % param, out=req)

def report(msg, out=False):
    if debug or out:
        print(msg)

    if out:
        print('kwex exited without finishing.')
        sys.exit()

def add_to_out(kw, dic=None, file=None, value=None, kw_replace=None):
    if value is None:
        try:
            #actual line that gets the value of a keyword
            value = dic[kw]
        except:
            report('keyword %s not found in %s' % (kw, file))
            value = 'KEYWORD_NOT_FOUND'
    if kw_replace is not None:
        #provides alternate kw for .kwl file when it differs from source
        kw = kw_replace
        if isinstance(value, str):
            #when fits keywords are strings, adds quotes for velocity
            value = '"%s"' % value

    output_list.append('%s = %s' % (kw, value))

def fix_path(path, exist=False):
    if os.path.isabs(path):
        return_path = os.path.normpath(path)
    else:
        return_path = os.path.normpath(os.path.join(os.getcwd(), path))

    if exist and not os.path.isfile(return_path):
        report ('%s not found.' % path, out=True)
    else:
        return return_path

#if help command given, print readme and exit
if get_arg('-h', flag=True) or get_arg('--help', flag=True):
    with open('readme.txt') as f:
        readme = f.read()
        print()
        print(readme)
    sys.exit()

#get command line arguments
debug = get_arg('-d', flag=True)
fits_file = fix_path(get_arg('-f', req=True), exist=True)
kw_file = fix_path(get_arg('-k', req=True), exist=True)
pds3_file = fix_path(get_arg('-l', '%s/%s.lbl' % (os.path.dirname(fits_file), os.path.splitext(os.path.basename(fits_file))[0])), exist = get_arg('-l', flag=True))
out_file = fix_path(get_arg('-o', '%s/%s.kwl' % (os.path.dirname(fits_file), os.path.splitext(os.path.basename(fits_file))[0])))

#get keyword list
with open(kw_file, newline='') as f:
    kw_reader = csv.reader(f, delimiter=',')
    try:
        kw_list = [(kw, kt) for (kw, kt) in kw_reader]
    except ValueError:
        report('invalid format in %s' % kw_file, out=True)

#reports invalid sources in csv file
for n, k in enumerate(kw_list):
    if k[1] not in ['PDS3', 'FITS', 'COMMENT']:
        report('invalid source %s found on line %s of %s' % (k[1], n+1, kw_file))

#creates a dictionary of each keyword source (FITS, PDS3, COMMENT)
#and populates each dictionary with all the keywords that match that source
kw_lists = {ktype:[rw for (rw, rt) in kw_list if rt == ktype] for ktype in set([kt for (kw, kt) in kw_list])}

report('loaded %s keywords from %s' % (len(kw_list), kw_file))

#reports duplicate keywords
for kt in kw_lists:
    for kw in set(kw_lists[kt]):
        if kw_lists[kt].count(kw) > 1:
            report('keyword %s found %s times' % (kw, kw_lists[kt].count(kw)))

output_list = []

#no matter what, assign filename to a keyword
add_to_out('FILENAME', value=os.path.splitext(os.path.basename(fits_file))[0])

#get pds3 keywords
if 'PDS3' in kw_lists.keys() and os.path.isfile(pds3_file):
    klist = []
    with open(pds3_file) as f:
        #split each line into tidy keyword:value pairs
        for line in f:
            #w is None if there's no equal sign or nothing on the other side of it
            k, w = ([p.strip() for p in line.split('=')][:2] + [None]*2)[:2]
            if w is not None:
                klist.append([k, w])
            elif not (k == 'END' or k == ''):
                #when there's no kw=value pair, add the current line to the
                #previous one if it's not empty or the end of the file
                try:
                    klist[-1][1] = ' '.join([klist[-1][1], k])
                except:
                    pass
            
    #identify each object in the label and which lines comprise that object
    obj_dict = defaultdict(lambda: []) #dictionary of object types, where each type will have a list of each instance of that type
    for n, line in enumerate(klist):
        kw, value = line
        if kw == 'OBJECT':
            obj_dict[value].append([]) #every time a new object is found, adds an empty list for this instance of the object
            obj_line_count = n+1
            while obj_line_count < len(klist) and not klist[obj_line_count] == ['END_OBJECT', value]:
                if klist[obj_line_count][0] not in ['OBJECT', 'END_OBJECT']:
                    obj_dict[value][-1].append(obj_line_count) #adds the current line number to the list for this instance of the object type
                obj_line_count += 1
                
    #add object names to keywords
    for obj in obj_dict:
        for n, line in enumerate(obj_dict[obj]):
            for l in line:
                klist[l][0] = '%s_%s.%s' % (obj, n, klist[l][0])

    #reverse object names in keywords to get proper order
    for k in klist:
        ksplit = k[0].split('.')
        if len(ksplit) > 1:
            k[0] = '_'.join(list(reversed(ksplit[:-1]))) + '_' + ksplit[-1]

    #search for requested keywords in pds3 keyword dictionary and add to output list
    for kw in kw_lists['PDS3']:
        add_to_out(kw, {k:v for (k, v) in klist}, pds3_file)
elif 'PDS3' in kw_lists.keys() and not os.path.isfile(pds3_file):
    report('PDS3 keywords found in %s but PDS3 label %s not found.' % (kw_file, pds3_file), out=True)

#search for requested comments in pds3 label and add to output list
if 'COMMENT' in kw_lists.keys() and os.path.isfile(pds3_file):
    kcomm = {}
    kw_found = defaultdict(lambda: False)
    with open(pds3_file) as f:
        for line in f:
            for kw in kw_lists['COMMENT']:
                if kw in line and not kw_found[kw]:
                    kcomm[kw] = line.split('=')[-1].strip()
                    kw_found[kw] = True

    for kw in kw_lists['COMMENT']:
        add_to_out(kw, kcomm, pds3_file)
elif 'COMMENT' in kw_lists.keys() and not os.path.isfile(pds3_file):
    report('PDS3 comments found in %s but PDS3 label %s not found.' % (kw_file, pds3_file), out=True)

#get fits headers
if 'FITS' in kw_lists.keys():
    with fits.open(fits_file) as f:
        hdr_list = [h.header for h in f]

    #search for requested keywords in fits keyword list and add to output list
    kw_loop = defaultdict(lambda: list())
    loop_count = 0

    for kw in kw_lists['FITS']:
        #check if kw is in extension header
        knn = re.sub(r'\d', '', kw)
        if knn.endswith('_EXT'):
            hdr = int(re.search(r'(?<=_EXT).+', kw).group(0))
            k = re.search(r'.+?(?=_EXT)', kw).group(0)
        else:
            #if no explicit extension in keyword, assume primary header
            hdr = 0
            k = kw

        #check for iterative keywords
        if k.endswith('.LOOP'):
            knl = k.replace('.LOOP', '')
            #counts how many FITS keywords with numbers stripped match knl
            loop_match = [[n.isnumeric() for n in kh].count(True) for kh in hdr_list[hdr] if re.sub(r'\d', '', kh) == knl]
            if not loop_match:
                add_to_out(knl, hdr_list[hdr], fits_file)

            loop_count = max([loop_count, len(loop_match)])

            for count, digit in enumerate(loop_match):
                #tracks original digits in kwNN indexing to pull from correctly
                digit_string = '{:0%sd}' % digit
                kw_loop[knl].append('%s%s' % (knl, digit_string.format(count)))
        else:
            add_to_out(k, hdr_list[hdr], fits_file, kw_replace=kw)

    #create output string of PDS3-like objects for any iterative keywords
    for n in range(loop_count):
        add_to_out('OBJECT', value='LOOP')
        for knl in kw_loop:
            #adds kw+nth as keyword value when kwNN doesn't work (because it wasn't found)
            try:
                kloop = kw_loop[knl][n]
            except:
                kloop = '%s%s' % (knl, n)

            add_to_out(kloop, hdr_list[hdr], fits_file, kw_replace='  %s' % knl)
        add_to_out('END_OBJECT', value='LOOP')
        
#output found keyword value pairs to kwl file
report('%s keyword:value pairs plus filename extracted' % (len([k for k in output_list if not 'LOOP' in k])-1))
with open(out_file, 'w') as f:
    q = f.write('\n'.join(output_list) + '\nEND\n')
