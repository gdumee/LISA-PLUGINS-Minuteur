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
import os, sys, uuid
from time import sleep
from lisa.Neotique.NeoTrans import NeoTrans
from lisa.Neotique.NeoTimer import NeoTimer


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

    #-----------------------------------------------------------------------------
    def setMinuteur(self, jsonInput):
        """
        Set a new timer
        """
        # Tests
        if __name__ == "__main__":
            print ("\n \n \n json d'entree = ", jsonInput,"\n \n \n ")

        # Get context
        context = jsonInput['context']

        # Get timer name
        context.createClientVar(name = 'minuteur_name', default = "")
        try:
            context.minuteur_name = jsonInput['outcome']['entities']['message_subject']['value']
        except:
            pass

        # Get duration
        context.createClientVar(name = 'minuteur_duration', default = 0)
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

            # Tests
            if __name__ == "__main__":
                return {'body': message}

            # Ask for duration
            self.askClient(context = context, text = message, answer_cbk = self._question_cbk)
            return

        # Start timer
        self._create(duration_s = context.minuteur_duration, name = context.minuteur_name, context = context)

        # Create confirmation message
        message = self._('start_timer').format(duration = self._duration_to_str(context.minuteur_duration), name = self._name_str(context.minuteur_name))

        # Tests
        if __name__ == "__main__":
            return {'body':message}

        # Clear context vars
        context.minuteur_duration = 0
        context.minuteur_name = ""

        # Return result to client
        self.speakToClient(context = jsonInput['context'], text = message)

    #-----------------------------------------------------------------------------
    def getMinuteur(self, jsonInput):
        """
        Get all timer or remaining time on a timer
        """
        # Get context
        context = jsonInput['context']
        context.createGlobalVar(name = 'minuteur_timers', default = {})

        # No active timer
        if len(context.minuteur_timers) == 0:
            message += self._("no_timer")

            # Answer client
            self.speakToClient(context = context, text = message)
            return

        # Get name
        name = ""
        try:
            name = str(jsonInput['outcome']['entities']['message_subject']['value'])
        except:
            # When only one timer, select it by default
            if len(context.minuteur_timers) == 1:
                name = context.minuteur_timers[context.minuteur_timers.keys()[0]]['name']
            else:
                name = ""

        # If there is a name
        if name != "":
            # Search named timer
            for uid in context.minuteur_timers:
                if context.minuteur_timers[uid]['name'] == name:
                    # Create message
                    message = self._("left_time").format(duration = self._duration_to_str(context.minuteur_timers[uid]['timer'].get_left_time_s()), name = self._name_str(name))

                    if __name__ == "__main__":
                        return {'body': message}

                    # Answer client
                    self.speakToClient(context = context, text = message)
                    return

        # No timer found
        self._getMinuteurList(context, context.minuteur_timers)

    #-----------------------------------------------------------------------------
    def stopMinuteur(self, jsonInput):
        """
        stop a timer
        """
        # Get context
        context = jsonInput['context']
        context.createGlobalVar(name = 'minuteur_timers', default = {})

        # No active timer
        if len(context.minuteur_timers) == 0:
            message += self._("no_timer")

            # Answer client
            self.speakToClient(context = context, text = message)
            return

        # Get name
        name = ""
        try:
            name = str(jsonInput['outcome']['entities']['message_subject']['value'])
        except:
            # When only one timer, select it by default
            if len(context.minuteur_timers) == 1:
                name = context.minuteur_timers[context.minuteur_timers.keys()[0]]['name']
            else:
                name = ""

        # If there is a name
        if name != "":
            # Search named timer
            for uid in context.minuteur_timers:
                if context.minuteur_timers[uid]['name'] == name:
                    # Stop Timer
                    context.minuteur_timers[uid]['timer'].stop()
                    message = self._("stop_timer").format(name = self._name_str(timer['name']))
                    context.minuteur_timers.pop(uid)

                    if __name__ == "__main__":
                        return {'body': message}

                    # Answer client
                    self.speakToClient(context = context, text = message)
                    return

        # No timer found
        self._getMinuteurList(context, context.minuteur_timers)

    #-----------------------------------------------------------------------------
    def _getMinuteurList(self, context, Timers):
        # No timer found, return timer list
        message = self._("unknown_timer") + ". "

        if len(Timers) == 0:
            message += self._("no_timer")
        else:
            message += self._("timer_list")

        for uid in Timers:
            message += ', ' + str(Timers[uid]['name'])

        if __name__ == "__main__":
            return {'body': message}

        # Answer client
        self.speakToClient(context = context, text = message)

    #-----------------------------------------------------------------------------
    def _create(self, duration_s, name, context):
        """
        Create a new timer
        """
        # Get context
        context.createGlobalVar(name = 'minuteur_timers', default = {})

        # Add a new timer
        uid = str(uuid.uuid1())
        context.minuteur_timers[uid] = {'uid': uid, 'name': name}
        context.minuteur_timers[uid]['timer'] = NeoTimer(duration_s = duration_s, user_cbk = self._timeout_cbk, user_param = {'context': context, 'uid': uid})

    #-----------------------------------------------------------------------------
    def _timeout_cbk(self, params):
        """
        Internal timer callback
        """
        # Get context
        context = params['context']
        uid = params['uid']
        context.createGlobalVar(name = 'minuteur_timers', default = {})
        timer = context.minuteur_timers[uid]

        # Notify user
        sMessage = self._("timer_over").format(name = self._name_str(timer['name']))

        # Remove timer
        context.minuteur_timers.pop(timer['uid'])

        # Tests
        if __name__ == "__main__":
            return {'body': sMessage}

        self.speakToClient(context = context, text = sMessage)

    #-----------------------------------------------------------------------------
    def _question_cbk(self, context, jsonAnswer):
        if jsonAnswer is None:
            # Reset values
            context.minuteur_duration = 0
            context.minuteur_name = ""
            return

        # Retry
        self.setMinuteur(jsonAnswer)

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


