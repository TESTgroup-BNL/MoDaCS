#Qt Imports
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QFont, QIcon
#System Imports
import importlib, logging, pickle
from time import time, strftime, sleep, localtime
#MoDaCS Imports
import ui.inst_ui_frame_dock
import remote
from util import QSignalHandler, Sig

class UI_interface(QtCore.QObject):
    
    remote_event_Sig = QtCore.pyqtSignal(object)
    remote_ui_updateTime = QtCore.pyqtSignal(object)
    
    def __init__(self, main_app, cp, active_insts, inst_list):
        super().__init__()
        
        self.active_insts = active_insts
        self.inst_list = inst_list
        self._rCount = 0
        self._sCount = 0

        try:
            if str.lower(cp["Remote"]["Protocol"]) == "udp":
                remote_protocol = "udp"
        except KeyError:
            remote_protocol = "tcp"
        
        if remote_protocol == "udp":
            self.server = remote.Server(cp["Server"], main_app, active_insts)
            self.client = remote.Client(cp["Client"], main_app, active_insts)
        else:
            self.server = remote.TCPConnection(cp["Server"], main_app, active_insts, "server")
            self.client = remote.TCPConnection(cp["Client"], main_app, active_insts, "client")
            
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
            self.ui.actionQuit.triggered.connect(main_app.close)
            self.ui.menuView.addAction(self.ui.dw_Conns.toggleViewAction())
            self.ui.menuView.addAction(self.ui.dw_MasterLog.toggleViewAction())
            self.ui.mdiArea.setViewMode(1)
            self.ui.mdiArea.setTabsClosable(False)
            self.ui.actionTabbed_Mode.triggered.connect(lambda state=0: self.ui.mdiArea.setViewMode(state))
            self.ui.actionTile_Horizontally.triggered.connect(self.ui.mdiArea.tileSubWindows)
            self.ui.actionTile_Cascade.triggered.connect(self.ui.mdiArea.cascadeSubWindows)
        else:
            self.ui.tbl_Instruments.setVisible(False)
            self.ui.tabWidget.currentChanged.connect(self.ui_tabChange)
            self.ui.tbl_Instruments.itemSelectionChanged.connect(lambda: self.ui_showinstUI(self.get_selected_inst()))
            self.ui.btn_quit.released.connect(main_app.close)
            
        
        self.ui.btn_Start_In.released.connect(lambda: self.ui_Trig_In("Start"))    
        self.ui.btn_Stop_In.released.connect(lambda: self.ui_Trig_In("Stop"))
        self.ui.btn_ManTrig_In.released.connect(lambda: self.ui_Trig_In("Indiv. Man."))
        self.ui.btn_InstRst.released.connect(lambda: self.ui_Reset())
        
        if self.client.enabled or self.server.enabled:
            #Client and Server
            self.client.dataRecievedSig.connect(self.ui_update_net_R)
            self.server.dataSentSig.connect(self.ui_update_net_S)
            
            
        else:
            #No Client or Server
            self.ui.gb_Network.setVisible(False)
            
        
        #Client Only
        if self.client.enabled and (not self.server.enabled):
            #No control
            if not self.client.provideControl:
                self.ui.btn_Start_In.setVisible(False)    
                self.ui.btn_Stop_In.setVisible(False)    
                self.ui.btn_ManTrig_In.setVisible(False)    
                self.ui.btn_InstRst.setVisible(False)
                self.ui.btn_ManTrig.setVisible(False) 
                self.ui.groupBox.setVisible(False)
        else:
            self.old_time = None
            self.clockTimer = QtCore.QTimer()
            self.clockTimer.timeout.connect(self.clock_update)
            self.clockTimer.start(10)    
        
        
        #Client
        if self.client.enabled:
            self.remote_ui_updateTime.connect(self.ui_updateTime)
            self.remote_event_Sig.connect(self.ui_remote_event) 
            #self.client.connectionSig.connect(self.ui_update_net_client)
            if self.client.provideControl:
                self.ui.btn_ManTrig.released.connect(lambda: self.client.controlServer.sendSig.emit("main_app.ui_int.ui.btn_ManTrig.released", None))
                self.client.controlServer.dataSentSig.connect(self.ui_update_net_S)
                #self.client.controlServerconnectionSig.connect(self.ui_update_net_server)
        
        #Server
        if self.server.enabled:
            self.remote_event_Sig.connect(lambda val: self.server.sendSig.emit("main_app.ui_int.remote_event_Sig", val))
            #self.server.connectionSig.connect(self.ui_update_net_server)
            if self.server.allowControl:
                self.server.controlClient.dataRecievedSig.connect(self.ui_update_net_R)
                #self.server.controlClient.connectionSig.connect(self.ui_update_net_client)

    def clock_update(self):
        lt = localtime()
        if not self.old_time == lt:
            self.old_time = lt
            self.ui_updateTime(lt)
            if self.server.enabled:
                self.server.sendSig.emit("main_app.ui_int.remote_ui_updateTime", lt)
                
    def ui_update_net_R(self, host, port, l):
        self._rCount += l
        self.ui.lbl_Rcount.setText(str(self._rCount))
        self.ui.lbl_R_IP.setText(host + " on port " + str(port))
        
    def ui_update_net_S(self, host, port, l):
        self._sCount += l
        self.ui.lbl_Scount.setText(str(self._sCount))
        self.ui.lbl_S_IP.setText(host + " on port " + str(port))
        
