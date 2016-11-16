from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QFont, QIcon

import importlib
from time import time, strftime, sleep, localtime

import logging, pickle
import ui.inst_ui_frame
import remote

class UI_interface(QtCore.QObject):
    
    remote_event_Sig = QtCore.pyqtSignal(object)
    remote_ui_updateTime = QtCore.pyqtSignal(object)
    
    def __init__(self, main_app, cp, active_insts, inst_list):
        super().__init__()
        
        self.active_insts = active_insts
        self.inst_list = inst_list

        self.server = remote.Server(cp["Server"], main_app, active_insts)
        self.client = remote.Client(cp["Client"], main_app, active_insts)
        
        self.ui_eventtree_wids = {}
        self.ui_eventtree_topwids = {}
        
        self.ui_large = False
        if cp.has_option("UI", "Size"):
            if cp["UI"]["Size"] == "large":
                self.ui_large = True
                
        if self.ui_large:
            from ui.ui_large import Ui_MainWindow
        else:
            from ui.ui import Ui_MainWindow
        
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
      
        self.ui.treeWidget.topLevelItem(1).setExpanded(True)
        self.ui.treeWidget.topLevelItem(2).setExpanded(True)
        self.ui.treeWidget.resize(0, 0) #Set size to minimum
        self.ui.treeWidget.setColumnWidth(1, 75)
        self.ui.treeWidget.setColumnWidth(0, 180)   
        
        if self.ui_large:
            self.ui.tbl_Instruments.cellDoubleClicked.connect(lambda: self.ui_showinstUI(self.get_selected_inst()))         
        else:
            self.ui.tbl_Instruments.setVisible(False)
            self.ui.tabWidget.currentChanged.connect(self.ui_tabChange)
            self.ui.tbl_Instruments.itemSelectionChanged.connect(lambda: self.ui_showinstUI(self.get_selected_inst()))
            
            
        if self.client.enabled:
            self.remote_ui_updateTime.connect(self.ui_updateTime)
            #self.remote_event_Sig.connect(lambda val: print(val))
            self.remote_event_Sig.connect(self.ui_remote_event)
            if self.server.enabled:
                self.remote_ui_updateTime.connect(lambda val: self.server.sendSig.emit("main_app.ui_int.remote_ui_updateTime", val))
            
            if self.client.provideControl:
                self.ui.btn_Start_In.released.connect(lambda: self.client.controlServer.sendSig.emit(self.get_selected_inst() + ".triggerSig", "Start"))
                self.ui.btn_Stop_In.released.connect(lambda: self.client.controlServer.sendSig.emit(self.get_selected_inst() + ".triggerSig", "Stop"))
                self.ui.btn_ManTrig_In.released.connect(lambda: self.client.controlServer.sendSig.emit(self.get_selected_inst() + ".triggerSig", "Manual"))
                self.ui.btn_ManTrig.released.connect(lambda: self.client.controlServer.sendSig.emit("main_app.ui_int.ui.btn_ManTrig.released", None))
                self.ui.btn_InstRst.released.connect(lambda: self.client.controlServer.sendSig.emit(self.get_selected_inst() + ".resetSig", None))
            else:
                self.ui.btn_Start_In.setVisible(False)    
                self.ui.btn_Stop_In.setVisible(False)    
                self.ui.btn_ManTrig_In.setVisible(False)    
                self.ui.btn_InstRst.setVisible(False)
                self.ui.btn_ManTrig.setVisible(False) 
                self.ui.groupBox.setVisible(False) 
                
                if self.server.enabled:
                    self.remote_event_Sig.connect(lambda val: self.server.sendSig.emit("main_app.remote_event_Sig", val))   #if running  as a client and server, just forward the remote event update
         
        else:
            self.old_time = None
            self.clockTimer = QtCore.QTimer()
            self.clockTimer.timeout.connect(self.clock_update)
            self.clockTimer.start(10)
            
            self.ui.btn_Start_In.released.connect(lambda: self.active_insts[self.get_selected_inst()].triggerSig.emit("Start"))    
            self.ui.btn_Stop_In.released.connect(lambda: self.active_insts[self.get_selected_inst()].triggerSig.emit("Stop"))
            self.ui.btn_ManTrig_In.released.connect(lambda: self.active_insts[self.get_selected_inst()].triggerSig.emit("Manual"))
            self.ui.btn_InstRst.released.connect(lambda: self.active_insts[self.get_selected_inst()].resetSig.emit())
        
            if self.server.enabled:
                self.remote_event_Sig.connect(lambda val: self.server.sendSig.emit("main_app.ui_int.remote_event_Sig", val))


    def clock_update(self):
        lt = localtime()
        if not self.old_time == lt:
            self.old_time = lt
            self.ui_updateTime(lt)
            if self.server.enabled:
                self.server.sendSig.emit("main_app.ui_int.remote_ui_updateTime", lt)

    def ui_remote_event(self, val):
        t_sig = self.ui_eventtree_wids[val["key"]]
        t_sig.setText(1, str(val["val"]))

    def ui_eventtree_add(self, i, key):
        t = None
        t_in = None
        t_out = None
        row = None
        if i["direct"]:
            t = QtWidgets.QTreeWidgetItem(self.ui.treeWidget.topLevelItem(1), [key], 0)
            #self.ui_eventtree_parent_wid[key] = t
            t_in = QtWidgets.QTreeWidgetItem(t, ["Inputs"], 0)
            t_out = QtWidgets.QTreeWidgetItem(t, ["Outputs"], 0)
            
            for ev_i, e_sig in i["inputs"].items():
                row = QtWidgets.QTreeWidgetItem(t_in, [ev_i], 0)
                widkey = ".".join(["1", key, "inputs", ev_i])
                i["widkey"] = widkey
                self.ui_eventtree_wids[widkey] = t
                if self.client.enabled:
                    e_sig = Sig(ev_i)
                e_sig.connect(lambda val=None, name=None, r=t: r.setText(1, str(val)))
                if self.server.enabled and not self.client.enabled:
                    e_sig.connect(lambda val=None, name=None, widkey=widkey: self.remote_event_Sig.emit({"key":widkey, "val":val}))
                                                                                                         
                    
            for ev_o, e_sig in i["outputs"].items():
                row = QtWidgets.QTreeWidgetItem(t_out, [ev_o], 0)

            t.setExpanded(False)
            t_in.setExpanded(True)
            t_out.setExpanded(True)
        else:
            t = QtWidgets.QTreeWidgetItem(self.ui.treeWidget.topLevelItem(2), [key], 0)
            #self.ui_eventtree_parent_wid[key] = t
            t_in = QtWidgets.QTreeWidgetItem(t, ["Inputs"], 0)
            t_out = QtWidgets.QTreeWidgetItem(t, ["Outputs"], 0)
            
            for ev_i, e_sig in i["inputs"].items():
                row = QtWidgets.QTreeWidgetItem(t_in, [ev_i], 0)
                widkey = ".".join(["2", key, "inputs", ev_i])
                self.ui_eventtree_wids[widkey] = row
                if self.client.enabled:
                    e_sig = Sig(ev_i)
                e_sig.connect(lambda val=None, name=None, r=row: r.setText(1, str(val)))
                if self.server.enabled and not self.client.enabled:
                    e_sig.connect(lambda val=None, name=None, widkey=widkey : self.remote_event_Sig.emit({"key":widkey, "val":val}))
                    
            for ev_o, e_sig in i["outputs"].items():
                row = QtWidgets.QTreeWidgetItem(t_out, [ev_o], 0)
                widkey = ".".join(["2", key, "outputs", ev_i])
                self.ui_eventtree_wids[widkey] = row
                if self.client.enabled:
                    e_sig = Sig(ev_o)
                e_sig.connect(lambda val=None, name=None, r=row: r.setText(1, str(val)))
                if self.server.enabled and not self.client.enabled:
                    e_sig.connect(lambda val=None, name=None, widkey=widkey : self.remote_event_Sig.emit({"key":widkey, "val":val}))
                    
            t.setExpanded(True)
            t_in.setExpanded(True)
            t_out.setExpanded(True)
        self.ui_eventtree_topwids[key] = t

    def ui_init_widgets(self):
        loaded = 0
        
        logging.info("Loading instrument UIs...")
        for key, i in self.active_insts.items():
            i.statusSig.connect(self.ui_update_inst_status) 
            i.tCountSig.connect(self.ui_update_tCount)
            
            if self.server.enabled:
                i.statusSig.connect(lambda val=None, key=key : self.server.sendSig.emit(key + ".statusSig", val))
                i.tCountSig.connect(lambda val=None, key=key : self.server.sendSig.emit(key + ".tCountSig", val))
            
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
                    i.inst_log_container = self.ui.stackedWidget_log.widget(self.ui.stackedWidget_log.addWidget(QtWidgets.QPlainTextEdit()))
                logging.debug("Created widget for %s: %s" % (key, str(i.inst_wid)))
                
                self.init_instUI(i)     
                i.interfaceReadySig.connect(self.init_UI_Sigs)
                self.init_UI_Sigs(i)
                loaded += 1
            except:
                raise
            
        logging.info("%d/%d instrument UIs loaded.\n" % (loaded, len(self.active_insts)))
            
    def init_instUI(self, i):
        #Create UI if available
        try:
            inst_ui_mod = importlib.import_module("instruments." + i.inst + ".ui")
            i.inst_ui = inst_ui_mod.Ui_Form()
            i.inst_ui.setupUi(i.inst_wid)
        except:
            i.instLog.info("UI not found, showing default")
            try:
                inst_ui_mod = importlib.import_module("ui.inst_default_ui")
                i.inst_ui = inst_ui_mod.Ui_Form()
                i.inst_ui.setupUi(i.inst_wid)
                i.inst_ui.plainTextEdit.setPlainText(i.cp_to_str(i.cp_inst))
            except:
                i.instLog.info("Default UI not found")        
        try:
            #self.inst_log_wid = QtWidgets.QPlainTextEdit(self.inst_log_container)
            #sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            #self.inst_log_wid.setSizePolicy(sizePolicy)
            #self.inst_log_wid.setGeometry(QtCore.QRect(0, 0, 271, 110))
            i.inst_log_wid = i.inst_log_container            
            i.inst_log_wid.setReadOnly(True)
            i.logupdateSig.connect(i.inst_log_wid.appendPlainText)
            i.instLog.addHandler(QSignalHandler(i.logupdateSig))
            if self.server.enabled:
                i.logupdateSig.connect(lambda val=None, target_sig=i.inst + ".logupdateSig" : self.server.sendSig.emit(target_sig, val))
        except Exception as e:
            i.instLog.warning("Error setting up log UI: %s" % e)
        
    
    def init_UI_Sigs(self, i):
        #Setup UI signals
        #print(i)
        try:
            for s in i.interface.ui_outputs:
                try:
                    s_list = s.split(".")
                    s_obj = s_list[0].strip()
                    s_atr = s_list[1].strip()
                    o = getattr(i.inst_ui, s_obj)
                    m = getattr(o, s_atr)
                    i.interface.ui_signals[s].connect(m)
                    #i.interface.ui_signals[s].connect(lambda val=None:print(val))
                    if self.server.enabled:
                        i.interface.ui_signals[s].connect(lambda val=None, name="", target_sig=i.inst + ".interface.ui_signals['" + s.replace(".","~") + "']" : self.server.sendSig.emit(target_sig, val))
                    #i.interface.ui_signals[s].connect(lambda s=s, val=None : logging.info("%s, %s" % (s, val)))
                except Exception as e:
                    i.instLog.warning("Error connecting UI signal '%s': %s" % (s, ev))
            
            for s in i.interface.ui_inputs:
                try:
                    s_list = s.split(".")
                    s_obj = s_list[0].strip()
                    s_atr = s_list[1].strip()
                    o = getattr(i.inst_ui, s_obj)
                    m = getattr(o, s_atr)
                    i.interface.ui_signals[s] = m
                    #i.interface.ui_signals[s].connect(lambda val=None:print(val))
                    if self.client.provideControl:
                        i.interface.ui_signals[s].connect(lambda val=None, name="", target_sig=i.inst + ".interface.ui_signals['" + s.replace(".","~") + "']" : self.client.controlServer.sendSig.emit(target_sig, val))
                        #i.interface.ui_signals[s].connect(lambda s=s, val=None : logging.info("%s, %s" % (s, val)))
                except Exception as e:
                    i.instLog.warning("Error connecting UI signal '%s': %s" % (s, ev))
        except:
            pass
        
        #Run any additional init
        try:
            i.ui.inst_ui = i.inst_ui
            i.ui.init()
        except:
            pass
        
    def get_selected_inst(self):
        if len(self.ui.tbl_Instruments.selectionModel().selectedRows()) > 0:
            return self.inst_list[self.ui.tbl_Instruments.selectionModel().selectedRows()[0].row()]

    def ui_showinstUI(self, i):
            if self.ui_large:
                self.active_insts[i].inst_ui_subwin.show()
                self.active_insts[i].inst_ui_widget.show()
                self.ui.mdiArea.setActiveSubWindow(self.active_insts[i].inst_ui_subwin)
            else:
                self.ui.stackedWidget.setCurrentIndex(self.ui.stackedWidget.indexOf(self.active_insts[i].inst_wid))
                self.ui.stackedWidget_log.setCurrentIndex(self.ui.stackedWidget_log.indexOf(self.active_insts[i].inst_log_container))
            
    def ui_eventreload(self, i, key):
        self.ui_eventtree_topwids[key].parent().removeChild(self.ui_eventtree_topwids[key])
        self.ui_eventtree_add(i, key)

    def ui_Trig_In(self, act, i):
            self.active_insts[i].triggerSig.emit(act)
            
    def ui_Reset(self, i):
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
            
    #def ui_update_run_status(self, s):
    #    self.ui.plainTextEdit.appendPlainText(s)
        
    def ui_update_inst_status(self, val):
        r = val[0]
        status = val[1]
        self.ui.tbl_Instruments.setItem(r, 2, QtWidgets.QTableWidgetItem(status))
        
    def ui_update_tCount(self, val):
        r = val[0]
        n = val[1]
        self.ui.tbl_Instruments.setItem(r, 1, QtWidgets.QTableWidgetItem(str(n)))
        
    def ui_set_tooltip(self, item):
        item.setToolTip(item.text())
        
    def ui_tabChange(self, t):
        if t == 0 or t == 4:
            self.ui.tbl_Instruments.setVisible(False)
        else:
            self.ui.tbl_Instruments.setVisible(True)
        
