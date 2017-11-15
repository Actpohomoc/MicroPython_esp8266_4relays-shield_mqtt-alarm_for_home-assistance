import gc
import network
import utime
from micropython import const

from loadconf import Config

CONFIG = Config()
FUSED_VALUES = 'fused_values'

from alarmod import check_for_alarm, check_empty_curr_house_alarm, check_any_horn_activated_to_long
from publish import publish_debug_info, publish_state, publish_sensor_alarm, publish_debug_state
from switchs import setup_pins
import topics as tp
import callbck


def connect_and_subscribe(wifi):
    """ connect to mqtt and republish all current info!!!! very important if it was not connected to mqtt!!! """
    CONFIG.client_init()
    CONFIG.client.set_callback(callbck.callback)
    ready = False
    status_ok = network.STAT_GOT_IP

    if not wifi.status() == status_ok:
        return False  # return in prev func to connect to wait for wifi
    try:
        CONFIG.client.connect(False)
        try:
            CONFIG.get_ntp_current_datetime()
            CONFIG.client.subscribe(tp.get_reset_topic())
            CONFIG.client.subscribe(tp.get_debug_topic())
            CONFIG.client.subscribe(tp.get_alarm_set_topic())
            CONFIG.client.subscribe(tp.get_alarm_topic())
            for t in range(2):
                utime.sleep(1)
                CONFIG.client.check_msg()
            utime.sleep(1)
            # ----------------------------------------------------
            # publish current states of the sensors and switches
            # ----------------------------------------------------
            # alarm sensors
            for nr in range(1, 3):
                publish_sensor_alarm(CONFIG.sensor_value[nr-1], nr)
            #
            for nr in range(1, 5):
                topic = tp.get_control_topic(nr)
                CONFIG.client.subscribe(topic)
                print("Subs to {}".format(topic))
                # publish current default state
                publish_state(nr)

            # fused values
            for nch in CONFIG.info[FUSED_VALUES]:
                topic = tp.get_control_topic(nch)
                CONFIG.client.subscribe(topic)
                print("Subs to {}".format(topic))
                # publish ini value to state topic
                topic = tp.get_state_topic(nch)
                mess = b"on" if CONFIG.info[FUSED_VALUES][nch] else b"off"
                CONFIG.client.publish(topic, mess, True)
            # utime date start
            topic = tp.topic_name(b"datetime", b"started")
            CONFIG.set_curr_datetime()
            CONFIG.client.publish(topic, CONFIG.curr_datetime, True)
            check_empty_curr_house_alarm()
            publish_debug_state()
            ready = True
        except OSError:
            return False  # return in prev func to connect to wait for wifi
    except OSError:
        return False  # return in prev func to connect to wait for wifi    #
    print("ok mqtt {} at {}".format(CONFIG.broker, CONFIG.curr_datetime))
    return True


def setup():
    if CONFIG.debug:
        print("{}".format(CONFIG.info))
    #
    setup_pins()


def set_active_ap_if(active):
    ap_if = network.WLAN(network.AP_IF)
    if ap_if.active() != active:
        ap_if.active(active)


def main_loop():
    wifi = network.WLAN(network.STA_IF)
    print(wifi.ifconfig())
    ap_if = network.WLAN(network.AP_IF)
    status_ok = network.STAT_GOT_IP
    CONFIG.need_reconnect = True
    while True:
        if not wifi.status() == status_ok:
            # save to info file that we lost wifi
            if not ap_if.active():
                ap_if.active(True)
            mcc = 0
            while mcc < const(5):  # 1 sec to check wifi
                mcc += 1
                if wifi.status() == status_ok:
                    print(wifi.ifconfig())
                    break
                utime.sleep(0.2)
            # we got wifi connection and ip addr
            CONFIG.need_reconnect = True
        # if something happened with mqtt connection we do renew it
        if CONFIG.need_reconnect:
            if connect_and_subscribe(wifi):
                #  ok
                CONFIG.need_reconnect = False
                #  only now
                ap_if.active(False)
        #
        mcc = 0
        while mcc < const(50):
            mcc += 1
            if not CONFIG.need_reconnect:
                try:
                    CONFIG.client.check_msg()
                    utime.sleep(0.1)  # max_sensor_count=5 -> 1 sec delay for sensor
                except Exception as e:
                    if CONFIG.check_for_keyboard_interrupt(e):
                        return e
                    # else:
                    CONFIG.need_reconnect = True
            # alarm check, publish only when not neen_reconnect
            for nr in range(1, 3):
                check_for_alarm(nr)
            # check for 6 hours since last ntptime.settime() 6*3600
            # turn debug off
        # memory
        gc.collect()
        if not CONFIG.need_reconnect:
            try:
                if CONFIG.check_to_set_time():
                    if CONFIG.debug:  # turn off debug when 6 hours
                        CONFIG.debug = False
                        publish_debug_state()
                if CONFIG.debug:
                    publish_debug_info(gc)
            except Exception as e:  # if wifi works, reconnect to the mqtt to to begin of the cycle
                if CONFIG.check_for_keyboard_interrupt(e):
                    return e
        #
        # we have to check if main horn is working 30 min already
        check_any_horn_activated_to_long()


def teardown():
    try:
        CONFIG.client.disconnect()  # maybe use it before any reconnect to mqtt?
    except:
        pass


def main():
    setup()
    try:
        main_loop()
    finally:
        teardown()
