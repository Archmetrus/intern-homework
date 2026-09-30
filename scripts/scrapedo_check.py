"""Aynı token ile API ve proxy modunu karşılaştır; Chrome kullanmaz."""

import getpass
import json
import os
from pathlib import Path
import subprocess
import tempfile
from urllib.parse import urlencode
import warnings

from scrapedo_support import CA_URL, PROXY

ROOT = Path(__file__).resolve().parents[1]


def curl_check(url, token, ca_file=None):
    # Token argv'ye veya diske yazılmaz; curl ayarlarını stdin'den okur.
    def quote(value):
        return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'

    config = ['url = ' + quote(url)]
    if ca_file:
        config += ['proxy = ' + quote(PROXY),
                   'proxy-user = ' + quote(token + ':render=false&sessionId=1234'),
                   'cacert = ' + quote(str(ca_file)), 'noproxy = ""']
    else:
        config += ['noproxy = "*"']
    result = subprocess.run(
        ['curl', '--disable', '--config', '-', '--silent', '--show-error',
         # CONNECT sonrasındaki TLS el sıkışması da curl tarafından bağlantı
         # aşaması sayılır. 15 saniyelik connect-timeout, ilan edilen 90
         # saniyelik toplam sınırı fiilen devre dışı bırakıyordu.
         '--max-time', '90', '--output', os.devnull,
         '--write-out', '%{json}'],
        input='\n'.join(config) + '\n', text=True, capture_output=True, timeout=95,
    )
    # %{json}, tam URL ve token içerebilir; yalnızca seçilen sayısal alanları göster.
    try:
        metadata = json.loads(result.stdout)
    except ValueError:
        metadata = {}
    # Bağlantının hangi aşamada takıldığını, URL veya kimlik bilgisi açmadan
    # göster. time_appconnect HTTPS tünelinin içindeki TLS el sıkışmasının,
    # time_starttransfer ise hedefin ilk yanıt baytının zamanıdır.
    summary = {key: metadata.get(key) for key in (
        'http_code', 'http_connect', 'size_download', 'time_connect',
        'time_appconnect', 'time_starttransfer', 'time_total',
        'ssl_verify_result',
    )}
    summary['curl_exit'] = result.returncode
    return summary


def main():
    print('İki tanı isteği gönderilecek: API ve HTTP proxy üzerinden https://example.com.')
    print('Başarılı istekler Scrape.do kotasını kullanabilir. Token ekrana/dosyaya yazılmaz.')
    print('Proxy kontrolünde tokenın proxyye taşınması TLS ile korunmaz.')
    token = os.environ.get('SCRAPEDO_TOKEN', '').strip()
    try:
        if not token:
            with warnings.catch_warnings():
                warnings.simplefilter('error', getpass.GetPassWarning)
                token = getpass.getpass('Scrape.do API tokenı: ').strip()
        if not token or any(c.isspace() for c in token) or ':' in token:
            print('Geçerli API tokenı gerekli.')
            return 2
        api_url = 'https://api.scrape.do/?' + urlencode({
            'token': token, 'url': 'https://example.com', 'render': 'false', 'sessionId': 1234,
        })
        print('API kontrolü yapılıyor (en fazla 90 saniye)...', flush=True)
        api = curl_check(api_url, token)
        print('API:', json.dumps(api))
        # Yalnızca herkese açık CA geçici dosyaya yazılır, işlem sonunda kaldırılır.
        with tempfile.TemporaryDirectory(prefix='ca-check-', dir=ROOT) as folder:
            ca = Path(folder) / 'scrapedo.crt'
            subprocess.run(['curl', '--disable', '--fail', '--silent', '--show-error',
                            '--max-time', '30', '--output', str(ca), CA_URL],
                           capture_output=True, check=True, timeout=35)
            print('Proxy kontrolü yapılıyor (en fazla 90 saniye)...', flush=True)
            proxy = curl_check('https://example.com', token, ca)
        print('PROXY:', json.dumps(proxy))
        good = lambda result: result['curl_exit'] == 0 and result['http_code'] == 200
        if good(api) and good(proxy):
            print('API ve proxy çalışıyor. Selenium/Chrome bağlantısını incelemeliyiz.')
        elif good(api):
            print('API çalışıyor, proxy başarısız. Proxy taşıması/sertifikası/servis yanıtı incelenmeli.')
            if proxy['http_connect'] == 200 and proxy['time_appconnect'] == 0:
                print('CONNECT kabul edildi; ancak proxy tünelindeki TLS el sıkışması başlamadı/tamamlanmadı.')
            elif proxy['http_connect'] == 200 and proxy['time_starttransfer'] == 0:
                print('CONNECT ve TLS tamamlandı; proxy veya hedef site ilk HTTP yanıtını zamanında göndermedi.')
        elif good(proxy):
            print('Proxy çalışıyor, API başarısız. API erişimi ayrıca incelenmeli.')
        else:
            print('Chrome olmadan da hata oluşuyor; tek neden Selenium olarak gösterilemez.')
        print('curl_exit: 0=istek tamamlandı, 28=zaman aşımı, 35=TLS hatası, 52=boş yanıt, 60=sertifika hatası.')
        print('CONNECT 407=proxy kimlik doğrulaması gerekli/reddedildi. HTTP durumunu panel kayıtlarıyla karşılaştır.')
        return 0 if good(api) and good(proxy) else 1
    except (EOFError, KeyboardInterrupt):
        print('\nİptal edildi.')
        return 2
    except (OSError, subprocess.SubprocessError, getpass.GetPassWarning) as exc:
        print(f'Tanı tamamlanamadı ({type(exc).__name__}); curl, ağ erişimi veya gizli token girişini kontrol et.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
