#!/usr/bin/env python
#
# Download GitHub Issued and PR as CSV
#
# written by Andreas 'ads' Scherbaum <andreas@scherbaum.la>
#
# version:     0.5   2016-08-27
#                    initial version
#              1.0   2016-09-04
#                    update help
#                    add options
#                    remove hardcoded organization and project


import re
import os
import sys
import logging
import tempfile
import atexit
import shutil
import argparse

_urllib_version = False
try:
    import urllib2
    _urllib_version = 2
except ImportError:
    import urllib3
    _urllib_version = 3
    try:
        import httplib
    except ImportError:
        import http.client as httplib

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import gzip
import zlib
from subprocess import Popen
try: from urlparse import urljoin # Python2
except ImportError: from urllib.parse import urljoin # Python3

import json





# start with 'info', can be overriden by '-q' later on
logging.basicConfig(level = logging.INFO,
		    format = '%(levelname)s: %(message)s')





# download_url()
#
# download a specific url, handle compression
#
# parameter:
#  - url
# return:
#  - content of the link
def download_url(url):
    global _urllib_version

    if (_urllib_version == 2):
        rq = urllib2.Request(url)
        rq.add_header('Accept-encoding', 'gzip')

        try:
            rs = urllib2.urlopen(rq)
        except urllib2.HTTPError as e:
            if (e.code == 400):
                logging.error('HTTPError = ' + str(e.code) + ' (Bad Request)')
            elif (e.code == 401):
                logging.error('HTTPError = ' + str(e.code) + ' (Unauthorized)')
            elif (e.code == 403):
                logging.error('HTTPError = ' + str(e.code) + ' (Forbidden)')
            elif (e.code == 404):
                logging.error('HTTPError = ' + str(e.code) + ' (URL not found)')
            elif (e.code == 408):
                logging.error('HTTPError = ' + str(e.code) + ' (Request Timeout)')
            elif (e.code == 418):
                logging.error('HTTPError = ' + str(e.code) + " (I'm a teapot)")
            elif (e.code == 500):
                logging.error('HTTPError = ' + str(e.code) + ' (Internal Server Error)')
            elif (e.code == 502):
                logging.error('HTTPError = ' + str(e.code) + ' (Bad Gateway)')
            elif (e.code == 503):
                logging.error('HTTPError = ' + str(e.code) + ' (Service Unavailable)')
            elif (e.code == 504):
                logging.error('HTTPError = ' + str(e.code) + ' (Gateway Timeout)')
            else:
                logging.error('HTTPError = ' + str(e.code))
            sys.exit(1)
        except urllib2.URLError as e:
            logging.error('URLError = ' + str(e.reason))
            sys.exit(1)
        except httplib.HTTPException as e:
            logging.error('HTTPException')
            sys.exit(1)
        except Exception:
            logging.error('generic exception')
            sys.exit(1)

        if rs.info().get('Content-Encoding') == 'gzip':
            b = StringIO(rs.read())
            f = gzip.GzipFile(fileobj = b)
            data = f.read()
        else:
            data = rs.read()

    elif (_urllib_version == 3):
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("httplib").setLevel(logging.WARNING)
        user_agent = {'user-agent': 'GPDB buildclient', 'accept-encoding': 'gzip, deflate'}
        #http = urllib3.PoolManager(maxsize = 3, retries = 2, headers = user_agent)
        http = urllib3.PoolManager(maxsize = 3, headers = user_agent)

        try:
            rs = http.urlopen('GET', url, redirect = True)
        except urllib3.exceptions.MaxRetryError as e:
            logging.error("Too many retries")
            sys.exit(1)
        except urllib3.URLError as e:
            logging.error('URLError = ' + str(e.code))
            sys.exit(1)
        except httplib.HTTPException as e:
            logging.error('HTTPException')
            sys.exit(1)
        except urllib3.exceptions.ConnectTimeoutError as e:
            logging.error("Timeout")
            sys.exit(1)
        except Exception:
            logging.error('generic exception')
            sys.exit(1)

        if (rs.status != 200):
            if (rs.status == 400):
                logging.error("HTTPError = 400 (Bad Request)")
            elif (rs.status == 401):
                logging.error("HTTPError = 401 (Unauthorized)")
            elif (rs.status == 403):
                logging.error("HTTPError = 403 (Forbidden)")
            elif (rs.status == 404):
                logging.error("HTTPError = 404 (URL not found)")
            elif (rs.status == 408):
                logging.error("HTTPError = 408 (Request Timeout)")
            elif (rs.status == 418):
                logging.error("HTTPError = 418 (I'm a teapot)")
            elif (rs.status == 500):
                logging.error("HTTPError = 500 (Internal Server Error)")
            elif (rs.status == 502):
                logging.error("HTTPError = 502 (Bad Gateway)")
            elif (rs.status == 503):
                logging.error("HTTPError = 503 (Service Unavailable)")
            elif (rs.status == 504):
                logging.error("HTTPError = 504 (Gateway Timeout)")
            else:
                logging.error("HTTPError = " + str(rs.status) + "")
            sys.exit(1)

        if (len(rs.data.decode()) == 0):
            logging.error("failed to download URL")
            sys.exit(1)

        data = rs.data.decode()

    else:
        logging.error("unknown urllib version!")
        sys.exit(1)


    logging.debug("fetched " + human_size(len(data)))

    return data



