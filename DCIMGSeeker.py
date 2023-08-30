#!/usr/bin/env python
# coding: utf-8

# Package installation borrowed from:
# https://stackoverflow.com/questions/12332975/installing-python-module-within-code/58040520#58040520
print("Initializing.\nChecking dependencies...")
import pkg_resources
import os
required = {'beautifulsoup4', 'requests', 'pandas'} 
installed = {pkg.key for pkg in pkg_resources.working_set}
missing = required - installed

if missing:
    print("Installing dependencies.")
    import sys
    import subprocess
    # implement pip as a subprocess:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing])
print("Checking directories...")
if not os.path.exists("input/"):
    try:
        os.mkdir("input/")
        raise ValueError("I need an input.json file in /input/ to run properly.")
    except OSError as error:
        print("I need an input.json file in /input/ to run properly. Also, you might not have permissions to create folders there.")
        raise ValueError(error)
if not os.path.exists("output/"):
    try:
        os.mkdir("output/")
    except OSError as error:
        print("Do you have permissions to create folders/files there?")
        raise ValueError(error)
if not os.path.exists("output/images"):
    try:
        os.mkdir("output/images")
    except OSError as error:
        print("Do you have permissions to create folders/files there?")
        raise ValueError(error)
from collections import defaultdict # dynamic dict. all my homies love dynamic dicts
import json # used to load json
import pandas as pd # you could probably do without pandas with some changes...
import requests # HTTP protocol
from bs4 import BeautifulSoup as bs4 # XML/HTML-handling
import warnings # just to shut bs4 up
from bs4 import XMLParsedAsHTMLWarning # same as above
warnings.filterwarnings('ignore', category=XMLParsedAsHTMLWarning) # Yes thank you BS4, I know XML is not HTML but if you load it any other way it doesn't find the thing I need so shush

recordIDs = [] # Define a list of Alvin IDs to look up. This is overridden by the input.json file.

print("Loading input from input/input.json...")
with open('input/input.json') as json_file:
    json = json.load(json_file)
print("OK.") # JSON file has been found and loaded

def stringReplaceTrash(oldString):
    oldString = oldString.replace("\n","")
    oldString = oldString.replace("\r","")
    newString = oldString.strip()
    return newString
print("What width (resolution) do you want the images to be? Default value 1250 - hit ENTER without input to default.")
size_images = int(input(">") or 1250)
print(size_images)
for collection_name in json: # For each name
    outputDict = defaultdict(dict) # Create an empty dict to serve as basis for csv output
    print(f"{collection_name}: {json[collection_name]}") # Confirmation
    recordIDs = json[collection_name] # RecordIDs are just the json[name] contents (a list)
    for recordID in recordIDs: # For every individual ID
        recordID = str(recordID) # Stringify just in case
        greater_series = recordID[:3]+"000" # Used to navigate the folder structure in IIPAPI
        lesser_series = recordID[3]+"00" # Same as line above.
        print(recordID,"|",greater_series,"|",lesser_series)
        url = "https://www.alvin-portal.org/oai/oai?verb=GetRecord&identifier=oai:ALVIN.org:"+recordID+"&metadataPrefix=oai_dc"
        print("\tFetching",url) # Print confirmation
        answer = requests.get(url) # Get http response
        if answer.status_code == 200: # If all good:
            rdfurl = "https://www.alvin-portal.org/oai/oai?verb=GetRecord&identifier=oai:ALVIN.org:"+recordID+"&metadataPrefix=ksamsok-rdf" # Create RDF-OAI url
            soup = bs4(answer.content,"lxml") # Soup the response from OAI DC
            metadataWhole = soup.find("metadata") # Snatch the metadata alone
            outputDict[recordID]["alvin:url"] = "http://urn.kb.se/resolve?urn=urn:nbn:se:alvin:portal:record-"+str(recordID) # Add the URL of the item to csv
            for metadataItem in metadataWhole.find('oai_dc:dc').contents: # For every dcterm we find
                if metadataItem != "\n": # There are random \ns around, we don't want those
                    metaNameSplit = str(metadataItem.name).split(":") # We actually get dc:term, we want the following
                    metaName = "dcterms:"+metaNameSplit[1] # Make it dcterms:term instead
                    metaText = str(metadataItem.text) # String the text of the item
                    if metaName in outputDict[recordID]: # If we already have an entry under this dcterm, splice this onto the end with pipe | as separator
                        part1 = outputDict[recordID][metaName] 
                        part2 = stringReplaceTrash(metaText)
                        outputDict[recordID][metaName] = part1+"|"+part2
                    else: # If it's new, just make sure there's no \n and \r before it goes in
                        metaText = stringReplaceTrash(metaText)
                        outputDict[recordID][metaName] = metaText
            imageIDsgotten = []
            rdfanswer = requests.get(rdfurl) # Http request to the RDF endpoint
            if rdfanswer.status_code == 200: # If it's good
                souprdf = bs4(rdfanswer.text, "lxml") # Soup the answer
                for item in souprdf.findAll("image", attrs={"rdf:nodeid":True}): # We're only going for the images here
                    if item.contents: # For each item in images
                        img_id = str(item.attrs['rdf:nodeid'])[-3:] # Get the last 3 digits of the image/attachment name, won't be a problem until one item has 1000+ images
                        img_id="0"+img_id # because there only are 3 digits provided, prepend a 0
                        img_url = f"https://www.alvin-portal.org/iipsrv/iipsrv.fcgi?FIF=/mnt/data/alvin/jp2/{greater_series}/{lesser_series}/alvin-record_{recordID}-ATTACHMENT-{img_id}.jp2&WID={str(size_images)}&CVT=jpeg"
                        if "images" in outputDict[recordID]: # Same procedure as before, append to the dict
                            part1 = outputDict[recordID]["images"]
                            part2 = img_url
                            outputDict[recordID]["images"] = part1+"|"+part2
                        else:
                            outputDict[recordID]["images"] = img_url
                        imageIDsgotten.append(img_id)

                        if not os.path.exists("output/images/"+collection_name):
                            try:
                                os.mkdir("output/images/"+collection_name)
                            except OSError as error:
                                print("Do you have permissions to create folders/files there?")
                                raise ValueError(error)
                        
                        if not os.path.exists(f"output/images/{collection_name}/{recordID}"):
                            try:
                                os.mkdir(f"output/images/{collection_name}/{recordID}")
                            except OSError as error:
                                print("Do you have permissions to create folders/files there?")
                                raise ValueError(error)
                            
                        img_data = requests.get(img_url).content
                        with open(f"output/images/{collection_name}/{recordID}/{img_id}.jpeg", 'wb') as handler:
                            handler.write(img_data)
                            
                kk = "/".join(imageIDsgotten)
                if kk:
                    print("\t\tImages:",kk)
            else:
                print("\tWARNING: Image fetch failed:",str(answer.status_code))
        else:
            print("\tWARNING: Fetch failed:",str(answer.status_code))
    df = pd.DataFrame.from_dict(outputDict)
    df = df.T.reset_index(drop=False)
    df = df.rename(columns={"index": "alvin:id"})
    df.to_csv("output/"+collection_name+".csv", index=False, encoding='utf-8-sig') # utf-8-sig is REQUIRED
    print("\t\tSaved to output/"+collection_name+".csv\n")
    # Ready for next item
print("All done!")