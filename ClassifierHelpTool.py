#!/usr/bin/env python
# -*- coding: utf-8 -*-
#ClassifierHelpTool.py

#Copyright (c) 2020-2025, Ernst Wittmann
# Copyright (c) 2015-2020, Richard Gerum, Sebastian Richter, Alexander Winterl
#
# This file is part of ClickPoints.
#
# ClickPoints is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ClickPoints is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ClickPoints. If not, see <http://www.gnu.org/licenses/>

from __future__ import division, print_function
from .Detector import detector, transferImg_To_8Bit
from .GetFlue import getandaddFlue
import clickpoints
from clickpoints.includes.QtShortCuts import AddQComboBox, AddQLabel, AddQLineEdit, AddQCheckBox
from qtpy import QtWidgets, QtCore
from matplotlib.figure import Figure
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from clickpoints.includes.matplotlibwidget import MatplotlibWidget, NavigationToolbar
import numpy as np
import cv2
import os
import matplotlib.pyplot as plt

class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class Addon(clickpoints.Addon):
    def __init__(self, *args, **kwargs):
        super(Addon, self).__init__(*args, **kwargs)
        ########||-- SET TITLE AND LAYOUT --||#####################
        self.setWindowTitle("ClassifierHelpTool - ClickPoints")
        self.layout = QtWidgets.QVBoxLayout(self)

        self.build_Combobox_Treshhold()
        self.label_numberofcontours = AddQLabel(self.layout, text="Number of Contours: 0")
        self.label_currentcontour = AddQLabel(self.layout, text="Current Contour: 0")
        self.build_Button_Detection()
        self.build_Entry_Checkbox_AutomaticBackgroundClassifier()

        ############||--CREATE CANVAS FOR BIG IMAGE--||####################
        self.layout_bigplot_plot_buttons = QtWidgets.QHBoxLayout()
        self.build_Canvas_BigPlot(self.layout_bigplot_plot_buttons) #self.canvasbig
        self.build_Canvas_CutPlot(self.layout_bigplot_plot_buttons) #self.canvascut
        self.layout_buttons = QtWidgets.QVBoxLayout()
        self.button_group = None
        self.button_list = []
        #wird mit "startDetection/addButtons" an self.layout angeheftet



        ##############||--IMPORTANT PARAMETERS--||#######################
        self.image = None
        self.pre_img, self.cont_img, self.contours, self.x_pox, self.y_pos = None,None,None,None,None
        self.big_img = None
        self.cut_img = None
        self.masktypes = None
        self.index = 0
        self.flueimg = None


    def build_Combobox_Treshhold(self):
        #########||-- SET TRESHOLD --||##############################
        self.addOption(key="treshold", display_name="Treshold",
                       default="Individual", value_type="int",
                       tooltip="If Intensity is under a defined Value, "
                               "it gets 0, else it gets 1")
        self.threshtype = ["Individual", "Ozsu", "Indi", "Binear"]
        self.input_threshtype = AddQComboBox(self.layout, "Treshtype: ", selectedValue=self.getOption("treshold"),
                                             values=self.threshtype)
        self.linkOption("treshold", self.input_threshtype)
    def build_Button_Detection(self):
        self.button_startdetector = QtWidgets.QPushButton("StartDetection")
        self.button_startdetector.clicked.connect(self.click_startdetection)
        self.layout.addWidget(self.button_startdetector)
    def bluid_Bottons_Masks(self):
        self.button_group = QtWidgets.QButtonGroup()
        self.layout_buttons.addStretch(1)
        for i in range(len(self.masktypes)):
            b = QtWidgets.QPushButton(str(self.masktypes[i].name)+" ("+str(i+1)+")")
            self.button_group.addButton(b,i)
            self.button_list.append(b)
            self.layout_buttons.addWidget(b)
        self.button_group.buttonClicked[int].connect(self.click_classify)
        self.layout_buttons.addStretch(1)
        self.layout_bigplot_plot_buttons.addLayout(self.layout_buttons)
        self.layout.addLayout(self.layout_bigplot_plot_buttons)
    def build_Canvas_BigPlot(self,a):
        self.canvasbig = None
        self.layout_bigplot = QtWidgets.QVBoxLayout()
        self.canvasbig = MplCanvas(self, width=30, height=40, dpi=100)
        toolbar = NavigationToolbar(self.canvasbig, self)
        self.layout.addWidget(toolbar)
        self.layout_bigplot.addWidget(self.canvasbig)

        a.addLayout(self.layout_bigplot)
    def build_Canvas_CutPlot(self,a):
        self.canvascut = None
        self.layout_cutplot = QtWidgets.QVBoxLayout()
        self.canvascut = MplCanvas(self, width=30, height=40, dpi=100)
        self.layout_cutplot.addWidget(self.canvascut)
        a.addLayout(self.layout_cutplot)
    def build_Canvas_FluePlot(self,a):
        self.canvasflue = None
        self.layout_flueplot = QtWidgets.QVBoxLayout()
        self.canvasflue = MplCanvas(self, width=30, height=40, dpi=100)
        self.layout_flueplot.addWidget(self.canvasflue)
        a.addLayout(self.layout_flueplot, stretch=2)
    def build_Checkbox_Flue(self): #chekbox_flue
        self.layout_flue = QtWidgets.QHBoxLayout()
        self.checkbox_flue = AddQCheckBox(self.layout_flue, text="activate FlueImg",strech=1)
        self.layout_flue.addStretch(stretch=2)
        self.checkbox_flue.clicked.connect(self.click_getFlue)
        self.layout.addLayout(self.layout_flue)
    def build_Entry_Checkbox_AutomaticBackgroundClassifier(self):
        self.layout_AutoBgCl = QtWidgets.QHBoxLayout()
        self.entry_AutoBgCl = AddQLineEdit(self.layout_AutoBgCl, text="MaxPixel: ")
        self.entry_AutoBgCl.setText("60")
        self.checkbox_AutoBgCl = AddQCheckBox(self.layout_AutoBgCl, text=" ")
        self.checkbox_AutoBgCl.clicked.connect(lambda: self.click_classify(0))
        self.layout.addLayout(self.layout_AutoBgCl)


    def keyPressEvent(self, QKeyEvent):
        if QKeyEvent.key() == QtCore.Qt.Key_1:
            self.click_classify(0)
        if QKeyEvent.key() == QtCore.Qt.Key_2:
            self.click_classify(1)
        if QKeyEvent.key() == QtCore.Qt.Key_3:
            self.click_classify(2)
        if QKeyEvent.key() == QtCore.Qt.Key_4:
            self.click_classify(3)
        if QKeyEvent.key() == QtCore.Qt.Key_5:
            self.click_classify(4)
        if QKeyEvent.key() == QtCore.Qt.Key_6:
            self.click_classify(5)
        if QKeyEvent.key() == QtCore.Qt.Key_7:
            self.click_classify(6)
        if QKeyEvent.key() == QtCore.Qt.Key_8:
            self.click_classify(7)
        if QKeyEvent.key() == QtCore.Qt.Key_9:
            self.click_classify(8)
        if QKeyEvent.key() == QtCore.Qt.Key_0:
            self.click_classify(9)

    def click_startdetection(self):
        try:
            self.deleteItemsOfLayout(self.layout_buttons)
            self.deleteItemsOfLayout(self.layout_flue)
            self.index=0
        except:
            None
        ###########||-GET IMPORTANT PARAMETERS--||#########################
        self.image = self.cp.getImage()
        self.masktypes = self.db.getMaskTypes()
        self.pre_img, self.cont_img, self.contours, self.x_pox, self.y_pos = detector(self.image, self.image.layer.name, self.input_threshtype.currentIndex())
        m, n, o, p = self.func_calculate_cutposition()
        self.label_numberofcontours.setText("Number of Contours: "+str(np.array(self.contours).shape))
        self.big_img = self.pre_img
        self.show_BigImg(m,n,o,p) #self.big_img
        self.cut_img = self.pre_img
        self.show_CutImg(m,n,o,p)
        self.bluid_Bottons_Masks()
        self.build_Checkbox_Flue()
        self.index = 1
        self.setMinimumSize(400, 300)
        self.label_currentcontour.setText("Current Contour: " + str(self.index))
    def click_auto_bg_cl(self):
        self.label_currentcontour.setText("Current Contour: " + str(self.index))
        if int(self.entry_AutoBgCl.text()) > len(self.contours[self.index]):
            self.func_setMask(1)
            self.index = self.index + 1
            self.click_auto_bg_cl()
        else:
            m, n, o, p = self.func_calculate_cutposition()
            self.updateBigImg(m, n, o, p)
            self.updateCutImg(m, n, o, p)
            self.index = self.index + 1
    def click_classify(self, i):
        self.label_currentcontour.setText("Current Contour: " + str(self.index))
        for button in self.button_group.buttons():
            if button is self.button_group.button(i):
                m,n,o,p = self.func_calculate_cutposition()
                self.updateBigImg(m, n, o, p)
                self.updateCutImg(m,n,o,p)
                self.func_setMask(i+1)
                if self.checkbox_AutoBgCl.checkState() == 2:
                    self.click_auto_bg_cl()
                else:
                    self.index = self.index + 1

        if self.checkbox_flue.checkState()==2:
            self.update_FlueImg(m,n,o,p)

    #LÖSUNG:   Lösch die kleinen Contouren einfach raus


    def click_getFlue(self):
        if self.checkbox_flue.checkState()==2:
            self.build_Canvas_FluePlot(self.layout_flue)
            self.flueimg = transferImg_To_8Bit(np.asarray(self.db.getImage(layer="Fluo")))
            m, n, o, p = self.func_calculate_cutposition()
            self.show_FlueImg(m, n, o, p)

        else:
            try:
                self.deleteItemsOfLayout(self.layout_flueplot)
            except:
                None

    def update_FlueImg(self,m,n,o,p):
        self.canvasflue.axes.cla()
        self.show_FlueImg(m,n,o,p)
    def show_FlueImg(self,m,n,o,p):
        self.canvasflue.axes.axis('off')
        self.canvasflue.axes.imshow(self.flueimg[o:p, m:n])
        self.canvasflue.draw()
    def updateBigImg(self, m,n,o,p):
        self.canvasbig.axes.cla()
        self.show_BigImg(m,n,o,p)
    def show_BigImg(self, m,n,o,p):
        self.canvasbig.axes.axis('off')
        cv2.drawContours(self.big_img, self.contours[self.index], -1, (255, 255, 255), -1)
        self.canvasbig.axes.imshow(self.big_img)
        self.canvasbig.axes.plot([m, n, n, m, m], [o, o, p, p, o], color="red")
        self.canvasbig.draw()
    def updateCutImg(self, m,n,o,p):
        self.canvascut.axes.cla()
        self.show_CutImg(m,n,o,p)
    def show_CutImg(self,m,n,o,p):
        self.canvascut.axes.axis('off')
        cv2.drawContours(self.cut_img, self.contours[self.index], -1, (255, 255, 255), -1)
        self.canvascut.axes.imshow(self.cut_img[o:p, m:n])
        self.canvascut.draw()


    def deleteItemsOfLayout(self,layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
                else:
                    self.deleteItemsOfLayout(item.layout())

    def func_setMask(self,i):
        print("mask: " + str(i))
        try:
            mask = self.db.getMask(image=self.image)
            mask = np.asarray(mask)
            filledcontours = self.func_getFilledContour()
            for cnt in filledcontours:
                mask[cnt[1]:cnt[2],cnt[0]] = i
        except:
            mask = np.zeros(np.asarray(self.image).shape)
            filledcontours = self.func_getFilledContour()
            for cnt in filledcontours:
                mask[cnt[1]:cnt[2], cnt[0]] = i
        mask = mask.astype(np.uint8)
        self.db.setMask(image=self.image,data=mask)
        self.cp.reloadMask()
        self.cp.reloadImage(frame_index=self.cp.getCurrentFrame())
    def func_calculate_cutposition(self):
        m = int(self.x_pox[self.index] - 25)
        n = int(self.x_pox[self.index] + 25)
        o = int(self.y_pos[self.index] - 25)
        p = int(self.y_pos[self.index] + 25)
        if m < 0:
            m=0
        if o < 0:
            o=0
        return m,n,o,p
    def func_getFilledContour(self):
        list_all = []
        for i,cnt_start in enumerate(self.contours[self.index-1]):
            a = cnt_start[0,0]
            list = []
            for cnt_end in self.contours[self.index-1]:
                if a == cnt_end[0,0]:
                   list.append(cnt_end[0,1])
            list = [a,min(list),max(list)]
            list_all.append(list)
        return list_all






    def run(self, start_frame=0):
        print("The user wants to run me")
    def buttonPressedEvent(self):
        self.show()
