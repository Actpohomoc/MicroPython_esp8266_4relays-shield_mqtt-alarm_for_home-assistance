import gc
import network
import utime
from micropython import const
import machine

from loadconf import CONFIG, FUSED_VALUES
from alarmod import check_for_alarm, check_empty_curr_house_alarm, check_any_horn_activated_to_long
from publish import publish_debug_info, publish_state, publish_sensor_alarm, publish_debug_state
from switchs import setup_pins
import topics as tp
import callbck as clb

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
        CONFIG.client.connect(True)  # True if first_run else False
        try:
            CONFIG.get_ntp_current_datetime()
            CONFIG.client.subscribe(tp.get_reset_topic(CONFIG.client_id))
            CONFIG.client.subscribe(tp.get_debug_topic(CONFIG.client_id))
            CONFIG.client.subscribe(tp.get_alarm_set_topic(CONFIG.client_id))
            CONFIG.client.subscribe(tp.get_alarm_topic(CONFIG.client_id))
            publish_debug_state()
            utime.sleep(1)
            for t in range(5):
                utime.sleep(0.2)
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
                topic = tp.get_control_topic(CONFIG.client_id, nr)
                CONFIG.client.subscribe(topic)
                print("Subs to {}".format(topic))
                # publish current default state
                publish_state(nr)

            # fused values
            for nch in CONFIG.info[FUSED_VALUES]:
                topic = tp.get_control_topic(CONFIG.client_id, nch)
                CONFIG.client.subscribe(topic)
                print("Subs to {}".format(topic))
                # publish ini value to state topic
                topic = tp.get_state_topic(CONFIG.client_id, nch)
                mess = b"on" if CONFIG.info[FUSED_VALUES][nch] else b"off"
                CONFIG.client.publish(topic, mess, True)
            # utime date start
            topic = tp.get_datetime_started_topic(CONFIG.client_id)
            CONFIG.set_curr_datetime()
            # send start info with datetime last teardown
            mess = b' '.join((reset_cause, CONFIG.curr_datetime, read_teardown(), ))
            del reset_cause
            CONFIG.client.publish(topic, mess, True)
            print('{} {}'.format(topic, mess))
            check_empty_curr_house_alarm()
            publish_debug_state()
            gc.collect()
            #
            first_run = False
        except OSError:
            return False  # return in prev func to connect to wait for wifi
    except OSError:
        return False  # return in prev func to connect to wait for wifi    #
    print("ok mqtt at {}".format(CONFIG.curr_datetime))
    return True


def setup():
    #
    for i, s in CONFIG.__dict__.items():
        print("{} {}".format(i, s))
    #
    setup_pins()
    #
    CONFIG.client.set_callback(clb.callback)


def main_loop():
    wifi = network.WLAN(network.STA_IF)
    curr_wifi = 0  # use to select next wifi network from wifis.ini
    print(wifi.ifconfig())
    status_ok = network.STAT_GOT_IP
    CONFIG.need_reconnect = True
    debug_at = 0
    while True:
        if wifi.status() == status_ok:
            # turn off local wifi if all ok
            set_active_ap_if(False)
        else:
            # save to info file that we lost wifi
            set_active_ap_if(True)
            if not wifi.status() == network.STAT_CONNECTING:
                # we need to start reconnect to the wifi
                import wifis
                curr_wifi = wifis.connect_next_wifi(curr_wifi, wifi)
                #
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
            if not first_run:
                CONFIG.client_disconnect()
            if connect_and_subscribe(wifi):
                #  ok
                CONFIG.need_reconnect = False
                #  only now
                #  ap_if.active(False)
        #
        mcc = 0
        try:
            while not CONFIG.need_reconnect and mcc < const(20):
                mcc += 1
                CONFIG.client.check_msg()
                # utime.sleep(0.1)  # max_sensor_count=5 -> 1 sec delay for sensor
                #
        except Exception as e:
            if CONFIG.check_for_keyboard_interrupt(e, 'ch'):
                return e
        #
        #  if True:
        try:
            # alarm check, publish only when not neen_reconnect
            for nr in range(1, 3):
                check_for_alarm(nr)
        except Exception as e:
            if CONFIG.check_for_keyboard_interrupt(e, 'al'):
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
                        if CONFIG.check_for_keyboard_interrupt(e, 'pds'):
                            return e
        #
        gc.collect()
        #
        if not CONFIG.need_reconnect:
            if utime.time() > debug_at + int(CONFIG.keepalive/2):
                try:
                    publish_debug_info(gc)
                    debug_at = utime.time()
                except Exception as e:
                    if CONFIG.check_for_keyboard_interrupt(e, 'pdi'):
                        return e
        #
        # check horn
        check_any_horn_activated_to_long()


def teardown():
    CONFIG.client_disconnect()
    utime.sleep(2)
    save_teardown()
    utime.sleep(2)
    # maybe restart here?
    set_active_ap_if(True)
    utime.sleep(2)
    # we can have here loading settings from file and look to reset or stay like this
    # machine.reset()


def set_active_ap_if(active):
    ap_if = network.WLAN(network.AP_IF)
    if ap_if.active() != active:
        ap_if.active(active)
        if active:
            import webrepl
            webrepl.start()


def save_teardown():
    with open('teardown.txt', 'w') as f:
        f.write(CONFIG.curr_datetime)


def read_teardown():
    res = b''
    try:
        with open('teardown.txt') as f:
            res = f.read().encode('ascii')
    except:
        pass
    return res


def main():
    setup()
    try:
        main_loop()
    finally:
        teardown()