#-----------------------------------------------------------------------------
# Tests
#-----------------------------------------------------------------------------
if __name__ == "__main__":
    jsonInput2 = {'from': u'Lisa-Web', 'zone': u'WebSocket',u'msg_id': u'd31f4acd-9ed0-4248-9344-b2b29b95982c',
        u'lisaprotocol': '<lisa.server.libs.server.Lisa instance at 0x7ffdcaea33b0>',
        u'msg_body': u'compte \xe0 rebours 20 secondes pour le poisson',
        u'outcome': {u'entities': {
        u'duration': {u'body': u'3 minutes', u'start': 17, u'end': 28, u'value': 180},
        u'message_subject': {u'body': u'pour le poisson', u'start': 29, u'end': 44, u'suggested': True, u'value': u'le jambon'}
        },u'confidence': 0.7,
        u'intent': u'minuteur_rebours'}, 'type': u'chat'}

    jsonInput3 = {'from': u'Lisa-Web', 'zone': u'WebSocket',u'msg_id': u'd31f4acd-9ed0-4248-9344-b2b29b95982c',
        u'lisaprotocol': '<lisa.server.libs.server.Lisa instance at 0x7ffdcaea33b0>',
        u'msg_body': u'compte \xe0 rebours 20 secondes pour le poisson',
        u'outcome': {u'entities': {
        u'duration': {u'body': u'3 minutes', u'start': 17, u'end': 28, u'value': 180},
        u'message_subject': {u'body': u'pour le poisson', u'start': 29, u'end': 44, u'suggested': True, u'value': u'le rat'}
        },u'confidence': 0.7,
        u'intent': u'minuteur_rebours'}, 'type': u'chat'}

    jsonInputGetallMinuteur = {'from': u'Lisa-Web', 'zone': u'WebSocket',u'msg_id': u'd31f4acd-9ed0-4248-9344-b2b29b95982c',
        u'lisaprotocol': '<lisa.server.libs.server.Lisa instance at 0x7ffdcaea33b0>',
        u'msg_body': u'combien de temps reste-t-il pour le lapin',
        u'outcome': {u'entities': {  },
        u'confidence': 0.949, u'intent': u'minuteur_tempsrestant'}, 'type': u'chat'}

    jsonInputGetMinuteur = {'from': u'Lisa-Web', 'zone': u'WebSocket',u'msg_id': u'd31f4acd-9ed0-4248-9344-b2b29b95982c',
        u'lisaprotocol': '<lisa.server.libs.server.Lisa instance at 0x7ffdcaea33b0>',
        u'msg_body': u'combien de temps reste-t-il pour le lapin',
        u'outcome': {u'entities': {
        u'message_subject': {u'body': u'le lapin', u'start': 33, u'end': 41, u'suggested': True, u'value': u'le poisson'}
        }, u'confidence': 0.949, u'intent': u'minuteur_tempsrestant'}, 'type': u'chat'}

    essai = Minuteur()
    ret = essai.setMinuteur(jsonInput2)
    print ret['body']


    sleep(3)
    essai = Minuteur()
    ret = essai.getMinuteur(jsonInputGetallMinuteur)
    print ret['body']
    ret = essai.getMinuteur(jsonInputGetMinuteur)
    print ret['body']

# --------------------- End of minuteur.py  ---------------------
