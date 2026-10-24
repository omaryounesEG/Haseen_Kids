@echo off
echo [حصين] ضبط جدار حماية ويندوز لمنع تخطي البروكسي...
netsh advfirewall firewall add rule name="Haseen_Allow_Proxy_In" dir=in action=allow protocol=TCP localport=8089
netsh advfirewall firewall add rule name="Haseen_Allow_Local" dir=out action=allow remoteip=127.0.0.1
echo تم إعداد جدار الحماية بنجاح.
