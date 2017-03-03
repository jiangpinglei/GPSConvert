# coding=utf-8


class GPS:
    def __init__(self, lng=0.0, lat=0.0):
        self.lng = lng
        self.lat = lat

    def tostring(self):
        return str(self.lng)+','+str(self.lat)