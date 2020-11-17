import numpy as np
import cv2
import matplotlib.pyplot as plt

def transferImg_To_8Bit(img):
    if img.max() < 2 ** 8:
        img = img.astype(np.uint8)
    elif img.max() < 2 ** 10:
        img = (img // 4).astype(np.uint8)
    elif img.max() < 2 ** 12:
        img = (img // 16).astype(np.uint8)
    elif img.max() < 2 ** 14:
        img = (img // 64).astype(np.uint8)
    elif img.max() < 2 ** 16:
        img = (img // 256).astype(np.uint8)
    return img

def treshhold(img, int_type_index, tresh=0):
    if int_type_index == 0:
        mask = img > tresh
        thresh = mask
    else:
        type = [cv2.THRESH_OTSU,cv2.THRESH_BINARY, cv2.THRESH_TRUNC]
        ret, thresh = cv2.threshold(img, tresh, 255, type[int_type_index-1])[-2:]
    return thresh

def getContours(img):
    _, contours, h = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    return contours

def ignoreContours(contours):
    conts = []
    for i,cnt in enumerate(contours):
        if len(cnt) > 7:
            conts.append(cnt)
    return conts

def showContours(img,contours):
    for cnt in contours:
        cv2.drawContours(img,cnt , -1, (0, 255, 0), -1)

def invertImg(img):
    return cv2.bitwise_not(img)

def detect_pos_of_contours(contours):
    ContourMeanList_x = np.array([])
    ContourMeanList_y = np.array([])
    for cnt in contours:
        #Hier werden von den Contouren die Mittelpunkte bestimmt
        mean_x = np.mean(np.array(cnt)[:,0,0])
        mean_y = np.mean(np.array(cnt)[:, 0, 1])
        ContourMeanList_x = np.append(ContourMeanList_x, mean_x)
        ContourMeanList_y = np.append(ContourMeanList_y, mean_y)
    return ContourMeanList_x, ContourMeanList_y

def detector(img, layer, int_type_index):
    pre_img = transferImg_To_8Bit(np.asarray(img))
    cont_img = pre_img.copy()
    thresh = treshhold(pre_img, int_type_index)
    invert_thresh = thresh
    if layer == "MinProj":
        invert_thresh = invertImg(thresh)
    else:
        None
    contours = getContours(invert_thresh)
    contours = ignoreContours(contours)
    showContours(thresh,contours)
    x,y = detect_pos_of_contours(contours)
    showContours(cont_img, contours)
    return pre_img,cont_img, contours, x, y


