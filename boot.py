import machine
print(('DEFAULT_RST', 'WDT_RST', 'EXCEPTION_RST', 'SOFT_WDT_RST', 'SOFT_RESTART',
       'DEEP_SLEEP_AWAKE', 'EXT_SYS_RST')[machine.reset_cause()])
import esp
esp.osdebug(None)
del esp
import webrepl
webrepl.start()
#import wifis as w
#w.start_wifi()
#del w