#    def ui_updateInstStat(self):
#        if len(self.ui.tbl_Instruments.selectionModel().selectedRows()) > 0:
#            r = self.ui.tbl_Instruments.selectionModel().selectedRows()[0].row()
#            i = self.inst_list[r]
#            self.ui.txt_InstStat.setPlainText("Name: " + self.active_insts[i].inst_cfg["InstrumentInfo"]["Name"])
#            self.ui.txt_InstStat.appendPlainText("Model: " + self.active_insts[i].inst_cfg["InstrumentInfo"]["Model"])
#            self.ui.txt_InstStat.appendPlainText("Data Location: " + self.active_insts[i].inst_cfg["Data"]["absolutePath"])
                                                     
#        else:
#            self.ui.txt_InstStat.setPlainText("")

    def ui_updateTime(self, time_val):
        self.ui.lcdTime.display(strftime("%H"+":"+"%M"+":"+"%S", time_val))
        
        
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

class Sig(QtCore.QObject):                      #Signal "wrapper" to allow programmatic definition of signals
    s = QtCore.pyqtSignal(object, object)
    
    def __init__(self, name):
        super().__init__()
        self.name = name
        
    def emit(self, object):
        self.s.emit(object, self.name)
        
    def connect(self, obj):
        self.s.connect(obj)