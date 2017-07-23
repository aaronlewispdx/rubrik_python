#!/usr/bin/env python

import requests
import base64
import sys
import os
import getopt
import requests
import urllib3
import traceback
import datetime
import time
from datetime import timedelta
from datetime import datetime
sys.path.append('../lib')
from Rubrik import Rubrik

# Disable SSL self-signed certificates
urllib3.disable_warnings()

def get_report_id(report, node, header):
    try:
        url = 'http://' + node + '/api/internal/report'
        response = requests.get(url, headers=header, verify=False, timeout=15)
        data = response.json()
        report_id = None
        for item in data['data']:
            if item['reportName'] == report:
                report_id = item['id']
        if report_id == None:
            sys.exit("**RUBRIK ERROR:  Report does not exist**")
        else:
            return report_id
    except:
        traceback.print_exc()

try:
    """ If the script has no options then exit the script
    Option usage:
        -n <node_IP or node_hostname> -r <report_name>
    """

    if len(sys.argv) != 5:
        print "***" +  sys.argv[0] + " usage: -n <node IP or hostname> -r <report name>"
        os._exit(1)

    myopts, args = getopt.getopt(sys.argv[1:],"n:r:")
    for opt, opt_value in myopts:
        if opt == '-n':
            node = opt_value
        elif opt == '-r':
            report = opt_value

    secrets_json_path = '../secrets3.json'
    rk = Rubrik(node, secrets_json_path)
    header = rk.create_get_header()

    report_id = get_report_id(report, node, header)
    
    report_columns = []
    url = 'https://' + node + '/api/internal/report/' + report_id + '/table/metadata'
    response  = requests.get(url, headers=header, verify=False, timeout=15)
    data = response.json()
    for item in data['columns']:
        report_columns.append(item)
    print report_columns 

    url2 = 'https://' + node + '/api/internal/report/' + report_id + '/table?limit=4000&sort_order=asc&timezone_offset=-420'
    response2 = requests.get(url2, headers=header, verify=False, timeout=15)
    data2 = response2.json()

    jobs = 0
    successful_jobs = 0
    failed_jobs = 0
    other_jobs = 0
    data_transferred = 0
    data_stored = 0
    duration = timedelta(hours=0, minutes=0, seconds=0)
    
    run_time = datetime.now()
    month = run_time.strftime("%B")
    day = run_time.strftime("%d")
    year = run_time.strftime("%Y")
    report_run_time = "%s %s, %s" % (month, day, year)

    min_start_date = datetime.now()
    max_end_date = datetime.now() - timedelta(days=7)
    for item in data2['data']:
        if item[report_columns.index('TaskStatus')] == "Succeeded":
            successful_jobs = successful_jobs + 1
        elif item[report_columns.index('TaskStatus')] == "Failed":
            failed_jobs = failed_jobs + 1
        else:
            other_jobs = other_jobs + 1

        start_date = datetime.strptime(item[report_columns.index('StartTime')], "%Y-%m-%d %H:%M:%S")
        end_date = datetime.strptime(item[report_columns.index('EndTime')], "%Y-%m-%d %H:%M:%S")
        if min_start_date > start_date:
            min_start_date = start_date
        if end_date > max_end_date:
            max_end_date = end_date
        jobs = jobs + 1

        job_duration = int(item[report_columns.index('Duration')])/ 1000
        duration = duration + timedelta(seconds=job_duration)

        data_transferred = data_transferred + int(item[report_columns.index('DataTransferred')])
        data_stored = data_stored + int(item[report_columns.index('DataStored')])

    total_job_time = max_end_date - min_start_date

    avg_job_time = duration / jobs

    data_transferred_gb = str("{0:.2f}".format(float(data_transferred) / (1000*1000*1000)))
    data_stored_gb = str("{0:.2f}".format(float(data_stored) / (1000*1000*1000)))

    avg_job_time_2 = str(time.strftime("%H:%M:%S", time.gmtime(avg_job_time.total_seconds())))

    """ --> Print HTML"""
    print '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">'
    print '<html xmlns="http://www.w3.org/1999/xhtml">'
    print '<head><meta http-equiv="Content-Type" content="text/html; charset=utf-8">'
    print '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
    print '<link href="https://fonts.googleapis.com/css?family=Ubuntu:500" rel="stylesheet"></head>'
    print '<body>'
    print '<style>'
    print '#leftcolumn dl{display:block;margin-left:20px;}'
    print '#leftcolumn dt{font-size:120%;color:#000;margin:10px 0 0;padding:0;}'
    print '#leftcolumn dt.imp strong{font-weight:normal;color:red;}'
    print '#leftcolumn dd{margin:0;padding:0;}'
    print '#hor-minimalist-b{font-family:\'Ubuntu\', sans-serif;font-size:14px;background:#fff;width:480px;border-collapse:collapse;text-align:left;margin:20px;}'
    print '#hor-minimalist-b th{font-size:16px;font-weight:600;color:#000;border-bottom:2px solid #000;padding:10px 30px;}'
    print '#hor-minimalist-b td{border-bottom:1px solid #000;color:#000;padding:6px 8px;}'
    print '#hor-minimalist-b tbody tr:hover td{color:#000;}'
    # print '#h1, h2, h3, h4, h5, h6 { margin-top: 12px; margin-bottom: 12px; }'
    print 'h2, h3, h4 { margin-top: 0.65em; margin-bottom: 0.23em; }'
    print '</style>'
    print '<font face="Ubuntu">'
    print '<img src="data:image/png;base64,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">'
    print '<h2>','Daily Backup Job Report','</h2>'
    print '<font size="4"><b>Report Run Time:&nbsp;&nbsp;&nbsp;',report_run_time,'</b></font>'
    print '<br>'

    print '<table id="hor-minimalist-b" summary="Job Summary Details">'
    print '<tr><th>Total # of Jobs</th><th>Successful Jobs</th><th>Failed Jobs</th><th>Other Jobs</th><th>Start Time</th><th>End Time</th><th>Total Job Duration</th><th>Data Transferred (GB)</th><th>Data Stored (GB)</th><th>Avg. Backup Job Time (hh:mm:ss)</th></tr>'
    print '<tr><th>',jobs,'</th><th>',successful_jobs,'</th><th>',failed_jobs,'</th><th>',other_jobs,'</th><th>',min_start_date,'</th><th>',max_end_date,'</th><th>',total_job_time,'</th><th>',data_transferred_gb,'</th><th>',data_stored_gb,'</th><th>',avg_job_time_2,'</th>'
    print '</table>'

    """
    # ---> Text outputs of the key metrics
    run_time = max_end_date - min_start_date
    print "Job Start Time: " + str(min_start_date)
    print "Job End Time: " + str(max_end_date)
    print "Run Time: " + str(run_time)
    print "# of Jobs: " + str(jobs)
    print "# of Successful Jobs: " + str(successful_jobs)
    print "# of Failed Jobs: " + str(failed_jobs)
    print "# of Other Jobs: " + str(other_jobs)
    print "Total Duration: " + str(duration)
    print "Data Transferred: " + str("{0:.2f}".format(data_transferred_gb))
    print "Data Stored: " + str("{0:.2f}".format(data_stored_gb))
    print "Average Backup Job Time: " + str(time.strftime("%H:%M:%S", time.gmtime(avg_job_time.total_seconds())))
    """

except:
    traceback.print_exc()
