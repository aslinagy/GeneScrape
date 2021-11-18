#!/usr/bin/python

import json
import requests
import httplib2 as http

from urllib.parse import urlparse
from pprint import pprint


if __name__ == '__main__':
    headers = {
    'Accept': 'application/json',
    }

    # uri = 'http://rest.genenames.org'
    # path = '/fetch/symbol/MKI67'

    target = urlparse('https://www.ebi.ac.uk/proteins/api/proteins?offset=0&size=100&accession=Q92734')
    method = 'GET'
    body = ''

    h = http.Http()

    response, content = h.request(
    target.geturl(),
    method,
    body,
    headers)

    if response['status'] == '200':
        # assume that content is a json reply
        # parse content with the json module
        data = json.loads(content)
        # print('Symbol:' + data['response']['docs'][0]['symbol'])
        pprint(data)

        with open('/home/joe/workspace/SzBK/GeneScrape/data/tfg_uniprot_example.json', 'w') as f:
            json.dump(data, f, indent=4)
    else:
        print('Error detected: ' + response['status'])


    # resp = requests.get(req_url)
    #
    # print(resp.status_code)
    # print(resp.raw)
    # print(resp.json())

