from loadconf import CONFIG


def setup_pins():
    for nr in range(1, 5):
        if CONFIG.info['default_on{0}'.format(nr)]:
            switch_on(nr)
        else:
            switch_off(nr)
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
    if CONFIG.debug:
        print("before channel {} pin={} => {}".format(nr, pin.value(), new_val))
    pin.value(new_val)
