#!/usr/bin/env fish
# PROXY_URL yalnızca protokol, adres ve port içermeli.
if contains -- --help $argv
    echo 'Kullanım: set -gx PROXY_URL http://HOST:PORT; fish scripts/proxy_check.fish'
    echo 'İsteğe bağlı: set -gx PROXY_USER kullanıcı_adı (curl parolayı sorar).'
    exit 0
end
if not set -q PROXY_URL; or test -z "$PROXY_URL"
    echo 'Önce set -gx PROXY_URL http://HOST:PORT komutuyla proxy adresini tanımla.' >&2
    exit 2
end
if not string match -rq '^(https?|socks5h?)://[^/@[:space:]]+:[0-9]+$' -- "$PROXY_URL"
    echo 'Proxy adresi http(s)://HOST:PORT veya socks5(h)://HOST:PORT biçiminde olmalı; parola içermemeli.' >&2
    exit 2
end
set -l auth_args
if set -q PROXY_USER; and test -n "$PROXY_USER"
    set auth_args --proxy-user "$PROXY_USER"
end
echo 'Doğrudan bağlantının dış IP adresi:'
curl --disable --noproxy '*' --fail --silent --show-error --connect-timeout 10 --max-time 30 --write-out '\n' https://api.ipify.org
or exit $status
echo 'Proxy üzerinden bağlantının dış IP adresi:'
curl --disable --noproxy '' --proxy "$PROXY_URL" $auth_args --fail --silent --show-error --connect-timeout 10 --max-time 30 --write-out '\n' https://api.ipify.org
exit $status
