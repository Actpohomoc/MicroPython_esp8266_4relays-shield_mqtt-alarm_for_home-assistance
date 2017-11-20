from utime import sleep
from loadconf import CONFIG, FUSED_VALUES
from alarmod import turn_alarm_off
from publish import publish_alarm, publish_state, publish_state_fused, publish_debug_state
from switchs import switch_on, switch_off


def callback(topic, msg):
    ls_topic = topic.split(b'/')
    main_topic = ls_topic[1]
    print("Got:{} in:{}".format(msg, topic))
    is_msg_on_off = (msg == b"on", msg == b"off")
    if CONFIG.debug:
        print("ls_topic: {}, main_topic: {}".format(ls_topic, main_topic))
    #
    if main_topic == b"alarm":
        if len(ls_topic) > 2 and ls_topic[2] == b"set":
            new_alarm_state = msg.decode("utf-8")
            if CONFIG.alarm_triggered:  # id already triggered go to spec function
                turn_alarm_off(new_alarm_state)
            else:
                CONFIG.curr_house_alarm = new_alarm_state
                publish_alarm(CONFIG.arm[new_alarm_state])
                # send small horn signal
                switch_on(3)
                sleep(1)
                switch_off(3)
                publish_state(3)
                #
        elif CONFIG.curr_house_alarm == "":  # we need to set up correct current state
            if msg == b'triggered':
                CONFIG.curr_house_alarm = "ARM_HOME"  # if already triggered
                publish_alarm(CONFIG.arm[CONFIG.curr_house_alarm])
            else:
                for k, v in CONFIG.arm.items():
                    if v == msg:
                        CONFIG.curr_house_alarm = k
                        break
    #
    elif main_topic == b"reset":
        if msg == b"on":
            if CONFIG.debug:
                print("RESET...")
            sleep(3)
            import machine
            machine.reset()
    #
    elif main_topic == b"debug":
        if any(is_msg_on_off):
            CONFIG.debug = True if msg == b"on" else False
            publish_debug_state()
    #
    elif main_topic == b"control":
        r = ls_topic[-1].decode("utf-8")
        if CONFIG.debug:
            print("r={}".format(r))
        # maybe it is not good way to check fused switch
        if len(r) == 2:
            nr, nch_c, nch_a = (int(r[0]), r, r[0]+('2' if r[1] == '1' else '1'))
            if any(is_msg_on_off):
                CONFIG.info[FUSED_VALUES][nch_c] = is_msg_on_off[0]
                if CONFIG.info[FUSED_VALUES][nch_a]:  # if another value if on
                    if is_msg_on_off[0]:  # on
                        print("Channel {} ON".format(nr))
                        switch_on(nr)
                        publish_state(nr)
                        # set time to turn alarm off after 30 min
                    else:  # off
                        print("Channel {} OFF".format(nr))
                        CONFIG.info[FUSED_VALUES][nch_a] = False
                        switch_off(nr)
                        publish_state(nr)
                #
                publish_state_fused(nch_c, nch_a)
        #
        elif int(r) in range(1, 5):
            nr = int(r)
            if any(is_msg_on_off):
                # on or off - other stuff checks down
                if is_msg_on_off[0]:
                    #
                    print("Channel {} ON".format(nr))
                    switch_on(nr)
                    if nr < 3:
                        # ARM_AWAY -> ARM_HOME auto when on sw 1,2
                        if CONFIG.curr_house_alarm == "ARM_AWAY":
                            CONFIG.curr_house_alarm = "ARM_HOME"
                            publish_alarm(CONFIG.arm[CONFIG.curr_house_alarm])
                        # wait 1 more sec and off
                        sleep(1)
                        switch_off(nr)
                #
                else:
                    print("Channel {} OFF".format(nr))
                    if nr < 3:
                        switch_on(nr)
                        # wait 1 more sec and off
                        sleep(1)
                    switch_off(nr)
                #
                publish_state(nr)
            #
            elif msg == b"state?":
                publish_state(nr)
            else:
                print(b"ign msg")