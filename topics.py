from loadconf import CONFIG


def topic_name(*args):
    parts = list(args)
    parts.insert(0, CONFIG.client_id.encode("ascii"))
    return b"/".join(parts)


def get_control_topic(nr):
    return topic_name(b"control", get_nr_encoded(nr))


def get_alarm_set_topic():
    # alarm_topic_set = b"house/alarm/set"
    return topic_name(b"alarm/set")


def get_alarm_topic():
    # alarm_topic = b"house/alarm"
    return topic_name(b"alarm")


def get_reset_topic():
    return topic_name(b"reset")


def get_debug_topic():
    return topic_name(b"debug")


def get_debug_state_topic():
    return topic_name(b"state", b"debug")


def get_alarm_datetime_topic(alarm):
    return topic_name(b"alarm", b"alarm_datetime", alarm)  # ALARM or OK


def get_sensor_alarm_topic(ns):
    return topic_name(b"sensor", b"sensor_alarm", get_nr_encoded(ns))


def get_datetime_topic(nr, on_off):
    return topic_name(b"datetime", get_nr_encoded(nr), on_off)


def get_sensor_alarm_datetime_topic(ns, alarm_ok):
    return topic_name(b"sensor", b"sensor_alarm_datetime", get_nr_encoded(ns), alarm_ok)  # ALARM or OK


def get_state_topic(nr):
    return topic_name(b"state", get_nr_encoded(nr))


def get_nr_encoded(nr):
    return '{}'.format(nr).encode("ascii")


def get_channel_nr(topic, kvo=1):
    # return last kvo digits as int
    res = 0
    try:
        res = int(topic[-kvo:].decode("utf-8"))
    except:
        pass
    return res


def get_info_fused_ch(topic):
    # return channel 4, current '41' and other '42' to check
    res = 0
    try:
        r = topic[-2:].decode("utf-8")
        res = (int(r[0]), r, r[0] + ('2' if r[1] == '1' else '1'))
        if CONFIG.debug:
            print("fused_ch({}): {} r={} r0={} r1={}".format(topic, res, r, r[0], r[1]))
    except:
        pass
    return res
