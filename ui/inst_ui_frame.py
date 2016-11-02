# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './Qt/inst_ui_frame.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.setWindowModality(QtCore.Qt.NonModal)
        Form.resize(291, 291)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        Form.setMinimumSize(QtCore.QSize(0, 0))
        self.gridLayout = QtWidgets.QGridLayout(Form)
        self.gridLayout.setContentsMargins(0, 3, 0, 0)
        self.gridLayout.setHorizontalSpacing(0)
        self.gridLayout.setVerticalSpacing(3)
        self.gridLayout.setObjectName("gridLayout")
        self.widgetcontainer = QtWidgets.QWidget(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widgetcontainer.sizePolicy().hasHeightForWidth())
        self.widgetcontainer.setSizePolicy(sizePolicy)
        self.widgetcontainer.setMinimumSize(QtCore.QSize(291, 121))
        self.widgetcontainer.setObjectName("widgetcontainer")
        self.gridLayout.addWidget(self.widgetcontainer, 1, 1, 1, 1, QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        self.dock_wid = QtWidgets.QDockWidget(Form)
        self.dock_wid.setFloating(False)
        self.dock_wid.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable)
        self.dock_wid.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.dock_wid.setObjectName("dock_wid")
        self.dockWidgetContents_2 = QtWidgets.QWidget()
        self.dockWidgetContents_2.setObjectName("dockWidgetContents_2")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.dockWidgetContents_2)
        self.verticalLayout.setContentsMargins(3, 0, 3, 3)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.widget_log = QtWidgets.QPlainTextEdit(self.dockWidgetContents_2)
        self.widget_log.setObjectName("widget_log")
        self.verticalLayout.addWidget(self.widget_log)
        self.dock_wid.setWidget(self.dockWidgetContents_2)
        self.gridLayout.addWidget(self.dock_wid, 3, 1, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.dock_wid.setWindowTitle(_translate("Form", "Instrument Log"))

