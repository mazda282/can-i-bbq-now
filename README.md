# KanJagGrillaNu

Well, this is the idea:

1. A script places a phonecall to brandstyrelsen
2. The Phonecall is recorded
3. The recorded phonecall is send to (google) speech to text cloud
4. A transcribed (txt) file is generated
5. The transcribed txt file is parsed for keywords (förbjuden) and a decision is made
6. The decision (JA, NEJ, nja) is uploaded to a Firestore database

Run recordAndTranscribe.py to test it out