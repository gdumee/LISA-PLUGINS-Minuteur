# -*- coding: UTF-8 -*-
#-----------------------------------------------------------------------------
# project     : Lisa plugins
# module      : Minuteur
# file        : minuteur.py
# description : Manage timers for users
# author      : G.Audet
#-----------------------------------------------------------------------------
# copyright   : Neotique
#-----------------------------------------------------------------------------


#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
import uuid
from time import time
from lisa.server.plugins.IPlugin import IPlugin
from lisa.Neotique.NeoTimer import NeoTimer
from lisa.Neotique.NeoConv import NeoConv


#-----------------------------------------------------------------------------
# Plugin Minuteur class
#-----------------------------------------------------------------------------
class Minuteur(IPlugin):
    """
    Plugin main class
    """
    # NeoTimers
    _ActiveTimers = {}

    #-----------------------------------------------------------------------------
    def __init__(self):
        super(Minuteur, self).__init__(plugin_name = "Minuteur")
        # TODO reload Timers from save conf

    #-----------------------------------------------------------------------------
    def __del__(self):
        # Stop active timers
        for t in self._ActiveTimers:
            self._ActiveTimers[t].stop()
        self._ActiveTimers = {}

    #-----------------------------------------------------------------------------
    def setTimer(self, jsonInput):
        """
        Set a new timer
        """
        # Get context
        context = jsonInput['context']

        # Get timer name
        try:
            context.minuteur_name = jsonInput['outcome']['entities']['message_subject']['value']
        except:
            pass

        # Get duration
        try:
            # If Wit returned multiple durations
            if type(jsonInput['outcome']['entities']['duration']) is list:
                for element in jsonInput['outcome']['entities']['duration']:
                    context.minuteur_duration += int(element['value'])
            # Only one duration
            elif type(jsonInput['outcome']['entities']['duration']) is dict:
                context.minuteur_duration = int(jsonInput['outcome']['entities']['duration']['value'])
        except:
            pass

        # Check duration
        if context.minuteur_duration <= 0:
            message = self._("no_duration")

            # Ask for duration
            self.askClient(context = context, text = message, wit_context = {'state': "ask_duration"}, answer_cbk = self._question_cbk)
            return

        # Start timer
        self._create(duration_s = context.minuteur_duration, name = context.minuteur_name, context = context)

        # Create confirmation message
        message = self._('start_timer').format(duration = self._duration_to_str(context.minuteur_duration), name = self._name_str(context.minuteur_name))

        # Clear context vars
        context.minuteur_duration = 0
        context.minuteur_name = ""

        # Return result to client
        self.speakToClient(context = jsonInput['context'], text = message)

    #-----------------------------------------------------------------------------
    def getTimer(self, jsonInput):
        """
        Get all timer or remaining time on a timer
        """
        # Get context
        context = jsonInput['context']

        # Get name
        name = ""
        try:
            name = str(jsonInput['outcome']['entities']['message_subject']['value'])
        except:
            pass

        # Get timer
        timer = self._getTimer(context = context, name = name)
        if timer is not None:
            # Create message
            if timer['active'] == False:
                message = self._("ended_timer").format(name = self._name_str(name))
            else:
                message = self._("left_time").format(duration = self._duration_to_str(timer['end'] - time()), name = self._name_str(name))

            # Answer client
            self.speakToClient(context = context, text = message)
            return

        # No timer found, return list
        self._getTimerList(context)

    #-----------------------------------------------------------------------------
    def stopTimer(self, jsonInput):
        """
        stop a timer
        """
        # Get context
        context = jsonInput['context']

        # Get name
        name = ""
        try:
            name = str(jsonInput['outcome']['entities']['message_subject']['value'])
        except:
            pass

        # Get timer
        timer = self._getTimer(context = context, name = name)
        if timer is not None:
            # Create message
            if timer['active'] == False:
                message = self._("ended_timer").format(name = self._name_str(name))
            else:
                # Stop Timer
                Minuteur._ActiveTimers[timer['uid']].stop()
                Minuteur._ActiveTimers.pop(timer['uid'])
                timer['active'] = False
                message = self._("stop_timer").format(name = self._name_str(timer['name']))

            # Answer client
            self.speakToClient(context = context, text = message)
            return

        # No timer found, return list
        self._getTimerList(context)

    #-----------------------------------------------------------------------------
    def _getTimer(self, context, name):
        # If there is a name
        if name == "":
            # When only one timer, select it by default
            if len(context.minuteur_timers) == 1:
                return context.minuteur_timers[context.minuteur_timers.keys()[0]]

        # Search named timer
        for uid in context.minuteur_timers:
            if NeoConv.compareSimilar(context.minuteur_timers[uid]['name'], name) == True:
                return context.minuteur_timers[uid]

        # Not found
        return None

    #-----------------------------------------------------------------------------
    def _getTimerList(self, context):
        # No active timer
        if len(Minuteur._ActiveTimers) == 0:
            message += self._("no_timer")
        else:
            # No timer found, return timer list
            message = self._("unknown_timer") + ". " + self._("timer_list")
            for uid in context.minuteur_timers:
                if context.minuteur_timers[uid]['active'] == True:
                    message += ', ' + str(context.minuteur_timers[uid]['name'])

        # Answer client
        self.speakToClient(context = context, text = message)

    #-----------------------------------------------------------------------------
    def _create(self, duration_s, name, context):
        """
        Create a new timer
        """
        # Add a new timer
        uid = str(uuid.uuid1())
        context.minuteur_timers[uid] = {'uid': uid}
        context.minuteur_timers[uid]['name'] = name
        context.minuteur_timers[uid]['start'] = time()
        context.minuteur_timers[uid]['end'] = time() + duration_s
        context.minuteur_timers[uid]['active'] = True
        Minuteur._ActiveTimers[uid] = NeoTimer(duration_s = duration_s, user_cbk = self._timeout_cbk, user_param = {'context': context, 'uid': uid})

    #-----------------------------------------------------------------------------
    def _timeout_cbk(self, params):
        """
        Internal timer callback
        """
        # Get context
        context = params['context']
        uid = params['uid']
        timer = context.minuteur_timers[uid]

        # Notify user
        sMessage = self._("timer_over").format(name = self._name_str(timer['name']))

        # Remove timer
        timer['active'] = False
        Minuteur._ActiveTimers.pop(timer['uid'])

        # Send message to client
        self.speakToClient(context = context, text = sMessage)

    #-----------------------------------------------------------------------------
    def _question_cbk(self, context, jsonAnswer):
        if jsonAnswer is None:
            # Reset values
            context.minuteur_duration = 0
            context.minuteur_name = ""
            return

        # Retry
        self.setTimer(jsonAnswer)

    #-----------------------------------------------------------------------------
    def _convert_duration(self, duration_s):
        """
        Convert duration to hours, minutes, seconds
        """
        ret = {}
        ret['m'], ret['s'] = divmod(int(duration_s), 60)
        ret['h'], ret['m'] = divmod(ret['m'], 60)
        return ret

    #-----------------------------------------------------------------------------
    def _duration_to_str(self, duration_s):
        """
        Convert a duration to string "[x hours] [y minutes] [z seconds]"
        """
        duration = self._convert_duration(duration_s)
        msg = ""
        if duration['h'] > 1:
            msg += "%d %ss" % (duration['h'], self._("hour"))
        elif duration['h'] > 0:
            msg += "%d %s" % (duration['h'], self._("hour"))

        if duration['m'] > 1:
            msg += "%d %ss" % (duration['m'], self._("minute"))
        elif duration['m'] > 0:
            msg += "%d %s" % (duration['m'], self._("minute"))

        if duration['s'] > 1:
            msg += "%d %ss" % (duration['s'], self._("second"))
        elif duration['s'] > 0:
            msg += "%d %s" % (duration['s'], self._("second"))

        return msg

    #-----------------------------------------------------------------------------
    def _name_str(self, name):
        if name == "":
            return ""
        return "{} ".format(self._("for")) + name

# --------------------- End of minuteur.py  ---------------------
