# -*- coding: UTF-8 -*-

# Imports
from httplib2 import Http
from urllib import urlencode

# Envoie un message vocal aux clients d'une zone
def NotifyClient(message, clients_zone = "all") :
    """
    Notify user in a zone with a TTS message
    pMessage = message text to send
    pClients_zone = Target zone : "cuisine", "chambre", "all"... 
    """
    
    # Send HTTP request to the local server
    h = Http()
    resp, content = h.request("http://localhost:8000/api/v1/lisa/speak/?" + urlencode({"message": message, "clients_zone": clients_zone}) + "&api_key=special-key", "POST")
