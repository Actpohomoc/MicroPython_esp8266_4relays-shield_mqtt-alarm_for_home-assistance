import esp
esp.osdebug(None)
import wifis as w
w.set_active_ap_if(True)
import webrepl
webrepl.start()
w.start_wifi()
webrepl.start()
