"""Constantes pour intégration Frisquet-Connect """
#Parametres de connexion
HOST="fcutappli.frisquet.com"
AUTH_API="/api/v1/authentifications"
SITE_API="/api/v1/sites"
ORDRES_API="/api/v1/ordres"

#General Chaudiere
C_MODE_ECS="1"
MODE_ECS = [
    { "nom" : "Stop",       "ecs_out": "5", "ecs_in":0,  "nValue":0},
    { "nom" : "Eco+ Timer", "ecs_out": "4", "ecs_in":10, "nValue":1},
    { "nom" : "Eco+",       "ecs_out": "3", "ecs_in":20, "nValue":1},
    { "nom" : "Eco Timer",  "ecs_out": "2", "ecs_in":30, "nValue":1},
    { "nom" : "Eco",        "ecs_out": "1", "ecs_in":40, "nValue":1},
    { "nom" : "Max",        "ecs_out": "0", "ecs_in":50, "nValue":1}
]

#Zones
C_TAMB="1"
C_CONS = [
    { "nom": "Confort",   "unit":"2", "mode":"CONS_CONF_Z"},
    { "nom": "Reduit",    "unit":"3", "mode":"CONS_RED_Z" },
    { "nom": "Hors-Gel",  "unit":"4", "mode":"CONS_HG_Z"  },
    { "nom": "Selecteur", "unit":"5", "mode":"SELECTEUR_Z"}
]
MODE_PERM = [
    { "nom":"Auto",               "perm_out":"5", "perm_in":0,  "nValue":0},
    { "nom":"Confort Permanent",  "perm_out":"6", "perm_in":10, "nValue":1},
    { "nom":"Reduit Permanent",   "perm_out":"7", "perm_in":20, "nValue":1},
    { "nom":"Hors-Gel Permanent", "perm_out":"8", "perm_in":30, "nValue":1},

]
