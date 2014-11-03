#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Import system libs
import os
import re
import sys
import argparse
import logging
from logging.handlers import RotatingFileHandler
import subprocess

try:
    import simplejson as json
except ImportError:
    import json

# PY3?
is_py3 = sys.version_info >= (3, 3)

script = os.path.basename(sys.argv[0])
scriptname = os.path.splitext(script)[0]
DEFAULT_LOG = "/var/log/" + scriptname
LOG = logging.getLogger(scriptname)

RET_OK           = 0
RET_FAILED       = 1
RET_INVALID_ARGS = 2

def error_exit(msg, status=1):
    LOG.error('%s\n' % msg)
    sys.exit(status)

USE_SHELL = sys.platform.startswith("win")
def exec_cmd_with_stderr(command,
                         retry_times = 1,
                         retry_interval_sec = 0,
                         universal_newlines = True,
                         useshell = True,
                         env = os.environ):
    ret = 0
    output = None
    errout = None

    while retry_times > 0:
        try:
            p = subprocess.Popen(command,
                              stdout = subprocess.PIPE,
                              stderr = subprocess.PIPE,
                              shell = useshell,
                              universal_newlines = universal_newlines,
                              env = env)

            output = p.stdout.read()
            p.wait()
            errout = p.stderr.read()
            p.stdout.close()
            p.stderr.close()
            ret = p.returncode
            break
        except subprocess.CalledProcessError, er:
            ret = er.returncode
            retry_times -= 1
            if retry_interval_sec > 0: time.sleep(retry_interval_sec)

    return ret, output, errout

def setup_logging(logfile=DEFAULT_LOG, max_bytes=None, backup_count=None):
    """Sets up logging and associated handlers."""

    LOG.setLevel(logging.INFO)
    if backup_count is not None and max_bytes is not None:
        assert backup_count > 0
        assert max_bytes > 0
        ch = RotatingFileHandler(logfile, 'a', max_bytes, backup_count)
    else:  # Setup stream handler.
        ch = logging.StreamHandler(sys.stdout)

    ch.setFormatter(logging.Formatter('%(asctime)s %(name)s[%(process)d] '
                                      '%(levelname)s: %(message)s'))
    LOG.addHandler(ch)

def parse_argument():

    parser = argparse.ArgumentParser()

    parser.add_argument('-v', '--version', action = 'version',
                version = '%(prog)s 1.0'
            )

    parser.add_argument('--max-bytes', action = 'store', dest = 'max_bytes', 
                      type = int, default = 64 * 1024 * 1024,
                      help = 'Maximum bytes per a logfile.')

    parser.add_argument('--backup-count', action = 'store',
                      dest = 'backup_count', type = int, default = 0, 
                      help='Maximum number of logfiles to backup.')

    parser.add_argument('--logfile', action = 'store', dest='logfile', 
                      type = str, default = DEFAULT_LOG,
                      help = 'Filename where logs are written to.')

    parser.add_argument('-d', '--dir', action = 'store',
                dest = 'dir', type = str,
                help = 'Dir to recursive remove spaces at the end of the line.'
            )

    parser.add_argument('-f', '--file', action = 'store',
                dest = 'file', type = str,
                help = 'File name for remove spaces at the end of the line.'
            )

    options = parser.parse_args()

    if options.file is None and options.dir is None:
        parser.print_usage()

    return parser, options

################# main route ######################
if __name__ == '__main__':
    parser, options = parse_argument()

    setup_logging(options.logfile, options.max_bytes or None,
                  options.backup_count or None)

    LOG.setLevel(logging.DEBUG)

    if options.dir is not None and\
        not os.path.exists(options.dir):
        errorMessage = "dir of %s is not exists." % options.dir
        error_exit(errorMessage)
    elif not os.path.exists(options.file):
        errorMessage = "file of %s is not exists." % options.file
        error_exit(errorMessage)

    cmd = 'sed -i \"s/[ \t]+$//g\"'
    if options.file is not None:
        if not options.file.strip().startswith("."):
            cmd = cmd + " " + options.file
            print cmd
            ret, output, errout = exec_cmd_with_stderr(cmd)
            if ret != 0:
                LOG.error("Run cmd %s failed." % errout)
            else:
                LOG.info("Run cmd successed %s:\n %s" % (cmd, output))
#
#    try:
#        print "\n" + "*" * 60
#        LOG.info("Now produce the command section.")
#        if "command" in jstr.keys():
#            command = jstr["command"]
#            for cmd in command:
#                LOG.debug("Now rum command: %s" % cmd)
#                if len(cmd.strip()) != 0:
#                    ret, output, errout = exec_cmd_with_stderr(cmd)
#                    if ret != 0:
#                        LOG.error("Run cmd %s failed." % errout)
#                    else:
#                        LOG.info("Run cmd successed %s:\n %s" % (cmd, output))
#        else:
#            LOG.info("No command section for produce.")
#
#    except Exception as e:
#        print sys.exc_info()
#        sys.exit(RET_FAILED)
