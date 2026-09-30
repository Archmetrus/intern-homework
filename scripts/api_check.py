"""Anti-Captcha bakiyesi veya PhantomBuster otomasyon sayısını sorgula."""

import argparse
import json
import os
import urllib.error
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('service', choices=['anticaptcha', 'phantombuster'])
    args = parser.parse_args()
    variable = 'ANTICAPTCHA_API_KEY' if args.service == 'anticaptcha' else 'PHANTOMBUSTER_API_KEY'
    key = os.environ.get(variable, '').strip()
    if not key:
        parser.error(f'{variable} tanımlı değil. fish içinde read --silent --export kullan.')
    headers = {'Accept': 'application/json'}
    if args.service == 'anticaptcha':
        url = 'https://api.anti-captcha.com/getBalance'
        headers['Content-Type'] = 'application/json'
        payload = json.dumps({'clientKey': key}).encode()
    else:
        url = 'https://api.phantombuster.com/api/v2/agents/fetch-all'
        headers['X-Phantombuster-Key'] = key
        org = os.environ.get('PHANTOMBUSTER_ORG_ID', '').strip()
        if org:
            headers['X-Phantombuster-Org'] = org
        payload = None
    # Kimlik doğrulama başlıklarını farklı bir adrese yönlendirmede gönderme.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    try:
        request = urllib.request.Request(url, data=payload, headers=headers)
        with urllib.request.build_opener(NoRedirect).open(request, timeout=30) as response:
            data = json.load(response)
        if args.service == 'anticaptcha':
            if not isinstance(data, dict) or data.get('errorId') != 0 or 'balance' not in data:
                print('API başarısız yanıt verdi. Anahtarı ve hesap durumunu kontrol et.')
                return 1
            print(f'Anti-Captcha bakiyesi (USD): {data["balance"]}')
        else:
            if not isinstance(data, list):
                print('Beklenen otomasyon listesi alınamadı; hesap/organizasyon ayarlarını kontrol et.')
                return 1
            print(f'PhantomBuster otomasyon sayısı: {len(data)}')
    except urllib.error.HTTPError as exc:
        print(f'HTTP {exc.code}: hesap yetkisini, API anahtarını ve servis limitlerini kontrol et.')
        return 1
    except (urllib.error.URLError, OSError, ValueError):
        print('Bağlantı kurulamadı veya geçerli JSON alınamadı (30 saniye zaman aşımı).')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
