import clickpoints
import os
import matplotlib.image as mpimg
import matplotlib.pyplot as plt

def getandaddFlue(path, searchname):
    data = path + r"\\" + searchname + ".tif"
    img = mpimg.imread(data)
    return img
