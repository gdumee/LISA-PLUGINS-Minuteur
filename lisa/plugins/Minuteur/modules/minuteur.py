# -*- coding: UTF-8 -*-

###################################
#    Minuteur
# plugin Lisa
# par Guillaume
###################################
#
#Le plugin permet de lancer des minuteurs en arriere plan
#Ces minuteurs sont simultanés et asynchrones : ils  ne bloque pas LISA
#
#
#Les fonctions publiques sont getxxx, setxxxx
#Les autres fonctions sont privées au module
#########################################


# TODO : stocker les timer dans un fichier pour y acceder pour apres un crash serveur par exemple
Version = "1.0.1"

# Imports
if __name__ == "__main__" :
    pass
else :
    from lisa.server.plugins.IPlugin import IPlugin
import gettext
import inspect
import os
from time import sleep
from NeoTimer import NeoTimer
import Notification
from Notification import NotifyClient


#################################################################
# Tests
if __name__ == "__main__" :
    jsonInput2 = {'from': u'Lisa-Web', 'zone': u'WebSocket',u'msg_id': u'd31f4acd-9ed0-4248-9344-b2b29b95982c',
        u'msg_body': u'compte \xe0 rebours 20 secondes pour le poisson',
        u'outcome': {u'entities': {
        u'duration': {u'body': u'20 secondes', u'start': 17, u'end': 28, u'value': 6},
        u'message_subject': {u'body': u'pour le poisson', u'start': 29, u'end': 44, u'suggested': True, u'value': u'le poisson'}
        },u'confidence': 0.7,
        u'intent': u'minuteur_rebours'}, 'type': u'chat'}

    jsonInput2Durations = {'from': u'Lisa-Web', 'zone': u'WebSocket',u'msg_id': u'd31f4acd-9ed0-4248-9344-b2b29b95982c',
        u'msg_body': u'compte \xe0 rebours 20 secondes pour le poisson',
        u'outcome': {u'entities': {
        u'duration': [{u'body': u'une heure', u'start': 9, u'end': 20, u'value': 3600},{u'body': u'une minutes', u'start': 9, u'end': 20, u'value': 60}, {u'body': u'25 secondes', u'start': 24, u'end': 35, u'value': 25}],
        u'message_subject': {u'body': u'le repas', u'start': 41, u'end': 49, u'suggested': True, u'value': u'le repas'}
        }, u'confidence': 0.91,
        u'intent': u'minuteur_rebours'}, 'type': u'chat'}

    jsonInputGetMinuteur = {'from': u'Lisa-Web', 'zone': u'WebSocket',u'msg_id': u'd31f4acd-9ed0-4248-9344-b2b29b95982c',
        u'msg_body': u'combien de temps reste-t-il pour le lapin',
        u'outcome': {u'entities': {
        u'message_subject': {u'body': u'le lapin', u'start': 33, u'end': 41, u'suggested': True, u'value': u'le poisson'}
        }, u'confidence': 0.949, u'intent': u'minuteur_tempsrestant'}, 'type': u'chat'}

    class IPlugin():
        def __init__(self):
            pass

class Minuteur(IPlugin):
    """
    Plugin main class
    """

    def __init__(self):
        # When testing
        self.path = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile(inspect.currentframe()))[0],os.path.normpath("../lang/"))))
        if __name__ <> "__main__" :
            super(Minuteur, self).__init__()
            self.configuration_plugin = self.mongo.lisa.plugins.find_one({"name": "Minuteur"})
            self._ = translation = gettext.translation(domain = 'Minuteur', localedir = self.path, fallback = True, languages = [self.configuration_lisa['lang']]).ugettext
        else:
            self._ = lambda x: x
            self._ = translation = gettext.translation(domain = 'Minuteur', localedir = self.path, fallback = True, languages = ['fr-FR']).ugettext
        self.Timers = []

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
        if duration_s <= 0:
            return {'plugin': "Minuteur", 'method': "setMinuteur", 'body': self._("You didn't specify a duration")}

        # Get zone and name
        zone = jsonInput['zone']
        name = ""
        try:
            name = str(jsonInput['outcome']['entities']['message_subject']['value'])
        except:
            pass

        # Start timer
        self._create(duration_s = duration_s, name = name, zone = zone)

        # Create confirmation message
        message = self._("I start a timer for %s") % (self.duration_to_str(duration_s))
        if name != "":
            message += " %s %s" % (self._("for"), name)
        return {'plugin': "Minuteur", 'method': "setMinuteur", 'body': message}

    def _create(self, duration_s, name, zone):
        """
        Create a new timer
        """
        # Add a new timer
        self.Timers.append({'name': name, 'zone': zone})
        self.Timers[-1]['timer'] = NeoTimer(duration_s = duration_s, user_cbk = self._timer_cbk, user_param = self.Timers[-1])

    def _timer_cbk(self, timer):
        """
        Internal timer callback
        """
        # Notify user
        sMessage = self._("The timer %s is over") % ("%s %s" % (self._("for"), timer['name']))
        if __name__ == "__main__" :
            print "Notify clients in zone %s : %s" % (timer['zone'], sMessage)
        else:
            NotifyClient(sMessage, timer['zone'])
        
        # Remove timer
        self.Timers.remove(timer)

    def getMinuteur(self, jsonInput):
        """
        Get left time on a timer
        """
        
        # Get name
        name = ""
        try:
            name = str(jsonInput['outcome']['entities']['message_subject']['value'])
        except:
            pass

        # Search timer
        for t in self.Timers:
            if t['name'] == name:
                # Create message
                message = self._("There is %s left") % (self.duration_to_str(t['timer'].get_left_time_s()))
                if name != "":
                    message += " %s %s" % (self._("for"), name)

                return {'plugin': "Minuteur", 'method': "getMinuteur", 'body': message}

        return {'plugin': "Minuteur", 'method': "getMinuteur", 'body': self._("I don't know this timer") }

    def ConvertDuration(self, duration_s):
        """
        Convert duration to hours, minutes, seconds
        """
        duration_s = int(duration_s)
        ret = {}
        ret['h'] = duration_s /3600
        duration_s -= ret['h'] * 3600
        ret['m'] = duration_s / 60
        ret['s'] = duration_s - ret['m'] * 60
        return ret

    def duration_to_str(self, duration_s):
        duration = self.ConvertDuration(duration_s)
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


#############################################################
# Tests
if __name__ == "__main__" :
    essai=Minuteur()
    ret = essai.setMinuteur(jsonInput2)
    print ret['body']

    sleep(3)
    ret = essai.getMinuteur(jsonInputGetMinuteur)
    print ret['body']
