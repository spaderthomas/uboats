import requests
from bs4 import BeautifulSoup
import pprint
import dateutil.parser as dparser
import datefinder
import re

printer = pprint.PrettyPrinter(indent=4)

sank_str = r'S[a|u]nk'
sank_re = re.compile(sank_str)
destroyed_str = r'Destroyed'
destroyed_re = re.compile(destroyed_str)
is_number_str = r'^[0-9]+$'
is_number_re = re.compile(is_number_str)

def string_or_na(string):
    return "N/A" if string == "" else string



# Parse UBoat information
base_url = "https://uboat.net/boats/u1.htm"

text = None
with open("u1.txt", "r") as f:
    text = f.read()
    
soup = BeautifulSoup(text, 'html.parser')

uboats = {}
uboat = "u1"
uboats[uboat] = {}
# TODO:
# Put the dates into a standard format
for row in soup.find_all('tr'):
    row_contents = [entry.contents for entry in row.find_all('td')]
    #print(row_contents)
    #print("\n")
    if row_contents[0] == ['Ordered']:
        # e.g. [['Ordered'], ['2 Feb 1935'], [<br/>]]
        uboats[uboat]["ordered"] = row_contents[1][0]
    elif row_contents[0] == ['Launched']:
        # e.g. [['Launched'], ['15 Jun 1935'], [<br/>]]
        uboats[uboat]["launched"] = row_contents[1][0]
    elif row_contents[0] == ['Commissioned']:
        # e.g. [['Commissioned'], ['29 Jun 1935'], ['Kptlt. Klaus Ewerth']]
        uboats[uboat]["commissioned"] = row_contents[1][0]
    if row_contents[0] == ['Fate']:
        fate_text = row_contents[1][1].get_text()
        uboats[uboat]["fate_text"] = fate_text
        
        # Find the first date -- this is probably when it's fate was
        # Put it into a standard format D/M/Y
        dates = list(datefinder.find_dates(fate_text))
        date = dates[0]

        date = "{}/{}/{}".format(date.day, date.month, date.year)
        uboats[uboat]["fate_date"] = date

        # Status is just the first word
        status = fate_text.split(' ')[0]
        if sank_re.match(status):
            uboats[uboat]["fate"] = "SANK"
        elif destroyed_re.match(status):
            uboats[uboat]["fate"] = "DESTROYED"
    if row_contents[0] == 'Ordered':
        pass


# Parse patrol information
# Parse UBoat information
text = None
with open("u1_patrols.txt", "r") as f:
    text = f.read()
    
soup = BeautifulSoup(text, 'html.parser')

# TODO:
# Put the dates into a standard format
# Remove extra spaces from the captain's name
patrols = []
for row in soup.find_all('tr'):
        row_contents = [entry.contents for entry in row.find_all('td')]
        #printer.pprint(row_contents)
        if is_number_re.match(row.contents[0].get_text()):
            patrols.append({})
            patrol = patrols[-1]
            patrol["patrol_number"] = string_or_na(row.contents[0].get_text())
            patrol["commander"] = string_or_na(row.contents[1].get_text())
            patrol["departure_date"] = string_or_na(row.contents[2].get_text()) # \xa0?
            patrol["departure_port"] = string_or_na(row.contents[3].get_text())
            patrol["arrival_date"] = string_or_na(row.contents[4].get_text()) # \xa0?
            patrol["arrival_port"] = string_or_na(row.contents[5].get_text())
            patrol["patrol_length"] = string_or_na(row.contents[6].get_text()[:-5])
            patrol["tonnage"] = string_or_na(row.contents[7].get_text())
            patrol["patrol_kind"] = string_or_na(row.contents[8].get_text()[-1]) #\x10P?

uboats[uboat]["patrols"] = patrols

printer.pprint(uboats)
