# coding=utf-8
import math
from gpsclass import GPS
from mjw import MJW


class GPSConvert:
    def __init__(self):
        self.x_pi = math.pi * 3000.0 / 180.0
        self.a = 6378245.0
        self.ee = 0.00669342162296594323
        self.MAXDIS = 0.5
        self.MAXERRDIS = 4

    def wgs2bd(self, wgs):
        gcj = self.wgs2gcj(wgs)
        bd = self.gcj2bd(gcj)
        return bd

    def gcj2bd(self, gcj):
        x = gcj.lng
        y = gcj.lat
        z = math.sqrt(x * x + y * y) + 0.00002 * math.sin(y * self.x_pi)
        theta = math.atan2(y, x) + 0.000003 * math.cos(x * self.x_pi)
        bd_lon = z * math.cos(theta) + 0.0065
        bd_lat = z * math.sin(theta) + 0.006
        bd = GPS(bd_lon, bd_lat)
        return bd

    def bd2gcj(self, bd):
        wgs = self.bd2wgs(bd)
        gcj = self.wgs2gcj(wgs)
        return gcj

    def wgs2gcj(self, wgs):
        wlng = wgs.lng
        wlat = wgs.lat
        dlat = self.transformlat(wlng - 105.0, wlat - 35.0)
        dlon = self.transformlng(wlng - 105.0, wlat - 35.0)
        radlat = wlat / 180.0 * math.pi
        magic = math.sin(radlat)
        magic = 1-self.ee*magic*magic
        sqrtmagic = math.sqrt(magic)
        dlat = (dlat * 180.0) / ((self.a * (1 - self.ee)) / (magic * sqrtmagic) * math.pi)
        dlon = (dlon * 180.0) / (self.a / sqrtmagic * math.cos(radlat) * math.pi)
        gcj = GPS(wlng+dlon, wlat + dlat)
        return gcj

    def outofchina(self, gps):
        if gps.lng < 72.004 or gps.lng > 137.8347:
            return True
        if gps.lat < 0.8293 or gps.lat > 55.8271:
            return True
        return False

    def transformlat(self, x, y):
        """
        transfer lat for what i don't know
        so as to transfer lng
        """
        ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
        ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
        ret += (20.0 * math.sin(y * math.pi) + 40.0 * math.sin(y / 3.0 * math.pi)) * 2.0 / 3.0
        ret += (160.0 * math.sin(y / 12.0 * math.pi) + 320.0 * math.sin(y * math.pi / 30.0)) * 2.0 / 3.0
        return ret

    def transformlng(self, x, y):
        ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
        ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
        ret += (20.0 * math.sin(x * math.pi) + 40.0 * math.sin(x / 3.0 * math.pi)) * 2.0 / 3.0
        ret += (150.0 * math.sin(x / 12.0 * math.pi) + 300.0 * math.sin(x / 30.0 * math.pi)) * 2.0 / 3.0
        return ret

    # degree to radian
    def deg2rad(self, degree):
        return degree / 180 * math.pi

    # radian to degree
    def rad2deg(self, radian):
        return radian * 180 / math.pi

    def distance(self, gps1, gps2):
        """
        * compute the distance between two gps
        * result basic unit: KM
         """
        jingdu1, weidu1 = gps1.lng, gps1.lat
        jingdu2, weidu2 = gps2.lng, gps2.lat
        theta = jingdu1-jingdu2
        dist = math.sin(self.deg2rad(weidu1)) * math.sin(self.deg2rad(weidu2)) + math.cos(self.deg2rad(weidu1)) * math.cos(self.deg2rad(weidu2)) * math.cos(self.deg2rad(theta))
        dist = math.acos(dist)
        dist = self.rad2deg(dist)
        return dist * 60 * 1.1515 * 1.609344 * 1000

    def bd2wgs(self, baidu):
        mjw = MJW()
        dis = self.adpate(baidu, 0.0, mjw)
        dis = self.adpate(baidu, 0.1, mjw)
        dis = self.adpate(baidu, 0.01, mjw)
        dis = self.adpate(baidu, 0.001, mjw)
        minmw = mjw.mw
        minmj = mjw.mj
        mindis = dis
        for i in range(0, 30):
            if dis > self.MAXDIS:
                dis = self.adpate(baidu, 0.0001, mjw)
                if dis > self.MAXDIS:
                    dis = self.adpate(baidu, 0.00001, mjw)
                if dis > self.MAXDIS:
                    dis = self.adpate(baidu, 0.000001, mjw)
                if mindis > dis:
                    mindis = dis
                    minmw = mjw.mw
                    minmj = mjw.mj
            else:
                break
        mjw.mw = minmw
        mjw.mj = minmj
        dis = mindis
        wgs = GPS(baidu.lng+mjw.mj, baidu.lat+mjw.mw)
        return wgs

    def distancefromwgstobaidu(self, wgs, baidu):
        return self.distance(self.wgs2bd(wgs), baidu)

    def adpate(self, baidu, p, mjw):
        dis = self.distancefromwgstobaidu(GPS(baidu.lng+mjw.mj, baidu.lat+mjw.mw), baidu)
        dis1 = self.distancefromwgstobaidu(GPS(baidu.lng+mjw.mj+p, baidu.lat+mjw.mw), baidu)
        if dis1 < dis:
            mjw.mj = mjw.mj + p
            while True:
                tmpdis = dis1
                dis1 = self.distancefromwgstobaidu(GPS(baidu.lng+mjw.mj+p, baidu.lat+mjw.mw), baidu)
                if dis1 < tmpdis:
                    mjw.mj = mjw.mj + p
                else:
                    break
        else:
            dis1 = self.distancefromwgstobaidu(GPS(baidu.lng+mjw.mj-p, baidu.lat+mjw.mw), baidu)
            if dis1 < dis:
                mjw.mj = mjw.mj - p
                while True:
                    tmpdis = dis1
                    dis1 = self.distancefromwgstobaidu(GPS(baidu.lng+mjw.mj-p, baidu.lat+mjw.mw), baidu)
                    if dis1 < tmpdis:
                        mjw.mj = mjw.mj - p
                    else:
                        break
        dis = self.distancefromwgstobaidu(GPS(baidu.lng+mjw.mj, baidu.lat+mjw.mw), baidu)
        dis2 = self.distancefromwgstobaidu(GPS(baidu.lng+mjw.mj, baidu.lat+mjw.mw+p), baidu)
        if dis2 < dis:
            mjw.mw = mjw.mw + p
            while True:
                tmpdis = dis2
                dis2 = self.distancefromwgstobaidu(GPS(baidu.lng+mjw.mj, baidu.lat+mjw.mw+p), baidu)
                if dis2 < tmpdis:
                    mjw.mw = mjw.mw + p
                else:
                    break
        else:
            dis2 = self.distancefromwgstobaidu(GPS(baidu.lng+mjw.mj, baidu.lat+mjw.mw-p), baidu)
            if dis2 < dis:
                mjw.mw = mjw.mw - p
                while True:
                    tmpdis = dis2
                    dis2 = self.distancefromwgstobaidu(GPS(baidu.lng+mjw.mj, baidu.lat+mjw.mw-p), baidu)
                    if dis2 < tmpdis:
                        mjw.mw = mjw.mw - p
                    else:
                        break
        dis = self.distancefromwgstobaidu(GPS(baidu.lng+mjw.mj, baidu.lat+mjw.mw), baidu)
        return dis










