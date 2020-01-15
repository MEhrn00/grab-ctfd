#!/usr/bin/python3

import json
import requests
import os
import re
import sys
import argparse
import getpass
from urllib.parse import urlparse

def main():

    parser = argparse.ArgumentParser(description="Automatically creates directory structure and downloads files from CTFs using CTFd's API.")
    parser.add_argument('name', help="Name of CTF.\nCurrent working directory --> CTF-Name --> Category --> Challenge")
    parser.add_argument('url', help='URL of the CTF (must be CTFd based)')
    parser.add_argument('username', help='Username of your account for the CTF')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help="Adds some debugging statements to output")

    args = parser.parse_args()

    # Name of the CTF
    ctfname = args.name
    # URL of CTFd base
    url = args.url
    # Username for the CTF
    username = args.username
    # Password for the CTF
    try:
        password = getpass.getpass()
    except Exception as error:
        print("Password error!", error)
    # Verbosity
    verbose = args.verbose

    # Checking if URL can be reached
    if not VerifyURL(url):
        # Not a valid URL
        print("Please enter a valid URL!")
        return
    if verbose:
        print("URL Verified")

    # Stripping backslash from URL
    url = NormalizeURL(url)
    
    # Grabbing all challenges using the API
    challenges = GetChallenges(url, username, password)
    if verbose:
        print("Got challenges from CTFd API")

    # Creating the directory structure
    # The basic structure is Category->Challenge
    CreateDirectories(ctfname, challenges)
    if verbose:
        print("Created directories")

    # Grabbing all descriptions and creating files
    CreateDescriptionFile(ctfname, challenges)
    if verbose:
        print("Created description files")

    # Downloads all files associated with challenges
    CreateChallengeFiles(url, ctfname, challenges)
    if verbose:
        print("Downloaded challenge files")


# Makes sure that the url is reachable
VerifyURL = lambda url: requests.get(url).status_code == 200


# Removes backslash from the end of URLs
def NormalizeURL(url):
    if url[-1] == '/':
        return url[:-1]
    return url


# Returns a set of the challenge names
def GetChallenges(url, username, password):
    loginpath = "/login"
    with requests.Session() as s:
        # Thanks to CTFd creators for not having a way to auth with API
        # Grabbing csrf token
        csrf = re.findall("[0-9a-fA-F]{64}", s.get(url+loginpath).text)[0]
        payload = {'name':username, 'password':password, 'nonce':csrf}
        # Logging in
        p = s.post(url+loginpath, data=payload)
        if not p.status_code:
            print("Login failed!")
        #default api path is /api/v1/challenges
        apipath = "/api/v1/challenges"
        challenges = []
        response = s.get(url+apipath)
        all = json.loads(response.text)
        if all["success"]:
            for d in all["data"]:
                category = d["category"]
                name = d["name"] 
                id = d["id"]
                value = d["value"]
                response = s.get(url+apipath+"/"+str(id))
                chall = json.loads(response.text)
                if chall["success"]:
                    description = chall["data"]["description"]
                    files = chall["data"]["files"]

                challenges.append({"id":id,"name":name,"category":category,
                "value":value,"description":description,"files":files})
    return challenges


# Creates the directories containing the challenges
def CreateDirectories(ctfname, challenges):
    for x in challenges:
        path = os.getcwd() + "/" + str(ctfname)
        path += "/" + x["category"] + "/" + x["name"]
        try:
            os.makedirs(path)
        except OSError:
            # We failed creating the directory
            print("Directory Creation Failed! %s" % path)
        else:
            # We made the directory
                pass
 

# Creates the description file from the challenge description
def CreateDescriptionFile(ctfname, challenges):
    for x in challenges:
        path = os.getcwd() + "/" + str(ctfname)
        path += "/" + x["category"] + "/" + x["name"] + "/"
        open(path + 'description.txt', 'w').write(x["description"])


# Downloads the challenge files from the challenge
def CreateChallengeFiles(url, ctfname, challenges):
    for x in challenges:
        if x["files"]:
            path = os.getcwd() + "/" + str(ctfname)
            path += "/" + x["category"] + "/" + x["name"] + "/"
            for f in x["files"]:
                r = requests.get(url+f, allow_redirects=True)
                open(path + GetFileNameFromURL(url+f), 'wb').write(r.content)


# Gets the file name from a URL
def GetFileNameFromURL(url):
    u = urlparse(url)
    return os.path.basename(u.path)

main()
