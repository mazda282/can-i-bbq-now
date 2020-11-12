# -*- coding: utf-8 -*-

import io
import os
import sys
import requests
import json
import time
from datetime import datetime

# Imports the Google Cloud client library
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="googlecredentials.json" #Google credentials. See https://cloud.google.com/docs/authentication/production

# Import the firestone database library
from firebase_admin import db
from firebase_admin import credentials
import firebase_admin
from firebase_admin import firestore
cred = credentials.Certificate('firebasekey.json') #FireStone Credentials. See https://firebase.google.com/docs/admin/setup#linux-or-macos
firebase_admin.initialize_app(cred, {'databaseURL': 'https://kanjaggrilla.firebaseio.com', 'projectId': 'kanjaggrilla'})

# 46 elks definitions
phoneNumberStockholmBrand = '+4684548339'   #The Phonenumber of the answering machine
phoneNumberFrom = '+46712345678'   #Your 46 elks number needs to be valid
API_USERNAME_46_ELKS = 'u********************************'    #Username
API_PASSWORD_46_ELKS  = '********************************'    #Password   

# Uses the google speech-to-text API to convert an audiofile into text
def openAndTranscribe(filename, filenameOut):
    # Instantiates a client
    client = speech.SpeechClient()
    # The name of the audio file to transcribe
    file_name = os.path.join(
        os.path.dirname(__file__),
        filename)

    # Loads the audio into memory
    with io.open(file_name, 'rb') as audio_file:
        content = audio_file.read()
        audio = types.RecognitionAudio(content=content)

    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=8000,
        language_code='sv-SE',
        # metadata = [{'recordingDeviceType':[enums.RecognitionConfig.metadata.recordingDeviceType.PHONE_LINE]}]   #I never got this working..
        )

    # Detects speech in the audio file
    response = client.recognize(config, audio)

    for result in response.results:
        f=open(filenameOut,"wb+")
        f.write(result.alternatives[0].transcript.encode("utf-8"))
        print(result.alternatives[0].transcript.encode("utf-8"))

# Places a phonecall using 46-elks API. Outputs a wav-file
def placeAndRecordCall(number, outputFilename):
    auth = (
        API_USERNAME_46_ELKS,  #Username
        API_PASSWORD_46_ELKS    #Password
        )
    
    fields = {
        'from': phoneNumberFrom,
        'to': number, 
        'timeout': '10',
        'voice_start': '{"record":"local/recording1"}'
        }

    # Place phonecall with recording request.
    response = requests.post(
        "https://api.46elks.com/a1/calls",
        data=fields,
        auth=auth
        )

    print(response.text)
    
    # parse the call ID
    response_dict = json.loads(response.text)
    ID = str(response_dict['id'])
    print("The id is: >>%s<<\n" % ID)
    

    # get the placed phonecall
    # This is a silly fix. But wait for the phonecall to finish. And check every 5 seconds. Maybe it's better to implement the URL hook instead.
    retryTime = 0
    while(retryTime<100):
        get = requests.get(
        "https://api.46elks.com/a1/recordings/"+ID+"-r0.wav",
        auth=auth
        )
        if(len(get.content)>100):  # Has to be bigger than 100B otherwise it's "empty"
            open(outputFilename, 'wb').write(get.content)
            retryTime = 1000
            
        else:
            print("Waiting for phonecall to finish...")
            time.sleep(5) 
        retryTime+=5

# Open and parse a transcribed textfile. Returns the text and a decision
def openAndParse(filename):
    retVal = "Nej!"
    with open(filename, encoding='utf-8') as f:
        parsedText = f.read()
        if 'inte eldningsf' in parsedText: #Need to figure out how to search for åäö
            print("Inget eldningsforbud!")
            retVal = "Ja!"

    return (parsedText, retVal)

# Upload a database entry to a firestone firestore DB.  
# The structure for now is that each city is its own "collection". 
# Every document in this collection uses the date as the name name. 
# TODO: Some of this information is duplicated and redundant 
def uploadResultToFirestoneDb(databaseName, entryName, decision, text, date):
    db = firestore.client()
    doc_ref = db.collection(databaseName)

    # This code can write to the database
    sthlm_ref = doc_ref.document(entryName)

    sthlm_ref.set({
        'city_name' : 'Stockholm',
        'date' : date,
        'text' : text,
        'decision' : decision
    })


if __name__ == "__main__":
    date = datetime.strftime(datetime.now(), "%Y%m%d_%H%M%S")
    date_webformat = datetime.strftime(datetime.now(), "%Y-%m-%d")
    filenameRecording = date+".wav"
    filenameTranscription = date+".txt"
    print(date)

    placeAndRecordCall(phoneNumberStockholmBrand, filenameRecording)
    openAndTranscribe(filenameRecording,filenameTranscription)
    transcribed_text, decision = openAndParse(filenameTranscription)
    print(decision)

    # print(transcribed_text)
    uploadResultToFirestoneDb("stockholm", date_webformat, decision, transcribed_text ,date_webformat)
    # uploadResultToFirestoneDb("testCity", date_webformat, decision, transcribed_text ,date_webformat)
