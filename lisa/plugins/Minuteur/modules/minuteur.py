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

# Main class
class Minuteur(IPlugin):
    dicTimer={}  #variable de class
    
    def __init__(self):
        if __name__ <> "__main__" :   #suppression pour le debug
            super(Minuteur, self).__init__()
            self.configuration_plugin = self.mongo.lisa.plugins.find_one({"name": "Minuteur"})
            self.path = os.path.realpath(os.path.abspath(os.path.join(os.path.split(
                inspect.getfile(inspect.currentframe()))[0],os.path.normpath("../lang/"))))
            #self._ = translation = gettext.translation(domain='Minuteur',
            #                                          localedir=self.path,
            #                                       fallback=True,
            #                                           languages=[self.configuration_lisa['lang']]).ugettext

    def setMinuteur(self, jsonInput):
        """
        configure le compte à rebours
        renvoit la notification à l'utilisateur 
        lance le compte a rebours dans un thread
        avertit l'utilisateur de la fin du minuteur
        """
        #print ("\n \n \n json d'entree = ", jsonInput,"\n \n \n ")   # pour debug
        
        #init
        sZone=""  #zone de retour pour la notification utilisateurs
        sObjet="" #le pourquoi du minuteur : ex : poulet
        Duree_s=0 #en seconde, renvoye par Wit
        sDuration=""
        
        #extraction des infos
        try :
            sDuration = jsonInput['outcome']['entities']['duration']
            #print sDuration
            if type(sDuration) is list  :
                for element in sDuration :
                    #print element
                    Duree_s += int(element['value'])
            elif type(sDuration) is dict :
                Duree_s =sDuration['value']
            else :
                return {"plugin": "Minuteur",  #Fatal
                    "method": "setRebours",
                    "body": ("Type de structure inconnues")
                    }
            #print Duree_s
        except :                           #Fatal
            return {"plugin": "Minuteur",
                    "method": "setRebours",
                    "body": ("Il manque la durée du minuteur")
                    }
        sZone = jsonInput['zone']
        try :
            sObjet = str(jsonInput['outcome']['entities']['message_subject']['value'])
            sObjet= ' '.join(sObjet.split()) #suppression espace en trop
            if "pour" not in sObjet :
                sObjet = "pour " + sObjet #des fois il manque le pour dans l'objet, Wit ne le renvoit pas
                #print sObjet
        except :                            #non bloquant
            sObjet = "timer-sans-objet"
        
        #lancement minuteur
        self.monMinuteur(Duree_s,sObjet,sZone)
        
        #construction du message de retour utilisateur
        sMessage = "je compte a rebours "
        #conversion secondes vers minutes, heures pour l'utilisateurs
        #print self.ConvertirDuree(Duree_s)
        if self.ConvertirDuree(Duree_s)[0] >= 1 :
            sHeures =self.ConvertirDuree(Duree_s)[0], " heures "
            sMessage=sMessage+ str(sHeures[0])+ str(sHeures[1])
            
        if self.ConvertirDuree(Duree_s)[1] >= 1 :
            sMinutes =self.ConvertirDuree(Duree_s)[1], " minutes "
            sMessage=sMessage+ str(sMinutes[0])+ str(sMinutes[1])

        if self.ConvertirDuree(Duree_s)[2] >= 1 :
            sSecondes =self.ConvertirDuree(Duree_s)[2], " secondes "
            sMessage=sMessage + str(sSecondes[0])+ str(sSecondes[1])

        sMessage=sMessage + str(sObjet)
        #print sMessage
        return {"plugin": "Minuteur",
                "method": "setRebours",
                "body": (sMessage)
        }

    def getMinuteur(self, jsonInput):
        """
        recupere la duree restante du  compte à rebours
        interroge le thread correspondant 
        retourne l'info
        """
        try :
            sObjet = str(jsonInput['outcome']['entities']['message_subject']['value'])
            if "pour" not in sObjet :
                sObjet = "pour " + sObjet #des fois il manque le pour dans l'objet, Wit ne le renvoit pas
            sObjet= ' '.join(sObjet.split()) #suppression espace en trop
        except :                            
            sObjet = "timer-sans-objet" #non bloquant

        #print "recherche du dico =", sObjet
        #for element in self.dicTimer :
        #   print "element dico :",element
        try :
            Duree_s = Minuteur.dicTimer[sObjet].get_left_time_s()
            Duree_s = int(Duree_s)  #suppression de toutes les decimales
            #print Duree_s
        except KeyError :
            print "Pas d'entree dans le dico"
            return {"plugin": "Minuteur",  #KO
                    "method": "setRebours",
                    "body": ("Je n'ai pas de minuteur avec ce nom.")
                    }

        #construction du message de retour utilisateur
        sMessage = "Il reste "
        #conversion secondes vers minutes, heures pour l'utilisateurs
        if self.ConvertirDuree(Duree_s)[0] >= 1 :
            sHeures =self.ConvertirDuree(Duree_s)[0], " heures "
            sMessage=sMessage+ str(sHeures[0])+ str(sHeures[1])
            
        if self.ConvertirDuree(Duree_s)[1] >= 1 :
            sMinutes =self.ConvertirDuree(Duree_s)[1], " minutes "
            sMessage=sMessage+ str(sMinutes[0])+ str(sMinutes[1])

        if self.ConvertirDuree(Duree_s)[2] >= 1 :
            sSecondes =self.ConvertirDuree(Duree_s)[2], " secondes "
            sMessage=sMessage + str(sSecondes[0])+ str(sSecondes[1])

        sMessage=sMessage + sObjet
        print sMessage
        return {"plugin": "Minuteur",
                "method": "setRebours",
                "body": (sMessage)
        }

    def monMinuteur(self,pDuree_s, psObject, psZone):
        #creer un timer avec callback
        def timer_cbk(pMessage):
            #print "Fin du minuteur {} dans {}".format(pMessage[0], pMessage[1])
            sMessage="Le compte a rebours ",pMessage[0], " est terminer"
            NotifyClient(sMessage,pMessage[1])
            #2eme couche de rappel
            sleep(5) #attente de la fin de la notification precendente
            sMessage="Je raipaite : le compte a rebours ",pMessage[0], " est terminer"  #raipaite car la synthese ne comprend pas répéte
            NotifyClient(sMessage,pMessage[1])
            #suppression du dico
            del Minuteur.dicTimer[psObject]

        monNouveauTimer = NeoTimer(pDuree_s, timer_cbk,(psObject,psZone))
        
        #ajout dans le dico
        print "entree du dico =", psObject
        Minuteur.dicTimer[psObject]=monNouveauTimer
        
        return()

    def ConvertirDuree(self,pDuree):
        """
        conversion d'un temps en seconde -> en heures, minutes, secondes
        """
        heures=0
        minutes=0
        
        heures = pDuree /3600
        pDuree %= 3600
        minutes = pDuree/60
        pDuree%=60
        return (heures,minutes,pDuree)


#############################################################
# Tests
if __name__ == "__main__" :
    essai=Minuteur()
    retourn = essai.setMinuteur(jsonInput2)
    print (retourn['body'])
    
    sleep(3)
    essai.getMinuteur(jsonInputGetMinuteur)
    
    #print essai.ConvertirDuree(75)
    #print essai.ConvertirDuree(75)[2]
