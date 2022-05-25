# coding=utf-8
class Origin:

    __slot__ = (
      'lat', 'lon'
    )

    def __init__(self,
        lat:float, 
        lon:float):

        self.lat = lat
        self.lon = lon