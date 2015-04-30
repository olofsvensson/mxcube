#!/usr/bin/env python
# vim: expandtab:tabstop=4:softtabstop=4:ai:syn=on:bg=dark
# input data model
#input_file : XSDataFile
#res_override : XSDataFloat optional #//cutoffs #completeness_cutoff : XSDataFloat optional #isig_cutoff : XSDataFloat optional
#r_value_cutoff : XSDataFloat optional
#cc_half_cutoff : XSDataFloat optional
#
#data_collection_id : XSDataInteger optional
#detector_max_res : XSDataFloat optional
#low_resolution_limit : XSDataFloat optional

# called this way
# xdsproc.pl -path /data/id23eh2/inhouse/opid232/20100209/mxschool/process -mode before -datacollectID 666783


import sys
import os
from stat import S_IRWXU, S_IXGRP, S_IRGRP, S_IXOTH, S_IROTH, S_IRUSR, S_IWUSR
import os.path
import tempfile
import subprocess
import time
import httplib
import urllib

import logging
from logging.handlers import HTTPHandler
import socket

import traceback


# XDS.INP creation is now asynchronous in mxcube, so it may not be here yet
# when we're started
WAIT_XDS_TIMEOUT = 300
WAIT_XDS_RESOLUTION = 5

def _template_to_image(fmt, num):
    # for simplicity we will assume the template to contain only one
    # sequence of '?' characters. max's code uses a regexp so this
    # further restrict the possible templates.
    start = fmt.find('?')
    end = fmt.rfind('?')
    if start == -1 or end == -1:
        # the caller test for the file existence and an empty path
        # does not exist
        return ''
    prefix = fmt[:start]
    suffix = fmt[end+1:]
    length = end - start + 1

    # this is essentially the python format string equivalent to the
    # template string
    fmt_string = prefix + '{0:0' + str(length) + 'd}' + suffix

    return fmt_string.format(num)

# setup the HTTP log handling
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# log stuff to the remote server if it's defined
def except_hook(exctype, value, tb):
    logging.error('Exception {0}, value {1}, trace: {2}'.format(exctype,
                                                                value,
                                                                '\n'.join(traceback.format_tb(tb))))
sys.excepthook = except_hook

# do the arg parsing by hand since neither getopt nor optparse support
# single dash long options.

args = sys.argv[1:]

if (len(args) % 2) != 0:
    logging.error('the argument list is not well formed (odd number of args/options)')
    sys.exit()

options = dict()
for x in range(0, len(args), 2):
    options[args[x]] = args[x+1]

path = options['-path']
input_file = os.path.join(path, 'XDS.INP')
nres = None
try:
    nres = float(options.get('-residues'))
except Exception:
    pass
spacegroup = options.get('-sg')
cell = options.get('-cell')

# parse the input file to find the first image
xds_appeared = False
wait_xds_start = time.time()
logging.debug('Waiting for XDS.INP file')
while not xds_appeared and (time.time() - wait_xds_start < WAIT_XDS_TIMEOUT):
    time.sleep(1)
    if os.path.exists(input_file) and os.stat(input_file).st_size > 0:
        time.sleep(1)
        xds_appeared = True
        logging.debug('XDS.INP file is there, size={0}'.format(os.stat(input_file).st_size))
if not xds_appeared:
    logging.error('XDS.INP file ({0}) failed to appear after {1} seconds'.format(input_file, WAIT_XDS_TIMEOUT))
    sys.exit(1)


output_file = tempfile.NamedTemporaryFile(suffix='.xml',
                                          prefix='edna-autoproc-results-',
                                          dir=path,
                                          delete=False)
# we only want the filename
output_path = output_file.name
output_file.close()
os.chmod(output_path, S_IRUSR|S_IWUSR|S_IRGRP|S_IROTH)

input_template = '''<?xml version="1.0"?>
<XSDataAutoprocInput>
  <input_file>
    <path>
      <value>{input_file}</value>
    </path>
  </input_file>
  <data_collection_id>
    <value>{dcid}</value>
  </data_collection_id>
  <output_file>
    <path>
      <value>{output_path}</value>
    </path>
  </output_file>
{nres_fragment}
{spacegroup_fragment}
{cell_fragment}
</XSDataAutoprocInput>
'''

#ignore null nres, which might happen for whatever reason
if nres is not None and nres != 0:
    nres_fragment = """  <nres>
    <value>{0}</value>
  </nres>""".format(nres)
else:
    nres_fragment = ""

if spacegroup is not None:
    spacegroup_fragment = """  <spacegroup>
    <value>{0}</value>
  </spacegroup>""".format(spacegroup)
else:
    spacegroup_fragment = ''

if cell is not None:
    cell_fragment = """  <unit_cell>
    <value>{0}</value>
  </unit_cell>""".format(cell)
else:
    cell_fragment = ''

# the other parameters are not used right now
input_dm = input_template.format(input_file=input_file,
                                 dcid=options['-datacollectionID'],
                                 output_path=output_path,
                                 nres_fragment=nres_fragment,
                                 cell_fragment=cell_fragment,
                                 spacegroup_fragment=spacegroup_fragment)

# we now need a temp file in the data dir to write the data model to
dm_file = tempfile.NamedTemporaryFile(suffix='.xml',
                                      prefix='edna-autoproc-input-',
                                      dir=path,
                                      delete=False)
dm_path = dm_file.name
dm_file.file.write(input_dm)
dm_file.close()
os.chmod(dm_path, S_IRUSR|S_IWUSR|S_IRGRP|S_IROTH)

# we also need some kind of script to run edna-plugin-launcher
script_file = tempfile.NamedTemporaryFile(suffix='.sh',
                                          prefix='edna-autoproc-launcher-',
                                          dir=path,
                                          delete=False)
script_template = '''#!/bin/sh
export EDNA_SITE=ESRF_ISPyBTest
export ISPyB_user="opid231"
export ISPyB_pass="tonic231"

cd {path}
/opt/pxsoft/bin/edna-plugin-launcher --inputFile {dm_path} --execute EDPluginControlAutoprocv1_0 
'''

script_file.file.write(script_template.format(path=path, dm_path=dm_path))
script_path = script_file.name
os.chmod(script_path, S_IRWXU|S_IXGRP|S_IRGRP|S_IXOTH|S_IROTH)


BES_HOST = "mxedna.esrf.fr"
BES_PORT = 8080

directories = path.split(os.path.sep)
try:
    if directories[2]=='visitor':
        beamline = directories[4]
        proposal = directories[3]
    else:
        beamline = directories[2]
        proposal = directories[4]
except:
    beamline = "unknown"
    proposal = "unknown" 

conn = httplib.HTTPConnection(BES_HOST, BES_PORT)
params = urllib.urlencode({"ednaDpLaunchPath":os.path.join(path, script_path),
                           "beamline": beamline,
                           "proposal": proposal,
                           "initiator": beamline,
                           "externalRef": proposal,
                           "reuseCase": "true" })
conn.request("POST", 
             "/BES/bridge/rest/processes/EDNA_dp/RUN?%s" % params, 
             headers={"Accept":"text/plain"})
response = conn.getresponse()
if response.status != 200:
    print("ERROR! RUN response status = {0}".format(response.status))



