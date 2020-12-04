"""
The purpose of this ansible module is to assist with the interaction
of Cray APIs in a non-type-checked capacity.

Copyright 2019-2020 Hewlett Packard Enterprise Development LP
"""

from base64 import decodestring
import logging
import os
import subprocess
from json import loads
import sys

# CASMCMS-4926: Adjust import path while using this library to find
# provided, version pinned libraries outside of the context of the Base OS
# installed locations. Insert at position 0 so provided source is always
# preferred; this allows fallback to the nominal system locations once
# the base OS provided RPM content reaches parity.
sys.path.insert(0, '/opt/cray/crayctl/lib/python2.7/site-packages')

from ansible.module_utils.basic import AnsibleModule
from requests.exceptions import HTTPError
from requests.adapters import HTTPAdapter

import oauthlib.oauth2
from requests.packages.urllib3.util.retry import Retry
import requests_oauthlib


LOGGER = logging.getLogger()
ORGANIZATION = 'hpe'
LOG_DIR = '/var/log/%s' % ( ORGANIZATION )
PROTOCOL = 'https'
API_GW_DNSNAME = 'api-gw-service-nmn.local'
TOKEN_URL_DEFAULT = "{}://{}/keycloak/realms/shasta/protocol/openid-connect/token".format(PROTOCOL, API_GW_DNSNAME)
ENDPOINT_PREFIX = "{}://{}/apis/".format(PROTOCOL, API_GW_DNSNAME)
OAUTH_CLIENT_ID_DEFAULT = "admin-client"
CLIENT_SECRET_NAME = 'admin-client-auth'
CERT_PATH_DEFAULT = "/var/opt/cray/certificate_authority/certificate_authority.crt"
DEFAULT_METHOD = "get"
ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview', 'stableinterface'],
    'supported_by': ORGANIZATION
}
DOCUMENTATION = '''
---
module: authorized

short_description: This module interacts with Cray Authored APIs using
keycloak granted authorization credentials, as obtained through explicit
passing or via lookup. This module is modeled in part after the ansible
URI module.

version_added: "2.7.10"

description:
    - Authenticates requests to APIs via Ansible

options:
    token-url:
        required: False
        type: String
        default: {TOKEN_URL_DEFAULT}
    oauth-client-id:
        required: False
        type: String
        default: {OAUTH_CLIENT_ID_DEFAULT}
    oauth-client-secret:
        required: False
        type: String
        default: ''
    oauth-client-secret-name:
        required: False
        type: String
        default: {CLIENT_SECRET_NAME}
    certificate:
        required: False
        type: String
        default: {CERT_PATH_DEFAULT}
    method:
        type: String
        required: False
        default: {DEFAULT_METHOD}
    endpoint:
        type: String
        required: True
    body:
        required: False
        type: Object

author:
    - jsl
'''.format(
    DEFAULT_METHOD=DEFAULT_METHOD,
    CLIENT_SECRET_NAME=CLIENT_SECRET_NAME,
    TOKEN_URL_DEFAULT=TOKEN_URL_DEFAULT,
    OAUTH_CLIENT_ID_DEFAULT=OAUTH_CLIENT_ID_DEFAULT,
    CERT_PATH_DEFAULT=CERT_PATH_DEFAULT)

EXAMPLES = '''
- name: Obtain a list of defined sessiontemplates through BOS API
  authorized:
    endpoint: bos/v1/sessiontemplate
  delegate_to: "{{ groups['bis'][0] }}"
  run_once: true

- name: Create a new session template
  authorized:
    endpoint: bos/v1/sessiontemplate
    method: post
    body:
      name: "mprimm"
      cfs_url: "https://api-gw-service-nmn.local/vcs/cray/config-management.git"
      cfs_branch: master
      enable_cfs: True
      partition: "p1"
      boot_sets:
        computes:
          boot_ordinal: 1
          ims_image_id: '12345'
          kernel_parameters: "root=gogogogogo_wooooo"
          network: nmn
          node_roles_groups: ["Compute"]
          rootfs_provider: s3
          rootfs_provider_passthrough: "cache=true"
  delegate_to: "{{ groups['bis'][0] }}"
  run_once: true

- name: Create a boot session from a BOS session template
  authorized:
    endpoint: bos/v1/session
    method: post
    body:
      templateUuid: kbs
      operation: reboot
'''
RETURN = '''
response:
    description: The JSON structured response from the API
    type: dict
    returned: always
changed:
    description: An indication of change.
    type: boolean
    returned: always
'''


