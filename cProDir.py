# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse as ap
import getpass
import math
import copy
import git
from datetime import datetime

version = '0.3.1'

### FUNCTIONS

def error(string, error_type=1):
    sys.stderr.write(f'ERROR: {string}\n')
    sys.exit(error_type)

def log(string, newline_before=False):
    if newline_before:
        sys.stderr.write('\n')
    sys.stderr.write(f'LOG: {string}\n')

def write(string, filepath1, filepath2=None):
    with open(filepath1, 'a+') as w:
        w.write(string + '\n')
    w.close()
    if filepath2 is not None:
        with open(filepath2, 'a+') as w:
            w.write(string + '\n')
        w.close()

def linkAllFiles(walkpath, dst, depth=0):
    files = 0
    folders = 1
    foldersize = 0

    # check and edit input path strings
    tab = '|---'
    if dst[-1] != '/' and dst != '':
        dst+='/'
    if walkpath[-1] != '/':
        walkpath+='/'

    # make sure directory exists
    if not os.path.exists(dst):
        os.makedirs(dst)

    # walk files and link them
    entry = next(os.walk(walkpath))
    for linkfile in entry[2]:
        linkdst = dst + linkfile
        os.link(src=walkpath + linkfile, dst=linkdst)

        # write readme and log
        points = '.' * (60-len(f'{tab*depth}|--> {linkdst.split(project_name)[-1]}'))
        filesize = os.path.getsize(linkdst)
        write(f'``{tab*depth}|--> {linkdst.split(project_name)[-1]}{points}{humanbytes(filesize)}``<br>', readmemd)
        log(f'Linked {walkpath + linkfile} to {dst + linkfile}')
        files += 1
        foldersize += filesize

    # walk directories
    for linkdir in entry[1]:
        write(f'``{tab*depth}|--> {dst.split(project_name)[-1]}{linkdir}``<br>', readmemd)
        return tuple(map(sum, zip((files, folders, foldersize), linkAllFiles(walkpath=walkpath + linkdir + '/', dst=dst + linkdir + '/', depth=depth + 1))))

    return (files, folders, foldersize)

# https://stackoverflow.com/questions/12523586/python-format-size-application-converting-b-to-kb-mb-gb-tb
def humanbytes(B):
    '''Return the given bytes as a human friendly KB, MB, GB, or TB string'''
    B = float(B)
    KB = float(1024)
    MB = float(KB ** 2) # 1,048,576
    GB = float(KB ** 3) # 1,073,741,824
    TB = float(KB ** 4) # 1,099,511,627,776

    if B < KB:
        return '{0} {1}'.format(B,'Bytes' if 0 == B > 1 else 'Byte')
    elif KB <= B < MB:
        return '{0:.4f} KB'.format(B/KB)
    elif MB <= B < GB:
        return '{0:.4f} MB'.format(B/MB)
    elif GB <= B < TB:
        return '{0:.4f} GB'.format(B/GB)
    elif TB <= B:
        return '{0:.4f} TB'.format(B/TB)


### PARAMS

parser = ap.ArgumentParser(
    description='Version 0.3 enables you to add your project to a precreated remote git repository - see param -g.\n' +
                'cProDir.py helps you with Creating your PROject DIRectory with good structure for better navigation and reproducibility.',
    formatter_class=ap.HelpFormatter,
    epilog=f'You are currently using version {version}!'
)

# required arguments
projectgroup = parser.add_mutually_exclusive_group(required=True, )
projectgroup.add_argument('-p', '--project', metavar='PROJECT_NAME', default=None, type=str, help='Name of the project you want to create locally.')
projectgroup.add_argument('-g', '--git', metavar='GIT_URL', type=str, default=None, help='Use this argument if you already made an empty repository and want to add your project to the remote repository.')

# optional arguments
parser.add_argument('-d', '--docext', metavar='EXTENSION', default='md', type=str, help='DOCumentation datatype EXTension for your documentation files. Standard is md for markdown.')
parser.add_argument('-l', '--link', metavar='PATH', type=str, default=None, help='Path of the folder of your resources/data.\nThe linked resources or data can be found in ./<project>/res/.')
parser.add_argument('-ml', '--machine_learning', nargs=2, metavar=('TRAINDATA', 'VALDATA'), type=str, default=(None, None), help='Path to traindata and path to validationsdata.\nData gets linked into ./<project>/res/ folder.')
parser.add_argument('-i', '--gitignore', metavar='LIST_FILES', action='append', default=None, help='List of directories or files that should be ignored in git version control.\nOnly possible if -g is used!')

parser.add_argument('-v', '--version', action='version', version=f'\n%(prog)s {version}')

args = parser.parse_args()

### CHECK INPUT
projectInput = {'project': False, 'git': False}

if args.project is not None:
    project_name = args.project
    projectInput['project'] = True

if args.git is not None:
    giturl = args.git
    project_name = giturl.split('/')[-1]
    git_user_name = giturl.split('/')[-2]
    git_service = giturl.split('/')[-3]
    projectInput['git'] = True
    log(f'Using git {giturl} for version control!')
    gitignore = '.gitignore'
    for f in args.gitignore:
        write(f, gitignore)

datalink = args.link
ext = args.docext
trainlink = args.machine_learning[0]
validationslink = args.machine_learning[1]
user = getpass.getuser()
time = datetime.now().strftime("%Y.%m.%d %H:%M:%S")

# create often used variables
cwd = os.getcwd()
pwd = cwd + '/' + project_name + '/'

### CREATE PROJECT DIRECTORY

# creating project working directory 'pwd'
if os.path.exists(pwd):
    error(f'Path {pwd} already exists!\nStopped with error code 1!', 1)

