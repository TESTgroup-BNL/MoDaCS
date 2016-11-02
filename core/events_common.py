import logging, objgraph
from PyQt5 import QtCore

import event_handlers


def events_init(self, cp_events):
  
    for ev, value in cp_events.items():
        try:          
            self.event_objs[ev] = Event_obj(self.active_insts, ev, value, self.reset_lambdas, self.globalTrig, self.event_reloadSig, event_handlers)
            self.event_addedSig.emit(self.event_objs[ev], ev)
        except Exception as e:
            logging.warning("Error loading events: %s" % e)


class Event_obj(QtCore.QObject):
    
    finishedSig = QtCore.pyqtSignal()
    
    def __init__(self, insts, ev, value, reset_lambdas, gloabalTrigger, event_reloadSig, event_handlers):
        super().__init__()
        self.ev = ev
        self.ev_value = value
        self.event_handlers = event_handlers
        self.reset_lambdas = [] #reset_lambdas
        self.globalTrigger = gloabalTrigger
        self.event_reloadSig = event_reloadSig
        self.event_handler = None
        self.event_thread = None
        self.insts = insts
        self.inputs = {}
        self.outputs = {}
        self.isDirect = False
        self.QueuedUniqueConnection = QtCore.Qt.QueuedConnection | QtCore.Qt.UniqueConnection
        
        self.event_thread = QtCore.QThread()                     #Create event thread
        self.moveToThread(self.event_thread)
        self.finishedSig.connect(self.event_thread.quit)     #make sure thread exits when inst is closed

        if "->" in value:
            self.inputs, self.outputs = self.connect_direct(ev, value)    #Direct connection
        else:
            self.inputs, self.outputs = self.connect_handler(ev, value)   #Event handler
            self.event_thread.started.connect(self.event_init)   #make sure object init when thread starts
                    
        self.event_thread.start()                                #start event thread

    def connect_direct(self, ev, value):
        inputs = {}
        outputs = {}

        #direct connection
        inputs_name = value.split("->")[0].strip()
        outputs_name = value.split("->")[1].strip()
        din = inputs_name.split(".")
        dout = outputs_name.split(".")
        try:
            inSig = self.insts[din[0]].interface.signals[din[1]].s
            inputs[inputs_name] = inSig
            outputs[outputs_name] = "Direct"
            if dout[0] == "GlobalTrigger":
                inSig.connect(lambda ev=ev, name=None, trig=self.globalTrigger : trig.emit(ev), self.QueuedUniqueConnection)
            else:
                m_out = getattr(self.insts[dout[0]].interface, dout[1])          #Lookup output method; not a lambda function but works
                inSig.connect(m_out, self.QueuedUniqueConnection)    #Connect signal to output
                self.connect_reinit_inst(dout[0])
            self.connect_reinit_inst(din[0])
            logging.info("Connection made: %s -> %s" % (inputs_name, outputs_name))
            self.isDirect = True
        except TypeError as e:
            logging.warning("Connection %s -> %s already connected" % (ev, o))   
            print(e)
        except Exception as e:
            logging.error("Connection error (%s -> %s): %s" % (inputs_name, outputs_name, e))
            raise
        
        return inputs, outputs
    
    def connect_handler(self, ev, value):
        inputs = {}
        outputs = {}
                    
        #event handler
        try:
            m = getattr(self.event_handlers, ev)
        except Exception as e:
            logging.error("Event '%s': No event handler found in event_hanlders.py" % ev)
            raise e
        inputs_names = value.split(";")[0].split(",")
        outputs_names = value.split(";")[1].split(",")
        
        print(self)
        print(inputs_names, outputs_names)        
        #self.event_handler = m()                        #Create event handler
        self.event_handler = m()
        #self.event_handler = self.event_handler_b
        print(self.event_handler)
        
        output_count = 0
        for o in outputs_names:
            o = o.strip()
            d = o.split(".")
            
            outSig = self.event_handler.output
            outputs[o] = outSig
            try:
                #self.events[ev].output.connect(lambda val=None, ev=ev, input_m=input_m : print("event: %s, val: %s, %s" %(ev, val, input_m)))
                if d[0] == "GlobalTrigger":
                    outSig.connect(lambda ev=ev, trig=self.globalTrigger : trig.emit(ev), self.QueuedUniqueConnection)
                else:
                    input_m = getattr(self.insts[d[0]].interface, d[1])
                    outSig.connect(lambda val=None, ev=ev, input_m=input_m : input_m(val, ev), self.QueuedUniqueConnection)
                    self.connect_reinit_inst(d[0])
                output_count += 1
            except TypeError as e:
                logging.warning("For event '%s': Receiving method '%s' already connected" % (ev, o))
                print(e)
            except Exception as e:
                logging.warning("For event '%s': No receiving method '%s' found, output ignored" % (ev, o))
                    
        if output_count == 0:   
            logging.error("For event '%s': No outputs found, event ignored" % ev)
            raise Exception("No outputs")
        
        for i in inputs_names:
            i = i.strip()
            d = i.split(".")
            
            inSig = self.insts[d[0]].interface.signals[d[1]].s
            inputs[i] = inSig
            try:
                inSig.connect(self.event_input, QtCore.Qt.UniqueConnection)
                self.connect_reinit_inst(d[0])
            except TypeError as e:
                logging.warning("For event '%s': Input '%s' already connected" % (ev, i))
            except Exception as e:
                logging.error("For event '%s', input '%s': %s" % (ev, i, e))
        
        logging.info("Event Loaded: %s, Inputs: %s, Outputs: %s" % (ev, inputs_names, outputs_names))
        return inputs, outputs
    
    #Run init for the event if present
    def event_init(self):
        if hasattr(self.event_handler, "init"):
            try:
                self.event_handler.init()
            except Exception as e:
                logging.error("Error initializing event '%s': %s" % (ev, e))
    
    #Process input for the event
    def event_input(self, data, name):
        try:
            self.event_handler.input(data, name)
        except Exception as e:
            logging.error("Error passing event input '%s': %s" % (name, e))
            
    def connect_reinit_inst(self, inst):
        if inst not in self.reset_lambdas:
            try:
                self.reset_lambdas.append(inst)
                print("reset lambda: %s, %s, %s" % (self.ev, inst, self.reset_lambdas))
                self.insts[inst].interfaceReadySig.connect(lambda inst=None, s=self : s.reinit_inst(inst), self.QueuedUniqueConnection)
                #self.insts[inst].interfaceReadySig.connect(self.reinit_inst) #, self.QueuedUniqueConnection)
            except Exception as e:
                print("ERROR %s" % e)
    
    #@QtCore.pyqtSlot(str)
    def reinit_inst(self, inst):
        #for ev, ev_obj in self.cp_events.items():
        if inst in self.ev_value:
            try:
                logging.info("Inputs: %s, Outputs: %s" % (self.inputs, self.outputs))
                try:
                    print(self.event_handler)
                    self.event_handler.deletelater()
                except:
                    pass
                #Disconnect all input signals
                #for i, i_sig in self.inputs.items():
                #    try:
                #        #objgraph.show_refs([i_sig], filename="C://temp//og_i_sig.dot")
                #        i_sig.disconnect()
                #    except:
                #        pass
                 
                self.inputs.clear()
                self.outputs.clear()
                print(self.ev, self.ev_value)
                if "->" in self.ev_value:
                    self.inputs, self.outputs = self.connect_direct(self.ev, self.ev_value)  #Direct connection
                else:
                    self.inputs, self.outputs = self.connect_handler(self.ev, self.ev_value) #Event handler
            except Exception as e:
                logging.error(e)               
            logging.info("Event reloaded for '%s': %s, Inputs: %s, Outputs: %s" % (inst, self.ev, self.inputs, self.outputs))
            self.event_reloadSig.emit(self, self.ev)

    
class waitforReady():

    def __init__(self, insts, taregt):
        self._insts = insts
        self._target = target
        
        self._checkReady()                      #If all are already ready, no need to set up signal listeners
                    
        for i in insts:
            i.readySig.connect(self._checkReady)      #Connect "ready" signals for updates

    def _checkReady(self):        
        for i in _insts:                         #Check ready states.  This is done directly (without signals/locals) to be efficient and because they are single reads only, it is thread-safe.
            if not i.ready:
                return
        self._target()                           #If all are ready, call the target
        
    


