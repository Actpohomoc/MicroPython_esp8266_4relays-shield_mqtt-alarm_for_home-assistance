# import os and load settings from wifis.ini file
# we create the list with dict {'ssid':,'psk'} with all possible wifi networks
# the program goes thrue the list and tries to connect to the wifi
# if ok then return if not - read the file again (maybe already change by webrepl
from utime import sleep
import ujson as json
import network

wifis_ini = "wifis.ini"
time_to_delay = 5
time_to_delay_retries = 1
times = 12


def load_config():
    try:
        with open(wifis_ini) as f:
            conf_new = json.loads(f.read())
            print("Loaded conf from {}".format(wifis_ini))
            return conf_new
    except Exception:
        print("Couldn't load from {}: {}".format(wifis_ini, Exception))
    conf = [
        {"ssid": "ssid1", "psk": 'BigBrotherPassword345#@!'},
        {"ssid": "ssid2", "psk": 'LittleBrotherPassword345#@!!'},
    ]
    save_default_ini(conf)
    return conf


def save_default_ini(conf):
    try:
        with open(wifis_ini, "w") as fs:
            fs.write(json.dumps(conf))
            print("Saved new conf to {}".format(wifis_ini))
    except OSError:
        print("Couldn't save to {}".format(wifis_ini))


def check_delay(wifi):
    retries = 0
    sleep(time_to_delay_retries)
    while retries < times:
        if wifi_is_connected(wifi):
            return True
        retries += 1
        sleep(time_to_delay_retries)
        print(".", end='')
    return False


def wifi_is_connected(wifi=None):
    if wifi is None:
        wifi = network.WLAN(network.STA_IF)
    return wifi.isconnected() and wifi.status() == network.STAT_GOT_IP


def connect_wifi(sid, psk, wifi=None):
    if wifi is None:
        wifi = network.WLAN(network.STA_IF)
    # until wifi connected
    if wifi_is_connected(wifi):
        return True
    # start to connect
    print('ssid: {}'.format(sid), end='')
    #
    wifi.active(False)
    sleep(time_to_delay_retries)
    wifi.active(True)
    wifi.connect(sid, psk)
    # wait and check
    if check_delay(wifi):
        print("{}>ok".format(sid))
        return True
    else:
        print("{}>not".format(sid))
    return False


def start_wifi(wifi=None):
    """ """
    if wifi is None:
        wifi = network.WLAN(network.STA_IF)
    # until wifi connected
    while not wifi_is_connected(wifi):
        # read list of dict from wifis.ini
        conf = load_config()
        for cnf in conf:
            if connect_wifi(cnf['ssid'], cnf['psk'], wifi):
                break
        else:
            sleep(time_to_delay)
    # ip info
    print('wifi is {}: NetConf: {}'.format(get_wifi_status(wifi), wifi.ifconfig()))


def get_wifi_status(wifi=None):
    if wifi is None:
        wifi = network.WLAN(network.STA_IF)
    status = wifi.status()
    if status == network.STAT_IDLE:
        r = 'IDLE'
    elif status == network.STAT_CONNECTING:
        r = 'CONNECTING'
    elif status == network.STAT_WRONG_PASSWORD:
        r = 'WRONG_PASSWORD'
    elif status == network.STAT_NO_AP_FOUND:
        r = 'NO_AP_FOUND'
    elif status == network.STAT_CONNECT_FAIL:
        r = 'CONNECT_FAIL'
    elif status == network.STAT_GOT_IP:
        r = 'GOT_IP'
    else:
        return "Unknown wifi status: {}".format(status)
    return 'STAT_{}'.format(r)
