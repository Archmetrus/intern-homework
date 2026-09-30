"""Anti-Captcha ile Google reCAPTCHA v2 demo sayfasını çöz ve formu gönder."""

import argparse
from contextlib import contextmanager
import getpass
import json
import os
from pathlib import Path
import tempfile
import time
import urllib.error
import urllib.request
import warnings

from browser_config import configure_browser
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
CREATE_TASK = 'https://api.anti-captcha.com/createTask'
TASK_RESULT = 'https://api.anti-captcha.com/getTaskResult'
DEMO_URL = 'https://www.google.com/recaptcha/api2/demo'
# Google'ın herkese açık reCAPTCHA v2 demo anahtarı.
DEMO_SITE_KEY = '6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-'


def api_call(url, payload):
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={'Accept': 'application/json', 'Content-Type': 'application/json'},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    if not isinstance(data, dict):
        raise ValueError('API beklenen JSON nesnesini döndürmedi.')
    if data.get('errorId') != 0:
        code = data.get('errorCode', 'UNKNOWN_ERROR')
        raise RuntimeError(f'Anti-Captcha API hatası: {code}')
    return data


def solve(key):
    task = api_call(CREATE_TASK, {
        'clientKey': key,
        'task': {
            'type': 'RecaptchaV2TaskProxyless',
            'websiteURL': DEMO_URL,
            'websiteKey': DEMO_SITE_KEY,
        },
    })
    task_id = task.get('taskId')
    if not isinstance(task_id, int):
        raise ValueError('API geçerli bir görev kimliği döndürmedi.')
    print('CAPTCHA çözüm görevi oluşturuldu; sonuç bekleniyor (en fazla 180 saniye)...')
    deadline = time.monotonic() + 180
    started = time.monotonic()
    polls = 0
    while time.monotonic() < deadline:
        time.sleep(5)
        polls += 1
        result = api_call(TASK_RESULT, {'clientKey': key, 'taskId': task_id})
        if result.get('status') == 'ready':
            token = result.get('solution', {}).get('gRecaptchaResponse')
            if not isinstance(token, str) or not token:
                raise ValueError('API boş reCAPTCHA yanıtı döndürdü.')
            cost = result.get('cost')
            print(f'CAPTCHA çözüldü' + (f' (maliyet: ${cost})' if cost is not None else '') + '.')
            return token
        status = result.get('status')
        if status != 'processing':
            raise RuntimeError(f'Anti-Captcha görevi beklenmeyen durumda sonlandı: {status}')
        if polls == 1 or polls % 3 == 0:
            elapsed = int(time.monotonic() - started)
            print(f'CAPTCHA hâlâ işleniyor ({elapsed} saniye geçti)...', flush=True)
    raise TimeoutError('Anti-Captcha sonucu 180 saniye içinde hazır olmadı.')


@contextmanager
def open_demo(driver_path=None):
    options = webdriver.ChromeOptions()
    configure_browser(options)
    options.add_argument('--window-size=1200,800')
    # CAPTCHA yanıtının tarayıcı profilinde kalmaması için geçici profil kullan.
    with tempfile.TemporaryDirectory(prefix='anticaptcha-demo-', dir=ROOT) as profile:
        options.add_argument(f'--user-data-dir={profile}')
        service = Service(executable_path=driver_path) if driver_path else Service()
        driver = webdriver.Chrome(service=service, options=options)
        try:
            driver.get(DEMO_URL)
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, 'g-recaptcha-response')))
            print('Chrome açıldı; CAPTCHA çözümü bekleniyor...')
            yield driver
        finally:
            driver.quit()


def submit_token(driver, token, keep_open):
    driver.execute_script('''
        const response = arguments[0];
        const field = document.getElementById('g-recaptcha-response');
        field.value = response;
        field.innerHTML = response;
        field.dispatchEvent(new Event('change', {bubbles: true}));
        document.querySelector('form').submit();
    ''', token)
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
    if 'Success' not in driver.find_element(By.TAG_NAME, 'body').text:
        raise RuntimeError('Demo formu başarı yanıtı vermedi.')
    print('Google reCAPTCHA demo formu başarıyla gönderildi.')
    if keep_open:
        input('Tarayıcıyı kapatmak için terminalde Enter tuşuna bas: ')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--keep-open', action='store_true', help='Başarılı gönderimden sonra Chrome’u açık tut.')
    parser.add_argument('--driver', help='İsteğe bağlı ChromeDriver dosya yolu.')
    args = parser.parse_args()
    print('Google reCAPTCHA demo sayfası için bir Anti-Captcha görevi oluşturulacak; kota kullanılabilir.')
    key = os.environ.get('ANTICAPTCHA_API_KEY', '').strip()
    try:
        if not key:
            with warnings.catch_warnings():
                warnings.simplefilter('error', getpass.GetPassWarning)
                key = getpass.getpass('Anti-Captcha API anahtarı (gizli giriş): ').strip()
        if not key or any(char.isspace() for char in key):
            print('Geçerli bir Anti-Captcha API anahtarı gerekli.')
            return 2
        with open_demo(args.driver) as driver:
            token = solve(key)
            submit_token(driver, token, args.keep_open)
        return 0
    except (EOFError, KeyboardInterrupt):
        print('\nİptal edildi.')
        return 2
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError, RuntimeError,
            TimeoutError, WebDriverException) as exc:
        print(f'Akış tamamlanamadı ({type(exc).__name__}): {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
