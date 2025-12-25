# Frisquet connect api plugin pour Domoticz
# Author: Krakinou
#
#TODO : BOOST
#       Chaudière en veille
#       Auto/manu
#       Temperature Exterieure
#       Vacances
#       programmation / jour
#       alarmes

"""
<plugin key="Frisquet-connect" name="Frisquet-Connect" author="Krakinou" version="0.2.1" wikilink="https://github.com/Krakinou/FrisquetConnectDomoticz">
    <description>
        <h2>Frisquet-connect pour Domoticz</h2><br/>
        Connecteur Frisquet-Connect pour Domoticz permettant de controler sa chaudiere à distance. Un boitier Frisquet-Connect et un compte actif sont requis pour ce plugin.
    </description>
    <params>
        <param field="Username" label="Username" required="true"/>
	<param field="Password" label="Password" password="true" required="true"/>
        <param field="Mode1" label="Numéro de chaudière">
            <description>
               <br/>Ne remplissez ce champs que si votre site possede plusieurs chaudiere. Dans ce cas vous devrez créer plusieurs instances du plugin, une par chaudiere. Si vous n'avez qu'une seule chaudiere, laisser ce champs vide.
            </description>
        </param>
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

import os
import Domoticz as Domoticz
import time
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import json
import random
import string
import const
import gettext

_ = gettext.gettext

class FrisquetConnectPlugin:
    enabled = False
    def __init__(self):
        self.active = True
        self.httpConn = None
        self.incomingPayload = None
        self.pendingPayload = None
        self.auth_token = None
        self.token_expiry = 0
        self.boilerID = None
        self.beatCounter = 0
        self.onceADay = None
        self.initializeEnergy = []
        return

    def is_token_valid(self):
        return self.auth_token is not None and time.time() < self.token_expiry

    def ensure_token(self):
        if not self.is_token_valid():
            Domoticz.Debug(_("Invalid or expired token, new token retrieval"))
            self.connectToFrisquet()

    def formatBoiler(self, s: str) -> bool:
        return isinstance(s, str) and len(s) == 14 and s.isdigit()

    def genererAppidRandom(self, longueur=22):
        caracteres = string.ascii_letters + string.digits
        return ''.join(random.choice(caracteres) for _ in range(longueur))

    def deviceUpdatedMoreThan(self, device, seconds):
        if device and device.Unit in Devices:
            last = datetime.strptime(device.LastUpdate, "%Y-%m-%d %H:%M:%S")
            return (datetime.now() - last).total_seconds() > seconds
        return 0

    def connectToFrisquet(self):
        if not self.active:
            return

        Domoticz.Debug(_("Starting Connect To Frisquet"))
        payload = {
             "locale": "fr",
             "email": Parameters["Username"],
             "password": Parameters["Password"],
             "type_client": "IOS"
        }
        self.pendingPayload = json.dumps(payload)
        Domoticz.Debug(_("Payload to push : " + str(self.pendingPayload)))

        Domoticz.Debug(_("Starting Connection to " + str(const.HOST)))
        self.httpConn = Domoticz.Connection(
             Name="connectToFrisquetAPI",
             Transport="TCP/IP",
             Protocol="HTTPS",
             Address= const.HOST,
             Port="443"
        )
        self.httpConn.Connect()

    def getFrisquetData(self):
        Domoticz.Debug(_("Starting data retrieval"))

        self.httpConnData = Domoticz.Connection(
            Name="getFrisquetData",
            Transport="TCP/IP",
            Protocol="HTTPS",
            Address= const.HOST,
            Port="443"
        )
        self.httpConnData.Connect()

    def getFrisquetEnergy(self):
        if self.onceADay == date.today():
            return
        self.onceADay = date.today()

        Domoticz.Debug(_("Starting energy consumption retrieval"))

        self.httpConnEnergy = Domoticz.Connection(
            Name="getFrisquetEnergy",
            Transport="TCP/IP",
            Protocol="HTTPS",
            Address= const.HOST,
            Port="443"
        )
        self.httpConnEnergy.Connect()

    def getValue(self, Unit, out, Level):
        device=Devices[Unit]
        if device.Unit > 9: #zone
           mode  = next((m["mode"] for m in const.C_ZONE if m["unit"] == str(Unit)[1]), None)
           value = next((m[out] for m in getattr(const, mode, None) if m["value_in"] == Level), None)
        else:
           mode  = next((m["mode"] for m in const.C_BOILER if m["unit"] == str(Unit)), None)
           value = next((m[out] for m in getattr(const, mode, None) if m["value_in"] == Level), None)
        return int(value)

    def pushUpdateToFrisquet(self, Unit, Level):
        Domoticz.Debug(_("Starting Push Data"))

        device = Devices[Unit]
        if device.Type == 242: #setpoint is always by zone
            #str(Unit)[0] is the zone number
            cle= next((m["mode"] for m in const.C_ZONE if m["unit"] == str(Unit)[1]), None) + '_Z' + str(Unit)[0]
            payloadValeur = Level * 10
        if device.Type == 244: #switch selector
            if Devices[Unit].Unit > 9: # zone value
                cle           = next((m["mode"] for m in const.C_ZONE if m["unit"] == str(Unit)[1]), None) + '_Z' + str(Unit)[0]
            else:                 #General value for the boiler
                cle           = next((m["mode"] for m in const.C_BOILER if m["unit"] == str(Unit)), None)
            payloadValeur = self.getValue(device.Unit, "value_out", Level)
        payload = [{"cle":cle,  "valeur": payloadValeur}]
        self.pendingPayload = json.dumps(payload)

        Domoticz.Debug(_("Payload to push : " + str(self.pendingPayload)))
        self.httpConn = Domoticz.Connection(
            Name="pushUpdateToFrisquet",
            Transport="TCP/IP",
            Protocol="HTTPS",
            Address= const.HOST,
            Port="443"
        )
        self.httpConn.Connect()

    def updateModeDero(self, zone, value_out):
        #Dero is a true/false flag inside the zone, but the trigger is made on the whole boiler. So there are at least 2 devices (at least) : one for the zone 
        # which is read-only and the boiler-level one which is modifiable
        device_dero=Devices[int(next((m["unit"] for m in const.C_BOILER if m["mode"] == "MODE_DERO"), None))]
        if not device_dero.Unit in Devices:
            return
        if value_out == False:
            if device_dero.nValue > 0:
                Domoticz.Debug(_("Updating %s with value 0") %  str(device_dero.Name))
                device.Update(nValue=0, sValue="0")
            return
        sValue_dero=str(next( (m["value_in"] for m in const.MODE_DERO if m["value_out"] == str(zone["carac_zone"]["MODE"])), None))
        Domoticz.Debug(_("Switch Selector value is %s, value to update is %d") %  (str(zone["carac_zone"]["MODE"]),  sValue_dero))
        if device_dero.sValue != sValue_dero:
            device_dero.Update(nValue=1, sValue=sValue_dero)
        return

    def getenergyFromJSON(self, data, type_energy, month, year):
        for item in data.get(type_energy, []):
            if item["mois"] == month and item["annee"] == year:
                return item["valeur"]
        return None

    def writeEnergy(self, type_energy, date, energy, energy_total):
        folder_plugin = Parameters["HomeFolder"]
        file_energy = os.path.join(folder_plugin, const.CONSOMMATION)
        if os.path.exists(file_energy):
            with open(file_energy, "r") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []
        else:
            data = []

        exist = False
        modified = False
        for entry in data:
            if (
                entry.get("boiler_id") == self.boilerID and
                entry.get("type") == type_energy and
                entry.get("date") == date
            ):
                if entry["energy"] != energy:
                    entry["energy"] = energy
                    Domoticz.Debug(_("Updating current energy consumption : %s") % str(entry))
                    modified = True
                if entry["monthly_energy_to_date"] != energy_total:
                    entry["monthly_energy_to_date"] = energy_total
                    Domoticz.Debug(_("Updating total energy consumption : %s") % str(entry))
                    modified = True
                exist = True
                break

        if not exist:
            record = {
                "boiler_id": self.boilerID,
                "type": type_energy,
                "date": date,
                "energy": energy,
                "monthly_energy_to_date": energy_total
            }
            Domoticz.Debug(_("Energy consumption storage : ") + str(record))
            modified = True
            data.append(record)
        if modified:
            with open(file_energy, "w") as f:
                json.dump(data, f, indent=4)

    def getEnergyFromFile(self):
        folder_plugin = Parameters["HomeFolder"]
        file_energy = os.path.join(folder_plugin, const.CONSOMMATION)
        if os.path.exists(file_energy):
            with open(file_energy, "r") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return []
        return []

    def getEnergyFiltered(self, boiler_id, type_energy):
        data = self.getEnergyFromFile()
        return [
            entry for entry in data
            if entry["boiler_id"] == boiler_id and entry["type"] == type_energy
        ]

    def getLastEnergyOfMonth(self, boiler_id, type_energy, month, year):
        data = self.getEnergyFiltered(boiler_id, type_energy)
        filtered = []
        for entry in data:
            try:
                entry_date = datetime.strptime(entry.get("date"), "%Y-%m-%d")
            except 	(ValueError, TypeError):
                continue
            if entry_date.year == year and entry_date.month == month:
                filtered.append((entry_date, entry))
        if not filtered: return None

        filtered.sort(key=lambda x: x[0], reverse=True)
        Domoticz.Debug(_("Value to return : ") + str(filtered[0][1]))
        return filtered[0][1]

    def updateEnergyFromFrisquet(self, incomingPayload):
        for device_init in self.initializeEnergy:
            Domoticz.Debug(_("Initializing historical data for ") + str(device_init))
            self.InitEnergyFromFrisquet(device_init, incomingPayload)
        for device_boiler in const.C_BOILER:
            device=Devices[int(device_boiler["unit"])]
            type_energy=device_boiler["mode"]
            if not type_energy in incomingPayload: continue
            date_yesterday=date.today() - timedelta(days=1)
            energy_total = self.getenergyFromJSON(incomingPayload, type_energy, date_yesterday.month, str(date_yesterday.year))
            if energy_total:
                energy_total = energy_total * 1000  #frisquet provides KWh, domoticz await for Wh
            else:
                energy_total= 0
            Domoticz.Debug(_("for %(name)s , total energy consumption is %(te)d KWh at %(date)s") % { "name":str(device.Name), "te":energy_total, "date":str(date_yesterday.strftime("%Y-%m-%d"))})
            energy_total_pre=0
            try:
                energy_total_pre=self.getLastEnergyOfMonth(self.boilerID, type_energy, date_yesterday.month, date_yesterday.year).get("monthly_energy_to_date", 0)
            except Exception:
                pass
            energy_yesterday = energy_total - energy_total_pre
            Domoticz.Debug(_("For %(name)s , total energy consumption of %(te)d KWh was stored, difference of %(diff)d KWh") % { "name":str(device.Name), "te":energy_yesterday, "diff":energy_yesterday})
            self.writeEnergy(type_energy, str(date_yesterday),energy_yesterday, energy_total)
            device.Update(nValue=0, sValue="-1;" + str(energy_yesterday) + ";" + str(date_yesterday))

    def InitEnergyFromFrisquet(self, device_init, incomingPayload):
        device = Devices[int(device_init[0])]
        type_energy=device_init[1]
        date_trt = (datetime.now() - relativedelta(months=24))                               #la chaudiere fourni uniquement 2 ans d'historiques
        date_trt = date(date_trt.year, date_trt.month, 1) + relativedelta(months=1, days=-1) #We have only one value per month, so we set it on the last day
        first_day_of_month = datetime.now().replace(day=1).date()
        Domoticz.Debug(_("Initializing energy data for %(name)s between %(d1)s and %(d2)s") % { "name":str(device.Name), "d1": str(date_trt.strftime("%Y-%m-%d")), "d2": str(first_day_of_month.strftime("%Y-%m-%d"))})
        if not type_energy in incomingPayload: return
        while date_trt < first_day_of_month:
            Domoticz.Debug(_("Processing ") + str(date_trt.strftime("%Y-%m-%d")))
            energy_total = self.getenergyFromJSON(incomingPayload, type_energy, date_trt.month, str(date_trt.year))
            if energy_total:
                energy_total = energy_total * 1000  #frisquet fourni des KWh, domoticz attend des Wh
                Domoticz.Debug(_("For %(name)s , total energy consumption is %(te)d KWh at %(date)s") %  { "name":str(device.Name), "te":str(energy_total), "date":str(date_trt.strftime("%Y-%m-%d"))})
                device.Update(nValue=0, sValue="-1;" + str(energy_total) + ";" + str(date_trt))
            else:
                Domoticz.Debug(_("Nothing to update for %(name)s at %(date)s") % { "name":str(device.Name), "date":str(date_trt.strftime("%Y-%m-%d"))})
            date_trt += relativedelta(months=1, day=31)
        del self.initializeEnergy[0]

    def updateDeviceFromFrisquetByZone(self, zone):
        num_zone = str(zone["numero"])
        for device_zone in const.C_ZONE:
            device=Devices[int(num_zone + device_zone["unit"])]
            value_out=zone["carac_zone"][device_zone["mode"]]
            Domoticz.Debug(_("Updating %(name)s , incoming value : %(value)s") % { "name":str(device.Name), "value":str(value_out)})
            if getattr(const, device_zone["mode"], None) == None:
                if isinstance(value_out, bool):
                    sValue=str(value_out)
                else:
                    sValue= value_out / 10.0
                    nValue= 0
            else:
                sValue= next( (m["value_in"] for m in getattr(const, device_zone["mode"], None) if m["value_out"] == str(value_out)), None)
                nValue= next( (m["nValue"]   for m in getattr(const, device_zone["mode"], None) if m["value_out"] == str(value_out)), None)
            if device_zone["mode"]=="DERO":
                self.updateModeDero(zone, value_out)
            if str(device.sValue) != str(sValue) or self.deviceUpdatedMoreThan(device, 300):
                Domoticz.Debug(_("Updating %(name)s to value %(value)s") % { "name":str(device.Name), "value":str(sValue)})
                if device.Unit in Devices:
                    device.Update(nValue=int(nValue), sValue=str(sValue))

    def updateDeviceFromFrisquetboiler(self):
        for device_boiler in const.C_BOILER:
            device=Devices[int(device_boiler["unit"])]
            if device_boiler["mode"] and getattr(const, device_boiler["mode"], None) == "MODE_ECS": #pour l'instant seulement ECS, donc on garde en dur
                ecs_out=str(self.incomingPayload["ecs"]["MODE_ECS"]["id"])
                Domoticz.Debug(_("Updating %(name)s , incoming value : %(value)s") % { "name":str(device.Name), "value":str(ecs_out)})
                ecs_in= next((m["value_in"] for m in getattr(const, device_boiler["mode"], None) if m["value_out"] == ecs_out), None)
                sValue=str(ecs_in)
                nValue= next((m["nValue"]   for m in getattr(const, device_boiler["mode"], None) if m["value_out"] == ecs_out), None)
                if device.sValue != sValue or self.deviceUpdatedMoreThan(device, 300):
                    Domoticz.Debug(_("Updating %(name)s , incoming value : %(value)s") % { "name":str(device.Name), "value":sValue})
                    if device.Unit in Devices:
                        device.Update(nValue=int(nValue), sValue=sValue)
#            else:
#               TO DO

    def createDeviceByZone(self, zone):
        #Zone 1 : 11 TAMB, 12 CONS_CONF, 13 CONS_RED, 14, CONS_HG, 15 MODE PERMANENT, 16 MODE ACTUEL
        #Zone 2:  21 TAMB, 22 CONS_CONF, etc.
        num_zone = str(zone["numero"])
        nom_zone = zone["nom"]
        for device_zone in const.C_ZONE:
            device_unit=int(num_zone + device_zone["unit"])
            if not Devices or device_unit not in Devices:
                Domoticz.Debug(_("Creating device %(name)s with unit %(unit)s and TypeName %(typename)s") % { "name":(device_zone["nom"] + " " + nom_zone), "unit":str(device_unit), "typename":device_zone["TypeName"]})
                Domoticz.Device(Name     = device_zone["nom"] + " " + nom_zone, \
                                Unit     = device_unit, \
                                TypeName = device_zone["TypeName"], \
                                Options  = device_zone["Options"]
                                ).Create()

    def createDeviceboiler(self):
        for device_boiler in const.C_BOILER:
            if not Devices or int(device_boiler["unit"]) not in Devices:
                if device_boiler["TypeName"]:
                    Domoticz.Debug(_("Creating device %(name)s with unit %(unit)s and TypeName %(typename)s") % { "name": device_boiler["nom"], "unit": device_boiler["unit"], "typename":device_boiler["TypeName"]})
                    Domoticz.Device(Name=device_boiler["nom"], \
                                    Unit=int(device_boiler["unit"]), \
                                    TypeName=device_boiler["TypeName"], \
                                    Options=device_boiler["Options"], \
                                    Image=device_boiler["Image"]
                                    ).Create()
                else:
                    Domoticz.Debug(_("Creating device %(name)s with unit %(unit)s, Type %(type)s and Subtype %(subtype)s") % { "name":device_boiler["nom"], "unit":device_boiler["unit"], "type": device_boiler["Type"], "subtype":device_boiler["Subtype"]})
                    Domoticz.Device(Name=device_boiler["nom"], \
                                    Unit=int(device_boiler["unit"]), \
                                    Type=device_boiler["Type"], \
                                    Subtype=device_boiler["Subtype"], \
                                    Options=device_boiler["Options"], \
                                    Image=device_boiler["Image"]
                                    ).Create()
                self.initializeEnergy.append((device_boiler["unit"], device_boiler["mode"]))

    def onStart(self):
        lang = str(Settings["Language"])
        translation = gettext.translation(
            domain="Frisquet-Connect",
            localedir=os.path.join(os.path.dirname(__file__), "locale"),
            languages=[lang],
        )
        translation.install()
        _ = translation.gettext

        Domoticz.Status(_("Starting Frisquet-connect"))

        if Parameters["Mode6"] != "0":
            Domoticz.Debugging(int(Parameters["Mode6"]))
            DumpConfigToLog()
        if Parameters["Mode1"] and not self.formatBoiler(Parameters["Mode1"]):
            Domoticz.Error(_("Boiler ID %s is not valid. Check your entry") % str(Parameters["Mode1"]))
            self.active = False
        if Parameters["Mode1"]:
            self.boilerID = Parameters["Mode1"]
        self.connectToFrisquet()

    def onStop(self):
        Domoticz.Debug(_("onStop called"))

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug(_("onConnect started for  : ") + str(Connection.Name))

        if (Status != 0):
            Domoticz.Log(_("Failed to connect (%(status)s) to %(address)s with error %(error)s") % { "status":str(Status), "address":Parameters["Address"], "error":Description})
            return

        match Connection.Name:
            case "connectToFrisquetAPI":
                appid = self.genererAppidRandom()
                sendData = { 'Verb' : 'POST',
                             'URL' : const.AUTH_API + '?app_id=' + appid,
                             'Headers' : { 'Content-Type': 'application/json', \
                                           'Connection': 'keep-alive', \
                                           'Accept': '*/*', \
                                           'Host': const.HOST
                                         },
                             'Data': self.pendingPayload
                            }
            case "getFrisquetData":
                sendData = { 'Verb' : 'GET',
                             'URL' : const.SITE_API + '/' + self.boilerID + '?token=' + self.auth_token,
                             'Headers' : { 'Connection': 'keep-alive', \
                                           'Accept': '*/*', \
                                           'Host': const.HOST
                                         }
                           }
            case "getFrisquetEnergy":
                sendData = { 'Verb' : 'GET',
                             'URL' : const.SITE_API + '/' + self.boilerID + '/conso?token=' + self.auth_token \
                                     + "&types[]=CHF&types[]=SAN",
                             'Headers' : { 'Connection': 'keep-alive', \
                                           'Accept': '*/*', \
                                           'Host': const.HOST
                                         }
                           }
            case "pushUpdateToFrisquet":
                sendData = { 'Verb' : 'POST',
                             'URL'  : const.ORDRES_API + '/' + self.boilerID + '?token=' + self.auth_token,
                             'Headers' : { 'Content-Type': 'application/json', \
                                           'Connection': 'keep-alive', \
                                           'Accept': '*/*', \
                                           'Host': const.HOST
                                         },
                             'Data' : self.pendingPayload
                           }
            case _:
                Domoticz.Error(_("Unknown connection"))
                return
        Domoticz.Debug(_("Method : %(method)s , URL : %(url)s") % {"method" : str(sendData["Verb"]), "url":str(sendData["URL"])})
        Connection.Send(sendData)

    def onMessage(self, Connection, Data):
        Domoticz.Debug(_("onMessage called for ") + str(Connection.Name))
        DumpHTTPResponseToLog(Data)
        self.pendingPayload = None
        try:
            self.incomingPayload=json.loads(Data["Data"].decode("utf-8", "ignore"))
        except (TypeError, json.JSONDecodeError):
            self.incomingPayload = None

        if Data.get("Data"):
            Status = int(Data["Status"])

        if (Status == 403):
            Domoticz.Error(_("Login Error : Username or password incorrect?"))
            self.auth_token = None
            self.token_expiry = 0
            return
        elif not 200 <= Status < 300:
            if self.incomingPayload is not None and self.incomingPayload.get("message"):
                message = str(self.incomingPayload["message"])
                Domoticz.Log(_("Server send an error %(status)d - %(message)s for %(name)s") % { "status":Status,  "message":message, "name":Connection.Name})
            else:
                Domoticz.Log(_("Server send an error %d for %s") % (Status, Connection.Name))
            return
        match Connection.Name:
            case "connectToFrisquetAPI":
                self.auth_token = self.incomingPayload["token"]
                Domoticz.Debug(_("token received : ") + self.auth_token)
                self.token_expiry = time.time() + 86400
                if not self.boilerID:
                    self.boilerID = self.incomingPayload["utilisateur"]["sites"][0]["identifiant_chaudiere"]
                Domoticz.Debug(_("Boiler ID : ") + self.boilerID)
                self.httpConn.Disconnect()
            case "getFrisquetData":
                self.createDeviceboiler()
                self.updateDeviceFromFrisquetboiler()
                for zone in self.incomingPayload["zones"]:
                    self.createDeviceByZone(zone)
                    self.updateDeviceFromFrisquetByZone(zone)
                self.httpConnData.Disconnect()
                self.getFrisquetEnergy()
            case "getFrisquetEnergy":
                self.updateEnergyFromFrisquet(self.incomingPayload)
                self.httpConnEnergy.Disconnect()
            case "pushUpdateToFrisquet":
                Domoticz.Debug(_("Data has been sent and received"))
                self.httpConn.Disconnect()
            case _:
                Domoticz.Error(_("Unknown connection"))

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug(_("onCommand called for Unit %(unit)d : Parameter '%(param)s', Level:  %(level)d") % { "unit":Unit, "param":str(Command), "level":Level})
        device=Devices[Unit]
        if device.Type==242 or device.Type==244: #à conserver?
            self.pushUpdateToFrisquet(Unit, Level)
            match device.Type:
                case 242: #setpoint
                    nValue=0
                case 244: #switch selector
                    nValue  = self.getValue(Unit, "nValue", Level)
            Domoticz.Debug(_("Updating %(name)s with nValue %(nvalue)d and sValue %(svalue)s") % { "name":device.Name, "nvalue":nValue,  "svalue":str(Level)})
            device.Update(nValue=nValue, sValue=str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        pass

    def onHeartbeat(self):
        if not self.active: #pb avec le numéro de chaudiere
            return
        self.beatCounter += 1
        if self.beatCounter % 3 != 1:
            return
        if self.is_token_valid() and self.boilerID:
            self.getFrisquetData()
        #on renouvelle le token à la fin du heartbeat pour éviter les problèmes entre la réponse du renouvellement et la nouvelle demande de données
        self.ensure_token()


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
