"""Elle giriş yapılan Chrome profiliyle yerel demo veya gerçek site aç."""

import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlsplit
import re
from getpass import GetPassWarning

from scrapedo_support import PROXY, ask_credentials, install_proxy_auth

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]


def chrome_error_codes(driver):
    """Chrome'un kendi hata belgesini başarılı bir yükleme sayma."""
    source = driver.page_source
    codes = sorted(set(re.findall(r'\bERR_[A-Z0-9_]+\b', source)))
    is_error_document = (driver.current_url.startswith('chrome-error://') or
                         'id="main-frame-error"' in source)
    return codes if is_error_document else []


def scrapedo_error(driver):
    """Scrape.do'nun HTTP hata gövdesini başarılı hedef belge sanma."""
    try:
        payload = json.loads(driver.find_element(By.TAG_NAME, 'body').text)
    except (ValueError, WebDriverException):
        return None
    if isinstance(payload, dict) and payload.get('ErrorType'):
        error_type = str(payload['ErrorType'])
        error_code = payload.get('ErrorCode')
        return f'{error_type}' + (f' (ErrorCode {error_code})' if error_code is not None else '')
    return None


def scrapedo_info():
    print('Scrape.do Proxy Mode:')
    print(f'  Sunucu: {PROXY}')
    print('  Proxy kullanıcı adı: Scrape.do panelindeki API tokenın')
    print('  Proxy parolası: render=false (servis parametresidir; hesap parolan değil)')
    print('  Tokenı proxy adresine ekleme veya burada paylaşma.')
    print('scrape.do seçilince token gizli olarak ve sessionId ayrıca sorulur.')
    print('Proxy bağlantısı HTTP kullanır; tokenın proxyye taşınması TLS ile korunmaz.')
    print('Bu Chrome oturumunda Scrape.do’nun ürettiği hedef sertifikaları için doğrulama kapatılır.')
    print('Kurulum açıklaması: README.md içindeki Scrape.do bölümü.')
    print('Resmi belge: https://scrape.do/documentation/proxy-mode/')


def normalize_proxy(value):
    """Adres:port girişini HTTP kabul et; hatalı adresleri reddet."""
    value = value.strip()
    if not value:
        raise ValueError('Proxy adresi boş olamaz.')
    if '://' not in value:
        value = 'http://' + value
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        raise ValueError('Proxy adresini ve portunu kontrol et.') from None
    if parsed.username is not None or parsed.password is not None:
        raise ValueError('Adrese kullanıcı adı/parola ekleme. Bu örnek proxy kimlik doğrulamasını otomatik yapmıyor.')
    if (parsed.scheme not in ('http', 'https', 'socks5')
            or not parsed.hostname or port is None or port < 1
            or parsed.path or parsed.query or parsed.fragment
            or any(char.isspace() for char in value)):
        raise ValueError('Adres HOST:PORT, http://HOST:PORT, https://HOST:PORT veya socks5://HOST:PORT olmalı (port: 1–65535).')
    if parsed.hostname.lower() == 'host':
        raise ValueError('HOST bir yer tutucudur; sağlayıcının verdiği gerçek adresi gir.')
    return value


