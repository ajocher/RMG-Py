#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
#                                                                             #
# RMG - Reaction Mechanism Generator                                          #
#                                                                             #
# Copyright (c) 2002-2018 Prof. William H. Green (whgreen@mit.edu),           #
# Prof. Richard H. West (r.west@neu.edu) and the RMG Team (rmg_dev@mit.edu)   #
#                                                                             #
# Permission is hereby granted, free of charge, to any person obtaining a     #
# copy of this software and associated documentation files (the 'Software'),  #
# to deal in the Software without restriction, including without limitation   #
# the rights to use, copy, modify, merge, publish, distribute, sublicense,    #
# and/or sell copies of the Software, and to permit persons to whom the       #
# Software is furnished to do so, subject to the following conditions:        #
#                                                                             #
# The above copyright notice and this permission notice shall be included in  #
# all copies or substantial portions of the Software.                         #
#                                                                             #
# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR  #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,    #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER      #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING     #
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER         #
# DEALINGS IN THE SOFTWARE.                                                   #
#                                                                             #
###############################################################################

"""
This module contains utilities related to compilation and code maintenance.
"""

import argparse
import os
import platform
import re
import subprocess


def check_dependencies():
    """
    Checks for and locates major dependencies that RMG requires.
    """
    missing = False

    print '\nChecking vital dependencies...\n'
    print '{0:<15}{1:<15}{2}'.format('Package', 'Version', 'Location')

    # Check for symmetry
    try:
        result = subprocess.check_output('symmetry -h', stderr=subprocess.STDOUT, shell=True)
    except subprocess.CalledProcessError:
        print '{0:<30}{1}'.format('symmetry', 'Not found. Please install in order to use QM.')
        missing = True
    else:
        match = re.search(r'\$Revision: (\S*) \$', result)
        version = match.group(1)
        if platform.system() == 'Windows':
            location = subprocess.check_output('where symmetry', shell=True)
        else:
            location = subprocess.check_output('which symmetry', shell=True)

        print '{0:<15}{1:<15}{2}'.format('symmetry', version, location.strip())

    # Check for RDKit
    try:
        import rdkit
        from rdkit import Chem
    except ImportError:
        print '{0:<30}{1}'.format('RDKit',
                                  'Not found. Please install RDKit version 2015.03.1 or later with InChI support.')
        missing = True
    else:
        try:
            version = rdkit.__version__
        except AttributeError:
            version = False
        location = rdkit.__file__
        inchi = Chem.inchi.INCHI_AVAILABLE

        if version:
            print '{0:<15}{1:<15}{2}'.format('RDKit', version, location)
            if not inchi:
                print 'RDKit installed without InChI Support. Please install with InChI.'
                missing = True
        else:
            print 'RDKit version out of date, please install RDKit version 2015.03.1 or later with InChI support.'
            missing = True

    # Check for OpenBabel
    try:
        import openbabel
    except ImportError:
        print '{0:<30}{1}'.format('OpenBabel',
                                  'Not found. Necessary for SMILES/InChI functionality for nitrogen compounds.')
        missing = True
    else:
        location = openbabel.__file__
        print '{0:<30}{1}'.format('OpenBabel', location)

    # Check for lpsolve
    try:
        import lpsolve55
    except ImportError:
        print '{0:<30}{1}'.format('lpsolve55',
                                  'Not found. Necessary for generating Clar structures for aromatic species.')
        missing = True
    else:
        location = lpsolve55.__file__
        print '{0:<30}{1}'.format('lpsolve55', location)

    # Check for pyrdl
    try:
        import py_rdl
    except ImportError:
        print '{0:<30}{1}'.format('pyrdl', 'Not found. Necessary for ring perception algorithms.')
        missing = True
    else:
        location = py_rdl.__file__
        print '{0:<30}{1}'.format('pyrdl', location)

    if missing:
        print """
There are missing dependencies as listed above. Please install them before proceeding.

Using Anaconda, these dependencies can be individually installed from the RMG channel as follows:

    conda install -c rmg [package name]

You can alternatively update your environment and install all missing dependencies as follows:

    conda env update -f environment_[linux/mac/windows].yml  # Choose the correct file for your OS

Be sure to activate your conda environment (rmg_env by default) before installing or updating.
"""
    else:
        print """
Everything was found :)
"""


