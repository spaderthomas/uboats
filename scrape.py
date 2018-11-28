import requests
from bs4 import BeautifulSoup
import pprint
import dateutil.parser as dparser
import datefinder
import arrow
import re
import json
import csv

printer = pprint.PrettyPrinter(indent=4)

sheet = csv.writer(open("uboats.csv", "w", newline=''))
sheet.writerow(["Boat ID", "Commander", "Patrol Number", "Patrol Length", "Patrol Kind", "Departure Date", "Departure Port", "Arrival Date", "Arrival Port", "Tonnage", "Date Ordered", "Date Launched", "Date Commissioned", "Fate", "Fate Text", "Date of Fate"])

# Utilities
sank_str = r'S[a|u]nk'
sank_re = re.compile(sank_str)
destroyed_str = r'Destroyed'
destroyed_re = re.compile(destroyed_str)
decom_str = r'Decommissioned'
decom_re = re.compile(decom_str)
is_number_str = r'^[0-9]+$'
is_number_re = re.compile(is_number_str)

def string_or_na(string):
    return "NA" if string == "" else string


uboats = {}
num_uboats = 1407
canary = "U-{}"
base_url = "https://uboat.net/boats/u{}.htm"
patrol_url = "https://uboat.net/boats/patrols/u{}.html"
for uboat in range(1, num_uboats + 1):
    url = base_url.format(str(uboat))
    r = requests.get(url)
    if canary.format(str(uboat)) not in r.text:
        print("Invalid URL: U-{}".format(str(uboat)))
        continue
              
    print("Parsing U-{}".format(str(uboat)))
    soup = BeautifulSoup(r.text, 'html.parser')
    uboats[uboat] = {}

    # Parse out the base U-Boat data
    for row in soup.find_all('tr'):
        row_contents = [entry.contents for entry in row.find_all('td')]
        if not len(row_contents):
            continue

        if row_contents[0] == ['Ordered']:
            # e.g. [['Ordered'], ['2 Feb 1935'], [<br/>]]
            if len(row_contents) >= 2 and len(row_contents[1]):
                date = arrow.get(row_contents[1][0], ["DD MMM YYYY", "D MMM YYYY"])
                uboats[uboat]["ordered"] = date.format("DD/MM/YYYY")
            else:
                uboats[uboat]["ordered"] = "NA"
        elif row_contents[0] == ['Launched']:
            # e.g. [['Launched'], ['15 Jun 1935'], [<br/>]]
            if len(row_contents) >= 2 and len(row_contents[1]):
                date = arrow.get(row_contents[1][0], ["DD MMM YYYY", "D MMM YYYY"])
                uboats[uboat]["launched"] = date.format("DD/MM/YYYY")
            else:
                uboats[uboat]["launched"] = "NA"
        elif row_contents[0] == ['Commissioned']:
            # e.g. [['Commissioned'], ['29 Jun 1935'], ['Kptlt. Klaus Ewerth']]
            if len(row_contents) >= 2 and len(row_contents[1]):
                date = arrow.get(row_contents[1][0], ["DD MMM YYYY", "D MMM YYYY"])
                uboats[uboat]["commissioned"] = date.format("DD/MM/YYYY")
            else:
                uboats[uboat]["commissioned"] = "NA"
        if row_contents[0] == ['Fate']:
            if len(row_contents) >= 2 and len(row_contents[1]) >= 2:
                fate_text = row_contents[1][1].get_text()   
                uboats[uboat]["fate_text"] = fate_text
            
                # Find the first date -- this is probably when it's fate was
                # Put it into a standard format D/M/Y
                dates = list(datefinder.find_dates(fate_text))
                for date in dates:
                    date = "{}/{}/{}".format(date.day, date.month, date.year)
                    try:
                        date = arrow.get(date, ["D/M/YYYY", "DD/M/YYYY", "D/MM/YYYY", "DD/MM/YYYY"])
                        uboats[uboat]["fate_date"] = date.format("DD/MM/YYYY")
                        break
                    except:
                        continue
                    
                    uboats[uboat]["fate_date"] = "NA"

                # Status is just the first word
                status = fate_text.split(' ')[0]
                if sank_re.match(status):
                    uboats[uboat]["fate"] = "SANK"
                elif destroyed_re.match(status):
                    uboats[uboat]["fate"] = "DESTROYED"
                elif decom_re.match(status):
                    uboats[uboat]["fate"] = "DECOM"
                else:
                    uboats[uboat]["fate"] = "NA"
            else:
                uboats[uboat]["fate_text"] = "NA"
                uboats[uboat]["fate_date"] = "NA"
                uboats[uboat]["fate"] = "NA"
        if row_contents[0] == 'Ordered':
            pass


    # Parse patrol information
    url = patrol_url.format(str(uboat))
    r = requests.get(url)
    patrol_canary = "Find U-boats on patrols on this date"
    if patrol_canary in r.text:
        print("No patrols found: U-{}".format(str(uboat)))
        patrol["patrol_number"] = "NA"
        patrol["commander"] = "NA"
        patrol["departure_date"] = "NA"
        patrol["departure_port"] = "NA"
        patrol["arrival_date"] = "NA"
        patrol["arrival_port"] = "NA"
        patrol["patrol_length"] = "NA"
        patrol["tonnage"] = "NA"
        patrol["patrol_kind"] = "NA"
        uboats[uboat]["patrols"] = patrols
        continue
              
    print("Parsing U-{} patrols".format(str(uboat)))
    soup = BeautifulSoup(r.text, 'html.parser')

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
                departure_date_maybe = string_or_na(row.contents[2].get_text()).replace('\xa0', '')
                if departure_date_maybe is not "NA":
                    departure_date_maybe = arrow.get(departure_date_maybe, ["DD MMM YYYY", "D MMM YYYY"]).format("DD/MM/YYYY")
                patrol["departure_date"] = departure_date_maybe
                patrol["departure_port"] = string_or_na(row.contents[3].get_text())
                arrival_date_maybe = string_or_na(row.contents[4].get_text()).replace('\xa0', '')
                if arrival_date_maybe is not "NA":
                    arrival_date_maybe = arrow.get(arrival_date_maybe, ["DD MMM YYYY", "D MMM YYYY"]).format("DD/MM/YYYY")
                patrol["arrival_date"] = arrival_date_maybe
                patrol["arrival_port"] = string_or_na(row.contents[5].get_text())
                patrol["patrol_length"] = string_or_na(row.contents[6].get_text()[:-5])
                patrol["tonnage"] = string_or_na(row.contents[7].get_text())
                patrol["patrol_kind"] = string_or_na(row.contents[8].get_text()[-1]).replace('\x10P', '')

    uboats[uboat]["patrols"] = patrols
    for patrol in patrols:
        sheet.writerow([str(uboat), patrol["commander"], patrol["patrol_number"], patrol["patrol_length"], patrol["patrol_kind"], patrol["departure_date"],
        patrol["departure_port"], patrol["arrival_date"], patrol["arrival_port"], patrol["tonnage"], uboats[uboat]["ordered"], uboats[uboat]["launched"], uboats[uboat]["commissioned"], uboats[uboat]["fate"], uboats[uboat]["fate_text"], uboats[uboat]["fate_date"]])

with open("uboats.json", "w") as outfile:
    json.dump(uboats, outfile)  