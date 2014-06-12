# -*- coding: UTF-8 -*-

# Imports
from threading import Timer
import time
from time import sleep

# Classe timer avec appel de callback
class NeoTimer():
    def __init__(self, duration_s, user_cbk, user_param):
        # Set internals
        self.running = True
        self.end = time.time() + duration_s
        self.user_cbk = user_cbk
        self.user_param = user_param

        # Start timer
        self.timer = Timer(duration_s, self.timer_cbk)
        self.timer.start()

    def timer_cbk(self):
        # Call user callback
        self.user_cbk(self.user_param)

        # Set running state
        self.running = False

    def get_left_time_s(self):
        # If not running
        if self.running == False:
            return 0

        return round(self.end - time.time())


#################################################################
# Tests
if __name__ == "__main__" :
    def timer_cbk(message):
        print "Fin du minuteur {} dans {}".format(message[0], message[1])

    print "avant le start"
    x = NeoTimer(5, timer_cbk, ("Poulet", "Cuisine"))
    print "Apres le start"

    for i in range(10):
        a = x.get_left_time_s()
        if a == 0:
            break;
        print "Reste {} s".format(a)
        sleep(1)
