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
        self.gb_Remote = QtWidgets.QGroupBox(Form)
        self.gb_Remote.setGeometry(QtCore.QRect(10, 10, 141, 101))
        self.gb_Remote.setObjectName("gb_Remote")
        self.dt_ClientClock = QtWidgets.QDateTimeEdit(self.gb_Remote)
        self.dt_ClientClock.setGeometry(QtCore.QRect(10, 70, 121, 22))
        self.dt_ClientClock.setFrame(True)
        self.dt_ClientClock.setReadOnly(True)
        self.dt_ClientClock.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.dt_ClientClock.setObjectName("dt_ClientClock")
        self.label = QtWidgets.QLabel(self.gb_Remote)
        self.label.setGeometry(QtCore.QRect(10, 50, 61, 16))
        self.label.setObjectName("label")
        self.pb_SetClock = QtWidgets.QPushButton(self.gb_Remote)
        self.pb_SetClock.setGeometry(QtCore.QRect(10, 20, 121, 23))
        self.pb_SetClock.setObjectName("pb_SetClock")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.gb_Remote.setTitle(_translate("Form", "Remote"))
        self.dt_ClientClock.setDisplayFormat(_translate("Form", "M/d/yyyy h:mm:ss AP"))
        self.label.setText(_translate("Form", "Sync Time:"))
        self.pb_SetClock.setText(_translate("Form", "Sync Clock to Client"))

