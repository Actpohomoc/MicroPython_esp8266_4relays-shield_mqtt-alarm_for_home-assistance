import gc
import network
import utime
from micropython import const
import machine

from loadconf import CONFIG, FUSED_VALUES
import callbck
from alarmod import check_for_alarm, check_empty_curr_house_alarm, check_any_horn_activated_to_long
from publish import publish_debug_info, publish_state, publish_sensor_alarm, publish_debug_state
from switchs import setup_pins
import topics as tp

first_run = True


def connect_and_subscribe(wifi):
    """ connect to mqtt and republish all current info!!!! very important if it was not connected to mqtt!!! """
    global first_run
    status_ok = network.STAT_GOT_IP
    reset_cause = (b'DEFAULT_RST', b'WDT_RST', b'EXCEPTION_RST', b'SOFT_WDT_RST',
                   b'SOFT_RESTART', b'DEEP_SLEEP_AWAKE', b'EXT_SYS_RST')[machine.reset_cause()]
    if not wifi.status() == status_ok:
        return False  # return in prev func to connect to wait for wifi
    try:
        CONFIG.client.connect(True if first_run else False)
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
            mess = b' '.join((reset_cause, CONFIG.curr_datetime,))
            del reset_cause
            CONFIG.client.publish(topic, mess, True)
            print('{} {}'.format(topic, mess))
            check_empty_curr_house_alarm()
            publish_debug_state()
            gc.collect()
            first_run = False
        except OSError:
            return False  # return in prev func to connect to wait for wifi
    except OSError:
        return False  # return in prev func to connect to wait for wifi    #
    print("ok mqtt {} at {}".format(CONFIG.broker, CONFIG.curr_datetime))
    return True


def setup():
    for i, s in CONFIG.__dict__.items():
        print("{} {}".format(i, s))
    #
    setup_pins()
    #
    CONFIG.client_init()
    CONFIG.client.set_callback(callbck.callback)


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
    debug_at = 0
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
        try:
            while not CONFIG.need_reconnect and mcc < const(100):
                mcc += 1
                CONFIG.client.check_msg()
                #utime.sleep(0.1)  # max_sensor_count=5 -> 1 sec delay for sensor
                #
        except Exception as e:
            if CONFIG.check_for_keyboard_interrupt(e, 'check_msg'):
                return e
        #
        try:
            # alarm check, publish only when not neen_reconnect
            for nr in range(1, 3):
                check_for_alarm(nr)
        except Exception as e:
            if CONFIG.check_for_keyboard_interrupt(e, 'check_for_alarm'):
                return e
        #
        if not CONFIG.need_reconnect:
            # check for 6 hours since last ntptime.settime() 6*3600
            if CONFIG.check_to_set_time():
                if CONFIG.debug:  # turn off debug when 6 hours
                    CONFIG.debug = False
                    try:
                        publish_debug_state()
                    except Exception as e:
                        if CONFIG.check_for_keyboard_interrupt(e, 'publish_debug_state'):
                            return e
        #
        gc.collect()
        #
        if not CONFIG.need_reconnect:
            if utime.time() > debug_at + CONFIG.keepalive:
                publish_debug_info(gc)
                debug_at = utime.time()
        # check horn
        check_any_horn_activated_to_long()


def teardown():
    try:
        CONFIG.client.disconnect()  # maybe use it before any reconnect to mqtt?
    except:
        pass
    fo = open('teardown.txt', 'w')
    fo.write(CONFIG.curr_datetime)
    fo.close()


def main():
    setup()
    try:
        main_loop()
    finally:
        teardown()
