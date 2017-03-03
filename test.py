# coding=utf-8
from gpsconvert import GPSConvert
from gpsclass import GPS

gpsobject = GPSConvert()
gpsbd = GPS(120.30766900025,  36.069121959576)
gpsgoogle = gpsobject.bd2gcj(gpsbd)
print(gpsgoogle.tostring())



