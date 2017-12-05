from loadconf import CONFIG


def setup_pins():
    # setting the pins by defaults
    for nr, dv in enumerate(CONFIG.defaults_on.split(',')):  # "defaults_on": "0,0,0,0"
        if dv == "1":
            switch_on(nr+1)
        else:
            switch_off(nr+1)
    # del unused default_on info
    CONFIG.del_default_on()

            
def switch_on(nr):
    # 1
    new_val = 1
    switch_on_off(nr, new_val)


def switch_off(nr):
    # 0
    new_val = 0
    switch_on_off(nr, new_val)


def switch_on_off(nr, new_val):
    pin = CONFIG.info['relay_pin{}'.format(nr)]
    print("before channel {} pin={} => {}".format(nr, pin.value(), new_val))
    pin.value(new_val)
