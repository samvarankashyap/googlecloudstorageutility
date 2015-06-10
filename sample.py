"""Command-line sample application for listing all objects
in a bucket using the Cloud Storage API.
Before running, authenticate with the Google Cloud SDK by running:
    $ gcloud auth login
Usage:
    $ python list_objects.py <your-bucket>
You can also get help on all the command-line flags the program understands
by running:
    $ python list_objects.py --help
"""

import argparse
import json
import sys

from apiclient import discovery
from oauth2client.client import GoogleCredentials


# Parser for command-line arguments.
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('bucket')


def main(argv):
    # Parse the command-line flags.
    args = parser.parse_args(argv[1:])

    # Get the application default credentials. When running locally, these are
    # available after running `gcloud auth login`. When running on compute
    # engine, these are available from the environment.
    credentials = GoogleCredentials.get_application_default()

    # Construct the service object for interacting with the Cloud Storage API.
    service = discovery.build('storage', 'v1', credentials=credentials)

    # Make a request to buckets.get to retrieve information about the bucket.
    req = service.buckets().get(bucket=args.bucket)
    resp = req.execute()
    print json.dumps(resp, indent=2)

    # Create a request to objects.list to retrieve a list of objects.
    fields_to_return = \
        'nextPageToken,items(name,size,contentType,metadata(my-key))'
    req = service.objects().list(bucket=args.bucket, fields=fields_to_return)

    # If you have too many items to list in one request, list_next() will
    # automatically handle paging with the pageToken.
    while req is not None:
        resp = req.execute()
        print json.dumps(resp, indent=2)
        req = service.objects().list_next(req, resp)

if __name__ == '__main__':
    main(sys.argv)
# [END all]
