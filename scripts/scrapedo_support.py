"""Scrape.do kimlik doğrulaması; token yalnızca bellekte tutulur."""

import base64
import getpass
import hashlib
import os
import subprocess
import warnings
from urllib.parse import urlsplit

PROXY = 'http://proxy.scrape.do:8080'
CA_URL = 'https://scrape.do/scrapedo_ca.crt'


def ask_credentials(super_proxy=False):
    print('Scrape.do proxy bağlantısı HTTP kullanır; proxy tokenı taşıma sırasında TLS ile korunmaz.')
    token = os.environ.get('SCRAPEDO_TOKEN', '').strip()
    while not token:
        # Gizli giriş mümkün değilse tokenı açık olarak isteme.
        with warnings.catch_warnings():
            warnings.simplefilter('error', getpass.GetPassWarning)
            token = getpass.getpass('Scrape.do API tokenı (gizli giriş): ').strip()
        if not token:
            print('Token boş olamaz. İptal için Ctrl+C.')
    if any(c.isspace() for c in token) or ':' in token:
        raise ValueError('Token biçimi hatalı; paneldeki API tokenını kullan.')
    while True:
        session = input('Scrape.do sessionId [1234, Enter ile kabul]: ').strip() or '1234'
        if session.isascii() and session.isdecimal() and 0 <= int(session) <= 1000000:
            break
        print('0–1000000 arasında bir tam sayı gir.')
    parameters = f'render=false&sessionId={int(session)}'
    if super_proxy:
        parameters += '&super=true'
        print('render=false ve super=true kullanılıyor. Residential/mobile proxy kotası daha yüksek olabilir.')
    else:
        print('render=false kullanılıyor. Tarayıcı istekleri Scrape.do kotasını kullanabilir.')
    print('Proxy IP oturumu 5 dakika hareketsizlikte sona erebilir; Chrome profili korunur.')
    return token, parameters


def ca_spki():
    """Resmi CA'yı TLS doğrulamasıyla al; yalnızca açık anahtar özetini döndür."""
    # Resmi uç nokta urllib istemcisine 403 döndürüyor; sistem curl'ü doğrulandı.
    cert = subprocess.run(
        ['curl', '--disable', '--fail', '--silent', '--show-error',
         '--proto', '=https', '--max-time', '30', '--max-filesize', '65536', CA_URL],
        capture_output=True, check=True, timeout=35,
    ).stdout
    if len(cert) > 65536:
        raise ValueError('CA yanıtı beklenenden büyük.')
    public_key = subprocess.run(
        ['openssl', 'x509', '-pubkey', '-noout'], input=cert,
        capture_output=True, check=True, timeout=10,
    ).stdout
    der = subprocess.run(
        ['openssl', 'pkey', '-pubin', '-outform', 'DER'], input=public_key,
        capture_output=True, check=True, timeout=10,
    ).stdout
    return base64.b64encode(hashlib.sha256(der).digest()).decode('ascii')


def install_proxy_auth(driver, username, password, proxy=PROXY):
    """Tokenı yalnızca beklenen proxy'nin 407 challenge'ına gönder."""
    devtools, connection = driver.start_devtools()
    expected = urlsplit(proxy)
    attempted = set()
    state = {'rejected': False, 'callback_failed': False, 'proxy_challenges': 0, 'credentials_sent': 0}

    def resume(event):
        try:
            connection.execute(devtools.fetch.continue_request(event.request_id))
        except Exception:
            state['callback_failed'] = True

    def authenticate(event):
        try:
            challenge = event.auth_challenge
            origin = urlsplit(challenge.origin)
            is_proxy = (challenge.source == 'Proxy' and
                        origin.hostname == expected.hostname and
                        origin.port == expected.port)
            if is_proxy:
                state['proxy_challenges'] += 1
            if not is_proxy:
                # Hedef sitenin 401 isteğine API tokenını ASLA gönderme.
                reply = devtools.fetch.AuthChallengeResponse('Default')
            elif event.request_id in attempted:
                state['rejected'] = True
                reply = devtools.fetch.AuthChallengeResponse('CancelAuth')
            else:
                attempted.add(event.request_id)
                state['credentials_sent'] += 1
                reply = devtools.fetch.AuthChallengeResponse('ProvideCredentials', username, password)
            connection.execute(devtools.fetch.continue_with_auth(event.request_id, reply))
        except Exception:
            # Callback traceback'leri hassas veri içerebilir; yalnızca durum döndür.
            state['callback_failed'] = True

    connection.add_callback(devtools.fetch.RequestPaused, resume)
    connection.add_callback(devtools.fetch.AuthRequired, authenticate)
    connection.execute(devtools.fetch.enable(handle_auth_requests=True))
    return state
