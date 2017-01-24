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
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.widget = QtWidgets.QWidget(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.widget.setMinimumSize(QtCore.QSize(291, 40))
        self.widget.setObjectName("widget")
        self.cb_correctNonlin = QtWidgets.QCheckBox(self.widget)
        self.cb_correctNonlin.setGeometry(QtCore.QRect(160, 20, 121, 17))
        self.cb_correctNonlin.setChecked(True)
        self.cb_correctNonlin.setObjectName("cb_correctNonlin")
        self.cb_correctDark = QtWidgets.QCheckBox(self.widget)
        self.cb_correctDark.setGeometry(QtCore.QRect(160, 5, 121, 17))
        self.cb_correctDark.setChecked(True)
        self.cb_correctDark.setObjectName("cb_correctDark")
        self.label = QtWidgets.QLabel(self.widget)
        self.label.setGeometry(QtCore.QRect(10, 5, 61, 31))
        self.label.setObjectName("label")
        self.spinBox = QtWidgets.QSpinBox(self.widget)
        self.spinBox.setGeometry(QtCore.QRect(70, 15, 71, 22))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.spinBox.sizePolicy().hasHeightForWidth())
        self.spinBox.setSizePolicy(sizePolicy)
        self.spinBox.setMinimum(1000)
        self.spinBox.setMaximum(65000000)
        self.spinBox.setSingleStep(1000)
        self.spinBox.setProperty("value", 10000)
        self.spinBox.setObjectName("spinBox")
        self.cb_correctNonlin.raise_()
        self.cb_correctDark.raise_()
        self.label.raise_()
        self.spinBox.raise_()
        self.cb_correctNonlin.raise_()
        self.cb_correctDark.raise_()
        self.label.raise_()
        self.spinBox.raise_()
        self.verticalLayout.addWidget(self.widget)
        self.pltWidget = QtWidgets.QWidget(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pltWidget.sizePolicy().hasHeightForWidth())
        self.pltWidget.setSizePolicy(sizePolicy)
        self.pltWidget.setMinimumSize(QtCore.QSize(291, 81))
        self.pltWidget.setMaximumSize(QtCore.QSize(291, 81))
        self.pltWidget.setObjectName("pltWidget")
        self.verticalLayout.addWidget(self.pltWidget)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.cb_correctNonlin.setText(_translate("Form", "Correct Nonlinearity"))
        self.cb_correctDark.setText(_translate("Form", "Correct Dark Counts"))
        self.label.setText(_translate("Form", "Integration\n"
"Time (uS):"))

