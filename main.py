import subprocess
import os
import networkx as nx
import shutil
import time
import sys
import signal

from Expelliarmus import Expelliarmus
from GuestFSHelper import GuestFSHelper
from Reassembler import Reassembler
from RepositoryDatabase import RepositoryDatabase
from StaticInfo import StaticInfo
from VMIDescription import VMIDescriptor
from CLI import MainInterpreter


def signal_handler_forceexit(signal, frame):
    """
    Signal Handler for CTRL+C
    :param signal:
    :param frame:
    :return:
    """
    print('\nProgram interrupted by CTRL+C.')
    sys.exit(0)

def init(argv):
    signal.signal(signal.SIGINT, signal_handler_forceexit)

    if len(argv) == 2:
        pathToLibGuestFS = argv[1]
        pathSet = True
    else:
        pathSet = False
    libguestfsWorking = False
    while not libguestfsWorking:
        while not pathSet:
            pathToLibGuestFS = raw_input("Please provide path to libguestfs:")
            if len(pathToLibGuestFS)>0:
                pathSet = True
        try:
            subprocess.call([pathToLibGuestFS + "/run", 'virt-customize','--version'], stdout=subprocess.PIPE)
            libguestfsWorking = True
        except OSError as e:
            print "ERROR: no run.sh in \"%s\", please try again." % pathToLibGuestFS
            pathSet = False

    StaticInfo.absPathLibguestfs = pathToLibGuestFS
    StaticInfo.absPathLibguestfsRun = os.path.join(pathToLibGuestFS, "run")

init(sys.argv)
cli = MainInterpreter()
cli.cmdloop()