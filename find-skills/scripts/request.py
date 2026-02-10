import hmac
import hashlib
import secrets
import urllib.parse
from datetime import datetime, timezone
from typing import Dict, Optional, Any
import requests


def generate_random_bytes_hex(size: int) -> str:
    """Generate random bytes and convert to hex string"""
    return secrets.token_hex(size)


def percent_code(s: str) -> str:
    """URL encode with custom replacements"""
    encoded = urllib.parse.quote(str(s), safe='')
    replacements = {
        '!': '%21',
        '(': '%28',
        ')': '%29',
        '+': '%20',
        "'": '%27',
        '*': '%2A'
    }
    for char, code in replacements.items():
        encoded = encoded.replace(urllib.parse.quote(char, safe=''), code)
    return encoded


def hmac_sha256(key: str, data: str) -> str:
    """Calculate HMAC-SHA256"""
    key_bytes = key.encode('utf-8')
    data_bytes = data.encode('utf-8')
    hmac_digest = hmac.new(key_bytes, data_bytes, hashlib.sha256)
    return hmac_digest.hexdigest().lower()


def hmac_sha1(key: str, data: str) -> str:
    """Calculate HMAC-SHA1 and return base64 encoded"""
    import base64
    key_bytes = key.encode('utf-8')
    data_bytes = data.encode('utf-8')
    hmac_digest = hmac.new(key_bytes, data_bytes, hashlib.sha1)
    return base64.b64encode(hmac_digest.digest()).decode('utf-8')


def sha256_hex(s: str) -> str:
    """Calculate SHA256 hash"""
    hash_digest = hashlib.sha256(s.encode('utf-8'))
    return hash_digest.hexdigest().lower()