def clean(subdirectory=''):
    """
    Removes files generated during compilation.

    For *nix systems, remove `.so` files and `.pyc` files.
    For Windows, remove `.pyd` files and `.pyc` files.
    """
    if platform.system() == 'Windows':
        extensions = ['.pyd', '.pyc']
    else:
        extensions = ['.so', '.pyc']

    directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), subdirectory)

    for root, dirs, files in os.walk(directory):
        for f in files:
            ext = os.path.splitext(f)[1]
            if ext in extensions:
                os.remove(os.path.join(root, f))


def update_headers():
    """
    Automatically update the headers for *.py, *.pyx, and *.pxd files
    in RMG-Py/rmgpy, RMG-Py/scripts, and the root RMG-Py directory.

    Other directories (e.g., examples, documentation, etc.) are ignored
    along with directories containing test data.

    The headers are automatically generated based on the LICENSE.txt file.
    Typical usage would involve running this script after updating the
    copyright date in the license file.

    Because this script makes assumptions regarding the contents at the
    start of each file, be sure to double-check the results to make sure
    important lines aren't accidentally overwritten.
    """
    shebang = """#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

    header = """###############################################################################
#                                                                             #
# RMG - Reaction Mechanism Generator                                          #
#                                                                             #
"""

    with open('LICENSE.txt', 'r') as f:
        for line in f:
            line = line.strip()
            newline = '# {0:<75} #\n'.format(line)
            header += newline

    header += """#                                                                             #
###############################################################################
"""

    print header

    def replace_header(oldfile):
        newfile = os.path.join('tmp', 'tempfile')

        ext = os.path.splitext(oldfile)[1]
        if ext == '.py':
            py_file = True
        elif ext == '.pyx' or ext == '.pxd':
            py_file = False
        else:
            raise Exception('Unexpected file type: {0}'.format(oldfile))

        with open(oldfile, 'r') as old, open(newfile, 'w+') as new:

            # Write shebang and encoding for python files only
            if py_file:
                new.write(shebang)

            # Read old file and copy over contents
            found_bar = False
            first_line = True
            start = False
            for i, line in enumerate(old):
                if i == 0 and line[0] != '#':
                    # Assume there's no header, so start copying lines right away
                    new.write(header)
                    start = True
                if start:
                    if first_line and line.strip() != '':
                        new.write('\n')
                    first_line = False
                    new.write(line)
                elif line.startswith('# cython:'):
                    # Copy over any cython directives
                    new.write(line)
                    new.write('\n')
                elif line.startswith('##########'):
                    if found_bar:
                        # We've reached the end of the license, so start copying lines starting with the next line
                        new.write(header)
                        start = True
                    else:
                        found_bar = True

        # Replace old file with new file
        os.rename(newfile, oldfile)

    # Create temporary directory for writing files
    if not os.path.exists('tmp'):
        os.makedirs('tmp')

    # Compile list of files to modify
    filelist = ['rmg.py', 'cantherm.py', 'setup.py']

    root_dirs = ['rmgpy', 'scripts']
    for root_dir in root_dirs:
        for root, dirs, files in os.walk(root_dir):
            if 'test_data' in root or 'files' in root or '/tools/data' in root or '/cantherm/data' in root:
                continue
            print root
            for f in files:
                ext = os.path.splitext(f)[1]
                if ext in ['.py', '.pyx', '.pxd']:
                    filelist.append(os.path.join(root, f))

    for f in filelist:
        print 'Updating {0} ...'.format(f)
        replace_header(f)

    # Remove temporary directory
    os.rmdir('tmp')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='RMG Code Utilities')

    parser.add_argument('command', metavar='COMMAND', type=str,
                        choices=['check-dependencies', 'clean', 'clean-solver', 'update-headers'],
                        help='command to execute')

    args = parser.parse_args()

    if args.command == 'check-dependencies':
        check_dependencies()
    elif args.command == 'clean':
        clean()
    elif args.command == 'clean-solver':
        clean('rmgpy/solver')
    elif args.command == 'update-headers':
        update_headers()
