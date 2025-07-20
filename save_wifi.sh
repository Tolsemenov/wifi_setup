#!/bin/bash

SSID=$1
PASSWORD=$2

cat <<EOF > /etc/wpa_supplicant/wpa_supplicant.conf
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=RU

network={
    ssid="$SSID"
    psk="$PASSWORD"
}
EOF

wpa_cli -i wlan0 reconfigure
