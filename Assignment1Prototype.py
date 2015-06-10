'''Copyright (c) 2015 HG,DL,UTA
   Python program runs on local host, uploads, downloads, encrypts local files to google.
   Please use python 2.7.X, pycrypto 2.6.1 and Google Cloud python module '''
#import statements.
import argparse
import httplib2
import os
import sys
import json
import time
import datetime
import io
import hashlib
import pdb
#Google apliclient (Google App Engine specific) libraries.
import pdb
from apiclient import discovery
from oauth2client import file
from oauth2client import client
from oauth2client import tools
from googleapiclient.http import MediaIoBaseDownload
#pycry#pto libraries.
from Crypto import Random
from Crypto.Cipher import AES


# Encryption using AES
#You can read more about this in the following link
#http://eli.thegreenplace.net/2010/06/25/aes-encryption-of-files-in-python-with-pycrypto


#Initial password to create a key
password = 'mygooglepassword'
#key to use
key = hashlib.sha256(password).digest()

#this implementation of AES works on blocks of "text", put "0"s at the end if too small.
def pad(s):
    return s + b"\0" * (AES.block_size - len(s) % AES.block_size)

#Function to encrypt the message
def encrypt(message, key, key_size=16):
    message = pad(message)
    #iv is the initialization vector
    iv = Random.new().read(AES.block_size)
    #encrypt entire message
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return iv + cipher.encrypt(message)

#Function to decrypt the message
def decrypt(ciphertext, key):
    iv = ciphertext[:AES.block_size]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = cipher.decrypt(ciphertext[AES.block_size:])
    return plaintext.rstrip(b"\0")

#Function to encrypt a given file
def encrypt_file(file_name, key):
    #Open file to read content in the file, encrypt the file data and
    #create a new file and then write the encrypted data to it, return the encrypted file name.
        fd1 = open(file_name,"rb")
        content = fd1.read()
        encrypted_content = encrypt(content, key)
        fd1.close()
        fd2= open(fd1.name,"wb")
        fd2.write(encrypted_content)
        encrypted_file_name = fd2.name
        fd2.close()
        return encrypted_file_name



#Function to decrypt a given file.
def decrypt_file(file_name, key):
    #open file read the data of the file, decrypt the file data and
    #create a new file and then write the decrypted data to the file.
        fd = open(file_name,"rb")
        encrypted_content = fd.read()
        fd.close()
        decrypted_content = decrypt(encrypted_content, key)
        fd = open("new_decrypted_file","wb")
        fd.write(decrypted_content)
        decrypted_file_name = fd.name
        fd.close()
        return decrypted_file_name

        
#testinggg the code till now 
#file_name = encrypt_file("ReadMe",key)
#print "Encrypted filename "+file_name
#file_name = decrypt_file(file_name,key)
#print "Decrypted filename"+file_name


_BUCKET_NAME = 'aes_bucket' #name of your google bucket.
_API_VERSION = 'v1'

# Parser for command-line arguments.
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[tools.argparser])


# client_secret.json is the JSON file that contains the client ID and Secret.
#You can download the json file from your google cloud console.
CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secret.json')

# Set up a Flow object to be used for authentication.
# Add one or more of the following scopes. 
# These scopes are used to restrict the user to only specified permissions (in this case only to devstorage) 
FLOW = client.flow_from_clientsecrets(CLIENT_SECRETS,
  scope=[
      'https://www.googleapis.com/auth/devstorage.full_control',
      'https://www.googleapis.com/auth/devstorage.read_only',
      'https://www.googleapis.com/auth/devstorage.read_write',
    ],
    message=tools.message_if_missing(CLIENT_SECRETS))

#Downloads the specified object from the given bucket and deletes it from the bucket.
def get(service):
  #User can be prompted to input file name(using raw_input) that needs to be be downloaded, 
  #as an example file name is hardcoded for this function.
  #pdb.set_trace()
  file_name = raw_input("Enter filename to be downloaded\n")
  try:
# Get Metadata
    req = service.objects().get(
            bucket=_BUCKET_NAME,
            object=file_name,
            fields='bucket,name,metadata(my-key)',
        
                )                   
    resp = req.execute()
    print json.dumps(resp, indent=2)

# Get Payload Data
    req = service.objects().get_media(
            bucket=_BUCKET_NAME	,
            object=file_name,
        )