# from: http://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size
# human_size()
#
# format number into human readable output
#
# parameters:
#  - number
# return:
#  - string with formatted number
def human_size(size_bytes):
    """
    format a size in bytes into a 'human' file size, e.g. bytes, KB, MB, GB, TB, PB
    Note that bytes/KB will be reported in whole numbers but MB and above will have greater precision
    e.g. 1 byte, 43 bytes, 443 KB, 4.3 MB, 4.43 GB, etc
    """
    if (size_bytes == 1):
        # because I really hate unnecessary plurals
        return "1 byte"

    suffixes_table = [('bytes',0),('KB',0),('MB',1),('GB',2),('TB',2), ('PB',2)]

    num = float(size_bytes)
    for suffix, precision in suffixes_table:
        if (num < 1024.0):
            break
        num /= 1024.0

    if (precision == 0):
        formatted_size = "%d" % num
    else:
        formatted_size = str(round(num, ndigits=precision))

    return "%s %s" % (formatted_size, suffix)



# write_output()
#
# write output file
#
# parameter:
#  - filename
#  - flag if Pull Requests (true) or Issues (false) should be printed
#  - list with PR/Issues
# return:
#  none
def write_output(file, is_pr, issues):
    f = open(file, 'w')
    f.write("ID\tTitle\tCreated\tURL\tState\n")

    for item_outer in issues:
        for item in item_outer:
            if (is_pr is False and 'pull_request' in item):
                continue
            if (is_pr is True and 'pull_request' not in item):
                continue

            f.write(str(item['number']) + "\t")
            f.write(str(item['title'].encode('utf-8')) + "\t")
            f.write(str(item['created_at']).replace('T', ' ').replace('Z', '') + "\t")
            # replace the API link with the WWW link
            url = item['url'].replace('https://api.github.com/', 'https://www.github.com/')
            f.write(str(url) + "\t")
            f.write(str(item['state']) + "\t")
            f.write("\n")
    f.close()



# print_help()
#
# print the help
#
# parameter:
#  - parser
# return:
#  none
def print_help(parser):
    parser.print_help()






#######################################################################
# Main program



parser = argparse.ArgumentParser(description = 'GitHub Issues and PR exporter',
                                 epilog = '',
                                 usage = '%(prog)s [options] <GitHub organization name> <GitHub project name>',
                                 add_help = False)
parser.add_argument('--help', default = False, dest = 'help', action = 'store_true', help = 'show this help')
parser.add_argument('--state', default = 'open', dest = 'state', help = 'Issue state (open, closed, all - Default: open)', choices = ['open', 'closed', 'all'])
parser.add_argument('--sort', default = 'created', dest = 'sort', help = 'Sort order (created, updated, comments - Default: created)', choices = ['created', 'updated', 'comments'])
parser.add_argument('-v', '--verbose', default = False, dest = 'verbose', action = 'store_true', help = 'be more verbose')
parser.add_argument('-q', '--quiet', default = False, dest = 'quiet', action = 'store_true', help = 'run quietly')


# parse parameters
parsed = parser.parse_known_args()
args = parsed[0]
remaining_args = parsed[1]


if (args.help is True):
    print_help(parser)
    sys.exit(0)


if (args.verbose is True and args.quiet is True):
    print_help(parser)
    print("")
    print("Error: --verbose and --quiet can't be set at the same time")
    sys.exit(1)

if (args.verbose is True):
    logging.getLogger().setLevel(logging.DEBUG)

if (args.quiet is True):
    logging.getLogger().setLevel(logging.ERROR)


if (len(remaining_args) < 2):
    print_help(parser)
    print("")
    print("")
    print('"GitHub organization name" and "GitHub project name" must be specified!')
    print("")
    sys.exit(1)

github_organization = remaining_args[0]
github_project = remaining_args[1]
logging.debug("Organization: " + github_organization)
logging.debug("     Project: " + github_project)



issues_json_all = []

# fetch all pages, until a page with no JSON data is returned
page = 0
while True:
    page += 1
    logging.debug("Page: " + str(page))
    issues_url = 'https://api.github.com/repos/' + github_organization + '/' + github_project + '/issues?state=' + args.state + '&sort=' + args.sort + '&filter=all&page=' + str(page)
    issues_data = download_url(issues_url)
    if (len(issues_data) < 20):
        # GitHub returns an empty JSON field if there is no more data available
        logging.info("fetched " + str(page - 1) + " pages with data")
        break
    issues_json = json.loads(issues_data)
    issues_json_all.append(issues_json)

#print(issues_json)

base_output_name = 'GitHub_' + github_organization + '_' + github_project + '_'
issues_output_name = base_output_name + 'Issues.csv'
pr_output_name = base_output_name + 'PR.csv'
#logging.debug("Base filename: " + base_output_name)
write_output(issues_output_name, False, issues_json_all)
write_output(pr_output_name, True, issues_json_all)
logging.info("Issues: " + issues_output_name)
logging.info("    PR: " + pr_output_name)



