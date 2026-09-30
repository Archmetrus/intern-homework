# Staj ödevi: tarayıcı otomasyonu

## Bağımsız kurulum

Depoyu klonladıktan sonra proje dizinine girin. Örnek komutlar bu dizinden çalıştırılır.

```sh
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
```

Windows: `py -m venv .venv`, ardından `.venv\Scripts\python -m pip install -r requirements.txt`. Fish başlatıcısı için fish gerekir; Python demoları doğrudan çalıştırılabilir.

`CHROME_PATH` ile Chrome/Chromium çalıştırılabilir dosyasını seçebilirsiniz. Varsayılan olarak PATH aranır, bulunamazsa Selenium Manager tarayıcıyı bulur. Sürücü için mevcut `--driver` seçeneğini kullanın; testlerde `CHROMEDRIVER_PATH` kullanılabilir.


Bu rehber; proxy, Chrome profilleri ve tarayıcı otomasyonu konularını uygulamalı
öğrenmek için hazırlanmıştır. Anlatım dili Türkçedir. İşletim sistemi Arch Linux
tabanlı CachyOS olarak kontrol edilmiştir. Teslim biçimi ve ödev için belirlenen
servisler henüz netleşmemiştir. Kabuk örnekleri Linux/fish içindir. Chrome komut adı dağıtıma göre değişebilir;
Python demoları tarayıcıyı otomatik bulur veya `CHROME_PATH` değerini kullanır.
Henüz ücretli servis kullanılmadı veya harici hesaplarda işlem yapılmadı.

## 1. curl ile proxy kullanımı

Proxy, bilgisayarın ile hedef sunucu arasındaki isteği ileten bir aracıdır.
Önce doğrudan gönderilen istek ile proxy üzerinden gönderilen isteği karşılaştır.
Aşağıdaki HOST ve PORT alanlarını gerçek proxy adresi ve portuyla değiştir;
bunlar örnek yer tutuculardır.

```fish
curl --noproxy '*' --fail --show-error --max-time 30 https://api.ipify.org
curl --noproxy '' --proxy http://HOST:PORT --fail --show-error --max-time 30 https://api.ipify.org
```

Kimlik doğrulaması isteyen proxy için `--proxy-user KULLANICI_ADI` ekle.
Yalnızca kullanıcı adı verildiğinde curl parolayı etkileşimli olarak ister.
SOCKS kullanırken alan adının proxy üzerinden çözümlenmesi için
`--proxy socks5h://HOST:PORT` kullan.

Gösterilecek sonuç: Her istekte görünen IP adresini kaydet ve sonucu açıkla.
IP adreslerinin aynı olması tek başına başarısızlık anlamına gelmez; yerel bir
proxy aynı internet bağlantısını kullanabilir. HTTP 407, proxy kimlik doğrulaması
gerektiğini belirtir. Bağlantı hatalarında önce adresi, portu ve erişilebilirliği kontrol et.

