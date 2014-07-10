# -*- coding: UTF-8 -*-

# Imports
from threading import Timer
from time import time, sleep

class NeoTimer():
    """
    Timer with a user callback
    """
    def __init__(self, duration_s, user_cbk, user_param):
        """
        Create a new timer
        """
        # Set internals
        self.running = True
        self.end = time() + duration_s
        self.user_cbk = user_cbk
        self.user_param = user_param

        # Start timer
        self.timer = Timer(duration_s, self._timer_cbk)
        self.timer.start()

    def _timer_cbk(self):
        """
        Internal Timer callback
        """
        # Call user callback
        self.user_cbk(self.user_param)

        # Set running state
        self.running = False

    def stop(self):
        """
        Stop current timer
        """
        # If not running
        if self.running == False:
            return

        # Stop timer
        self.running = False
        self.timer.stop()

    def get_left_time_s(self):
        """
        Return timer left time in seconds
        """
        # If not running
        if self.running == False:
            return 0

        return self.end - time()


#################################################################
# Tests
if __name__ == "__main__" :
    def timer_cbk(message):
        print "Fin du minuteur {} dans {}".format(message[0], message[1])

    print "avant le start"
    x = NeoTimer(5, timer_cbk, ("Poulet", "Cuisine"))
    print "Apres le start"

    for i in range(10):
        x.stop()
        a = x.get_left_time_s()
        if a == 0:
            break;
        print "Reste {} s".format(a)
        sleep(1)
