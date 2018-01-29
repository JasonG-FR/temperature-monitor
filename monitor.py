#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  monitor.py
#  
#  Copyright 2018 Jason Gombert <jason.gombert@protonmail.com>
# 
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#

import socket
import nmap
import configparser
import time


class Sensor(object):
    # TODO : See if it's possible to stay connected rather than create a new connection every 3 seconds
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.hostname = ""
        self.temperature = 0

    def get_hostname(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.ip, self.port))
            s.send("hostname".encode())
            r = s.recv(2048)
            self.hostname = r.decode()

    def get_temperature(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.ip, self.port))
            s.send("temperature".encode())
            r = s.recv(2048)
            self.temperature = int(r.decode())

    def __str__(self):
        return f"{self.hostname} ({self.ip}) : {self.temperature} °C"


def get_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(('8.8.8.8', 1))  # connect() for UDP doesn't send packets
        local_ip_address = s.getsockname()[0]

    return local_ip_address


def get_sensors(ip, port):
    print("Looking for sensors in the local network...")
    sensors = []
    nm = nmap.PortScanner()
    nm.scan(hosts=f'{ip}/24', arguments=f'-p {port}')
    hosts = nm.all_hosts()
    for ip in hosts:
        if nm[ip]['tcp'][port]['state'] == "open":
            sensors.append(ip)
    print(f"{len(sensors)} sensors found.")

    return sensors


def monitor():
    # Get the IP address
    ip = get_ip()

    # Read the configuration file
    config = configparser.ConfigParser()
    config.read("temperature-monitor.conf")

    port = config["monitor"]["port"]

    # Scan the network to find every sensors online
    ip_sensors = get_sensors(ip, int(port))

    # For each sensor, get their name and store it associated with the IP address
    sensors = []
    for ip in ip_sensors:
        sensor = Sensor(ip, int(port))
        sensor.get_hostname()
        sensors.append(sensor)

    # Loop on each sensors to get the measures every 3 seconds
    while True:
        for sensor in sensors:
            sensor.get_temperature()

        # TODO : Take care of network related problems (disconnected sensor, disconnected computer)

        # TODO : Display the results on the console
        [print(sensor) for sensor in sensors]

        # TODO : Store the results in a database

        time.sleep(3)


if __name__ == '__main__':
    monitor()
