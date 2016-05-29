import time
import requests
import json
import glob
import os
import re
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('filename', help="File to submit")
parser.add_argument('problemset', help="Problemset name")
parser.add_argument('problemname', help="Problem name")
args = parser.parse_args()

JUDGE_URL = "http://judge.juice500.ml"

def submit(problemset, problem, filename):
    try:
        binfile = open(filename, "rb")
    except FileNotFoundError:
        print("No such file [%s]" % filename)
        return None

    filetype = filename.split('.')[-1]
    if filetype != 'py' and filetype != 'txt':
        print("Only .py or .txt file can be submitted.")
        return None

    url = "%s/%s/%s/submit/" % (JUDGE_URL, problemset, problem)
    r = requests.post(url, files = {'upfile': binfile})
    if r.status_code != 200:
        print("Wrong problemset name [%s] or problem name [%s]" % (problemset, problem))
        return None

    # Parsing status url
    i = r.text.find("/api/status/")
    j = r.text.find("',\n        data: {last_updated")
    api = r.text[i:j]

    while True:
        r = requests.get(JUDGE_URL + api)
        if r.status_code != 200:
            print('Server Error: [%s] not found' % api)
            return None

        status = json.loads(r.text)["status"]
        print("[%s] %s" % (filename, status))
        if status == "JudgeStatus.FAILED":
            return False
        if status == "JudgeStatus.FINISHED":
            return True
        time.sleep(1)

problemset = args.problemset
problem = args.problemname
filename = args.filename

if submit(problemset, problem, filename):
    print('[%s] Judging Done for %s from %s\nYou are correct!' % (filename, problem, problemset))
else:
    print('[%s] Judging Done for %s from %s\nTry again' % (filename, problem, problemset))
