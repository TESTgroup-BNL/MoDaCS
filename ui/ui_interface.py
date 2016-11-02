from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QFont, QIcon

from time import time, strftime, sleep

import logging
import ui.inst_ui_frame

class UI_interface(QtCore.QObject):
    
    def __init__(self, main_app, cp, active_insts, inst_list):
        super().__init__()
        self.ui_eventtree_wids = {}
        self.active_insts = active_insts
        self.inst_list = inst_list
        self.ui_large = False
        if cp.has_option("UI", "Size"):
            if cp["UI"]["Size"] == "large":
                self.ui_large = True
                
        #if self.ui_large:
        #    self.ui_large_init(main_app)
        #else:
        self.ui_init(main_app)
        
        self.ui_connections()

    
    def ui_connections(self):
        self.ui.btn_Start_In.released.connect(lambda: self.ui_Trig_In("Start"))    
        self.ui.btn_Stop_In.released.connect(lambda: self.ui_Trig_In("Stop"))
        self.ui.btn_ManTrig_In.released.connect(lambda: self.ui_Trig_In("Manual"))
        self.ui.btn_InstRst.released.connect(self.ui_Reset)


    def ui_init_widgets(self):
        for key, i in self.active_insts.items():
            i.statusSig.connect(self.ui_update_inst_status) 
            i.tCountSig.connect(self.ui_update_tCount)
            
            try:
                if self.ui_large:   
                    i.inst_ui_subwin = self.ui.mdiArea.addSubWindow(QtWidgets.QMdiSubWindow())
                    i.inst_ui_frame = ui.inst_ui_frame.Ui_Form()
                    i.inst_ui_widget = QtWidgets.QWidget()
                    i.inst_ui_subwin.setWidget(i.inst_ui_widget)
                    i.inst_ui_frame.setupUi(i.inst_ui_widget)
                    i.inst_ui_subwin.setWindowFlags(QtCore.Qt.Dialog)
                    i.inst_ui_subwin.setWindowTitle(i.cp_inst["InstrumentInfo"]["Name"])
                    i.inst_ui_subwin.setWindowIcon(QIcon())
                    i.inst_wid = i.inst_ui_frame.widgetcontainer
                    i.inst_log_container = i.inst_ui_frame.widget_log
                else:
                    i.inst_wid = self.ui.stackedWidget.widget(self.ui.stackedWidget.addWidget(QtWidgets.QWidget()))
                    i.inst_log_container = self.ui.stackedWidget_log.widget(self.ui.stackedWidget_log.addWidget(QtWidgets.QWidget()))
                logging.debug("Created widget for %s: %s" % (key, str(i.inst_wid)))
                i.init_instUI()
            except:
                raise