# The BytesIO object may be replaced with any io.Base instance.

    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, req, chunksize=1024*1024) #show progress at download
    done = False
    while not done:
        status, done = downloader.next_chunk()
        if status:
            print 'Download %d%%.' % int(status.progress() * 100)
        print 'Download Complete!'
    dec = decrypt(fh.getvalue(),key)
    with open(file_name, 'wb') as fo:
        fo.write(dec)
        print json.dumps(resp, indent=2)

  except client.AccessTokenRefreshError:
    print ("Error in the credentials")

    #Puts a object into file after encryption and deletes the object from the local PC.

#get(service)

def put(service):
    """User inputs the file name that needs to be uploaded.
       Encrypt the given file using AES encryption
       and then upload the file to your bucket on the google cloud storage.
       Remove the file from your local machine after the upload. """
    try:
        filename = raw_input("Enter File name\n")
        enc_file_name = encrypt_file(filename,key)
        req = service.objects().insert(media_body=enc_file_name,name=enc_file_name, bucket=_BUCKET_NAME)
        resp = req.execute()
        print '>Uploaded source file %s' % filename
        print json.dumps(resp, indent=2)
        os.remove(filename)
    except client.AccessTokenRefreshError:
        print ("Error in the credentials")
    except Exception as e:
        print "File named "+filename+"is not found please try again \n"


#Lists all the objects from the given bucket name
def listobj(service):
    """List all the objects that are present inside the bucket."""
    req = service.buckets().get(bucket=_BUCKET_NAME)
    resp = req.execute()
    fields_to_return = \
        'nextPageToken,items(name,size,contentType,metadata(my-key))'
    req = service.objects().list(bucket=_BUCKET_NAME, fields=fields_to_return)
    print "list of files in the current bucket are:"
    while req is not None:
        resp = req.execute()
        for object in resp["items"]:
            print object["name"],"\n"
        req = service.objects().list_next(req, resp)


#This deletes the object from the bucket
def deleteobj(service):
    '''Prompt the user to enter the name of the object to be deleted from your bucket.
        Pass the object name to the delete() method to remove the object from your bucket'''
    object_name = raw_input("Enter the filename you want to delete \n")
    #pdb.set_trace()
    try:
        service.objects().delete(bucket=_BUCKET_NAME, object=object_name).execute()
    except Exception as e:
        print "File named "+object_name+"is not found please try again \n"

def main(argv):
  # Parse the command-line flags.
  flags = parser.parse_args(argv[1:])
  #pdb.set_trace()
  
  #sample.dat file stores the short lived access tokens, which your application requests user data, attaching the access token to the request.
  #so that user need not validate through the browser everytime. This is optional. If the credentials don't exist 
  #or are invalid run through the native client flow. The Storage object will ensure that if successful the good
  # credentials will get written back to the file (sample.dat in this case). 
  storage = file.Storage('sample.dat')
  credentials = storage.get()
  if credentials is None or credentials.invalid:
    credentials = tools.run_flow(FLOW, storage, flags)

  # Create an httplib2.Http object to handle our HTTP requests and authorize it
  # with our good Credentials.
  http = httplib2.Http()
  http = credentials.authorize(http)

  # Construct the service object for the interacting with the Cloud Storage API.
  service = discovery.build('storage', _API_VERSION, http=http)
  #testing the get function

  #This is kind of switch equivalent in C or Java.
  #Store the option and name of the function as the key value pair in the dictionary.
  options = {1: put, 2: get, 3:listobj, 4:deleteobj}
  while(True):
      print "Welcome to the google cloud storage menu please select one of the following options\n"
      print "1.Put : Upload a local file to cloud storage\n"
      print "2.Get : Download a cloud file to local\n"
      print "3.List: List out all the files on the cloud\n"
      print "4.Delete : Delete a existing file\n"
      print "5.Quit : Quit from application\n"
      option = raw_input("Enter your choice from [1-5]\n")
      if option =="1":
          options[1](service)
      elif option =="2":
          options[2](service)
      elif option =="3":
          options[3](service)
      elif option =="4":
          options[4](service)
      elif option =="5":
          sys.exit(0)
      else:
          print "Invalid option please try again \n"

if __name__ == '__main__':
  main(sys.argv)
# [END all]
