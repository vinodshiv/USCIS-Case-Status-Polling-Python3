# USCIS Case Status Polling

This is a simple python script to poll USCIS case status and optionally generate email alert on status change.

This is an improvement on [co89757](https://github.com/co89757)'s original script - [USCIS Case Status Polling](https://github.com/co89757/USCISCasePoll) using Python 3 and simplified email utilizing [dimaba's Python Email Sender](https://github.com/dimaba/sendmail#python-email-sender)

The core script is `poll_uscis.py`




# Usage
## Setup
To set up the environment for the python script, in the repo directory, do:

```sh
# do this in your virtualenv or normal terminal with sudo
pip3 install -r requirements.txt
```

Within the script, update your recipient details under the EMAIL SETTINGS section:

```python

# ----------------- EMAIL SETTINGS -------------------
mailto = 'john.doe@gmail.com'
password = 'xxxxxxx'
smtpserver = ('smtp.gmail.com', 465)
useSSL = True
sender_name = 'USCIS Poller'
```

**Ensure that sendmail.py is in the same folder as the core script**


## Run script

Before you run the script, it's highly helpful to take a quick look at the manual

```sh
python poll_uscis.py -h
```

The only mandatory argument to the script is obviously your USCIS case receipt number, so a simple run looks like:

```sh
## simple run with minimal information including status, and days elapsed since received
python poll_uscis.py -c <your_case_number>

## request detail text on status as well
python poll_uscis.py -c <casenumber> -d/--detail

## send email alert
python poll_uscis.py -c <casenumber> --mailto <comma-separated-emails>
```
## Set it to periodic scheduled job 

### Unix

Use crontab to set a daily poll job:

```sh

# edit your cron jobs and append a cronjob to it 
$crontab -e 
```

In the opened editor, depending on the schedule you need, append the below lines:
```sh
# Every two hours between 00 AM and 11 AM
*/120 0-11 * * 1-5 cd <script-directory> && /usr/local/bin/python3 poll_uscis.py -c <case-number> -d --mailto=john.doe@gmail.com > ./logs/uscis_case_check_$(date +\%Y\%m\%d\%H\%M).txt

# Every hour between 12 PM and 11 PM
*/60 12-23 * * 1-5 cd <script-directory> && /usr/local/bin/python3 poll_uscis.py -c <case-number> -d --mailto=john.doe@gmail.com > ./logs/uscis_case_check_$(date +\%Y\%m\%d\%H\%M).txt
```