if datalink is not None and not os.path.exists(datalink):
    error(f'Path {datalink} does not exist!\nStopped with error code 2!', 2)

if datalink is not None and (trainlink is not None or validationslink is not None):
    error(f'Cannot use --link and --machine_learning together! Please choose only one of them!', 3)

if args.gitignore is not None and args.git is None:
    error(f'Can use --gitignore only if --git is used!', 4)

if projectInput['git']:
    repo = git.Repo.clone_from(giturl, pwd)

if projectInput['project']:
    os.makedirs(pwd)

readmemd = pwd + 'README.md'
readmesh = pwd + 'README.sh'
log(f'Created project {project_name} directory in {pwd}')

# making directories
readmes = {}
project_dirs = ['src', 'res', 'bin', 'lib', 'doc', 'build', 'out', 'out/plots', 'temp']
for dire in project_dirs:

    # check if path already exists
    if os.path.exists(pwd + dire):
        log(f'Path {pwd+dire} already exists!')    
    else:
        os.makedirs(pwd + dire)
        log(f'Created {pwd + dire}')
    
    # dont create readmes for out/plots and doc
    if dire != 'out/plots' and dire != 'doc':
        readmes[dire] = pwd + dire + '/README.md'
        write(f'Created markdown file for {dire} on {time} from {user}.', readmes[dire])
        log(f'Created {readmes[dire]}')

write(f'res contains the resource data the way you like, either the hard links to your resource data or the actual resource data files.', readmes['res'])


### CREATE PROJECT FILES

# creating documentation file
docfile = pwd + f'doc/{project_name}_protocol.{ext}'
write(f'# Project {project_name}: {ext} documentation file of {project_name}.', docfile)
write(f'{project_name} created by {user} on {time}.', docfile)
command = ''
for arg in sys.argv:
    command += arg
write(f'Used command for creation is:\n{command}', docfile)
log(f'Created {docfile}')

# add files to commit for git
if projectInput['git']:
    files = list(readmes.values())
    files.append(docfile)
    repo.index.add(files)
    repo.index.commit(f'initial commit of {project_name} with cProDir {version}')
    log(f'Added {len(files)} files to git commit.')

# writing major readme file
write(f'# Project {project_name} created on {time} from {user}.', readmemd, readmesh)
write(f'# Created with cProDir version {version}.', readmesh, docfile)

if projectInput['git']:
    write(f'# Using git {giturl} for version control on account {git_user_name} on {git_service}.', readmesh)
    write(f'-    Using git {giturl} for version control on account {git_user_name} on {git_service}.', readmemd)

write(f'-    Created with cProDir version {version}.', readmemd)
write(f'-    Project {project_name} created on {time} from {user}.', readmemd)
write(f'\n# {project_name} directory structure:', readmemd, docfile)
write('-   src: containing project scripts', readmemd, docfile)
write('-   res: containing project resources and data', readmemd, docfile)
write('-   bin: containing project binaries', readmemd, docfile)
write('-   lib: containing external libraries', readmemd, docfile)
write('-   doc: containing project documentation files', readmemd, docfile)
write('-   build: containing project binaries', readmemd, docfile)
write('-   temp: containing temporary files', readmemd, docfile)
write('-   out: containing output files, produced by processing/analyzing resources', readmemd, docfile)
write('-   out/plots: containing output plot files and diagrams', readmemd, docfile)

# if no datalink provided create train and validate data folders
if trainlink is not None or validationslink is not None:
    os.makedirs(pwd + 'res/traindata/')
    log(f'Created {pwd}res/traindata/')
    os.makedirs(pwd + 'res/valdata/')
    log(f'Created {pwd}res/valdata/')
    write('\n# Data to be analyzed:', readmemd, docfile)
    
    if trainlink is not None:
        write(f'Resources/Data linked from<br>\n{os.path.abspath(trainlink)}<br>', readmemd, docfile)
        (files, folders, datasize) = linkAllFiles(walkpath=trainlink, dst=pwd+'res/traindata/')
        log(f'Linked traindata: {files} files in {folders} folders.')
        log(f'Linked traindata of size {humanbytes(datasize)}')
        write(f'Linked traindata: {files} files in {folders} folders with a total datasize of {humanbytes(datasize)}.<br>\n', readmemd, docfile)

    if validationslink is not None:
        write(f'Resources/Data linked from<br>\n{os.path.abspath(validationslink)}<br>', readmemd, docfile)
        (files, folders, datasize) = linkAllFiles(walkpath=validationslink, dst=pwd+'res/valdata/')
        log(f'Linked validationdata: {files} files in {folders} folders.')
        log(f'Linked validationdata of size {humanbytes(datasize)}')
        write(f'Linked validationdata: {files} files in {folders} folders with a total datasize of {humanbytes(datasize)}.<br>\n', readmemd, docfile)

# linking data
elif datalink is not None:
    write('\n# Data to be analyzed:', readmemd)
    write(f'Resources/Data linked from<br>\n{os.path.abspath(datalink)}<br>', readmemd, docfile)
    (files, folders, datasize) = linkAllFiles(walkpath=datalink, dst=pwd+'res/')
    log(f'Linked {files} files in {folders} folders.')
    write(f'Linked {files} files in {folders} folders with a total datasize of {humanbytes(datasize)}.', readmemd, docfile)
    log(f'Linked data of size {humanbytes(datasize)}')
    log('Done linking resources/data.')

# push commits to git remote
if projectInput['git']:
    repo.remote("origin").push()
    log(f'Pushed files to {giturl}.')

log(f'Created {readmemd}, {readmesh} and {docfile}')
log('Done')