#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  sensor.py.py
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

import configparser
import socket
import threading
import subprocess


class ClientThread(threading.Thread):
    def __init__(self, ip, port, clientsocket, hostname, rpi, sensor_id, sensor_name):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.clientsocket = clientsocket
        self.hostname = hostname
        self.rpi = rpi
        self.sensor_id = sensor_id
        self.sensor_name = sensor_name
        # print(f"[+] New thread for {self.ip}:{self.port}")

    def run(self):
        try:
            r = self.clientsocket.recv(2048)
            try:
                r = r.decode()
                # Send the hostname when requested
                if r == "hostname":
                    print(f"Hostname requested by {self.ip}:{self.port}")
                    self.clientsocket.send(self.hostname.encode())
                # Get the temperature and send it back when requested
                elif r == "temperature":
                    print(f"Temperature requested by {self.ip}:{self.port}")
                    self.clientsocket.send(get_temperature(self.rpi, self.sensor_name, self.sensor_id).encode())
            except UnicodeDecodeError:
                pass
        except ConnectionResetError:
            pass


def get_temperature(rpi, sensor_name, sensor_id):
    temperature = -1
    if rpi:
        # TODO : Test this on an actual RPi to see if everything is OK
        # Show the value from /sys/class/thermal/thermal_zone0/temp / 1000
        process = subprocess.Popen("cat /sys/class/thermal/thermal_zone0/temp", stdout=subprocess.PIPE, shell=True)
        output, error = process.communicate()
        temperature = int(int(output.decode().strip()) / 1000)
    else:
        # Get the value from lm_sensors
        process = subprocess.Popen(f'sensors -u "{sensor_name}"', stdout=subprocess.PIPE, shell=True)
        output, error = process.communicate()
        values = output.decode().split("\n")
        for item in values[values.index(f"{sensor_id}:"):]:
            if "_input" in item:
                temperature = int(float(item.split(":")[-1].strip()))
                break

    return str(temperature)


def sensor():
    # Read the configuration file
    config = configparser.ConfigParser()
    config.read("temperature-monitor.conf")

    hostname = config["sensor"]["hostname"]
    port = config["sensor"]["port"]
    sensor_name = config["sensor"]["sensor_name"]
    sensor_id = config["sensor"]["sensor_id"]
    rpi = True if config["sensor"]["is_rpi"] == "yes" else False

    # Start the server
    tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcpsock.bind(("", int(port)))

    print("Waiting for a connection...")
    while True:
        tcpsock.listen(10)
        (clientsocket, (ip, port)) = tcpsock.accept()
        newthread = ClientThread(ip, port, clientsocket, hostname, rpi, sensor_id, sensor_name)
        newthread.start()


if __name__ == '__main__':
    sensor()
