#!/usr/bin/env fish
if contains -- --help $argv
    echo 'Kullanım: fish scripts/chrome_profile.fish [--proxy]'
    echo 'Proxy modu PROXY_URL değişkenini kullanır; Chrome kimlik doğrulaması ayrıca yapılır.'
    exit 0
end
if test (count $argv) -gt 1; or begin; test (count $argv) -eq 1; and test "$argv[1]" != --proxy; end
    echo 'Geçersiz seçenek. --help kullan.' >&2
    exit 2
end
set -l project_dir (path resolve (status dirname)/..)
set -l chrome_bin /usr/bin/google-chrome-stable
set -l chrome_args "--user-data-dir=$project_dir/chrome-data" --profile-directory=Default
set -l target https://example.com
if contains -- --proxy $argv
    if not set -q PROXY_URL; or not string match -rq '^(https?|socks5)://[^/@[:space:]]+:[0-9]+$' -- "$PROXY_URL"
        echo 'PROXY_URL: http(s)://HOST:PORT veya socks5://HOST:PORT gerekli; kimlik bilgisi ekleme.' >&2
        exit 2
    end
    set -a chrome_args "--proxy-server=$PROXY_URL"
    set target https://api.ipify.org
end
echo "Ödev profili: $project_dir/chrome-data"
echo 'Parametreleri değiştirmeden önce bu profili kullanan Chrome pencerelerini kapat.'
exec "$chrome_bin" $chrome_args "$target"
