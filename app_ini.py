import ujson as json


def save_default_ini(conf_ini, conf):
    try:
        with open(conf_ini, "w") as f:
            f.write(json.dumps(conf))
            print("Saved new conf to {}".format(conf_ini))
    except OSError:
        print("Couldn't save to {}".format(conf_ini))


def load_config(conf_ini, conf_default=None):
    try:
        with open(conf_ini) as f:
            conf_new = json.loads(f.read())
        print("Load conf from {}".format(conf_ini))
    except (OSError, ValueError):
        if conf_default is not None:
            print("Can't load {} load default".format(conf_ini))
            save_default_ini(conf_ini, conf_default)
            return conf_default
        else:
            return None
    return conf_new
