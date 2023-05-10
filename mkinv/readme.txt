Using make_inventory
====================

This tool takes as input a path to a PDS4 collection and outputs an inventory
file, which contains a list of each product LIDVID in the collection.

make_inventory is a Python script run by the Python interpreter and therefore
requires Python (3.x) to use. Make sure to place the tool somewhere in your
Python PATH.

The basic command for running the script is:

python make_inventory <path to collection>

The input path should either be to the root directory of the collection, or to a
collection file in the root directory of the collection. If the path is to a
collection file, the tool will extract the collection LID from that file to
compare against the LIDs it discovers in the collection. Otherwise it will look
for a LID to serve as the collection LID. If a product's LID does not match the
collection LID, it will be marked as a secondary product ('S') in the inventory
file rather than a primary product ('P').


Optional Parameters
===================

-l <collection LID>     Tool uses this LID instead of one from the collection
                        file.

-f <inventory file>     Sets a custom name for the inventory file. Default is
                        inventory.csv in the collection directory.

-e <xml/lblx>           Finds labels of the given extension. Default is xml.

-v <IM major version>   Used to set the namespace for XML attribute searches.
                        Default is 1, but for future-proofing can be set to 2.

-a                      Include to append LIDVIDs to an already extant
                        inventory file. Be sure to include the -i parameter as
                        well, or this will append all LIDVIDs found rather than
                        only new ones.

-i                      Include to perform integrity checking against the
                        various product LIDs found by this tool.

-d <optional log file>  Include to print some basic debugging info to the
                        console. If a file is included, writes the debugging to
                        a log file instead.

-h, --help              Print this file to the console.


Contact Info
============

For any questions or issues, contact Ben Hirsch of the PDS Small Bodies Node at
bhirsch1@umd.edu.
