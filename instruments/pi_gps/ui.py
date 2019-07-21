# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './ui.ui'
#
# Created by: PyQt5 UI code generator 5.10
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
        self.lat = QtWidgets.QLineEdit(Form)
        self.lat.setGeometry(QtCore.QRect(70, 40, 71, 20))
        self.lat.setReadOnly(True)
        self.lat.setObjectName("lat")
        self.long_2 = QtWidgets.QLineEdit(Form)
        self.long_2.setGeometry(QtCore.QRect(70, 70, 71, 20))
        self.long_2.setReadOnly(True)
        self.long_2.setObjectName("long_2")
        self.alt = QtWidgets.QLineEdit(Form)
        self.alt.setGeometry(QtCore.QRect(70, 100, 71, 20))
        self.alt.setReadOnly(True)
        self.alt.setObjectName("alt")
        self.ts = QtWidgets.QLineEdit(Form)
        self.ts.setGeometry(QtCore.QRect(70, 10, 111, 20))
        self.ts.setReadOnly(True)
        self.ts.setObjectName("ts")
        self.sats = QtWidgets.QLineEdit(Form)
        self.sats.setGeometry(QtCore.QRect(250, 10, 31, 20))
        self.sats.setReadOnly(True)
        self.sats.setObjectName("sats")
        self.label = QtWidgets.QLabel(Form)
        self.label.setGeometry(QtCore.QRect(0, 10, 61, 21))
        self.label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(Form)
        self.label_2.setGeometry(QtCore.QRect(190, 10, 51, 21))
        self.label_2.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(Form)
        self.label_3.setGeometry(QtCore.QRect(30, 40, 31, 21))
        self.label_3.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(Form)
        self.label_4.setGeometry(QtCore.QRect(30, 70, 31, 21))
        self.label_4.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_4.setObjectName("label_4")
        self.label_5 = QtWidgets.QLabel(Form)
        self.label_5.setGeometry(QtCore.QRect(30, 100, 31, 21))
        self.label_5.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_5.setObjectName("label_5")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label.setText(_translate("Form", "Timestamp:"))
        self.label_2.setText(_translate("Form", "Satellites:"))
        self.label_3.setText(_translate("Form", "Lat:"))
        self.label_4.setText(_translate("Form", "Long:"))
        self.label_5.setText(_translate("Form", "Alt:"))

