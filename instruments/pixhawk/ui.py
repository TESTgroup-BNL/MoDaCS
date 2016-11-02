# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(291, 121)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        self.pb2 = QtWidgets.QProgressBar(Form)
        self.pb2.setGeometry(QtCore.QRect(140, 30, 51, 16))
        self.pb2.setStyleSheet("QProgressBar::chunk {background-color:rgb(0, 85, 255) ; width: 1px; }\n"
"\n"
" QProgressBar {border: 1px solid grey; border-radius: 1px; text-align: center; }")
        self.pb2.setMinimum(1000)
        self.pb2.setMaximum(2000)
        self.pb2.setProperty("value", 1500)
        self.pb2.setAlignment(QtCore.Qt.AlignCenter)
        self.pb2.setObjectName("pb2")
        self.pb1 = QtWidgets.QProgressBar(Form)
        self.pb1.setGeometry(QtCore.QRect(120, 20, 16, 41))
        font = QtGui.QFont()
        font.setPointSize(4)
        self.pb1.setFont(font)
        self.pb1.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.pb1.setStyleSheet("QProgressBar::chunk {background-color:rgb(0, 85, 255) ; width: 10px; }\n"
"\n"
" QProgressBar {border: 1px solid grey; border-radius: 1px; text-align: center; }")
        self.pb1.setMinimum(1000)
        self.pb1.setMaximum(2000)
        self.pb1.setProperty("value", 1500)
        self.pb1.setAlignment(QtCore.Qt.AlignCenter)
        self.pb1.setTextVisible(True)
        self.pb1.setOrientation(QtCore.Qt.Vertical)
        self.pb1.setInvertedAppearance(False)
        self.pb1.setTextDirection(QtWidgets.QProgressBar.TopToBottom)
        self.pb1.setObjectName("pb1")
        self.pb4 = QtWidgets.QProgressBar(Form)
        self.pb4.setGeometry(QtCore.QRect(220, 30, 51, 16))
        self.pb4.setStyleSheet("QProgressBar::chunk {background-color:rgb(0, 85, 255) ; width: 1px; }\n"
"\n"
" QProgressBar {border: 1px solid grey; border-radius: 1px; text-align: center; }")
        self.pb4.setMinimum(1000)
        self.pb4.setMaximum(2000)
        self.pb4.setProperty("value", 1500)
        self.pb4.setAlignment(QtCore.Qt.AlignCenter)
        self.pb4.setObjectName("pb4")
        self.pb3 = QtWidgets.QProgressBar(Form)
        self.pb3.setGeometry(QtCore.QRect(200, 20, 16, 41))
        font = QtGui.QFont()
        font.setPointSize(4)
        self.pb3.setFont(font)
        self.pb3.setStyleSheet("QProgressBar::chunk {background-color:rgb(0, 85, 255) ; width: 10px; }\n"
"\n"
" QProgressBar {border: 1px solid grey; border-radius: 1px; text-align: center; }")
        self.pb3.setMinimum(1000)
        self.pb3.setMaximum(2000)
        self.pb3.setProperty("value", 1500)
        self.pb3.setAlignment(QtCore.Qt.AlignCenter)
        self.pb3.setTextVisible(True)
        self.pb3.setOrientation(QtCore.Qt.Vertical)
        self.pb3.setInvertedAppearance(False)
        self.pb3.setTextDirection(QtWidgets.QProgressBar.TopToBottom)
        self.pb3.setObjectName("pb3")
        self.pb5 = QtWidgets.QProgressBar(Form)
        self.pb5.setGeometry(QtCore.QRect(120, 70, 71, 16))
        self.pb5.setStyleSheet("QProgressBar::chunk {background-color:rgb(0, 85, 255) ; width: 1px; }\n"
"\n"
" QProgressBar {border: 1px solid grey; border-radius: 1px; text-align: center; }")
        self.pb5.setMinimum(1000)
        self.pb5.setMaximum(2000)
        self.pb5.setProperty("value", 1500)
        self.pb5.setAlignment(QtCore.Qt.AlignCenter)
        self.pb5.setObjectName("pb5")
        self.pb7 = QtWidgets.QProgressBar(Form)
        self.pb7.setGeometry(QtCore.QRect(120, 90, 71, 16))
        self.pb7.setStyleSheet("QProgressBar::chunk {background-color:rgb(0, 85, 255) ; width: 1px; }\n"
"\n"
" QProgressBar {border: 1px solid grey; border-radius: 1px; text-align: center; }")
        self.pb7.setMinimum(1000)
        self.pb7.setMaximum(2000)
        self.pb7.setProperty("value", 1500)
        self.pb7.setAlignment(QtCore.Qt.AlignCenter)
        self.pb7.setObjectName("pb7")
        self.pb6 = QtWidgets.QProgressBar(Form)
        self.pb6.setGeometry(QtCore.QRect(200, 70, 71, 16))
        self.pb6.setStyleSheet("QProgressBar::chunk {background-color:rgb(0, 85, 255) ; width: 1px; }\n"
"\n"
" QProgressBar {border: 1px solid grey; border-radius: 1px; text-align: center; }")
        self.pb6.setMinimum(1000)
        self.pb6.setMaximum(2000)
        self.pb6.setProperty("value", 1500)
        self.pb6.setAlignment(QtCore.Qt.AlignCenter)
        self.pb6.setObjectName("pb6")
        self.pb8 = QtWidgets.QProgressBar(Form)
        self.pb8.setGeometry(QtCore.QRect(200, 90, 71, 16))
        self.pb8.setStyleSheet("QProgressBar::chunk {background-color:rgb(0, 85, 255) ; width: 1px; }\n"
"\n"
" QProgressBar {border: 1px solid grey; border-radius: 1px; text-align: center; }")
        self.pb8.setMinimum(1000)
        self.pb8.setMaximum(2000)
        self.pb8.setProperty("value", 1500)
        self.pb8.setAlignment(QtCore.Qt.AlignCenter)
        self.pb8.setObjectName("pb8")
        self.groupBox = QtWidgets.QGroupBox(Form)
        self.groupBox.setGeometry(QtCore.QRect(110, 0, 171, 116))
        self.groupBox.setObjectName("groupBox")
        self.groupBox_2 = QtWidgets.QGroupBox(Form)
        self.groupBox_2.setGeometry(QtCore.QRect(10, 0, 101, 116))
        self.groupBox_2.setObjectName("groupBox_2")
        self.pb_Battery = QtWidgets.QProgressBar(self.groupBox_2)
        self.pb_Battery.setGeometry(QtCore.QRect(10, 20, 81, 16))
        self.pb_Battery.setAutoFillBackground(False)
        self.pb_Battery.setStyleSheet("QProgressBar::chunk {background-color:rgb(0, 255, 0) ; width: 1px; }\n"
"\n"
" QProgressBar {border: 1px solid grey; border-radius: 1px; text-align: center; }")
        self.pb_Battery.setMinimum(0)
        self.pb_Battery.setMaximum(100)
        self.pb_Battery.setProperty("value", 100)
        self.pb_Battery.setAlignment(QtCore.Qt.AlignCenter)
        self.pb_Battery.setInvertedAppearance(False)
        self.pb_Battery.setObjectName("pb_Battery")
        self.pb_Vcc = QtWidgets.QProgressBar(self.groupBox_2)
        self.pb_Vcc.setGeometry(QtCore.QRect(10, 40, 81, 16))
        self.pb_Vcc.setAutoFillBackground(False)
        self.pb_Vcc.setStyleSheet("QProgressBar::chunk {background-color:rgb(0, 255, 0) ; width: 1px; }\n"
"\n"
" QProgressBar {border: 1px solid grey; border-radius: 1px; text-align: center; }")
        self.pb_Vcc.setMinimum(4000)
        self.pb_Vcc.setMaximum(6000)
        self.pb_Vcc.setProperty("value", 5000)
        self.pb_Vcc.setAlignment(QtCore.Qt.AlignCenter)
        self.pb_Vcc.setInvertedAppearance(False)
        self.pb_Vcc.setObjectName("pb_Vcc")
        self.groupBox.raise_()
        self.pb2.raise_()
        self.pb1.raise_()
        self.pb4.raise_()
        self.pb3.raise_()
        self.pb5.raise_()
        self.pb7.raise_()
        self.pb6.raise_()
        self.pb8.raise_()
        self.groupBox_2.raise_()

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.pb2.setFormat(_translate("Form", "%v"))
        self.pb1.setFormat(_translate("Form", "%v"))
        self.pb4.setFormat(_translate("Form", "%v"))
        self.pb3.setFormat(_translate("Form", "%v"))
        self.pb5.setFormat(_translate("Form", "%v"))
        self.pb7.setFormat(_translate("Form", "%v"))
        self.pb6.setFormat(_translate("Form", "%v"))
        self.pb8.setFormat(_translate("Form", "%v"))
        self.groupBox.setTitle(_translate("Form", "RC Inputs"))
        self.groupBox_2.setTitle(_translate("Form", "Vehicle"))
        self.pb_Battery.setFormat(_translate("Form", "Batt: %v%"))
        self.pb_Vcc.setFormat(_translate("Form", "Vcc: %vmV"))

