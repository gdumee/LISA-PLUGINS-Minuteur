# -*- coding: UTF-8 -*-

# Imports
from httplib2 import Http   #il faut installer la lib dans l'environnement virtuel de lisa
from urllib import urlencode

# Envoie un message vocal aux clients d'une zone
def NotifyClient(message, clients_zone = "all") :
    """
    Envoie une notification à l'utilisateur suivant sa zone
    pMessage = message texte a envoyer
    pClients_zone = zone d'envoi : cuisine, chambre, all... 
    """
    
    # send HTTP request
    h = Http()
    resp, content = h.request("http://localhost:8000/api/v1/lisa/speak/?" + urlencode({"message" : message, "clients_zone" : clients_zone}) + "&api_key=special-key", "POST")
