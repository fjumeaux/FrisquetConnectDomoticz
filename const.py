"""Constantes pour intégration Frisquet-Connect """
#Parametres de connexion
HOST="fcutappli.frisquet.com"
AUTH_API="/api/v1/authentifications"
SITE_API="/api/v1/sites"
ORDRES_API="/api/v1/ordres"

CONSOMMATION="consommation.json"

#General Chaudiere
MODE_ECS = [
    { "nom":"Stop",       "value_out":"5", "value_in":0,  "nValue":0},
    { "nom":"Eco+ Timer", "value_out":"4", "value_in":10, "nValue":1},
    { "nom":"Eco+",       "value_out":"3", "value_in":20, "nValue":1},
    { "nom":"Eco Timer",  "value_out":"2", "value_in":30, "nValue":1},
    { "nom":"Eco",        "value_out":"1", "value_in":40, "nValue":1},
    { "nom":"Max",        "value_out":"0", "value_in":50, "nValue":1}
]

MODE_DERO = [
    { "nom":"Stop",    "value_out":"5", "value_in":0,  "nValue":0},
    { "nom":"Confort", "value_out":"6", "value_in":10, "nValue":1},
    { "nom":"Réduit",  "value_out":"7", "value_in":20, "nValue":1},
]

OPTIONS_ECS = {"LevelActions": "|| ||",
               "LevelNames": "Stop|Eco+ Timer|Eco+|Eco Timer|Eco|Max",
               "LevelOffHidden": "false",
               "SelectorStyle": "1"}

OPTIONS_DERO = {"LevelActions": "|| ||",
               "LevelNames": "Pas de dérogation|Confort|Réduit",
               "LevelOffHidden": "false",
               "SelectorStyle": "1"}


C_BOILER = [
    { "nom":"Mode Eau Chaude Sanitaire", "unit":"1", "mode":"MODE_ECS",   "TypeName":"Selector Switch", "Image":11, "Options":OPTIONS_ECS},
    { "nom":"Mode Dérogation",           "unit":"2", "mode":"MODE_DERO",  "TypeName":"Selector Switch", "Image":0,  "Options":OPTIONS_DERO},
    { "nom":"Consommation Chauffage",    "unit":"3", "mode":"CHF",        "TypeName":None, "Type":243, "Subtype":33, "Image":0,  "Options":None},
    { "nom":"Consommation ECS",          "unit":"4", "mode":"SAN",        "TypeName":None, "Type":243, "Subtype":33, "Image":0,  "Options":None},
    { "nom":"Alarmes",                   "unit":"5", "mode":"alarmes",    "TypeName":"Alert",           "Image":0,  "Options":None},
    { "nom":"Alarmes Pro",               "unit":"6", "mode":"alarmes_pro","TypeName":"Alert",           "Image":0,  "Options":None}
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
MODE = [
    { "nom":"Confort",  "value_out":"6", "value_in":"Confort",  "nValue":0},
    { "nom":"Réduit",   "value_out":"7", "value_in":"Réduit",   "nValue":0 },
    { "nom":"Hors-Gel", "value_out":"8", "value_in":"Hors-Gel", "nValue":0}
]

C_ZONE = [
    { "nom":"Temperature",       "unit":"1", "mode":"TAMB",      "TypeName":"Temperature",     "Options":None},
    { "nom":"Confort",           "unit":"2", "mode":"CONS_CONF", "TypeName":"Setpoint",        "Options":None},
    { "nom":"Reduit",            "unit":"3", "mode":"CONS_RED",  "TypeName":"Setpoint",        "Options":None},
    { "nom":"Hors-Gel",          "unit":"4", "mode":"CONS_HG",   "TypeName":"Setpoint",        "Options":None},
    { "nom":"Mode Permanent",    "unit":"5", "mode":"SELECTEUR", "TypeName":"Selector Switch", "Options":OPTIONS_MODE},
    { "nom":"Mode Actuel",       "unit":"6", "mode":"MODE",      "TypeName":"Text",            "Options":None},
    { "nom":"Dérogation",        "unit":"7", "mode":"DERO",      "TypeName":"Text",            "Options":None},
    { "nom":"Consigne actuelle", "unit":"8", "mode":"CAMB",      "TypeName":"Temperature",     "Options":None}
]