class POPRequest:
    """
    POP Request class for Alibaba Cloud API calls
    """

    ALGORITHM = 'ACS3-HMAC-SHA256'
    SIGNATURE_VERSION_V1 = '1.0'
    SIGNATURE_VERSION_V3 = '3.0'

    def __init__(
            self,
            http_method: str,
            canonical_uri: str,
            x_acs_action: str,
            host: str,
            base_url: str,
            x_acs_version: str,
            environment: str = 'production',
            signature_version: str = '1.0'
    ):
        """
        Initialize POP Request

        Args:
            http_method: HTTP method (GET, POST, PUT, etc.)
            canonical_uri: URI path
            x_acs_action: Alibaba Cloud action name
            host: Host header value
            base_url: Base URL for the request
            x_acs_version: API version
            environment: Environment ('development' or 'production')
        """
        self.http_method = http_method.upper()
        self.canonical_uri = canonical_uri if environment == 'development' else '/'
        self.host = host
        self.base_url = base_url
        self.x_acs_version = x_acs_version
        self.x_acs_action = x_acs_action
        self.environment = environment
        self.signature_version = signature_version
        self.headers: Dict[str, str] = {}
        self.body: Optional[str] = None
        self.query_param: Dict[str, Any] = {}
        self.app_version: str = '1.0.0'  # Default version

        self._init_builder()

    def _init_builder(self):
        """Initialize request headers"""
        date = datetime.now(timezone.utc)
        if self.signature_version == '1.0':
            # V1 signature doesn't use custom headers
            self.headers = {}
        else:
            # V3 signature uses custom x-acs headers
            self.headers = {
                'host': self.host,
                'x-acs-action': self.x_acs_action,
                'x-acs-version': self.x_acs_version,
                'x-acs-date': date.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'x-acs-signature-nonce': generate_random_bytes_hex(6)
            }

    def set_body(self, body: str):
        """Set request body"""
        self.body = body
        return self

    def set_query_params(self, params: Dict[str, Any]):
        """Set query parameters"""
        self.query_param = params
        return self

    def set_app_version(self, version: str):
        """Set application version"""
        self.app_version = version
        return self

    def get_signature_v1(self) -> str:
        """
        Generate signature using V1 method (HMAC-SHA1)

        Returns:
            Signature string
        """
        # Build complete query parameters including signature params
        all_params = self.query_param.copy()
        all_params.update({
            'Format': 'JSON',
            'Version': self.x_acs_version,
            'SignatureMethod': 'HMAC-SHA1',
            'Timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'SignatureVersion': '1.0',
            'SignatureNonce': generate_random_bytes_hex(16),
            'Action': self.x_acs_action
        })

        # Sort parameters
        sorted_params = sorted(all_params.items())

        # Build canonical query string
        canonical_query_string = '&'.join(
            f"{percent_code(key)}={percent_code(str(value))}"
            for key, value in sorted_params
        )

        # Build string to sign
        string_to_sign = f"{self.http_method}&{percent_code('/')}&{percent_code(canonical_query_string)}"

        # Calculate signature
        signature = hmac_sha1('' + '&', string_to_sign)

        # Add signature to params
        all_params['Signature'] = signature

        # Store for URL building
        self.signed_params = all_params

        return signature

    def get_authorization(self) -> str:
        """
        Generate authorization header

        Returns:
            Authorization header value
        """
        try:
            if self.signature_version == '1.0':
                # V1 uses query parameter signature, not Authorization header
                return self.get_signature_v1()

            # V3 signature method (ACS3-HMAC-SHA256)
            # Step 1: Build canonical query string
            canonical_query_string = '&'.join(
                f"{percent_code(key)}={percent_code(value)}"
                for key, value in sorted(self.query_param.items())
            )

            # Request payload
            request_payload = self.body or ''
            hashed_request_payload = sha256_hex(request_payload)
            self.headers['x-acs-content-sha256'] = hashed_request_payload

            # Convert all header keys to lowercase
            self.headers = {k.lower(): v for k, v in self.headers.items()}

            # Filter and sort headers
            sorted_keys = sorted([
                key for key in self.headers.keys()
                if key.startswith('x-acs-') or key == 'host' or key == 'content-type'
            ])

            # Signed headers list
            signed_headers = ';'.join(sorted_keys)

            # Build canonical headers
            canonical_headers = ''.join(
                f"{key}:{self.headers[key]}\n"
                for key in sorted_keys
            )

            # Build canonical request
            canonical_request = (
                f"{self.http_method}\n"
                f"{self.canonical_uri}\n"
                f"{canonical_query_string}\n"
                f"{canonical_headers}\n"
                f"{signed_headers}\n"
                f"{hashed_request_payload}"
            )

            # Step 2: Build string to sign
            hashed_canonical_request = sha256_hex(canonical_request)
            string_to_sign = f"{self.ALGORITHM}\n{hashed_canonical_request}"

            # Step 3: Calculate signature
            signature = hmac_sha256('', string_to_sign)

            # Step 4: Build Authorization header
            authorization = (
                f"{self.ALGORITHM} "
                f"Credential={self.access_key_id},"
                f"SignedHeaders={signed_headers},"
                f"Signature={signature}"
            )
            self.headers['authorization'] = authorization

            return authorization

        except Exception as e:
            print(f"Failed to get authorization: {e}")
            raise

    def get_url(self) -> str:
        """
        Build complete URL with query parameters

        Returns:
            Complete URL string
        """
        protocol = 'http' if self.environment == 'development' else 'https'
        url = f"{protocol}://{self.base_url}{self.canonical_uri}"

        if self.signature_version == '1.0':
            # V1 signature: use signed_params generated by get_signature_v1
            if hasattr(self, 'signed_params'):
                query_string = urllib.parse.urlencode(self.signed_params)
                url += f"?{query_string}"
        else:
            # V3 signature: build query params normally
            if self.query_param:
                query_params = {
                    'Format': 'json',
                    'Action': self.x_acs_action,
                    'AppVersion': self.app_version
                }

                for key, value in self.query_param.items():
                    if self.environment == 'development':
                        # Convert first letter to lowercase in development
                        param_key = key[0].lower() + key[1:] if key else key
                    else:
                        param_key = key
                    query_params[param_key] = str(value)

                query_string = urllib.parse.urlencode(query_params)
                url += f"?{query_string}"

        return url

    def get_headers(self) -> Dict[str, str]:
        """
        Get request headers as dictionary

        Returns:
            Dictionary of headers
        """
        return {key: str(value) for key, value in self.headers.items()}

    async def call_async(self) -> str:
        """
        Make async HTTP request (requires aiohttp)

        Returns:
            Response text
        """
        try:
            import aiohttp

            self.get_authorization()
            url = self.get_url()

            async with aiohttp.ClientSession() as session:
                if self.http_method in ['POST', 'PUT'] and self.body:
                    async with session.request(
                            self.http_method,
                            url,
                            headers=self.get_headers(),
                            data=self.body
                    ) as response:
                        return await response.text()
                else:
                    async with session.request(
                            self.http_method,
                            url,
                            headers=self.get_headers()
                    ) as response:
                        return await response.text()

        except ImportError:
            raise ImportError("aiohttp is required for async calls. Install with: pip install aiohttp")
        except Exception as e:
            print(f"Failed to send request: {e}")
            raise

    def call(self) -> str:
        """
        Make synchronous HTTP request

        Returns:
            Response text
        """
        try:
            self.get_authorization()
            url = self.get_url()

            if self.http_method in ['POST', 'PUT'] and self.body:
                response = requests.request(
                    self.http_method,
                    url,
                    headers=self.get_headers(),
                    data=self.body
                )
            else:
                response = requests.request(
                    self.http_method,
                    url,
                    headers=self.get_headers()
                )

            response.raise_for_status()
            return response.text

        except requests.exceptions.RequestException as e:
            print(f"Failed to send request: {e}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            raise


def parse_event(event_str: str) -> Dict[str, str]:
    """
    Parse Server-Sent Events (SSE) format

    Args:
        event_str: SSE formatted string

    Returns:
        Dictionary with event data
    """
    event = {}
    lines = event_str.split('\n')

    for line in lines:
        if line.startswith('data: '):
            event['data'] = line.replace('data: ', '', 1)
        elif line.startswith('id: '):
            event['id'] = line.replace('id: ', '', 1)
        elif line.startswith('event: '):
            event['event'] = line.replace('event: ', '', 1)

    return event


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 4:
        print("Usage: python request.py <action> <query> <topk>")
        print("Example: python request.py SearchPublicMarketSkill 'slack' 10")
        sys.exit(1)

    action = sys.argv[1]
    query = sys.argv[2]
    topk = sys.argv[3]

    # Configuration
    config = {
        'host': 'wuyingai.cn-shanghai.aliyuncs.com',
        'base_url': 'wuyingai.cn-shanghai.aliyuncs.com',
        'x_acs_version': '2026-01-08'
    }

    # Create request
    request = POPRequest(
        http_method='GET',
        canonical_uri='/',
        x_acs_action=action,
        **config
    )

    # Set query parameters from command line arguments
    request.set_query_params({
        'UserQuery': query,
        'TopK': topk
    })

    # Make request
    try:
        response = request.call()
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")