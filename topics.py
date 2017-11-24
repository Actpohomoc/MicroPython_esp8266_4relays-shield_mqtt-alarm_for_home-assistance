# ready to move to precompiled module to decrease memory usage


def topic_name(*args):
    parts = list(args)
    # parts.insert(0, client_id.encode("ascii"))
    return b"/".join(parts)


def get_info_topic(client_id):
    return topic_name(get_nr_encoded(client_id), b'info')


def get_control_topic(client_id, nr):
    return topic_name(get_nr_encoded(client_id), b"control", get_nr_encoded(nr))


def get_alarm_set_topic(client_id):
    # alarm_topic_set = b"house/alarm/set"
    return topic_name(get_nr_encoded(client_id), b"alarm/set")


def get_alarm_topic(client_id):
    # alarm_topic = b"house/alarm"
    return topic_name(get_nr_encoded(client_id), b"alarm")


def get_reset_topic(client_id):
    return topic_name(get_nr_encoded(client_id), b"reset")


def get_debug_topic(client_id):
    return topic_name(get_nr_encoded(client_id), b"debug")


def get_debug_state_topic(client_id):
    return topic_name(get_nr_encoded(client_id), b"state", b"debug")


def get_alarm_datetime_topic(client_id, alarm):
    return topic_name(get_nr_encoded(client_id), b"alarm", b"alarm_datetime", alarm)  # ALARM or OK


def get_sensor_alarm_topic(client_id, ns):
    return topic_name(get_nr_encoded(client_id), b"sensor", b"sensor_alarm", get_nr_encoded(ns))


def get_datetime_topic(client_id, nr, on_off):
    return topic_name(get_nr_encoded(client_id), b"datetime", get_nr_encoded(nr), on_off)


def get_sensor_alarm_datetime_topic(client_id, ns, alarm_ok):
    return topic_name(get_nr_encoded(client_id), b"sensor", b"sensor_alarm_datetime", get_nr_encoded(ns), alarm_ok)  # ALARM or OK


def get_datetime_started_topic(client_id):
    return topic_name(get_nr_encoded(client_id), b"datetime", b"started")


def get_sensor_memory_topic(client_id):
    return topic_name(get_nr_encoded(client_id), b"sensor", b"memory")


def get_state_topic(client_id, nr):
    return topic_name(get_nr_encoded(client_id), b"state", get_nr_encoded(nr))


def get_nr_encoded(nr):
    return '{}'.format(nr).encode("ascii")

