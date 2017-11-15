from app import CONFIG, FUSED_VALUES
from topics import topic_name, get_state_topic, get_datetime_topic, get_alarm_topic, get_sensor_alarm_topic, \
    get_sensor_alarm_datetime_topic, get_alarm_datetime_topic, get_debug_state_topic
import ujson
from utime import time


def publish_alarm(mess):
    CONFIG.client.publish(get_alarm_topic(), mess, True)
    CONFIG.set_curr_datetime()
    CONFIG.client.publish(get_alarm_datetime_topic(mess), CONFIG.curr_datetime, True)
    if CONFIG.debug:
        print("{} published: {} at {}".format(get_alarm_topic(), mess, CONFIG.curr_datetime))


def publish_state_fused(nch_a, nch_c):
    CONFIG.set_curr_datetime()
    for nch in (nch_a, nch_c):
        topic = get_state_topic(nch)
        mess = b"on" if CONFIG.info[FUSED_VALUES][nch] else b"off"
        CONFIG.client.publish(topic, mess, False)
        topic = get_datetime_topic(nch, mess)
        CONFIG.client.publish(topic, CONFIG.curr_datetime, True)
        if CONFIG.debug:
            print("Channel {} published: {} at {}".format(nch, mess, CONFIG.curr_datetime))


def publish_state(nr):
    topic = get_state_topic(nr)
    if nr <= 2:
        pin_val = CONFIG.info['sensor_pin{}'.format(nr)].value()  # cover and lock - sensor's value
    else:
        pin_val = CONFIG.info['relay_pin{}'.format(nr)].value()
    #
    mess = b"on" if pin_val else b"off"
    # start at
    if pin_val and nr > 2:
        CONFIG.info['at'] = time()
    #
    CONFIG.client.publish(topic, mess, True)
    topic = get_datetime_topic(nr, mess)
    CONFIG.set_curr_datetime()
    CONFIG.client.publish(topic, CONFIG.curr_datetime, True)

    if CONFIG.debug:
        print("Channel {} pin_val = {} published: {} at {}".format(nr, str(pin_val), mess, CONFIG.curr_datetime))


def publish_debug_state():
    topic = get_debug_state_topic()
    mess = b"on" if CONFIG.debug else b"off"
    CONFIG.client.publish(topic, mess, False)


def publish_config():
    topic = topic_name('info'.encode('ascii'))
    if CONFIG.debug:
        ls_mess = {'info': CONFIG.info, 'sensor_value': CONFIG.sensor_value, 'sensor_count': CONFIG.sensor_count}
        mess = ujson.dumps(ls_mess).encode('ascii')
        print(mess)
    else:
        mess = b''
        CONFIG.client.publish(topic, mess, True)


def publish_debug_info(gc):
    CONFIG.set_curr_datetime()
    res = {'alloc': str(gc.mem_alloc()).encode("ascii"),
           'free': str(gc.mem_free()).encode("ascii"), 'datetime': CONFIG.curr_datetime}
    res = ujson.dumps(res)
    topic = topic_name(b"sensor", b"memory")
    CONFIG.client.publish(topic, res, True)
    print("memory: {}".format(res))


def publish_sensor_alarm(current_value, nr):
    res = b"ALARM" if current_value == 1 else b"OK"
    topic = get_sensor_alarm_topic(nr)
    CONFIG.client.publish(topic, res, True)  # publish alarm sensor state
    topic = get_sensor_alarm_datetime_topic(nr, res)
    CONFIG.set_curr_datetime()
    CONFIG.client.publish(topic, CONFIG.curr_datetime, True)  # publish alarm or ok sensor datetime state
    if CONFIG.debug:
        print("sa{}: {} at {}".format(nr, res, CONFIG.curr_datetime))