def ask_proxy():
    candidate = os.environ.get('PROXY_URL', '')
    if candidate:
        try:
            normalized = normalize_proxy(candidate)
            if urlsplit(normalized).hostname == 'proxy.scrape.do':
                scrapedo_info()
            return normalized
        except ValueError as exc:
            print(f'PROXY_URL geçerli değil: {exc}')
    print('Proxy sağlayıcının verdiği sunucu adresini ve portunu gir.')
    print('Biçim: adres:port (HTTP) veya socks5://adres:port. API tokenı bu alana girilmez.')
    print('İptal etmek için q yaz. Girilen adres dosyaya kaydedilmez.')
    print('Scrape.do ile bağlanmak için scrape.do yaz; token sonraki adımda gizli sorulur.')
    while True:
        try:
            candidate = input('Proxy adresi: ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\nProxy girişi iptal edildi.')
            return None
        if candidate.lower() == 'q':
            return None
        if candidate.lower() in ('scrape.do', 'scrapedo'):
            return PROXY
        try:
            normalized = normalize_proxy(candidate)
            if urlsplit(normalized).hostname == 'proxy.scrape.do':
                scrapedo_info()
            return normalized
        except ValueError as exc:
            print(exc)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scrapedo-info', action='store_true', help='Scrape.do bağlantı gereksinimlerini göster ve çık.')
    parser.add_argument('--scrapedo', action='store_true', help='Doğrudan Scrape.do bağlantısını seç.')
    parser.add_argument('--headless', action='store_true', help='Pencere açmadan çalıştır.')
    parser.add_argument('--proxy', action='store_true', help='PROXY_URL kullan veya terminalde sor; URL verilmezse dış IP kontrolü yap.')
    parser.add_argument('--url', help='Açılacak gerçek sitenin http(s) adresi.')
    parser.add_argument('--keep-open', action='store_true', help='Kapatmadan önce terminalde Enter bekle.')
    parser.add_argument('--screenshot', action='store_true', help='Gerçek site için de ekran görüntüsü kaydet.')
    parser.add_argument('--block-images', action='store_true', help='Scrape.do modunda görselleri engelle; bazı sitelerin görünümü bozulabilir.')
    parser.add_argument('--super', action='store_true', help='Scrape.do super=true ile residential/mobile proxy kullan; daha fazla kota harcayabilir.')
    parser.add_argument('--driver', help='İsteğe bağlı ChromeDriver dosya yolu.')
    args = parser.parse_args()
    if args.scrapedo_info:
        scrapedo_info()
        return 0
    if args.scrapedo:
        args.proxy = True
        if not args.url:
            try:
                args.url = input('Proxy ile açılacak hedef URL [https://example.com]: ').strip() or 'https://example.com'
            except (EOFError, KeyboardInterrupt):
                print('\nHedef URL girişi iptal edildi.')
                return 2
    if args.url:
        try:
            target = urlsplit(args.url)
            valid_url = target.scheme in ('http', 'https') and target.hostname and not target.username and not target.password
        except ValueError:
            valid_url = False
        if not valid_url:
            parser.error('--url kullanıcı adı/parola içermeyen bir http(s) adresi olmalı.')
    if args.keep_open and args.headless:
        parser.error('--keep-open için --headless seçeneğini kaldır.')
    profile_dir = ROOT / 'chrome-data'
    # Linux Chrome kilidi bir sembolik bağlantıdır; hedefi dosya olmayabilir.
    if os.path.lexists(profile_dir / 'SingletonLock'):
        parser.error('Ödev profili kilitli. Bu profille açılan Chrome oturumunu kapatıp tekrar dene. Kilit dosyasını silme.')
    options = webdriver.ChromeOptions()
    options.binary_location = '/usr/bin/google-chrome-stable'
    options.add_argument('--window-size=1200,800')
    # chrome_profile.fish ile aynı kök ve alt profil; sırayla kullanılır.
    options.add_argument(f'--user-data-dir={profile_dir}')
    options.add_argument('--profile-directory=Default')
    # QUIC UDP kullanır ve HTTP proxy tünelinden geçmez.
    options.add_argument('--disable-quic')
    if args.headless:
        options.add_argument('--headless=new')
    credentials = None
    if args.proxy:
        proxy = PROXY if args.scrapedo else ask_proxy()
        if proxy is None:
            return 2
        if urlsplit(proxy).hostname == 'proxy.scrape.do':
            proxy = PROXY
            try:
                credentials = ask_credentials(args.super)
                # Chrome'un SPKI listesi bir sertifikanın kendi anahtarını
                # eşleştirir; CA anahtarını değil. Scrape.do ise her hedef için
                # farklı bir yaprak sertifika ürettiğinden CA SPKI'si burada
                # güven sağlamaz. Sağlayıcının proxy modu önerisi doğrultusunda
                # yalnızca bu Chrome sürecinde doğrulamayı kapat.
                options.add_argument('--ignore-certificate-errors')
                print('Bu Scrape.do Chrome oturumunda sertifika doğrulaması kapatıldı.')
            except (EOFError, KeyboardInterrupt):
                print('\nScrape.do kurulumu iptal edildi.')
                return 2
            except (ValueError, GetPassWarning) as exc:
                print(f'Scrape.do hazırlığı tamamlanamadı ({type(exc).__name__}). Token girişini kontrol et.')
                return 1
            # Chrome'un güncelleme, ölçüm ve ilk çalıştırma istekleri de
            # proxyden geçer. Bunları kapatmak, kota isteklerini hedef sayfa
            # ve onun gerekli kaynaklarıyla sınırlar.
            for argument in (
                '--disable-background-networking', '--disable-component-update',
                '--disable-domain-reliability', '--disable-sync', '--no-first-run',
                '--no-default-browser-check', '--metrics-recording-only',
            ):
                options.add_argument(argument)
            if args.block_images:
                # Profil tercihini değiştirmeden yalnızca bu süreçte uygula.
                options.add_argument('--blink-settings=imagesEnabled=false')
                print('Kota tasarrufu için görseller yüklenmeyecek.')
        options.add_argument(f'--proxy-server={proxy}')
        if credentials:
            print(f'Scrape.do HTTP proxy etkin: {proxy}')
    driver = None
    auth_state = None
    stage = 'Chrome başlatma'
    try:
        service = Service(executable_path=args.driver) if args.driver else Service()
        driver = webdriver.Chrome(service=service, options=options)
        stage = 'Proxy kimlik doğrulaması kurulumu'
        auth_state = install_proxy_auth(driver, *credentials) if credentials else None
        # İlk Scrape.do isteği curl tanısında yaklaşık 46 saniye sürdü. Chrome
        # tarafında bunun üzerine sayfanın kendi kaynakları da eklenebilir.
        driver.set_page_load_timeout(180 if credentials else 30)
        wait = WebDriverWait(driver, 10)
        stage = 'Sayfaya bağlanma'
        if args.url:
            driver.get(args.url)
            stage = 'Sayfa içeriğini bekleme'
            wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            codes = chrome_error_codes(driver)
            if codes:
                raise RuntimeError('Chrome hata belgesi: ' + ', '.join(codes))
            if credentials:
                provider_error = scrapedo_error(driver)
                if provider_error:
                    raise RuntimeError('Scrape.do yanıtı: ' + provider_error)
            print('Sayfa yüklendi. Site yanıtını ve giriş durumunu tarayıcıdan kontrol et.')
        elif args.proxy:
            driver.get('https://api.ipify.org')
            body = wait.until(EC.visibility_of_element_located((By.TAG_NAME, 'body')))
            # Bir hata sayfasını başarılı IP sonucu olarak raporlama.
            import ipaddress
            address = ipaddress.ip_address(body.text.strip())
            print(f'Proxy üzerinden görünen IP: {address}')
        else:
            driver.get((ROOT / 'demo.html').as_uri())
            wait.until(EC.visibility_of_element_located((By.ID, 'name'))).send_keys('Stajyer')
            driver.find_element(By.CSS_SELECTOR, 'button[type=submit]').click()
            wait.until(EC.text_to_be_present_in_element((By.ID, 'result'), 'Merhaba, Stajyer!'))
            print(driver.find_element(By.ID, 'result').text)
        if auth_state and (auth_state['rejected'] or auth_state['callback_failed']):
            print('Proxy kimlik doğrulaması tamamlanamadı. Tokenı ve hesap durumunu kontrol et.')
            return 1
        if args.keep_open:
            input('Tarayıcıyı kapatmak için terminalde Enter tuşuna bas: ')
        if not args.url or args.screenshot:
            output_dir = ROOT / 'outputs'
            output_dir.mkdir(exist_ok=True)
            filename = 'site.png' if args.url else ('proxy.png' if args.proxy else 'selenium-demo.png')
            screenshot = output_dir / filename
            if not driver.save_screenshot(str(screenshot)):
                raise OSError('Ekran görüntüsü kaydedilemedi.')
            print(f'Ekran görüntüsü: {screenshot}')
    except (EOFError, KeyboardInterrupt):
        print('Oturum kapatılıyor.')
        return 0
    except (WebDriverException, ValueError, OSError, RuntimeError) as exc:
        # Ham hata URL/token içerebilir; yalnızca ağ kodlarını göster.
        codes = sorted(set(re.findall(r'\bERR_[A-Z0-9_]+\b', str(exc))))
        print(f'Alıştırma başarısız. Aşama: {stage}. Hata türü: {type(exc).__name__}.')
        if codes:
            print('Chrome ağ kodu: ' + ', '.join(codes))
        if auth_state:
            print(f'Proxy doğrulama isteği: {auth_state["proxy_challenges"]}; kimlik bilgisi gönderimi: {auth_state["credentials_sent"]}')
        if auth_state and auth_state['rejected']:
            print('Proxy kimlik doğrulaması reddedildi; API tokenını ve hesap durumunu kontrol et.')
        elif auth_state and auth_state['callback_failed']:
            print('Proxy kimlik doğrulama callback işlemi başarısız oldu.')
        elif stage == 'Sayfaya bağlanma':
            print('Chrome açıldı ancak hedef sayfaya bağlantı tamamlanamadı.')
        if driver is not None and args.keep_open:
            try:
                input('Hata sayfasını inceleyebilirsin. Chrome’u kapatmak için Enter: ')
            except (EOFError, KeyboardInterrupt):
                pass
        return 1
    finally:
        if driver is not None:
            driver.quit()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
