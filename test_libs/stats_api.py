import network


class Handler:
    def __init__(self):
        pass

    #
    # callbacks
    #

    def get(self):
        return self.get_response()

    #
    # internal operations
    #

    def get_response(self):
        return {
            'sys': self.get_sys_stats(),
            'machine': self.get_machine_stats(),
            'esp': self.get_esp_stats(),
            'gc': self.get_gc_stats(),
            'network': self.get_network_stats()
        }

    def get_sys_stats(self):
        import sys
        implementation = sys.implementation
        return {
            'byteorder': sys.byteorder,
            'implementation': {
                'name': implementation[0],
                'version': implementation[1]
            },
            'maxsize': sys.maxsize,
            'modules': self.keys(sys.modules),
            'path': sys.path,
            'platform': sys.platform,
            'version': sys.version,
            'vfs': self.get_vfs_stats()
        }

    def get_vfs_stats(self):
        import os
        stats = os.statvfs('/')
        return {
            'frsize': stats[1],
            'blocks': stats[2],
            'bavail': stats[4]
        }

    def keys(self, pairs):
        ret = []
        for k, v in pairs.items():
            ret.append(k)
        return ret

    def get_machine_stats(self):
        import machine
        import ubinascii
        id = "0x{}".format(ubinascii.hexlify(machine.unique_id()).decode().upper())
        return {
            'freq': machine.freq(),
            'unique_id': id
        }

    def get_esp_stats(self):
        import esp
        return {
            'flash_id': esp.flash_id(),
            'flash_size': esp.flash_size(),
            'free_mem': esp.freemem()
        }

    def get_gc_stats(self):
        import gc
        return {
            'mem_alloc': gc.mem_alloc(),
            'mem_free': gc.mem_free()
        }

    def get_network_stats(self):
        return {
            'phy_mode': self.get_phy_mode(),
            'sta': self.get_sta_stats(),
            'ap': self.get_ap_stats()
        }

    def get_sta_stats(self):
        sta = network.WLAN(network.STA_IF)
        return self.get_wlan_stats(sta)

    def get_ap_stats(self):
        ap = network.WLAN(network.AP_IF)
        wlan_stats = self.get_wlan_stats(ap)
        wlan_stats['config'] = self.get_wlan_config_stats(ap)
        return wlan_stats

    def get_wlan_stats(self, wlan):
        if wlan.active():
            ip, subnet, gateway, dns = wlan.ifconfig()
            return {
                'status': self.get_wlan_status(wlan),
                'ifconfig': {
                    'ip': ip,
                    'subnet': subnet,
                    'gateway': gateway,
                    'dns': dns
                }
            }
        else:
            return {}

    def get_wlan_config_stats(self, ap):
        import ubinascii
        return {
            'mac': "0x{}".format(ubinascii.hexlify(ap.config('mac')).decode()),
            'essid': ap.config('essid'),
            'channel': ap.config('channel'),
            'hidden': ap.config('hidden'),
            'authmode': self.get_auth_mode(ap.config('authmode'))
        }

    def get_auth_mode(self, mode):
        if mode == network.AUTH_OPEN:
            return "AUTH_OPEN"
        elif mode == network.AUTH_WEP:
            return "AUTH_WEP"
        elif mode == network.AUTH_WPA_PSK:
            return "AUTH_WPA_PSK"
        elif mode == network.AUTH_WPA2_PSK:
            return "AUTH_WPA2_PSK"
        elif mode == network.AUTH_WPA_WPA2_PSK:
            return "AUTH_WPA_WPA2_PSK"
        else:
            return "Unknown auth_mode: {}".format(mode)

    def get_wlan_status(self, wlan):
        status = wlan.status()
        if status == network.STAT_IDLE:
            return 'STAT_IDLE'
        elif status == network.STAT_CONNECTING:
            return 'STAT_CONNECTING'
        elif status == network.STAT_WRONG_PASSWORD:
            return 'STAT_WRONG_PASSWORD'
        elif status == network.STAT_NO_AP_FOUND:
            return 'STAT_NO_AP_FOUND'
        elif status == network.STAT_CONNECT_FAIL:
            return 'STAT_CONNECT_FAIL'
        elif status == network.STAT_GOT_IP:
            return 'STAT_GOT_IP'
        else:
            return "Unknown wlan status: {}".format(status)

    def get_phy_mode(self):
        phy_mode = network.phy_mode()
        if phy_mode == network.MODE_11B:
            return 'MODE_11B'
        elif phy_mode == network.MODE_11G:
            return 'MODE_11G'
        elif phy_mode == network.MODE_11N:
            return 'MODE_11N'
        else:
            return "Unknown phy_mode: {}".format(phy_mode)
