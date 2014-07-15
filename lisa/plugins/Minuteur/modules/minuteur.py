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

# TODO :
# stocker les timer dans un fichier pour y acceder pour apres un crash serveur par exemple


#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from lisa.server.plugins.IPlugin import IPlugin
import gettext
import inspect
import os, sys
from time import sleep
from lisa.Neotique.NeoTrans import NeoTrans
from lisa.Neotique.NeoTimer import NeoTimer
from lisa.Neotique.NeoDialog import NeoDialog


#-----------------------------------------------------------------------------
# Plugin Minuteur class
#-----------------------------------------------------------------------------
class Minuteur(IPlugin):
    """
    Plugin main class
    """
    def __init__(self):
        super(Minuteur, self).__init__()
        self.configuration_plugin = self.mongo.lisa.plugins.find_one({"name": "Minuteur"})
        self.path = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile(inspect.currentframe()))[0],os.path.normpath("../lang/"))))
        self._ = NeoTrans(domain = 'minuteur', localedir = self.path, fallback = True, languages = [self.configuration_lisa['lang']]).Trans

        self.Timers = []
        self.dialog = NeoDialog(self.configuration_lisa)

    #-----------------------------------------------------------------------------
    def setMinuteur(self, jsonInput):
        """
        Set a new timer
        """
        if __name__ == "__main__" :
            print ("\n \n \n json d'entree = ", jsonInput,"\n \n \n ")

        # Get duration
        duration_s = 0
        try:
            # If Wit returned multiple durations
            if type(jsonInput['outcome']['entities']['duration']) is list:
                for element in jsonInput['outcome']['entities']['duration']:
                    duration_s += int(element['value'])
            # Only one duration
            elif type(jsonInput['outcome']['entities']['duration']) is dict:
                duration_s = int(jsonInput['outcome']['entities']['duration']['value'])
            else:
                # Unknown
                raise
        except:
            pass

        # Check duration
        if duration_s <= 0:
            message = self._("You didn't specify a duration")
            return self.dialog.AnswerWithQuestion(plugin = __name__.split('.')[-1], method = sys._getframe().f_code.co_name, message = message, protocol = jsonInput['lisaprotocol'], caller = self, caller_cbk = self._question_cbk, caller_param = jsonInput)

        # Get timer name
        name = ""
        try:
            name = str(jsonInput['outcome']['entities']['message_subject']['value'])
        except:
            pass

        # Start timer
        self._create(duration_s = duration_s, name = name, protocol = jsonInput['lisaprotocol'])

        # Create confirmation message
        message = self._('I start a timer for').format(self._duration_to_str(duration_s))
        if name != "":
            message += " {0} {1}".format(self._("for"), name)

        return self.dialog.SimpleAnswer(plugin = __name__.split('.')[-1], method = sys._getframe().f_code.co_name, message = message, protocol = jsonInput['lisaprotocol'])

    #-----------------------------------------------------------------------------
    def getMinuteur(self, jsonInput):
        """
        Get all timer or remaining time on a timer
        """

        # Get name
        name = ""
        try:
            name = str(jsonInput['outcome']['entities']['message_subject']['value'])
        except:
            pass

        if name =="" : #get all timer
            listtimer = []
            for t in self.Timers :
                listtimer.append(str(t['name']) + ' ')
            message = self._('existing timer').format(slist=', '.join(listtimer))
            return self.dialog.SimpleAnswer(plugin = __name__.split('.')[-1], method = sys._getframe().f_code.co_name, message = message, protocol = jsonInput['lisaprotocol'])

        message = self._("I don't know this timer")
        # Search timer
        for t in self.Timers :
            if t['name'] == name:
                # Create message
                message = self._("There is remaining").format(self._duration_to_str(t['timer'].get_left_time_s()))
                if name != "":
                    message += " {0} {1}" .format(self._("for"), name)
                break

        return self.dialog.SimpleAnswer(plugin = __name__.split('.')[-1], method = sys._getframe().f_code.co_name, message = message, protocol = jsonInput['lisaprotocol'])

    #-----------------------------------------------------------------------------
    def stopMinuteur(self, jsonInput):
        """
        stop a timer
        """
        # Get name
        name = ""
        try:
            name = str(jsonInput['outcome']['entities']['message_subject']['value'])
            
            # Search timer
            message = self._("I don't know this timer")
            for t in self.Timers:
                if t['name'] == name:
                    # Create message
                    t['timer'].stop()
                    message = self._("I stop timer").format(name = name)
        except:
            message = self._("cant stop timer")


        return self.dialog.SimpleAnswer(plugin = __name__.split('.')[-1], method = sys._getframe().f_code.co_name, message = message, protocol = jsonInput['lisaprotocol'])

    #-----------------------------------------------------------------------------
    def _create(self, duration_s, name, protocol):
        """
        Create a new timer
        """
        # Add a new timer
        self.Timers.append({'name': name, 'protocol': protocol})
        self.Timers[-1]['timer'] = NeoTimer(duration_s = duration_s, user_cbk = self._timeout_cbk, user_param = self.Timers[-1])

    #-----------------------------------------------------------------------------
    def _timeout_cbk(self, timer):
        """
        Internal timer callback
        """
        # Notify user
        if timer['name'] != "":
            sMessage = self._("The timer is over").format("%s %s" % (self._("for"), timer['name']))
        else:
            sMessage = self._("The timer is over").format("")
        if __name__ == "__main__" :
            print "Notify client : %s" % (sMessage)
        else:
            self.dialog.SimpleNotify(plugin = "Minuteur", method = "setMinuteur", message = sMessage, protocol = timer['protocol'])

        # Remove timer
        self.Timers.remove(timer)

    #-----------------------------------------------------------------------------
    def _question_cbk(self, jsonInput, jsonAnswer):
        if jsonAnswer is None:
            return

        try:
            # Add duration to first json
            jsonInput['outcome']['entities']['duration'] = jsonAnswer['outcome']['entities']['duration']
            self.setMinuteur(jsonInput)
        except:
            pass

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
# Tests
#-----------------------------------------------------------------------------
if __name__ == "__main__" :
    jsonInput2 = {'from': u'Lisa-Web', 'zone': u'WebSocket',u'msg_id': u'd31f4acd-9ed0-4248-9344-b2b29b95982c',
        u'msg_body': u'compte \xe0 rebours 20 secondes pour le poisson',
        u'outcome': {u'entities': {
        u'duration': {u'body': u'23 secondes', u'start': 17, u'end': 28, u'value': 23},
        u'message_subject': {u'body': u'pour le poisson', u'start': 29, u'end': 44, u'suggested': True, u'value': u'le poisson'}
        },u'confidence': 0.7,
        u'intent': u'minuteur_rebours'}, 'type': u'chat'}


    jsonInputGetallMinuteur = {'from': u'Lisa-Web', 'zone': u'WebSocket',u'msg_id': u'd31f4acd-9ed0-4248-9344-b2b29b95982c',
        u'msg_body': u'combien de temps reste-t-il pour le lapin',
        u'outcome': {u'entities': {  },
        u'confidence': 0.949, u'intent': u'minuteur_tempsrestant'}, 'type': u'chat'}

    jsonInputGetMinuteur = {'from': u'Lisa-Web', 'zone': u'WebSocket',u'msg_id': u'd31f4acd-9ed0-4248-9344-b2b29b95982c',
        u'msg_body': u'combien de temps reste-t-il pour le lapin',
        u'outcome': {u'entities': {
        u'message_subject': {u'body': u'le lapin', u'start': 33, u'end': 41, u'suggested': True, u'value': u'le poisson'}
        }, u'confidence': 0.949, u'intent': u'minuteur_tempsrestant'}, 'type': u'chat'}

    essai = Minuteur()
    ret = essai.setMinuteur(jsonInput2)
    print ret['body']

    sleep(3)
    ret = essai.getMinuteur(jsonInputGetallMinuteur)
    print ret['body']
    ret = essai.getMinuteur(jsonInputGetMinuteur)
    print ret['body']

# --------------------- End of minuteur.py  ---------------------