#     def printstuff(self, val):
#         try:
#             print(val)
#             val.setText(1, "blah")
#         except Exception as e:
#             print(e)

    def ui_eventtree_add(self, i, key):
        t = None
        t_in = None
        t_out = None
        row = None
        if i.isDirect:
            t = QtWidgets.QTreeWidgetItem(self.ui.treeWidget.topLevelItem(0), [key], 0)
            t_in = QtWidgets.QTreeWidgetItem(t, ["Inputs"], 0)
            t_out = QtWidgets.QTreeWidgetItem(t, ["Outputs"], 0)
            for ev_i, e_sig in i.inputs.items():
                row = QtWidgets.QTreeWidgetItem(t_in, [ev_i], 0)
                e_sig.connect(lambda val=None, name=None, r=t: r.setText(1, str(val)))
            for ev_o, e_sig in i.outputs.items():
                row = QtWidgets.QTreeWidgetItem(t_out, [ev_o], 0)
            t.setExpanded(False)
            t_in.setExpanded(True)
            t_out.setExpanded(True)
        else:
            t = QtWidgets.QTreeWidgetItem(self.ui.treeWidget.topLevelItem(1), [key], 0)
            t_in = QtWidgets.QTreeWidgetItem(t, ["Inputs"], 0)
            t_out = QtWidgets.QTreeWidgetItem(t, ["Outputs"], 0)
            for ev_i, e_sig in i.inputs.items():
                row = QtWidgets.QTreeWidgetItem(t_in, [ev_i], 0)
                print(row)
                #e_sig.connect(lambda val=None, name=None, r=row: self.printstuff(r))
                e_sig.connect(lambda val=None, name=None, r=row: r.setText(1, str(val)))
            for ev_o, e_sig in i.outputs.items():
                row = QtWidgets.QTreeWidgetItem(t_out, [ev_o], 0)
                e_sig.connect(lambda val=None, name=None, r=row: r.setText(1, str(val)))
            t.setExpanded(True)
            t_in.setExpanded(True)
            t_out.setExpanded(True)
        self.ui_eventtree_wids[key] = t
            
    def ui_eventreload(self, i, key):
        self.ui_eventtree_wids[key].parent().removeChild(self.ui_eventtree_wids[key])
        self.ui_eventtree_add(i, key)
                

    def ui_Trig_In(self, act):
        if len(self.ui.tbl_Instruments.selectionModel().selectedRows()) > 0:
            r = self.ui.tbl_Instruments.selectionModel().selectedRows()[0].row()
            i = self.inst_list[r]
            self.active_insts[i].triggerSig.emit(act)
            
    def ui_Reset(self):
        if len(self.ui.tbl_Instruments.selectionModel().selectedRows()) > 0:
            r = self.ui.tbl_Instruments.selectionModel().selectedRows()[0].row()
            i = self.inst_list[r]
            self.active_insts[i].resetSig.emit()
        
    def ui_set_inst_table(self, cp_inst):
        self.ui.plainTextEdit.appendPlainText("- " + cp_inst["InstrumentInfo"]["Name"])
        r = self.ui.tbl_Instruments.rowCount()
        self.ui.tbl_Instruments.insertRow(r)
        item = QtWidgets.QTableWidgetItem(cp_inst["InstrumentInfo"]["Name"])
        item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
        self.ui.tbl_Instruments.setItem(r, 0, item)
        #self.ui.tbl_Instruments.setItem(r, 1, QtWidgets.QTableWidgetItem(cp_inst["InstrumentInfo"]["Model"]))
        self.ui.tbl_Instruments.setItem(r, 1, QtWidgets.QTableWidgetItem("0"))
        self.ui.tbl_Instruments.setItem(r, 2, QtWidgets.QTableWidgetItem("Standby"))
        self.try_pass(self.ui.tbl_Instruments.setItem, r, 3, QtWidgets.QTableWidgetItem(cp_inst["Data"]["absolutePath"]))
        
        
        #self.ui.lst_Instruments.addItem(QtWidgets.QListWidgetItem(cp_inst["InstrumentInfo"]["Name"]))
            
    def ui_update_run_status(self, s):
        self.ui.plainTextEdit.appendPlainText(s)
        
    def ui_update_inst_status(self, r, status):
        self.ui.tbl_Instruments.setItem(r, 2, QtWidgets.QTableWidgetItem(status))
        
    def ui_update_tCount(self, r, n):
        self.ui.tbl_Instruments.setItem(r, 1, QtWidgets.QTableWidgetItem(str(n)))

