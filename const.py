"""Constantes pour intégration Frisquet-Connect """
#Parametres de connexion
HOST="fcutappli.frisquet.com"
AUTH_API="/api/v1/authentifications"
SITE_API="/api/v1/sites"
ORDRES_API="/api/v1/ordres"

#General Chaudiere
C_MODE_ECS="1"

MODE_ECS = [
    { "nom":"Stop",       "value_out":"5", "value_in":0,  "nValue":0},
    { "nom":"Eco+ Timer", "value_out":"4", "value_in":10, "nValue":1},
    { "nom":"Eco+",       "value_out":"3", "value_in":20, "nValue":1},
    { "nom":"Eco Timer",  "value_out":"2", "value_in":30, "nValue":1},
    { "nom":"Eco",        "value_out":"1", "value_in":40, "nValue":1},
    { "nom":"Max",        "value_out":"0", "value_in":50, "nValue":1}
]

OPTIONS_ECS = {"LevelActions": "|| ||",
               "LevelNames": "Stop|Eco+ Timer|Eco+|Eco Timer|Eco|Max",
               "LevelOffHidden": "false",
               "SelectorStyle": "1"}
C_CHAUDIERE = [
    { "nom":"Mode Eau Chaude Sanitaire", "unit":"1", "mode":"MODE_ECS", "TypeName":"Selector Switch", "Image":11, "Options":OPTIONS_ECS}
]


#Zones
SELECTEUR = [
    { "nom":"Auto",               "value_out":"5", "value_in":0,  "nValue":0},
    { "nom":"Confort Permanent",  "value_out":"6", "value_in":10, "nValue":1},
    { "nom":"Reduit Permanent",   "value_out":"7", "value_in":20, "nValue":1},
    { "nom":"Hors-Gel Permanent", "value_out":"8", "value_in":30, "nValue":1}
]

OPTIONS_MODE = {"LevelActions": "|| ||",
                "LevelNames": "Auto|Confort|Reduit|Hors-Gel",
                "LevelOffHidden": "false",
                "SelectorStyle": "1"}

C_ZONE = [
    { "nom":"Temperature",    "unit":"1", "mode":"TAMB",      "TypeName":"Temperature",     "Options":None},
    { "nom":"Confort",        "unit":"2", "mode":"CONS_CONF", "TypeName":"Setpoint",        "Options":None },
    { "nom":"Reduit",         "unit":"3", "mode":"CONS_RED",  "TypeName":"Setpoint",        "Options":None},
    { "nom":"Hors-Gel",       "unit":"4", "mode":"CONS_HG",   "TypeName":"Setpoint",        "Options":None},
    { "nom":"Mode Permanent", "unit":"5", "mode":"SELECTEUR", "TypeName":"Selector Switch", "Options":OPTIONS_MODE}
]
