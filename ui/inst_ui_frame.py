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
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form.sizePolicy().hasHeightForWidth())
        Form.setSizePolicy(sizePolicy)
        Form.setMinimumSize(QtCore.QSize(291, 291))
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.dockWidget = QtWidgets.QDockWidget(Form)
        self.dockWidget.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable|QtWidgets.QDockWidget.DockWidgetMovable)
        self.dockWidget.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea|QtCore.Qt.TopDockWidgetArea)
        self.dockWidget.setObjectName("dockWidget")
        self.dockWidgetContents = QtWidgets.QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.widgetcontainer = QtWidgets.QWidget(self.dockWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(1)
        sizePolicy.setHeightForWidth(self.widgetcontainer.sizePolicy().hasHeightForWidth())
        self.widgetcontainer.setSizePolicy(sizePolicy)
        self.widgetcontainer.setMinimumSize(QtCore.QSize(291, 121))
        self.widgetcontainer.setObjectName("widgetcontainer")
        self.verticalLayout_3.addWidget(self.widgetcontainer)
        self.dockWidget.setWidget(self.dockWidgetContents)
        self.verticalLayout_2.addWidget(self.dockWidget)
        self.label = QtWidgets.QLabel(Form)
        self.label.setText("")
        self.label.setObjectName("label")
        self.verticalLayout_2.addWidget(self.label)
        self.dock_wid = QtWidgets.QDockWidget(Form)
        self.dock_wid.setMinimumSize(QtCore.QSize(291, 168))
        self.dock_wid.setFloating(False)
        self.dock_wid.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable|QtWidgets.QDockWidget.DockWidgetMovable)
        self.dock_wid.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea|QtCore.Qt.LeftDockWidgetArea)
        self.dock_wid.setObjectName("dock_wid")
        self.dockWidgetContents_2 = QtWidgets.QWidget()
        self.dockWidgetContents_2.setObjectName("dockWidgetContents_2")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.dockWidgetContents_2)
        self.verticalLayout.setContentsMargins(3, 0, 3, 3)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.widget_log = QtWidgets.QPlainTextEdit(self.dockWidgetContents_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget_log.sizePolicy().hasHeightForWidth())
        self.widget_log.setSizePolicy(sizePolicy)
        self.widget_log.setMinimumSize(QtCore.QSize(285, 139))
        self.widget_log.setObjectName("widget_log")
        self.verticalLayout.addWidget(self.widget_log)
        self.dock_wid.setWidget(self.dockWidgetContents_2)
        self.verticalLayout_2.addWidget(self.dock_wid)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.dock_wid.setWindowTitle(_translate("Form", "Instrument Log"))

