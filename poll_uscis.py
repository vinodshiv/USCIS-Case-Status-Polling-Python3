# @author: vinodshiv
# @date: 2022-05-16
# @filename: poll_uscis.py
"""
usage:
python3 poll_uscis.py -c <case_number> -d --mailto=john.doe@gmail.com
"""

from pyquery import PyQuery as pq
import requests
import os
import sys
import os.path
import re
from email.utils import COMMASPACE, formatdate
from optparse import OptionParser
from datetime import datetime, date
from sendmail import MailSender


STATUS_OK = 0
STATUS_ERROR = -1
FILENAME_LASTSTATUS = os.path.join(sys.path[0], "LAST_STATUS_{0}.txt")
DASHES = '-'*60

# ----------------- EMAIL SETTINGS -------------------
# set up your email recipient here

mailto = 'john.doe@gmail.com'
password = 'xxxxxxx'
smtpserver = ('smtp.gmail.com', 465)
useSSL = True
sender_name = 'USCIS Poller'
ourmailsender = MailSender(mailto, password,smtpserver , useSSL)


def poll_optstatus(casenumber):
    """
    poll USCIS case status given receipt number (casenumber)
    Args:
        param1: casenumber the case receipt number

    Returns:
        a tuple (status, details) containing status and detailed info
    Raise:
        error:
    """
    headers = {
        'Accept': 'text/html, application/xhtml+xml, image/jxr, */*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language':
        'en-US, en; q=0.8, zh-Hans-CN; q=0.5, zh-Hans; q=0.3',
        'Cache-Control': 'no-cache',
        'Connection': 'Keep-Alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Host': 'egov.uscis.gov',
        'Referer': 'https://egov.uscis.gov/casestatus/mycasestatus.do',
        'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586'
    }
    url = "https://egov.uscis.gov/casestatus/mycasestatus.do"
    data = {"appReceiptNum": casenumber, 'caseStatusSearchBtn': 'CHECK+STATUS'}

    res = requests.post(url, data=data, headers=headers)
    doc = pq(res.text)
    status = doc('h1').text()
    code = STATUS_OK if status else STATUS_ERROR
    details = doc('.text-center p').text()
    return (code, status, details)


def on_status_fetch(status, casenumber):
    """
    fetch status and update last_status record file,
    or create it if it doesn't exist
    Returns:
        changed flag indicating if status has changed since last time and last status
        (changed, last_status)
        If no prior history is available, then return (False, None)
    """
    # normalize
    status = status.strip()
    record_filepath = FILENAME_LASTSTATUS.format(casenumber)
    changed = False
    last_status = None
    if not os.path.exists(record_filepath):
        with open(record_filepath, 'w') as f:
            f.write(status)
    # there is prior status, read it and compare with current
    else:
        with open(record_filepath, 'r+') as f:
            last_status = f.read().strip()
            # update status on difference
            if status != last_status:
                changed = True
                f.seek(0)
                f.truncate()
                f.write(status)
    return (changed, last_status)

def get_days_since_received(status_detail):
        """parse case status and computes number of days elapsed since case-received"""

        # Get the date from the beginning of the status detail
        if str.upper("on") in status_detail[:20].upper():
            date_regex = re.compile(r'^On (\w+ +\d+, \d{4}), .*')
        elif str.upper("as of") in status_detail[:20].upper():
            date_regex = re.compile(r'^As of (\w+ +\d+, \d{4}), .*')

            m = date_regex.match(status_detail)
            datestr = m.group(1)
            if not datestr:
                return -1
            recv_date = datetime.strptime(datestr, "%B %d, %Y").date()
            today = date.today()
            span = (today - recv_date).days
            return span

if __name__ == '__main__':
    
    usage = """usage: %prog -c <case_number> [options]"""

    # add parsers
    parser = OptionParser(usage=usage)
    parser.add_option(
        '-c',
        '--casenumber',
        type='string',
        action='store',
        dest='casenumber',
        default='',
        help='the USCIS case receipt number you can to query')
    parser.add_option(
        '-d',
        '--detail',
        action='store_true',
        dest='detailOn',
        help="request details about the status returned")
    parser.add_option(
        '--mailto',
        action='store',
        dest='receivers',
        help=(
            "optionally add one or more emails addresses, separated by comma,"
            " to send the notification mail to"))
    opts, args = parser.parse_args()
    casenumber = opts.casenumber
    if not casenumber:
        raise parser.error("No case number is provided")

    ### poll status ###
    code, status, detail = poll_optstatus(casenumber)
    if code == STATUS_ERROR:
        print(f"\n{DASHES}\nThe case number entered ({casenumber}) is invalid!"
            f" Try again..\n{DASHES}\n")
        exit(1)
    else:
        # Get values from report
        days_elapsed = get_days_since_received(detail)
        changed, laststatus = on_status_fetch(status, casenumber)
        
        ### Build report format for output ###

        # Print report format
        report = (f"\n\t-------  "
                    f"Your USCIS Case [{casenumber}] "
                    f"---------\n"
                    f"\nCurrent Status \t\t: {status}"
                    f"\nDays since received \t: {days_elapsed}"
                    f"\nPrevious Status \t: {laststatus}"
                    f"\nChanged? \t\t: {changed}"
                    f"\nCurrent Timestamp\t: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n{DASHES}\n")
        # if detail is ON, add detail to output
        if opts.detailOn:
            report = '\n'.join((report, f"\nDetail:\n{detail}\n{DASHES}"))

        # Print html report format for email
        html_break = '<br>'
        html_tab = '&emsp;'
        report_html = report.replace('\n',html_break).replace('\t','&emsp;')

        # console output
        print(report)

        # Email notification on status change ONLY
        if opts.receivers and changed:
            recv_list = opts.receivers.split(',')
            subject = f"Your USCIS Case {casenumber} Status Change Notice"

            ourmailsender.set_message(
                in_plaintext=report_html,
                in_subject=subject,
                in_from=sender_name,
                in_htmltext=report_html)
            ourmailsender.set_recipients(recv_list)
            ourmailsender.connect()
            ourmailsender.send_all()

