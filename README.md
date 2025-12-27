# FrisquetConnectDomoticz
Domoticz Plugin For Frisquet Connect Boiler control

# Prerequisites
- You must first have a working Frisquet Connect Site with a boiler identified and installed.
- Only one boiler must be referenced on the site. In case of multiple boilers, it may work but it has never been tested
- You will need your username and password to access the frisquetConnect site
- Domoticz 2023.2 or higher


# Features
- Control one or multiple boilers
- Control Heating mode (Confort, reduced and Frost Protection) for one or multiple zone(s)
- Control setpoints for each of the heating mode for each of the zone
- Force one or multiple zone on a mode irrespectively of the program (derogation and permanent mode)
- Access the temperature from one or multiple zone(s)
- Hot Water Control
- Check Boiler energy consumption (in KWh)

# Work in Progress
- Add image for heating mode
- Boost control
- On/Off control
- Automatic/Manual trigger
- External temperature sensor
- Holidays
- Program
- Alarms
- Plugin update message

# Installation

Paths and commands may vary depending on your Domoticz installation.
- Go to your Domoticz plugin folder (for example : `/var/www/domoticz/plugins/`)
- `git clone https://github.com/Krakinou/FrisquetConnectDomoticz`
- Restart your Domoticz instance `sudo service domoticz restart`

Also check that the folder `FrisquetConnectDomoticz` and files are owned by the Domoticz user running the instance.

# Updating
- Go to your Domoticz plugin folder (for example : `/var/www/domoticz/plugins/`)
- `git pull`
- Restart your Domoticz instance `sudo service domoticz restart`

# Configuration
- Add a new Hardware and select "Frisquet-Connect"
- Just enter your user and password
- In case you have multiple boilers, create one instance of plugin per boiler and enter your boiler id in the dedicated parameters (you can retrieve them in the Frisquet app). Otherwise, just let the field empty
- Devices should be created in the next minute

Following devices are created, Zone dependent devices are created multiple times:
Device Name | Type | Zone Dependent | Fonction |
|------------|------|----|---------------------------------------|
|Temperature Zone X |Temperature| Yes | Temperature sensor from the Frisquet Visio Module for Zone X. If mutiple zones are available mutiple devices will be created |
|Consigne actuelle Zone X | Temperature | Yes | Actual setpoint used by the boiler. Please note that it may take until 15 minutes to update after a setpoint or mode change|
|Consigne Hors-Gel Zone X | Setpoint |Yes | Frost Protection Thermostat setpoint for Zone X |
|Consigne Reduit Zone X | Setpoint | Yes |Reduce Thermostat setpoint Zone X |
|Consigne Confort Zone X | Setpoint | Yes |Confort Thermostat setpoint Zone X |
|Mode Permanent Zone X | Selector Switch| Yes | Force the zone to a given mode |
|Mode Dérogation | Selector Switch | No | Will force Confort or Reduce mode for all zone until the next cycle |
|Mode Actuel Zone X | Text | Yes | Indicate the current heating mode |
|Mode Eau Chaude Sanitaire | Selector Switch | No | Hot Water control |
|Consommation Chauffage | Managed Counter | Non | How many KWh consummed for heating |
|Consommation ECS | Managed Counter | Non | How many KWh consummed for hot water |

Please note that the boiler only provides energy consumption on a monthly agregate, and that the figures are updated only once a day, at midnight, for the previous day.
Daily energy consumption is calculated by the plugin by substracting the total consumption of the previous day to the current consumption.

# Contribute
Submit your PR on the dev branch.

# Version history
 - 0.1.0 Initial version
 - 0.2.0 Adding Permanent mode and current heating status. Code refactoring
 - 0.2.1 Adding Derogation mode
 - 0.3.0 Adding multiple boilers control, energy consumption and fr/en translation