#     def ui_update_net_server(self, host, port, l):
#         self.ui.lbl_R_IP.setText(host + " on port " + str(port))
#         
#     def ui_update_net_client(self, host, port, l):
#         self.ui.lbl_S_IP.setText(host + " on port" + str(port))

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

                    i.inst_ui_subwin_main = QtWidgets.QMainWindow()
                    i.inst_ui_subwin_main.setWindowFlags(QtCore.Qt.Widget)
                    
                    #i.inst_ui_widget = QtWidgets.QWidget()
                    i.inst_ui_frame = ui.inst_ui_frame_dock.Ui_MainWindow()
                    i.inst_ui_frame.setupUi(i.inst_ui_subwin_main)
                    #i.inst_ui_subwin_main.setCentralWidget(i.inst_ui_subwin_main.label)
                    #i.inst_ui_subwin_main.addDockWidget(QtCore.Qt.RightDockWidgetArea, i.inst_ui_frame.dock_wid)
                    
                    i.inst_ui_subwin.setWindowFlags(QtCore.Qt.Dialog)
                    i.inst_ui_subwin.setWindowTitle(i.cp_inst["InstrumentInfo"]["Name"])
                    i.inst_ui_subwin.setWindowIcon(QIcon())
                    
                    i.inst_ui_subwin.setWidget(i.inst_ui_subwin_main)
                    
                    i.inst_wid = i.inst_ui_frame.widgetcontainer
                    i.inst_log_container = i.inst_ui_frame.widget_log
                else:
                    i.inst_wid = self.ui.stackedWidget.widget(self.ui.stackedWidget.addWidget(QtWidgets.QWidget()))
                    i.inst_log_container = self.ui.stackedWidget_log.widget(self.ui.stackedWidget_log.addWidget(QtWidgets.QPlainTextEdit()))
                
                if self.init_instUI(i):    #If using a user UI, connect UI signals
                    i.interfaceReadySig.connect(self.init_UI_Sigs)
                    self.init_UI_Sigs(i)
                else:
                    i.interfaceReadySig.connect(self.uiReadySkip)
                loaded += 1
            except:
                raise
            
        logging.info("%d/%d instrument UIs loaded.\n" % (loaded, len(self.active_insts)))
        
    def uiReadySkip(self, i):
        i.uiReady = True
        i.uiReadySig.emit()
            
    def init_instUI(self, i):
        #Create UI if available
        using_user_ui = False
        try:
            inst_ui_mod = importlib.import_module("instruments." + i.inst + ".ui")
            i.inst_ui = inst_ui_mod.Ui_Form()
            i.inst_ui.setupUi(i.inst_wid)
            using_user_ui = True
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
        finally:
            if not using_user_ui:
                i.uiReady = True
            return using_user_ui
        
    
    def init_UI_Sigs(self, i):
        #Setup UI signals
        i.ui_interface.ui = i.inst_ui
        try:
            for s in i.interface.ui_outputs:
                try:
                    s_list = s.split(".")
                    m = i.ui_interface
                    for s_obj in s_list:
                        m = getattr(m, s_obj.strip())
                    i.interface.ui_signals[s].connect(m)
                    if self.server.enabled:
                        i.interface.ui_signals[s].connect(lambda val=None, name="", target_sig=i.inst + ".interface.ui_signals['" + s.replace(".","~") + "']" : self.server.sendSig.emit(target_sig, val))
                    #i.interface.ui_signals[s].connect(lambda s=s, val=None : logging.info("%s, %s" % (s, val)))
                except Exception as e:
                    i.instLog.warning("Error connecting UI signal '%s': %s" % (s, e))
        except Exception as e:
            i.instLog.warning("Error connecting UI outputs: %s" % e)
        
        try:
            for s in i.interface.ui_inputs:
                try:
                    s_list = s.split(".")
                    m = i.ui_interface
                    for s_obj in s_list:
                        m = getattr(m, s_obj.strip())
                    i.interface.ui_signals[s] = m
                    #i.interface.ui_signals[s].connect(lambda val=None:print(val))
                    if self.client.provideControl:
                        i.interface.ui_signals[s].connect(lambda val=None, name="", target_sig=i.inst + ".interface.ui_signals['" + s.replace(".","~") + "']" : self.client.controlServer.sendSig.emit(target_sig, val))
                        #i.interface.ui_signals[s].connect(lambda s=s, val=None : logging.info("%s, %s" % (s, val)))
                except Exception as e:
                    i.instLog.warning("Error connecting UI signal '%s': %s" % (s, e))
        except Exception as e:
            i.instLog.warning("Error connecting UI inputs: %s" % e)
        
        #Run any additional init
        try:
            i.ui_interface.provideControl = self.client.provideControl
            i.ui_interface.ui_large = self.ui_large
            i.ui_interface.init()
        except:
            pass
        i.uiReady = True
        i.uiReadySig.emit()
        
    def get_selected_inst(self):
        if len(self.ui.tbl_Instruments.selectionModel().selectedRows()) > 0:
            return self.inst_list[self.ui.tbl_Instruments.selectionModel().selectedRows()[0].row()]

    def ui_showinstUI(self, i):
            if self.ui_large:
                self.active_insts[i].inst_ui_subwin.show()
                #self.active_insts[i].inst_ui_widget.show()
                self.active_insts[i].inst_ui_subwin_main.show()
                self.ui.mdiArea.setActiveSubWindow(self.active_insts[i].inst_ui_subwin)
            else:
                self.ui.stackedWidget.setCurrentIndex(self.ui.stackedWidget.indexOf(self.active_insts[i].inst_wid))
                self.ui.stackedWidget_log.setCurrentIndex(self.ui.stackedWidget_log.indexOf(self.active_insts[i].inst_log_container))
            
    def ui_eventreload(self, i, key):
        self.ui_eventtree_topwids[key].parent().removeChild(self.ui_eventtree_topwids[key])
        self.ui_eventtree_add(i, key)

    def ui_Trig_In(self, act):
        try:
            if self.client.provideControl:
                self.client.controlServer.sendSig.emit(self.get_selected_inst() + ".triggerSig", act)
            else:
                self.active_insts[self.get_selected_inst()].triggerSig.emit(act)
        except:
            pass
            
    def ui_Reset(self):
        try:
            if self.client.provideControl:
                self.client.controlServer.sendSig.emit(self.get_selected_inst() + ".resetSig", None)
            else:
                self.active_insts[self.get_selected_inst()].resetSig.emit()
        except:
            pass

    def ui_set_inst_table(self, cp_inst, inst):
        r = self.ui.tbl_Instruments.rowCount()
        self.ui.tbl_Instruments.insertRow(r)
        self.inst_list[r] = inst
        
        item = QtWidgets.QTableWidgetItem(cp_inst["InstrumentInfo"]["Name"])
        item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
        self.ui.tbl_Instruments.setItem(r, 0, item)
        #self.ui.tbl_Instruments.setItem(r, 1, QtWidgets.QTableWidgetItem(cp_inst["InstrumentInfo"]["Model"]))
        self.ui.tbl_Instruments.setItem(r, 1, QtWidgets.QTableWidgetItem("0"))
        self.ui.tbl_Instruments.setItem(r, 2, QtWidgets.QTableWidgetItem("Standby"))
        self.ui.tbl_Instruments.setItem(r, 3, QtWidgets.QTableWidgetItem(cp_inst["Data"]["absolutePath"]))
            
    #def ui_update_run_status(self, s):
    #    self.ui.plainTextEdit.appendPlainText(s)
        
    def ui_update_inst_status(self, val):
        r = self.inst_list.index(val[0])
        status = val[1]
        self.ui.tbl_Instruments.setItem(r, 2, QtWidgets.QTableWidgetItem(status))
        
    def ui_update_tCount(self, val):
        r = self.inst_list.index(val[0])
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
        
        
