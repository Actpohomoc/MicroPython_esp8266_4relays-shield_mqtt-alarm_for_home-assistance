from loadconf import CONFIG, FUSED_VALUES
from publish import publish_state, publish_state_fused, publish_alarm, publish_sensor_alarm
from switchs import switch_on, switch_off
from utime import time
from micropython import const


def check_for_alarm(nr):
    """ checking sensor pin 1 and 2 if it is 1 (not connected to the ground) - alarm  """
    # if all 0 - nothing or disable alarm if it is triggered before in case time for alarm is over """
    spin = "sensor_pin{}".format(nr)
    current_value = CONFIG.info[spin].value()
    if CONFIG.sensor_value[nr - 1] != current_value:
        if CONFIG.sensor_count[nr - 1] < CONFIG.max_sensor_count:  # count times with same new values
            CONFIG.sensor_count[nr - 1] += 1  # just exit - waiting for next round
        else:
            # if changed state more then max_sensor_count times
            CONFIG.sensor_count[nr - 1] = 0
            CONFIG.sensor_value[nr - 1] = current_value  # remember current state
            # state alarms and switches 1 and 2 - cover and door lock
            if not CONFIG.need_reconnect:
                publish_sensor_alarm(current_value, nr)
                publish_state(nr)  # cover switch send signal that is open 1->1 2->2 switch !!!!

            #
            if current_value == 1:
                if CONFIG.curr_house_alarm == "DISARM":  # or CONFIG.curr_house_alarm == "":
                    pass
                else:
                    turn_alarm_on()
            #
    # every time we checks that time is pass
    if CONFIG.alarm_triggered:
        alarm_time_diff = time() - CONFIG.info['at']
        if all(CONFIG.sensor_value) == 0 or alarm_time_diff > const(1500):  # if more than 30 min - turn it off
            # if alarm_away and alarm_home - different time delays
            if CONFIG.curr_house_alarm == "ARM_AWAY" and alarm_time_diff > CONFIG.alarm_away_trig_time or \
                    CONFIG.curr_house_alarm != "ARM_AWAY" and alarm_time_diff > CONFIG.alarm_home_trig_time:
                    # turn alarm off when alarm_trig_time pass
                    turn_alarm_off()


def turn_alarm_on():
    CONFIG.alarm_triggered = True
    CONFIG.info['at'] = time()
    #
    if CONFIG.curr_house_alarm == "ARM_AWAY":
        turn_main_alarm_horn(True)
    #
    turn_small_alarm_horn(True)
    if not CONFIG.need_reconnect:
        publish_alarm(b'triggered')


def turn_alarm_off(new_alarm_state=None):
    CONFIG.alarm_triggered = False
    CONFIG.info['at'] = const(0)
    #
    if CONFIG.curr_house_alarm == "ARM_AWAY":
        turn_main_alarm_horn(False)
    #
    turn_small_alarm_horn(False)
    #
    if new_alarm_state is not None:  # from callback function
        CONFIG.curr_house_alarm = new_alarm_state  # we set new alarm state to current
    #
    if not CONFIG.need_reconnect:
        publish_alarm(CONFIG.arm[CONFIG.curr_house_alarm])


def turn_main_alarm_horn(on_off):
    if on_off:
        switch_on(4)
    else:
        switch_off(4)
    if not CONFIG.need_reconnect:
        publish_state(4)
    #
    fused_values = CONFIG.info[FUSED_VALUES]
    for nch in fused_values:
        if nch[0] == '4':
            fused_values[nch] = on_off
    if not CONFIG.need_reconnect:
        publish_state_fused('41', '42')


def turn_small_alarm_horn(on_off):
    if on_off:
        switch_on(3)
    else:
        switch_off(3)
    if not CONFIG.need_reconnect:
        publish_state(3)


def check_empty_curr_house_alarm():
    if CONFIG.curr_house_alarm == "":  # we need to set up correct current state
        CONFIG.curr_house_alarm = "ARM_HOME"  # default
        if not CONFIG.need_reconnect:
            publish_alarm(CONFIG.arm[CONFIG.curr_house_alarm])


def check_any_horn_activated_to_long():
    if CONFIG.alarm_triggered or 'at' not in CONFIG.info or CONFIG.info['at'] == const(0):
        return
    # if any already activated for 30 min - turn it off (callbk)
    pins_val = [CONFIG.info['relay_pin{}'.format(i)].value() for i in range(3, 5)]
    if any(pins_val):
        alarm_time_diff = time() - CONFIG.info['at']
        if alarm_time_diff > const(1500):  # if more than 30 min - turn it off
            for i, v in enumerate(pins_val):
                if v:
                    switch_off(3+i)
                    if not CONFIG.need_reconnect:
                        try:
                            publish_state(3+i)
                        except Exception as e:
                            CONFIG.check_for_keyboard_interrupt(e, 'check_any_horn_activated_to_long')