class AuthenticatedRequestModule(AnsibleModule):
    """
    This is a general purpose Ansible Module which allows for ansible to interact
    with an API in an authenticated capacity. This module does not otherwise
    check for accurate schematic content, but instead relies on the API in
    question to check the validity of the request.
    """
    def __init__(self, *args, **kwargs):
        super(AuthenticatedRequestModule, self).__init__(*args, **kwargs)
        # Expose Certain parameters as private attributes
        for keyword in ('oauth-client-secret-name', 'oauth-client-secret', 'method',
                        'endpoint'):
            if keyword in self.params:
                setattr(self, '_%s' %(keyword).replace('-', '_'), self.params[keyword])
        # Expose certain parameters as public attributes
        for keyword in ('oauth-client-id', 'certificate', 'token-url',
                        'ssl_cert', 'body'):
            if keyword in self.params:
                setattr(self, keyword.replace('-', '_'), self.params[keyword])

    @property
    def oauth_client_secret(self):
        if hasattr(self, "_oath_client_secret"):
            return self._oauth_client_secret
        # Populate client secret from k8s if not specified
        stdout = subprocess.check_output(['kubectl', 'get', 'secrets', self._oauth_client_secret_name,
                                           "-ojsonpath='{.data.client-secret}"])
        self._oauth_client_secret = decodestring(stdout.strip())
        return self._oauth_client_secret

    @property
    def endpoint(self):
        """
        The endpoint to contact; if the endpoint given to the __init__ method is
        prefixed with a protocol, use it as an absolute endpoint path, otherwise
        use the cluster gateway as a prefix.
        """
        if self._endpoint.startswith('http'):
            return self._endpoint
        else:
            return '%s%s' %(ENDPOINT_PREFIX, self._endpoint)

    @property
    def method(self):
        if self._method.lower() not in ('post', 'get', 'patch', 'delete'):
            raise AttributeError("Unsupported method type: '%s'" % (self._method))
        return getattr(self.session, self._method.lower())

    @property
    def session(self):
        """
        Create an authenticated session, or reference an existing session.
        """
        if hasattr(self, '_session'):
            return self._session
        if not all([self.oauth_client_id, self.oauth_client_secret, self.token_url]):
            raise ValueError('Invalid oauth configuration. Please check that the oauth_client_id, '
                             'oauth_client_secret and token_url parameters are being specified and '
                             'are correct. Determine the specific information that '
                             'is missing or invalid and then re-run the request with valid')
        oauth_client = oauthlib.oauth2.BackendApplicationClient(client_id=self.oauth_client_id)
        self._session = requests_oauthlib.OAuth2Session(
            client=oauth_client, auto_refresh_url=self.token_url,
            auto_refresh_kwargs={
                'client_id': self.oauth_client_id,
                'client_secret': self.oauth_client_secret}, token_updater=lambda t: None)
        self._session.verify = self.certificate
        self._session.timeout = 2000
        #Make the session resilient to service outages
        retries = Retry(total=10, backoff_factor=2, status_forcelist=[502, 503, 504])
        self._session.mount(self.endpoint, HTTPAdapter(max_retries=retries))
        # Bootstrap the client with a new token
        LOGGER.debug("Bootstrapping authorization token...")
        self._session.fetch_token(token_url=self.token_url,
                                 client_id=self.oauth_client_id,
                                 client_secret=self.oauth_client_secret)
        # Provide Logging hooks for generating authentication
        self._session.hooks['response'].append(AuthenticatedRequestModule.log_request)
        self._session.hooks['response'].append(AuthenticatedRequestModule.log_response)
        return self._session

    @staticmethod
    def log_request(resp, *args, **kwargs):
        """
        This function logs the request.
    
        Args:
            resp : The response
        """
        if LOGGER.isEnabledFor(logging.DEBUG):
            LOGGER.debug('\n%s\n%s\n%s\n\n%s',
                                       '-----------START REQUEST-----------',
                                       resp.request.method + ' ' + resp.request.url,
                                       '\n'.join('{}: {}'.format(k, v) for k, v in resp.request.headers.items()),
                                       resp.request.body)

    @staticmethod
    def log_response(resp, *args, **kwargs):
        """
        This function logs the response.
    
        Args:
            resp : The response
        """
        if LOGGER.isEnabledFor(logging.DEBUG):
            LOGGER.debug('\n%s\n%s\n%s\n\n%s',
                         '-----------START RESPONSE----------',
                         resp.status_code,
                         '\n'.join('{}: {}'.format(k, v) for k, v in resp.headers.items()),
                         resp.content)

    def __call__(self):
        self.session.fetch_token(token_url=self.token_url,
                                 client_id=self.oauth_client_id,
                                 client_secret=self.oauth_client_secret)
        result = {}
        response = None
        try:
            LOGGER.info("Endpoint: %s" % self.endpoint)
            LOGGER.info("Method: %s" % self.method)
            LOGGER.info("Body: %s" % self.body)
            response = self.method(self.endpoint, json=self.body)
            response.raise_for_status()
            try:
                result['response'] = loads(response.text)
            except ValueError:
                result['response'] = {"text": response.text} if hasattr(response, "text") and response.text else {}
        except HTTPError as hpe:
            if hasattr(response, 'text'):
                self.fail_json(msg="Exception running module: %s, response: %s" % (hpe, response.text))
            else:
                self.fail_json(msg="Exception running module: %s" % hpe)
        if self._method == 'get':
            result['changed'] = False
        else:
            result['changed'] = True
        self.exit_json(**result)


def main():
    fields = {# Authentication Information
              'token-url': {'required': False, "type": 'str', 'default': TOKEN_URL_DEFAULT},
              'oauth-client-id': {'required': False, "type": "str", 'default': OAUTH_CLIENT_ID_DEFAULT},
              'oauth-client-secret': {'required': False, "type": 'str'},
              'oauth-client-secret-name': {'required': False, "type": "str", "default": CLIENT_SECRET_NAME},
              'certificate': {'required': False, "type": "str", "default": CERT_PATH_DEFAULT},
              'method': {'required': False, 'type': "str", 'default': DEFAULT_METHOD},
              'endpoint': {'required': True, 'type': "str"},
              'body': {'required': False, 'type': "dict", "default": {}}
              }
    module = AuthenticatedRequestModule(argument_spec=fields)
    module()


if __name__ == '__main__':
    try:
        os.makedirs(LOG_DIR)
    except OSError:
        pass
    level = logging.DEBUG
    _disk_output_handler = logging.FileHandler(os.path.join(LOG_DIR, 'authorized_ansible_module.log'))
    _disk_output_handler.setLevel(level)
    LOGGER.addHandler(_disk_output_handler)
    LOGGER.setLevel(level)
    main()

