# Logation [NGINX]
_Analyse your NGINX access logs and create beautiful maps of the locations from which people access your service._

![result](https://i.imgur.com/PQKeerX.png)
____
[![Build Status](https://travis-ci.org/joemccann/dillinger.svg?branch=master)](https://travis-ci.org/joemccann/dillinger)

## How to use

First of all, make sure you have python3.x and *geolite2* installed. The later can be installed via pip with `pip install python-geoip-geolite2`.

Then simply clone this repository, put a *copy* of your NGINX access.log in the 
`./rawData/` folder and run Logation.py.

The map can then be found at `./map/map.html`.

The `./cleanData/` folder contains the .json and .txt files with the geolocations of all unique ips and some other statistics (like what OS has been used etc.).   

On an ordinary laptop 100mb of access.log size takes about 30s to analyse.