#     def ui_init(self, main_app):     
#         
#         from ui.ui import Ui_MainWindow
#         
#         self.ui = Ui_MainWindow()
#         self.ui.setupUi(main_app)
#         
#         stylesheet = "::section{Background-color:rgb(210,210,210);}"
#         self.ui.tbl_Instruments.horizontalHeader().setStyleSheet(stylesheet)
#         self.ui.tbl_Instruments.setColumnWidth(0, 75)
#         self.ui.tbl_Instruments.setColumnWidth(1, 25)
#         self.ui.tbl_Instruments.setColumnWidth(2, 150)
#         self.ui.tbl_Instruments.horizontalHeader().setStretchLastSection(True)
#         
#         #self.ui.progressBar.setVisible(False)
#           
#         #self.ui.tbl_Instruments.itemSelectionChanged.connect(self.ui_updateInstStat)
#         self.ui.tbl_Instruments.itemSelectionChanged.connect(self.ui_showinstUI)
#         
#         self.ui.tabWidget.currentChanged.connect(self.ui_tabChange)
#         
#         self.clockTimer = QtCore.QTimer()
#         self.clockTimer.timeout.connect(self.ui_updateTime)
#         self.clockTimer.start(10) 
        
    def ui_init(self, main_app):     
        
        from ui.ui_large import Ui_MainWindow
        
        self.ui = Ui_MainWindow()
        self.ui.setupUi(main_app)
        
        stylesheet = "section::{Background-color:rgb(210,210,210);}"
        fnt = QFont()
        fnt.setPointSize(10)
        self.ui.tbl_Instruments.setFont(fnt)
        self.ui.tbl_Instruments.horizontalHeader().setStyleSheet(stylesheet)
        self.ui.tbl_Instruments.setColumnWidth(0, 150)
        self.ui.tbl_Instruments.setColumnWidth(1, 50)
        self.ui.tbl_Instruments.setColumnWidth(2, 500)
        self.ui.tbl_Instruments.horizontalHeader().setStretchLastSection(True)
        self.ui.tbl_Instruments.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.ui.tbl_Instruments.itemChanged.connect(self.ui_set_tooltip)
    
        #self.ui.progressBar.setVisible(False)
          
        #self.ui.tbl_Instruments.itemSelectionChanged.connect(self.ui_updateInstStat)
        #self.ui.tbl_Instruments.itemSelectionChanged.connect(self.ui_showinstUI)
        self.ui.tbl_Instruments.cellDoubleClicked.connect(self.ui_showinstUI)
        
        #self.ui.tabWidget.currentChanged.connect(self.ui_tabChange)
        self.ui.treeWidget.topLevelItem(0).setExpanded(True)
        self.ui.treeWidget.topLevelItem(1).setExpanded(True)
        #header.setResizeMode(1, QtGui.QHeaderView.Stretch)
        #header.setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
        self.ui.treeWidget.resize(0, 0) #Set size to minimum
        self.ui.treeWidget.setColumnWidth(1, 75)
        self.ui.treeWidget.setColumnWidth(0, 180)
        #header = self.ui.treeWidget.header()
        #header.setStretchLastSection(True)
        
        #self.inst_addedSig.connect(self.ui_set_inst_table)
        #self.status.connect(self.update_run_status)
        
        self.clockTimer = QtCore.QTimer()
        self.clockTimer.timeout.connect(self.ui_updateTime)
        self.clockTimer.start(10) 
        
    def ui_set_tooltip(self, item):
        item.setToolTip(item.text())
        
    def ui_tabChange(self, t):
        if t == 0 or t == 4:
            self.ui.tbl_Instruments.setVisible(False)
        else:
            self.ui.tbl_Instruments.setVisible(True)
    
    def ui_showinstUI(self):
        if len(self.ui.tbl_Instruments.selectionModel().selectedRows()) > 0:
            r = self.ui.tbl_Instruments.selectionModel().selectedRows()[0].row()
            i = self.inst_list[r]
            
            if self.ui_large:
                self.active_insts[i].inst_ui_subwin.show()
                self.active_insts[i].inst_ui_widget.show()
                self.ui.mdiArea.setActiveSubWindow(self.active_insts[i].inst_ui_subwin)
            else:
                self.ui.stackedWidget.setCurrentIndex(self.ui.stackedWidget.indexOf(self.active_insts[i].inst_wid))
                self.ui.stackedWidget_log.setCurrentIndex(self.ui.stackedWidget_log.indexOf(self.active_insts[i].inst_log_container))
        
    def ui_updateInstStat(self):
        if len(self.ui.tbl_Instruments.selectionModel().selectedRows()) > 0:
            r = self.ui.tbl_Instruments.selectionModel().selectedRows()[0].row()
            i = self.inst_list[r]
            self.ui.txt_InstStat.setPlainText("Name: " + self.active_insts[i].inst_cfg["InstrumentInfo"]["Name"])
            self.ui.txt_InstStat.appendPlainText("Model: " + self.active_insts[i].inst_cfg["InstrumentInfo"]["Model"])
            self.ui.txt_InstStat.appendPlainText("Data Location: " + self.active_insts[i].inst_cfg["Data"]["absolutePath"])
                                                     
        else:
            self.ui.txt_InstStat.setPlainText("")

    def ui_updateTime(self):
        self.ui.lcdTime.display(strftime("%H"+":"+"%M"+":"+"%S"))
        
        
    def try_pass(self, func, *args):
        try:
            func(*args)
        except:
            pass
        

class QSignalHandler(logging.Handler):          #logging handler that emits all log entries through a specified signal
    
    def __init__(self, sig):
        super().__init__()
        self.sig = sig

    def emit(self, record):
        msg = self.format(record)
        self.sig.emit(msg)

    def write(self, m):
        pass
