from django.http import HttpResponseRedirect
from django.shortcuts import render
import csv
import requests
import numpy
import math
from datetime import datetime


def google_geocode(current_address):
    current_address = current_address.replace(" ", "+")

    geocode_url = "https://maps.googleapis.com/maps/api/geocode/json?address={}".format(current_address)
    geocode_url += "&key=API_KEY"

    results = requests.get(geocode_url)
    results = results.json()

    if results['status'] != "OK":
        return -1

    answer = results['results'][0]
    location = {
        "latitude": answer.get('geometry').get('location').get('lat'),
        "longitude": answer.get('geometry').get('location').get('lng'),
    }
    return location


def convert(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600


    if hour == 0:
        stamp = 'AM'
        hour = 12
    elif hour == 12:
        stamp = 'PM'
    elif hour > 12:
        stamp = 'PM'
        hour = hour - 12
    else:
        stamp = 'AM'
    return "%d:00%s" % (hour, stamp)


crimeInfo = []  # ALL CRIME INFO STORED HERE
month_names = ["January", "February", "March", "April", "May", "June", "July",
               "August", "September", "October", "November", "December"]

def mainView(request):
    crimeInfo.clear()
    with open(
            "/Users/kevry/Dev/CrimeProject/src/CrimeApp/main/NYPD_Complaint_Data_Current_YTD.csv") as csv_file:  # OPENING CSV FILE
        csv_reader = csv.reader(csv_file)

        for row in csv_reader:
            crimeInfo.append(row)

    return render(request, 'CrimeMain.html')


def result(request):

    lat = None
    lon = None
    out = None
    useful_info = []  # INFORMATION USEFUL FOR GIVEN LOCATION
    crimes_committed = []  # ALL CRIMES COMMITTED
    all_times_in_secs = []  # USED TO FIND MEAN TIME
    time_count = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    current_month = int(datetime.today().month)
    final_time_range = []

    address = request.GET["curr_add"]

    if address == '':  # NO INPUT GIVEN. USER ENTERS NOTHING
        return HttpResponseRedirect('/')

    lat_lon = google_geocode(address)  # GETTING THE LATITUDE AND LONGITUDE OF LOCATION

    if lat_lon == -1:  # CONDITION FOR INVALID ADDRESS
        return render(request, 'failedRes.html')
    else:
        lat = lat_lon["latitude"]
        lon = lat_lon["longitude"]

        incident_flag = False

        for row in crimeInfo[1:]:

            date_of_incident = row[0]

            if len(date_of_incident) == 0:  # CHECKING FOR EMPTY CELL
                continue
            if len(row[1]) == 0:  # CHECKS IF TIME SLOT IS EMPTY
                continue
            if len(row[18]) == 0 or len(row[19]) == 0:  # CHECKING IF LATITUDE OR LONGITUDE IS EMPTY
                continue

            split_date = date_of_incident.split('/')  # SPLITTING DATE
            if len(split_date) != 3:
                continue

            month_of_incident = int(split_date[0])  # MONTH OF INCIDENT

            month_max = current_month + 1
            month_min = current_month - 1

            if (current_month + 1) == 13:
                month_max = 1
            if (current_month - 1) == 0:
                month_min = 12

            # CHECK IF LAT AND LONG IS WITHIN BOUNDS
            if (float(row[18]) < (lat + 0.005)) and (float(row[18]) > (lat - 0.005)) and (
                    float(row[19]) < (lon + 0.005)) and (float(row[19]) > (lon - 0.005)):

                time_of_incident = row[1]
                (h, m, s) = time_of_incident.split(':')  # USING TOTAL SECONDS TO FIND MEAN

                if len(time_of_incident.split(':')) != 3:
                    continue

                incident_flag = True
                time_count[int(h)] += 1
                crimes_committed.append(row[6])

                latlng_info = [float(row[18]), float(row[19])]
                useful_info.append(latlng_info)

                #total_in_sec = int(h) * 3600 + int(m) * 60 + int(s)
                #all_times_in_secs.append(total_in_sec)
                #useful_info.append(row)

        if not incident_flag:  # IF NO LAT/LONG FOUND WITHIN RANGE
            return render(request, 'emptyRes.html', {'longitude': lon, 'latitude': lat})
        else:

            save_time = []
            i = 0
            for x in time_count:
                if x > 100:
                    save_time.append(i)
                i += 1

            if len(save_time) == 0:
                return render(request, 'emptyRes.html', {'longitude': lon, 'latitude': lat})

            print(save_time)
            continue_var = 0
            place_holder = 0
            for y in range(len(save_time)):
                if y ==len(save_time)-1:
                    time_str = "{} - {}".format(convert(save_time[place_holder] * 3600), convert((save_time[place_holder + continue_var] + 1) * 3600))
                    final_time_range.append(time_str)
                elif save_time[y]+1 == save_time[y+1]:
                    continue_var += 1
                else:
                    time_str = "{} - {}".format(convert(save_time[place_holder]*3600), convert((save_time[place_holder + continue_var] + 1)*3600))
                    final_time_range.append(time_str)
                    place_holder = y+1
                    continue_var = 0

            crimes_committed = set(crimes_committed)

    return render(request, 'results.html',
                  {'crimes_commit': crimes_committed, 'final_times': final_time_range, 'longitude': lon, 'latitude': lat,
                'address': address, 'useful_info': useful_info})
