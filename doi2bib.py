# import sys
import urllib.request
from urllib.error import HTTPError
import sys

BASE_URL = 'http://dx.doi.org/'

def grab(doi):
    url = BASE_URL + doi
    req = urllib.request.Request(url)
    req.add_header('Accept', 'application/x-bibtex')
    try:
        with urllib.request.urlopen(req) as f:
            bibtex = f.read().decode()
        return ('Success',bibtex)
    except HTTPError as e:
        if e.code == 404:
            return ('DOI not found.',None)
        else:
            return('Service unavailable.',None)
        
if __name__ == "__main__":
    try:
        doi = sys.argv[1]
    except IndexError:
        print('Usage:\n{} <doi>'.format(sys.argv[0]))
        sys.exit(1)

    out = grab(doi)
    if out[0] != 'Success':
        print(out[0])
        sys.exit(1)
    else:
        print(out[1])