Kaynak: [curl kullanım kılavuzu](https://curl.se/docs/manpage.html).

## 2. Chrome için ayrı kullanıcı verisi dizini oluşturma

Kullanıcı verisi dizini (user data directory), tarayıcı verilerini ve profilleri
barındırır. `--user-data-dir` bu ana dizini, `--profile-directory` ise içindeki
bir profili seçer. Chrome, yazma izni varsa yeni kullanıcı verisi dizinini ilk
açılışta oluşturur.

```fish
google-chrome-stable --user-data-dir="$PWD/chrome-data" --profile-directory=Default https://example.com
```

Chrome'un çalıştırılabilir dosya adı ve yolu işletim sistemine göre değişebilir;
Chromium kullanılıyorsa komut adı `chromium` olabilir. `chrome://version` sayfasını
aç ve **Profil Yolu (Profile Path)** alanını incele. Bir yer işareti ekle, bu
Chrome oturumunu kapat ve aynı parametrelerle yeniden aç. Yer işaretinin
korunduğunu doğrula. Aynı kullanıcı verisi diziniyle iki bağımsız Chrome sürecini
aynı anda başlatma.

Gösterilecek sonuç: Profilin dosya yolu ve yeniden başlatma sonrasında korunan yer işareti.

Kaynak: [Chromium profilleri](https://www.chromium.org/developers/creating-and-using-profiles/).

## 3. Chrome ile proxy kullanımı

Profil alıştırmasına proxy ayarını ekle:

```fish
google-chrome-stable --user-data-dir="$PWD/chrome-data" --proxy-server=http://HOST:PORT https://api.ipify.org
```

Başlatma parametrelerini değiştirmeden önce bu dizini kullanan Chrome oturumunu
kapat. Chrome'un URL içine yazılan proxy kullanıcı adı ve parolasını kabul
edeceğini varsayma; kimlik doğrulama kurulumu proxy türüne göre ayrıca ele alınmalıdır.

Gösterilecek sonuç: Chrome'da görünen IP adresini aynı proxy ile çalışan curl
sonucuyla karşılaştır. Tarayıcıya verilen proxy ayarı, curl'ün veya tüm işletim
sisteminin proxy ayarını değiştirmez.

Kaynak: [Chromium ağ ayarları](https://www.chromium.org/developers/design-documents/network-settings/).

## 4. Selenium

Python ile Chrome'u aynı seçeneklerle başlat, bir demo sayfasına git, bir öğenin
hazır olmasını bekle, metnini oku ve tarayıcıyı `finally` bloğunda kapat.
Belirli koşulların gerçekleşmesini beklemek için explicit wait kullan.
İlk alıştırmayı proxy olmadan çalıştır; ardından doğruladığın proxy ayarıyla tekrarla.

Gösterilecek sonuç: Tekrar çalıştırılabilen bir betik, çıktısı ve ekran görüntüsü.
Tarayıcı profilleri oturum bilgileri içerebildiği için bunları Git'e ekleme.

Kaynak: [Selenium başlangıç rehberi](https://www.selenium.dev/documentation/webdriver/getting_started/).

## 5. PhantomBuster

PhantomBuster, bulutta çalışan otomasyonlar sunar. Bir Phantom'un hangi girdileri
aldığını, hangi hesap bağlantısına ihtiyaç duyduğunu ve hangi çıktıyı ürettiğini
öğren. Ödevde istenen Phantom'u seç, kurulum talimatlarını incele ve kullanımına
izin verilen küçük bir veri kümesiyle elle bir çalıştırma başlat. Girdiyi,
ayarları, çalışma durumunu ve çıktıyı kaydet. Hangi otomasyonun kullanılacağını
ödev gereksinimleri netleşince belirleyeceğiz.

Gösterilecek sonuç: Bulutta çalışan otomasyon ile bilgisayarında çalışan Selenium
betiğinin farkını açıkla ve seçilen otomasyonun sonucunu göster.
Çalıştırmadan önce hesap limitlerini kontrol et.

Kaynak: [PhantomBuster tanıtımı](https://support.phantombuster.com/hc/en-us/articles/22306827153810-What-is-PhantomBuster-and-What-Can-You-Automate).

## 6. Anti-Captcha + Selenium

Ödevde kastedilen Anti-Captcha servisi ise asenkron API akışını öğren:
`createTask` bir görev kimliği döndürür; `getTaskResult` ile sonuç alınır.
Görev türü, demoda kullanılan CAPTCHA'ya bağlıdır. API anahtarlarını kaynak
kodun dışında tut, servis hatalarını ele al ve sonuç sorgulama döngüsüne
bir zaman aşımı sınırı koy.

Entegrasyon alıştırmasında bir demo veya test etme yetkin olan bir site kullan.
Görev ayrıntıları ve formun işlenmesi, sitenin CAPTCHA uygulamasına bağlıdır.
Normal otomatik uygulama testlerinde Selenium, test ortamında CAPTCHA'nın
kapatılmasını veya test için özel bir geçiş mekanizması sağlanmasını önerir.
Bu test yaklaşımı ile CAPTCHA servisi API'sini öğrenme alıştırmasını ayrı değerlendir.

Gösterilecek sonuç: İstek ve sonuç akışını, zaman aşımı davranışını ve demo
formunda başarının nasıl doğrulandığını açıkla. Canlı entegrasyon için demo ve
hesap kurulumu henüz belirlenmedi; herhangi bir CAPTCHA çözüm isteği gönderilmedi.

Kaynaklar: [Anti-Captcha API](https://anti-captcha.com/apidoc),
[Selenium CAPTCHA rehberi](https://www.selenium.dev/documentation/test_practices/discouraged/captchas/).

## Teslim notları

Her alıştırma için amacı, kullanılan komutu veya betiği, beklenen sonucu,
gözlenen sonucu ve karşılaştığın bir sorunu açıklamasıyla kaydet.
Ekran görüntülerinde ve günlüklerde parolaları, API anahtarlarını ve oturum
çerezlerini gizle.

## Kontrol edilen çalışma ortamı

7 Eylül 2026 tarihindeki yerel kontrol sonuçları:

| Araç | Durum |
| --- | --- |
| İşletim sistemi | Arch tabanlı CachyOS |
| Google Chrome | 152.0.7977.75 — `/usr/bin/google-chrome-stable` |
| Python | 3.14.7 |
| curl | 8.22.0 |
| uv | `uv (PATH)` üzerinden erişilebilir |
| Selenium | Mevcut proje sanal ortamında 4.48.0 |

Yukarıdaki bağımsız kurulumdan sonra Selenium sürümünü şu komutla kontrol edebilirsin:

```fish
./.venv/bin/python -c 'import selenium; print(selenium.__version__)'
```

Chrome sürüm komutu ve Selenium içe aktarma işlemi başarıyla çalıştırıldı.
fish sürümü 4.9.1. Canlı proxy ve API kontrolleri için kendi servis bilgilerini
terminalinde tanımlaman gerekiyor.

## Hazır scriptleri fish ile çalıştırma

### Scrape.do kullanacaksan

`ERR_EMPTY_RESPONSE` görüyorsan önce Chrome'dan bağımsız karşılaştırmayı çalıştır:

```fish
./.venv/bin/python scripts/scrapedo_check.py
```

Token gizli sorulur. Aynı hedefe bir API ve bir proxy isteği gönderilir;
başarılı istekler kota kullanabilir. Her kontrol en fazla 90 saniye bekler.
Çıktıdaki `API:` ve `PROXY:` satırları HTTP kodu, CONNECT kodu, indirilen bayt
sayısı ve curl çıkış kodunu içerir. Token, tam API URL'si ve ham yanıtlar
yazdırılmaz. Bu iki satırı sorun teşhisi için paylaşabilirsin.

İki yol da başarılıysa Chrome tarafına odaklanılır; yalnızca API başarılıysa
proxy erişimi/sertifika yolu incelenir. İkisi de başarısızsa hesap, ağ ve servis
yanıtları araştırılır. Bu sonuçlar tek başına tokenın yanlış olduğunu kanıtlamaz.
Scrape.do panelindeki istek kayıtları da karşılaştırılmalıdır.
[Scrape.do durum kodları](https://scrape.do/documentation/api-response/status-codes/).

Yerel HTTP ve HTTPS CONNECT proxy kimlik doğrulama testleri başarılıdır;
gerçek hesapla uçtan uca bağlantı henüz doğrulanmamıştır.

Sağlayıcı Scrape.do olarak belirlendi. Bağlantı bilgilerini terminalde görmek için:

```fish
./.venv/bin/python scripts/selenium_demo.py --scrapedo-info
```

Bağlantı kurmak için aşağıdaki komutu kullan. Token gizli olarak, ardından
`sessionId` sorulur; Enter ile örnek oturum numarası 1234 seçilir.

```fish
./.venv/bin/python scripts/selenium_demo.py --scrapedo --url 'https://example.com' --keep-open
```

`--url` vermezsen script proxy ile açılacak hedef bağlantıyı sorar; Enter ile
`https://example.com` seçilir.

Önceki `--proxy` komutunda `Proxy adresi:` sorusuna `scrape.do` yazmak da
aynı bağlantı akışını başlatır. Artık açıklamayı gösterip tekrar adres sormaz.
Token kaynak koda veya dosyaya kaydedilmez. İstersen `SCRAPEDO_TOKEN` ortam
değişkeninden de okunabilir. Terminalde token girerken karakter görünmemesi normaldir.
`example.com` yerine kullanacağın siteyi yaz; açılan pencerede elle giriş yap.
Tarayıcıyı kapattıktan sonra aynı komut, aynı `chrome-data/Default` profilini açar.
Scrape.do akışında yeni sekme yerine açılan sekmeyi kullan; otomatik kimlik
doğrulaması bu sekmeye bağlanır. Script istekleri hesabının kotasını kullanabilir.
Scrape.do seçildiğinde Chrome'un güncelleme, ölçüm ve ilk çalıştırma ağı istekleri
kapatılır; bu, kota kullanımını hedef sayfa ve gerekli kaynaklarıyla sınırlar.
Görselleri de engellemek istersen komuta `--block-images` ekle; bazı sitelerin
görünümü veya işlevi buna bağlı olabilir. Tanı scripti her çalıştırmada bir API
ve bir proxy isteği gönderdiğinden, başarılı sonucu aldıktan sonra yeniden
çalıştırma.

Bir hedef için `ROTATION_FAILED` veya Error 90 görülürse sağlayıcının önerdiği
residential/mobile çıkışı denemek için `--super` ekle. Bu seçenek daha fazla
kota harcayabilir:

```fish
./.venv/bin/python scripts/selenium_demo.py --scrapedo --super --url 'https://hedef-site.com' --keep-open
```

| Alan | Değer |
| --- | --- |
| Proxy sunucusu | `http://proxy.scrape.do:8080` |
| Proxy kullanıcı adı | Scrape.do panelindeki API tokenın |
| Proxy parolası | `render=false` gibi servis parametreleri; hesap parolan değil |

Yerel Chrome sayfayı işlediğinden Scrape.do, kendi tarayıcı otomasyonunla
`render=false` önerir. HTTPS bağlantıları için istemcinin Scrape.do CA
sertifikasına güvenmesi gerekir; belgelerde alternatif olarak doğrulamayı
kapatmak da gösterilir. Bu script, yalnızca Scrape.do ile başlattığı Chrome
sürecinde sertifika doğrulamasını kapatır; sistemin güven deposu değişmez ve
kalıcı CA kurulumu yapılmaz. Proxy bağlantısı HTTP kullanır; proxy tokenı bu
bağlantıda TLS ile korunmaz. Hedef adresin HTTPS olması bundan ayrı bir konudur.
Yerel kontrolde `https://proxy.scrape.do:8080` TLS `wrong version number`
hatası verdi; HTTP bağlantısı ise beklenen 407 kimlik doğrulama yanıtını verdi.
[Resmi Proxy Mode belgesi](https://scrape.do/documentation/proxy-mode/).

Scrape.do'nun Selenium örneği, kimlik doğrulamasını `selenium-wire` üzerinden
yapar. Bu projede mevcut Selenium'un Chrome DevTools desteği kullanılır;
ek paket kurulmaz. API tokenı yalnızca `proxy.scrape.do:8080` proxy challenge'ına
gönderilir; hedef sitenin HTTP kimlik doğrulama isteğine gönderilmez.
[Resmi kütüphane örnekleri](https://scrape.do/documentation/libraries/).

Chrome profili ile Scrape.do IP oturumu farklı şeylerdir. `sessionId`, belirli
bir süre aynı çıkış IP'sini kullanmak içindir; 0–1000000 arası sayı kabul eder.
Örneğin parametre parolası `render=false&sessionId=1234` olabilir. Beş dakika
istek gitmezse proxy oturumu kapanır; başarısız istekte de IP değişebilir.
Bu yüzden Chrome çerezlerini korumak, sonraki gün aynı çıkış IP'sini korumak
anlamına gelmez. IP değişmesi de tek başına web sitesi oturumunun kesin
sonlanacağı anlamına gelmez; kararı hedef site verir.
[Resmi Session ID belgesi](https://scrape.do/documentation/api-response/session-id/).

Önce proje klasörüne geç ve mevcut Selenium ortamının Python yolunu tanımla:

```fish
cd (git rev-parse --show-toplevel)
set -gx HW_PYTHON "$PWD/.venv/bin/python"
```

Python dosyaları kabuktan bağımsızdır; başlatma komutları ve `.fish` dosyaları
fish içindir. Ortamı etkinleştirmek istersen fish komutu
`source ./.venv/bin/activate.fish` şeklindedir.

| Script | Ne yapar? |
| --- | --- |
| `scripts/proxy_check.fish` | Doğrudan ve proxy üzerinden dış IP adreslerini gösterir. |
| `scripts/chrome_profile.fish` | Ödeve özel kalıcı Chrome profili açar; `--proxy` seçeneği vardır. |
| `scripts/selenium_demo.py` | Yerel formu doldurur, sonucu bekler ve ekran görüntüsü kaydeder. |
| `scripts/api_check.py` | Anti-Captcha bakiyesini veya PhantomBuster otomasyon sayısını sorgular. |

### Chrome ve Selenium

```fish
fish scripts/chrome_profile.fish
$HW_PYTHON scripts/selenium_demo.py --headless
```

Selenium'da pencereyi görmek için `--headless` seçeneğini kaldır. İşlem bitince
tarayıcı kapanır; ekran görüntüsü `outputs/selenium-demo.png` dosyasına yazılır.
Tekrar çalıştırma aynı ekran görüntüsünü günceller. Yerel demo ağ bağlantısı
gerektirmez; Selenium Manager'ın ilk sürücü edinme işlemi internet gerektirebilir.
Hazır ChromeDriver kullanmak için `--driver /tam/yol/chromedriver` ekleyebilirsin.

Manuel Chrome ve Selenium artık aynı `chrome-data/Default` profilini kullanır.
Önce manuel Chrome oturumunu tamamen kapat, ardından Selenium'u başlat.
Aynı profili iki süreçte eşzamanlı kullanma. Selenium, profil kilitliyse açıklama
vererek durur; kilidi silmez. Önceki `selenium-data` dizini varsa korunur ancak
artık bu script tarafından kullanılmaz.

### Elle giriş yaptığın oturumu Selenium ile kullanma

Önce `PROXY_URL` değişkenini yukarıdaki gibi kendi proxy adresinle tanımla.

```fish
fish scripts/chrome_profile.fish --proxy
```

Açılan Chrome'da yeni sekmede hedef siteye git ve elle giriş yap. Ardından bu
profile ait tüm Chrome pencerelerini kapat. Aşağıdaki örnek adresi kendi sitenin
adresiyle değiştirip Selenium'u aynı proxy ve profille başlat:

```fish
$HW_PYTHON scripts/selenium_demo.py --proxy --url 'https://example.com' --keep-open
```

`--keep-open`, sen terminalde Enter'a basana kadar pencereyi açık tutar.
Bağlantı hatalarında da pencere açık tutulur; terminalde başarısız aşama ve
varsa Chrome `ERR_...` ağ kodu gösterilir. Ham hata metni token veya URL
içerebileceğinden yazdırılmaz.
Selenium komutunda `--proxy` verilip `PROXY_URL` tanımlanmadıysa veya hatalıysa
script proxy adresini terminalde sorar. Sağlayıcının verdiği `adres:port`
bilgisini gir; protokol yazılmazsa HTTP kabul edilir. SOCKS için
`socks5://adres:port` yaz. Hatalı girişte tekrar sorulur, `q` veya Ctrl+C ile
iptal edilir. Bu giriş dosyaya veya fish ortam değişkenlerine kaydedilmez.
API tokenı proxy adresi değildir. Scrape.do için `scrape.do` yaz veya doğrudan
`--scrapedo` kullan; token ayrı ve gizli sorulur. Diğer sağlayıcılar için
otomatik kimlik doğrulama desteği henüz yoktur.
Gerçek site modunda script yalnızca sayfayı açar; otomatik giriş, form gönderimi
veya CAPTCHA çözümü yapmaz. Giriş durumunu pencereden kontrol edebilirsin.
Proxy kullanmayacaksan her iki komuttan da `--proxy` seçeneğini kaldır.
`--url` yoksa önceki yerel demo/IP kontrolü davranışı devam eder.

Gerçek site ekran görüntüsü varsayılan olarak alınmaz. İstersen `--screenshot`
ekle; sonuç `outputs/site.png` olur ve tekrar çalıştırmada güncellenir.
Profil çerezleri saklar ancak sunucunun oturumu geçersiz kılmasını veya CAPTCHA
istemesini engellemez. Aynı proxy adresi de sağlayıcının dönen IP kullanması
durumunda aynı dış IP anlamına gelmez.

### Proxy değişkenleri

HOST ve PORT alanlarını sağlayıcının verdiği adres ve portla değiştir:

```fish
set -gx PROXY_URL http://HOST:PORT
fish scripts/proxy_check.fish
fish scripts/chrome_profile.fish --proxy
$HW_PYTHON scripts/selenium_demo.py --proxy --headless
```

curl proxy kullanıcı adı istiyorsa aşağıdaki değişkeni ekle; parola curl tarafından
sorulur. Parolayı URL'ye veya komut satırına yazma:

```fish
set -gx PROXY_USER KULLANICI_ADI
fish scripts/proxy_check.fish
```

`PROXY_USER` yalnızca curl scripti içindir. Chrome/Selenium örneği, kimlik
doğrulamasız veya sağlayıcı tarafında IP izin listesiyle yetkilendirilmiş proxy
için hazırdır. Kullanıcı adı/parola isteyen Chrome proxy kurulumu, sağlayıcı
belirlendiğinde ayrıca uyarlanacaktır. curl için `socks5h://`, Chrome için
`socks5://` kullanılır. Bir scraping API tokenı tek başına proxy adresi değildir.
Bu paragraf genel `--proxy` adresleri içindir. Scrape.do'nun otomatik kimlik
doğrulaması Selenium scriptindeki `--scrapedo` akışında desteklenir;
`chrome_profile.fish` ve `proxy_check.fish` henüz bu akışı içermez.

### API anahtarlarını fish içinde girme

Elindeki servise ait bölümü kullan. `read --silent` girişi maskeler; anahtar
komut geçmişine yazılmaz. Değişkenler bu kabuk oturumunda ve başlattığı süreçlerde
erişilebilir. Anahtarları README'ye veya scriptlere ekleme.

Anti-Captcha bağlantı kontrolü (CAPTCHA çözüm görevi başlatmaz):

```fish
read --silent --export --prompt-str 'Anti-Captcha API anahtarı: ' ANTICAPTCHA_API_KEY
python3 scripts/api_check.py anticaptcha
set -e ANTICAPTCHA_API_KEY
```

Bakiye sorgusunu 30 saniyeden sık tekrarlama.

Google'ın herkese açık reCAPTCHA v2 demo sayfasında uçtan uca çözüm akışını
denemek için aşağıdaki komutu kullan. Görev oluşturulması Anti-Captcha kotasını
kullanabilir; anahtar ve çözülen token yazdırılmaz veya kalıcı profil dosyasına
kaydedilmez.

```fish
./.venv/bin/python scripts/anticaptcha_recaptcha_demo.py --keep-open
```

Script, `RecaptchaV2TaskProxyless` görevi oluşturur, sonucu bekler, yanıtı yalnızca
Google demo formuna yerleştirir ve formu gönderir. Tarayıcı kapanınca geçici profil
de silinir.

PhantomBuster bağlantı kontrolü (otomasyon çalıştırmaz):

```fish
read --silent --export --prompt-str 'PhantomBuster API anahtarı: ' PHANTOMBUSTER_API_KEY
python3 scripts/api_check.py phantombuster
set -e PHANTOMBUSTER_API_KEY
```

Hesabın organizasyon seçimi istiyorsa sorgudan önce
`set -gx PHANTOMBUSTER_ORG_ID ORGANIZASYON_ID` kullan. Script, otomasyon
argümanlarını ve hesap yanıtının tamamını ekrana basmaz; yalnızca sayıyı gösterir.
API scripti Python standart kütüphanesiyle çalışır, ek paket gerektirmez.
`api_check.py` yalnızca bağlantı/bakiye kontrolü içindir; demo çözüm akışı ayrı
`anticaptcha_recaptcha_demo.py` scriptindedir.

### Doğrulama sonuçları

fish scriptlerinin sözdizimi ve tüm scriptlerin yardım komutları kontrol edildi.
Yerel Selenium demosu Chrome 152.0.7977.75 ve aynı sürümdeki ChromeDriver ile
başarıyla çalıştı: form sonucu `Merhaba, Stajyer!` olarak doğrulandı ve
`outputs/selenium-demo.png` oluşturuldu. Asistanın kısıtlı ortamındaki localhost
bağlantı engeli nedeniyle tarayıcı testi ek çalıştırma izniyle yapıldı.
Gerçek proxy ve API istekleri henüz denenmedi; anahtarlar kullanılmadı.
Scrape.do desteği için ayrıca yerel 407 proxy challenge'ı, gizli girişin yeniden
sorulması ve tokenın hedef siteye/farklı proxy'ye gönderilmemesi test edildi.
Resmi CA indirmesi ve anahtar özeti hesaplaması doğrulandı. Gerçek Scrape.do
hesabıyla uçtan uca bağlantı testi yapılmadı; kullanıcı tokenı kullanılmadı.

Kaynaklar: [fish değişkenleri](https://fishshell.com/docs/current/tutorial.html),
[fish read](https://fishshell.com/docs/current/cmds/read.html),
[Selenium Chrome seçenekleri](https://www.selenium.dev/documentation/webdriver/browsers/chrome/),
[Anti-Captcha getBalance](https://anti-captcha.com/apidoc/methods/getBalance),
[PhantomBuster fetch-all](https://hub.phantombuster.com/reference/get_agents-fetch-all).
