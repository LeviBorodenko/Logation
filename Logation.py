import random
import json
from geolite2 import geolite2
import itertools


class Log(object):
    """
    Class for analysing your nginx log.

    """

    def __init__(self, access_log_file="access.log",
                 clean_dir="./cleanData/", raw_dir="./rawData/", asset_dir="./map/assets/"):
        super(Log, self).__init__()

        # creating all file and directory names
        self.clean_dir = clean_dir
        self.raw_dir = raw_dir
        self.asset_dir = asset_dir
        self.data_file = raw_dir + access_log_file
        self.data = self.clean_dir + "data.json"
        self.responseJson = self.clean_dir + "response.json"
        self.locationsJS = self.asset_dir + "locations.js"

        # object that gathers miscellaneous information
        self.information = {"total": 0,
                            "OS": {
                                "Windows": 0,
                                "Android": 0,
                                "iOS": 0,
                                "Linux": 0,
                                "Other": 0}
                            }

    def getIP(self, line):
        """Get ip from nginx log line"""
        return line.split(" ")[0]

    def removeDublicates(self):
        """Scans the log file and removes doublicate ips"""
        with open(self.data_file, "r") as f:

            # storing all already added IPs
            addedIPs = []

            # creating file that just stores the ips
            self.ip_file = self.clean_dir + "ip.txt"

            # file that stores the log lines without doublicate ips
            self.unique_data_file = self.clean_dir + "noDublicatesLog.txt"
            with open(self.ip_file, "w") as dump:
                with open(self.unique_data_file, "w") as clean:

                    # check if we already saw the ip (within the last 1000 ips)
                    # and ignore it if we did.
                    # Otherwise, write it down.
                    for line in f:
                        IP = self.getIP(line)
                        if IP not in addedIPs[max(-len(addedIPs), -1000):]:
                            addedIPs.append(IP)
                            clean.write(line)
                        else:
                            pass

                dump.write("\n".join(addedIPs))
        print("Removed Dublicates.")

    def getLine(self):
        """For Debugging.
        Gets a random line from the log file."""
        index = random.randint(0, 20000)
        with open(self.data_file, "r") as data_file:
            for i, line in enumerate(data_file):
                if i == index:
                    return(line)

    def getContext(self, line):
        """Helper"""
        return(line.rsplit("\"")[5])

    def getOS(self, line):
        """Gets the OS from a log file entry"""
        context = self.getContext(line).rsplit("(")[1]
        rawOS = context.rsplit(";")[1].lower()

        if "win" in rawOS:
            return("Windows")
        elif "android" in rawOS:
            return("Android")
        elif "mac" in rawOS:
            if "ipad" or "iphone" in context:
                return("iOS")
            else:
                return("Mac")
        elif "linux" or "ubuntu" in rawOS:
            return("Linux")
        else:
            return("Other")

    def getData(self):
        """Removes all dublicates and and creates a file where
        each entry is an ip and its OS"""
        self.removeDublicates()

        with open(self.unique_data_file, "r") as data_file:
            with open(self.data, "w") as json_file:
                result = []
                for line in data_file:
                    try:
                        entry = {}
                        entry["ip"] = self.getIP(line)
                        entry["OS"] = self.getOS(line)
                        result.append(entry)

                        # updating the information Object
                        self.information["total"] += 1

                        if entry["OS"] == "Windows":
                            self.information["OS"]["Windows"] += 1
                        elif entry["OS"] == "iOS":
                            self.information["OS"]["iOS"] += 1
                        elif entry["OS"] == "Linux":
                            self.information["OS"]["Linux"] += 1
                        elif entry["OS"] == "Android":
                            self.information["OS"]["Android"] += 1
                        elif entry["OS"] == "Other":
                            self.information["OS"]["Other"] += 1

                    except Exception as e:
                        pass

                json.dump(result, json_file)
        print("Cleaned Data.")

    def addLocation(self):
        """
        Scans all ips for their geolocation
        """
        self.getData()
        with open(self.data, "r") as json_file:
            data = json.load(json_file)
            reader = geolite2.reader()
            result = []
            for item in data:
                ip_info = reader.get(item["ip"])
                if ip_info is not None:
                    try:
                        item["latitude"] = ip_info["location"]["latitude"]
                        item["longitude"] = ip_info["location"]["longitude"]
                        result.append(item)
                    except Exception as e:
                        pass

        with open(self.data, "w") as json_file:
            json.dump(result, json_file)

        print("Added locations")

    def analyseLog(self):
        self.addLocation()
        self.rasterizeData()
        print("Rasterised Data")
        self.createJs()
        print("Done!")

    def rasterizeData(self, resLat=200, resLong=250):
        """
        Splits the map into equal resLat*resLong chunks and
        counts how many visits came from each chunk.

        Returns
            {
                "information": Object with stats about what
                    OS your users use and how many unique visitors came,

                "raster": list with entries:
                    [[center of square], # of visitors to that square]
            }

        """

        latStep, longStep = 180 / resLat, 360 / resLong
        # Build the rasterised coord. system
        gridX, gridY = [], []
        x = -180
        y = -90

        for i in range(resLong):
            gridX.append(x)
            x += longStep
        gridX.reverse()

        for i in range(resLat):
            gridY.append(y + i * latStep)
        gridY.reverse()

        gridItems = itertools.product(gridX, gridY)
        grid = {i: 0 for i in gridItems}

        # Now assign each data point to its grid square
        with open(self.data, "r") as json_file:
            data = json.load(json_file)

            for point in data:
                lat, lon = point["latitude"], point["longitude"]
                for x in gridX:
                    if lon >= x:
                        coordX = x
                        break
                for y in gridY:
                    if lat >= y:
                        coordY = y
                        break
                grid[(coordX, coordY)] += 1

            # remove squres with 0 entries
            for key in list(grid.keys()):
                if grid[key] == 0:
                    del grid[key]

            # center squares
            raster = []

            # creating raster and information object
            for key in grid:
                x = round(key[0] + longStep / 2, 5)
                y = round(key[1] + latStep / 2, 5)
                raster.append([[x, y], grid[key]])

            # noting the size of the grid squares
            self.information["dx"] = round(longStep / 2, 5)
            self.information["dy"] = round(latStep / 2, 5)

            # generating responseJson
            with open(self.responseJson, "w") as json_dump:
                json.dump({"information": self.information,
                           "raster": raster}, json_dump)

    def createJs(self):
        with open(self.responseJson, "r") as response:
            dataString = "const LOCATIONS = " + str(json.load(response))
            with open(self.locationsJS, "w") as f:
                f.write(dataString)


test = Log()
test.analyseLog()
