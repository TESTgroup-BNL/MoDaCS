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
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        Form.setMinimumSize(QtCore.QSize(291, 121))
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.pltWidgetframe = QtWidgets.QWidget(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pltWidgetframe.sizePolicy().hasHeightForWidth())
        self.pltWidgetframe.setSizePolicy(sizePolicy)
        self.pltWidgetframe.setMinimumSize(QtCore.QSize(291, 81))
        self.pltWidgetframe.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.pltWidgetframe.setObjectName("pltWidgetframe")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.pltWidgetframe)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pltWidget = QtWidgets.QWidget(self.pltWidgetframe)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pltWidget.sizePolicy().hasHeightForWidth())
        self.pltWidget.setSizePolicy(sizePolicy)
        self.pltWidget.setMinimumSize(QtCore.QSize(220, 81))
        self.pltWidget.setObjectName("pltWidget")
        self.horizontalLayout.addWidget(self.pltWidget)
        self.verticalLayout.addWidget(self.pltWidgetframe)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))

