# Frisquet connect api plugin pour Domoticz
#!!!!! Attention : il s'agit d'une version alpha!!!!!!
# Author: Krakinou
#
#TODO : Derogation
#       Numéro chaudiere optionnelle
#       Mode et selecteur
#       CAMB
#       BOOST
#       Chaudière en veille
#       Auto/manu
#       Temperature Exterieure
#       Vacances
#       programmation / jour
#       alarmes
"""
<plugin key="Frisquet-connect" name="Frisquet-Connect" author="Krakinou" version="0.0.2" wikilink="https://wiki.domoticz.com/Plugins">
    <description>
        <h2>Frisquet-connect pour Domoticz</h2><br/>
        Version Alpha d'un plugin frisquet-Connect pour Domoticz permettant de controler sa chaudiere si un Frisquet-Connect est connecte. Les dispositifs suivants sont crees automatiquement par le plugin :
        <ul style="list-style-type:square">
            <li>Temperature de zone</li>
            <li>Consigne Hors-Gel de zone</li>
            <li>Consigne Reduit de zone</li>
            <li>Consigne Confort de zone</li>
            <li>Réglage du mode ECS (Eau Chaude Sanitaire)</li>
        </ul>
    </description>
    <params>
        <param field="Username" label="Username" required="true"/>
	<param field="Password" label="Password" password="true" required="true"/>
	<param field="Mode6" label="Debug" width="150px">
            <options>
                <option label="None" value="0"  default="true" />
                <option label="Python Only" value="2"/>
                <option label="Basic Debugging" value="62"/>
                <option label="Basic+Messages" value="126"/>
                <option label="Queue" value="128"/>
                <option label="Connections Only" value="16"/>
                <option label="Connections+Queue" value="144"/>
                <option label="All" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""

import Domoticz as Domoticz
import time
import json
import const
#import frisquetAPI


class FrisquetConnectPlugin:
    enabled = False
    def __init__(self):
        self.httpConn = None
        self.incomingPayload = None
        self.pendingPayload = None
        self.auth_token = None
        self.token_expiry = 0
        self.num_chaudiere = None
        self.ecs_in_to_out = {m["ecs_in"]: m["ecs_out"] for m in const.MODE_ECS}
        self.ecs_out_to_in = {m["ecs_out"]: m["ecs_in"] for m in const.MODE_ECS}
        self.ecs_in_to_nValue = {m["ecs_in"]: m["nValue"] for m in const.MODE_ECS}
        self.ecs_out_to_nValue = {m["ecs_out"]: m["nValue"] for m in const.MODE_ECS}
        return

    def onStart(self):
        Domoticz.Status("Starting Frisquet-connect")
        if Parameters["Mode6"] != "0":
            Domoticz.Debugging(int(Parameters["Mode6"]))
            DumpConfigToLog()
        self.connectToFrisquet()
        Domoticz.Debug("Fin du onstart")

    def connectToFrisquet(self):
        Domoticz.Debug("Starting Connect To Frisquet")
        payload = {
             "locale": "fr",
             "email": Parameters["Username"],
             "password": Parameters["Password"],
             "type_client": "IOS"
        }
        self.pendingPayload = json.dumps(payload)
        Domoticz.Debug("Payload to push : " + str(self.pendingPayload))

        Domoticz.Debug("Starting Connection to " + str(const.HOST))
        self.httpConn = Domoticz.Connection(
             Name="connectToFrisquetAPI",
             Transport="TCP/IP",
             Protocol="HTTPS",
             Address= const.HOST,
             Port="443"
        )
        self.httpConn.Connect()

    def getFrisquetData(self):
        Domoticz.Debug("Starting data retrieval")
        self.httpConn = Domoticz.Connection(
            Name="getFrisquetData",
            Transport="TCP/IP",
            Protocol="HTTPS",
            Address= const.HOST,
            Port="443"
        )
        self.httpConn.Connect()

    def pushUpdateToFrisquet(self, Unit, Level):
        Domoticz.Debug("Starting Push Data")
        if Devices[Unit].Type == 242:
            payloadLevel = Level * 10
            match str(Unit)[1]:
                case "2": #Confort
                    mode = "CONF"
                case "3": #Reduit
                    mode = "RED"
                case "4": #HG
                    mode = "HG"
            payload = [{"cle":"CONS_" + mode + "_Z" + str(Unit)[0], "valeur":payloadLevel}]

        if Devices[Unit].Type == 244:
            payload = [{"cle":"MODE_ECS", "valeur": str(self.ecs_in_to_out.get(Level))}]

        self.pendingPayload = json.dumps(payload)
        Domoticz.Debug("Payload to push : " + str(self.pendingPayload))

        self.httpConn = Domoticz.Connection(
            Name="pushUpdateToFrisquet",
            Transport="TCP/IP",
            Protocol="HTTPS",
            Address= const.HOST,
            Port="443"
        )
        self.httpConn.Connect()

    def is_token_valid(self):
        return self.auth_token is not None and time.time() < self.token_expiry

    def ensure_token(self):
        if not self.is_token_valid():
            Domoticz.Debug("Token invalide ou expire, recuperation d'un nouveau token")
            self.connectToFrisquet()

    def onStop(self):
        Domoticz.Debug("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug("onConnect started for  : " + str(Connection.Name))

        if (Status != 0):
            Domoticz.Log("Failed to connect ("+str(Status)+") to: "+Parameters["Address"]+":"+Parameters["Mode1"]+" with error: "+Description)
            return

        match Connection.Name:
            case "connectToFrisquetAPI":
                sendData = { 'Verb' : 'POST',
                             'URL' : const.AUTH_API,
                             'Headers' : { 'Content-Type': 'application/json', \
                                           'Connection': 'keep-alive', \
                                           'Accept': '*/*', \
                                           'Host': const.HOST
                                         },
                             'Data': self.pendingPayload
                            }
            case "getFrisquetData":
                sendData = { 'Verb' : 'GET',
                             'URL' : const.SITE_API + '/' + self.num_chaudiere + '?token=' + self.auth_token,
                             'Headers' : { 'Connection': 'keep-alive', \
                                           'Accept': '*/*', \
                                           'Host': const.HOST
                                         }
                           }
            case "pushUpdateToFrisquet":
                sendData = { 'Verb' : 'POST',
                             'URL'  : const.ORDRES_API + '/' + self.num_chaudiere + '?token=' + self.auth_token,
                             'Headers' : { 'Content-Type': 'application/json', \
                                           'Connection': 'keep-alive', \
                                           'Accept': '*/*', \
                                           'Host': const.HOST
                                         },
                             'Data' : self.pendingPayload
                           }
            case _:
                Domoticz.Error("Connection inconnue")
                return
        Domoticz.Debug("Methode : " + str(sendData["Verb"]) + ", URL : " + str(sendData["URL"]))
        Connection.Send(sendData)

    def onMessage(self, Connection, Data):
        Domoticz.Debug("onMessage called for " + str(Connection.Name))
        DumpHTTPResponseToLog(Data)
        self.pendingPayload = None
        self.incomingPayload = None

        if Data.get("Data"):
            self.incomingPayload=json.loads(Data["Data"].decode("utf-8", "ignore"))
        Status = int(Data["Status"])
        match Connection.Name:
            case "connectToFrisquetAPI":
                if (Status == 201):
                    self.auth_token = self.incomingPayload["token"]
                    Domoticz.Debug("token received : " + self.auth_token)
                    self.token_expiry = time.time() + 3600
                    self.num_chaudiere = self.incomingPayload["utilisateur"]["sites"][0]["identifiant_chaudiere"]
                    Domoticz.Debug("numero chaudiere : " + self.num_chaudiere)
                elif (Status == 403):
                    Domoticz.Error("Erreur de connexion : Nom ou mot de passe incorrect?")
                    self.auth_token = None
                    self.token_expiry = 0
                else:
                    self.auth_token = None
                    self.token_expiry = 0
                    Domoticz.Log("Connection impossible, erreur : " + str(Status))
            case "getFrisquetData":
                if (Status == 200):
                    self.createDeviceChaudiere()
                    self.updateDeviceFromFrisquetChaudiere()
                    for zone in self.incomingPayload["zones"]:
                        self.createDeviceByZone(zone)
                        self.updateDeviceFromFrisquetByZone(zone)
            case "pushUpdateToFrisquet":
                if (Status != 200):
                    if self.incomingPayload is not None and self.incomingPayload.get("message"):
                        message = str(self.incomingPayload["message"])
                        Domoticz.Log("Le serveur a renvoye une erreur  " + str(Status) + " - " + message)
                    else:
                        Domoticz.Log("Le serveur a renvoye une erreur  " + str(Status))

            case _:
                Domoticz.Error("Connection inconnue")
        self.httpConn.Disconnect()


    def updateDeviceFromFrisquetByZone(self, zone):
        num_zone = str(zone["numero"])
        devices_zone = [
            { "unit": int(num_zone + const.C_TAMB), "nValue":0, "sValue":str(zone["carac_zone"]["TAMB"] / 10.0) },
            { "unit": int(num_zone + const.C_CONS_RED), "nValue":0, "sValue":str(zone["carac_zone"]["CONS_RED"] / 10.0) },
            { "unit": int(num_zone + const.C_CONS_HG), "nValue":0, "sValue":str(zone["carac_zone"]["CONS_HG"] / 10.0) },
            { "unit": int(num_zone + const.C_CONS_CONF), "nValue":0, "sValue":str(zone["carac_zone"]["CONS_CONF"] / 10.0) }
            ]
        for device_zone in devices_zone:
            device=Devices[device_zone["unit"]]
            Domoticz.Debug("Mise à jour de " + str(device.Name) + " à la valeur " + str(device_zone["sValue"]))
            if device.sValue != str(device_zone["sValue"]):
                device.Update(nValue=0, sValue=str(device_zone["sValue"]))

    def updateDeviceFromFrisquetChaudiere(self):
        devices_chaudiere = [
            { "unit":1, "nValue":self.ecs_out_to_nValue.get(str(self.incomingPayload["ecs"]["MODE_ECS"]["id"])), "sValue":self.ecs_out_to_in.get(str(self.incomingPayload["ecs"]["MODE_ECS"]["id"])) }
            ]
        for device_chaudiere in devices_chaudiere:
            device=Devices[device_chaudiere["unit"]]
            Domoticz.Debug("Mise à jour de " + str(device.Name) + " à la valeur " + str(device_chaudiere["sValue"]))
            device.Update(nValue=int(device_chaudiere["nValue"]), sValue=str(device_chaudiere["sValue"]))

    def createDeviceByZone(self, zone):
#Zone 1 : 11 TAMB, 12 CONS_CONF, 13 CONS_RED, 14, CONS_HG
#Zone 2:  21 TAMB, 22 CONS_CONF, etc.
#          'MODE': 8,
#          'SELECTEUR': 8,
#	       'TAMB': 150, Température de la zone
#	       'CAMB': 150,
#	       'DERO': False, Dérogation
#	       'ACTIVITE_BOOST': False
        num_zone = str(zone["numero"])
        nom_zone = zone["nom"]
        devices_zone = [
            {"unit": int(num_zone + const.C_TAMB), "name": "Temperature " + nom_zone, "TypeName": "Temperature"},
            {"unit": int(num_zone + const.C_CONS_RED), "name": "Consigne Reduit " + nom_zone, "TypeName": "Setpoint"},
            {"unit": int(num_zone + const.C_CONS_CONF), "name": "Consigne Confort " + nom_zone, "TypeName": "Setpoint"},
            {"unit": int(num_zone + const.C_CONS_HG), "name": "Consigne Hors-Gel " + nom_zone, "TypeName": "Setpoint"}
            ]
        for device_zone in devices_zone:
            if not Devices or device_zone["unit"] not in Devices:
                Domoticz.Debug("Creation du device " + device_zone["name"])
                Domoticz.Device(Name=device_zone["name"], \
                                Unit=device_zone["unit"], \
                                TypeName=device_zone["TypeName"] \
                                ).Create()

    def createDeviceChaudiere(self):
#1 ECS
        Options_ecs = {"LevelActions": "|| ||",
                   "LevelNames": "Stop|Eco+ Timer|Eco+|Eco Timer|Eco|Max",
                   "LevelOffHidden": "false",
                   "SelectorStyle": "1"}
        devices_chaudiere = [
            {"unit":1, "name": "Mode Eau Chaude Sanitaire", "TypeName": "Selector Switch", "Options": Options_ecs, "Image":11}
        ]
        for device_chaudiere in devices_chaudiere:
            if not Devices or device_chaudiere["unit"] not in Devices:
                Domoticz.Debug("Creation du device " + device_chaudiere["name"])
                Domoticz.Device(Name=device_chaudiere["name"], \
                                Unit=device_chaudiere["unit"], \
                                TypeName=device_chaudiere["TypeName"], \
                                Options=device_chaudiere["Options"], \
                                Image=device_chaudiere["Image"]
                                ).Create()

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        device=Devices[Unit]
        if device.Type==242 or device.Type==244:
            self.pushUpdateToFrisquet(Unit, Level)
            match device.Type:
                case 242:
                    device.Update(nValue=0, sValue=str(Level))
                case 244:
                    device.Update(nValue=self.ecs_in_to_nValue.get(Level), sValue=str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Debug("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat called")
        self.ensure_token()
        if self.auth_token and self.num_chaudiere:
            self.getFrisquetData()


global _plugin
_plugin = FrisquetConnectPlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

# Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return

def DumpHTTPResponseToLog(httpResp, level=0):
    if (level==0): Domoticz.Debug("HTTP Details ("+str(len(httpResp))+"):")
    indentStr = ""
    for x in range(level):
        indentStr += "----"
    if isinstance(httpResp, dict):
        for x in httpResp:
            if not isinstance(httpResp[x], dict) and not isinstance(httpResp[x], list):
                Domoticz.Debug(indentStr + ">'" + x + "':'" + str(httpResp[x]) + "'")
            else:
                Domoticz.Debug(indentStr + ">'" + x + "':")
                DumpHTTPResponseToLog(httpResp[x], level+1)
    elif isinstance(httpResp, list):
        for x in httpResp:
            Domoticz.Debug(indentStr + "['" + x + "']")
    else:
        Domoticz.Debug(indentStr + ">'" + x + "':'" + str(httpResp[x]) + "'")
