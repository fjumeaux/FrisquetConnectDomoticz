#!/bin/bash

xgettext -o ./Frisquet-Connect.pot ../plugin.py
msgmerge --update --backup=none ./fr/LC_MESSAGES/Frisquet-Connect.po ./Frisquet-Connect.pot
msgmerge --update --backup=none ./en/LC_MESSAGES/Frisquet-Connect.po ./Frisquet-Connect.pot
