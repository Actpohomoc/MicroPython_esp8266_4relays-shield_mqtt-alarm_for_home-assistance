from machine import unique_id, Pin
from ubinascii import hexlify
from micropython import const
import utime
import ntptime
import sys
from umqtt.simple import MQTTClient

ntptime.NTP_DELTA -= 7200  # current time zone


class Config:
    """ Config """
    def __init__(self):
        """ init config with values """
        from app_ini import load_config
        conf = load_config('app.ini')
        del sys.modules['app_ini']
        try:
            self.client_id = conf['client_id'].format(hexlify(unique_id()).decode("utf-8"))
            # mqtt
            self.broker = conf['broker']
            self.port = conf['port']
            self.user = conf['user']
            self.password = conf['password']
            # alarm topic
            self.max_sensor_count = conf['max_sensor_count']
            # current running values info
            self.info = {}
            # relays based on relay_pins="13,12,14,4"
            l_pins = conf['relay_pins'].split(',')
            for n, rn in enumerate(l_pins):
                self.info['relay_pin{}'.format(n + 1)] = Pin(int(rn), Pin.OUT)
            #
            self.sensor_value = []
            self.sensor_count = []
            #
            l_pins = conf['sensor_pins'].split(',')
            for n, rn in enumerate(l_pins):
                pull_up = Pin.PULL_UP if rn != '16' else None
                pin = Pin(int(rn), Pin.IN, pull_up)
                self.info['sensor_pin{}'.format(n + 1)] = pin
                # we have to put current value
                self.sensor_value.append(pin.value())
                self.sensor_count.append(0)
            #
            l_pins = conf['defaults_on'].split(',')
            for n, rn in enumerate(l_pins):
                self.info['default_on{}'.format(n + 1)] = False
            # based of pin number 4
            self.info['fused_values'] = {'{}1'.format(conf['fused_pin']): False, '{}2'.format(conf['fused_pin']): False}
            #
            # alarm vars
            self.arm = {
                'ARM_AWAY': b'armed_away',
                'ARM_HOME': b'armed_home',
                'ARM_NIGHT': b'armed_night',
                'DISARM': b'disarmed'}
            self.curr_datetime = b""
            self.alarm_triggered = False
            self.alarm_away_trig_time = conf['alarm_away_trig_time']
            self.alarm_home_trig_time = conf['alarm_home_trig_time']
            self.curr_house_alarm = ""
            self.time_last_set = 0
            self.debug = True
            self.client = None
            self.need_reconnect = True
        except Exception:
            raise Exception

    def del_default_on(self):
        for k in self.info:
            if 'default_on' in k:
                del (self.info[k])

    def get_ntp_current_datetime(self):
        try:
            ntptime.settime()
            self.time_last_set = ntptime.time()
            # set curr_datetime
            self.set_curr_datetime()
        except Exception:
            return False
        return True

    def check_to_set_time(self):
        six_hours = const(21600)
        if utime.time() - self.time_last_set > six_hours:
            return self.get_ntp_current_datetime()
        return False

    def set_curr_datetime(self):
        year, month, day, hour, minute, second = utime.localtime()[:6]
        self.curr_datetime = b"%02d:%02d:%02d %02d.%02d.%d" % (hour, minute, second, day, month, year)

    def client_init(self):
        """init mqtt client"""
        self.client = MQTTClient(self.client_id, self.broker, self.port, self.user, self.password, 120)

    def client_disconnect(self):
        try:
            self.client.disconnect()
        except:
            pass

    def check_for_keyboard_interrupt(self, e):
        """ handle the KeyboardInterrupt all others need to reconnect mqtt"""
        if e == KeyboardInterrupt:
            self.client_disconnect()
            self.need_reconnect = True
            return True
        return False
