#!/usr/bin/env python2

""" 
CellController.py: CogRIoT Cell Controller main application 

"""
__author__ = "Daniel Mazzer"
__copyright__ = "Copyright 2016, CogRIoT Project"
__credits__ = "Inatel - Wireless and Optical Convergent Access Laboratory"
__license__ = "MIT"
__maintainer__ = "Daniel Mazzer"
__email__ = "dmazzer@gmail.com"


from PyQt4 import Qt
from PyQt4.QtCore import QObject, pyqtSlot
from gnuradio import analog
from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import zeromq
from gnuradio import filter
from gnuradio import gr
from gnuradio import qtgui
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from gnuradio.qtgui import Range, RangeWidget
from grc_gnuradio import blks2 as grc_blks2
from optparse import OptionParser
import mmatrix
import osmosdr
import sensing
import sip
import sys
import time
from distutils.version import StrictVersion

## Sensing Platform System imports
import ConfigParser
import ChannelController
import SectorController
from Logger import Logger
from zmqutils.collector import ZMQCollector


## Sensing Platform GNURadio imports
from SensingProcessor import sensingprocessor_hier
from uuid import uuid1
from ngconfiginterface.nginterface import NGInterface


#------------------------------------------------------------------------------

class CellController(gr.top_block, Qt.QWidget):
    def __init__(self, rtl_source, gnuradio_listener_address):
        logger.log("CellController  - Starting")
        
        gr.top_block.__init__(self, "CogRIoT - Sensing Cell Controller")
        Qt.QWidget.__init__(self)
        self.setWindowTitle("CogRIoT - Sensing Cell Controller")
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except:
            pass
###
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "CellController")
        self.restoreGeometry(self.settings.value("geometry").toByteArray())


        ##################################################
        # Variables
        ##################################################
        self.zmq_harddecision_pub_address = zmq_harddecision_pub_address = gnuradio_listener_address
        self.samp_rate = samp_rate = 2000000
        self.rx_gain_if = rx_gain_if = 20
        self.rx_gain_bb = rx_gain_bb = 20
        self.rx_gain = rx_gain = 0
        self.rx_freq = rx_freq = 950000000
        self.rx_bw = rx_bw = samp_rate/2
        self.remotesensor_address = remotesensor_address = rtl_source
        self.sensingprocessor_lambda = sensingprocessor_lambda = 0.5
        

        ##################################################
        # Blocks
        ##################################################
        
        # receiver
        
        self._remotesensor_address_tool_bar = Qt.QToolBar(self)
        if None:
            self._remotesensor_address_formatter = None
        else:
            self._remotesensor_address_formatter = lambda x: x
        self._remotesensor_address_tool_bar.addWidget(Qt.QLabel("Sensing Cell"+": "))
        self._remotesensor_address_label = Qt.QLabel(str(self._remotesensor_address_formatter(self.remotesensor_address)))
        self._remotesensor_address_tool_bar.addWidget(self._remotesensor_address_label)
        self.top_grid_layout.addWidget(self._remotesensor_address_tool_bar, 0,0,1,2)

        self._rx_gain_if_tool_bar = Qt.QToolBar(self)
        self._rx_gain_if_tool_bar.addWidget(Qt.QLabel("RX IF Gain"+": "))
        self._rx_gain_if_line_edit = Qt.QLineEdit(str(self.rx_gain_if))
        self._rx_gain_if_tool_bar.addWidget(self._rx_gain_if_line_edit)
        self._rx_gain_if_line_edit.returnPressed.connect(
            lambda: self.set_rx_gain_if(float(str(self._rx_gain_if_line_edit.text().toAscii()))))
        self.top_grid_layout.addWidget(self._rx_gain_if_tool_bar, 2,0,1,1)
        
        self._rx_gain_bb_tool_bar = Qt.QToolBar(self)
        self._rx_gain_bb_tool_bar.addWidget(Qt.QLabel("RX BB Gain"+": "))
        self._rx_gain_bb_line_edit = Qt.QLineEdit(str(self.rx_gain_bb))
        self._rx_gain_bb_tool_bar.addWidget(self._rx_gain_bb_line_edit)
        self._rx_gain_bb_line_edit.returnPressed.connect(
            lambda: self.set_rx_gain_bb(float(str(self._rx_gain_bb_line_edit.text().toAscii()))))
        
        self.top_grid_layout.addWidget(self._rx_gain_bb_tool_bar, 3,0,1,1)
        self._rx_gain_tool_bar = Qt.QToolBar(self)
        self._rx_gain_tool_bar.addWidget(Qt.QLabel("RX Gain"+": "))
        self._rx_gain_line_edit = Qt.QLineEdit(str(self.rx_gain))
        self._rx_gain_tool_bar.addWidget(self._rx_gain_line_edit)
        self._rx_gain_line_edit.returnPressed.connect(
            lambda: self.set_rx_gain(float(str(self._rx_gain_line_edit.text().toAscii()))))
        self.top_grid_layout.addWidget(self._rx_gain_tool_bar, 1,0,1,1)

        self._rx_freq_tool_bar = Qt.QToolBar(self)
        self._rx_freq_tool_bar.addWidget(Qt.QLabel("RX Freq"+": "))
        self._rx_freq_line_edit = Qt.QLineEdit(str(self.rx_freq))
        self._rx_freq_tool_bar.addWidget(self._rx_freq_line_edit)
        self._rx_freq_line_edit.returnPressed.connect(
            lambda: self.set_rx_freq(int(str(self._rx_freq_line_edit.text().toAscii()))))
        self.top_grid_layout.addWidget(self._rx_freq_tool_bar, 1,1,1,1)
        
        self.rtlsdr_source_0 = osmosdr.source( args="numchan=" + str(1) + " " + remotesensor_address )
        self.rtlsdr_source_0.set_sample_rate(samp_rate)
        self.rtlsdr_source_0.set_center_freq(rx_freq, 0)
        self.rtlsdr_source_0.set_freq_corr(0, 0)
        self.rtlsdr_source_0.set_dc_offset_mode(0, 0)
        self.rtlsdr_source_0.set_iq_balance_mode(0, 0)
        self.rtlsdr_source_0.set_gain_mode(False, 0)
        self.rtlsdr_source_0.set_gain(rx_gain, 0)
        self.rtlsdr_source_0.set_if_gain(rx_gain_if, 0)
        self.rtlsdr_source_0.set_bb_gain(rx_gain_bb, 0)
        self.rtlsdr_source_0.set_antenna("", 0)
        self.rtlsdr_source_0.set_bandwidth(rx_bw, 0)

        self.zeromq_pub_msg_sink_0 = zeromq.pub_msg_sink(zmq_harddecision_pub_address, 100)


        # sensing processor
        
        self._Lambda_tool_bar = Qt.QToolBar(self)
        self._Lambda_tool_bar.addWidget(Qt.QLabel("Lambda"+": "))
        self._Lambda_line_edit = Qt.QLineEdit(str(self.sensingprocessor_lambda))
        self._Lambda_tool_bar.addWidget(self._Lambda_line_edit)
        self._Lambda_line_edit.returnPressed.connect(
            lambda: self.set_sensingprocessor_lambda(eng_notation.str_to_num(str(self._Lambda_line_edit.text().toAscii()))))
        self.top_grid_layout.addWidget(self._Lambda_tool_bar, 2,1,1,1)
        self.sensingprocessor_hier_0 = sensingprocessor_hier(
            sensingprocessorLambda=sensingprocessor_lambda,
        )

        self.blocks_moving_average_xx_0 = blocks.moving_average_ff(1000, .001, 4000)
        
        # others
                                
        self.blocks_message_debug_0 = blocks.message_debug()
                    
        # graphic elements
        
        self.qtgui_time_sink_x_0_0 = qtgui.time_sink_f(
            1024, #size
            samp_rate, #samp_rate
            "", #name
            2 #number of inputs
        )
        self.qtgui_time_sink_x_0_0.set_update_time(0.10)
        self.qtgui_time_sink_x_0_0.set_y_axis(-0.2, 1.2)
        
        self.qtgui_time_sink_x_0_0.set_y_label("Probability of Detection", "")
        
        self.qtgui_time_sink_x_0_0.enable_tags(-1, True)
        self.qtgui_time_sink_x_0_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_time_sink_x_0_0.enable_autoscale(False)
        self.qtgui_time_sink_x_0_0.enable_grid(False)
        self.qtgui_time_sink_x_0_0.enable_control_panel(False)
        
        if not True:
            self.qtgui_time_sink_x_0_0.disable_legend()
        
        labels = ["Avg", "Dec", "", "", "",
                  "", "", "", "", ""]
        widths = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
                  "magenta", "yellow", "dark red", "dark green", "blue"]
        styles = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
                   -1, -1, -1, -1, -1]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]
        
        for i in xrange(2):
            if len(labels[i]) == 0:
                self.qtgui_time_sink_x_0_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_time_sink_x_0_0.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_0_0.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_0_0.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_0_0.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_0_0.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_0_0.set_line_alpha(i, alphas[i])
        
        self._qtgui_time_sink_x_0_0_win = sip.wrapinstance(self.qtgui_time_sink_x_0_0.pyqwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_time_sink_x_0_0_win, 4,1,1,1)
        self.qtgui_number_sink_0 = qtgui.number_sink(
                gr.sizeof_float,
                0,
                qtgui.NUM_GRAPH_HORIZ,
            1
        )
        self.qtgui_number_sink_0.set_update_time(0.10)
        self.qtgui_number_sink_0.set_title("")
        
        labels = ["Pd/Pfa", "", "", "", "",
                  "", "", "", "", ""]
        units = ["", "", "", "", "",
                  "", "", "", "", ""]
        colors = [("white", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"),
                  ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black")]
        factor = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        for i in xrange(1):
            self.qtgui_number_sink_0.set_min(i, 0)
            self.qtgui_number_sink_0.set_max(i, 1)
            self.qtgui_number_sink_0.set_color(i, colors[i][0], colors[i][1])
            if len(labels[i]) == 0:
                self.qtgui_number_sink_0.set_label(i, "Data {0}".format(i))
            else:
                self.qtgui_number_sink_0.set_label(i, labels[i])
            self.qtgui_number_sink_0.set_unit(i, units[i])
            self.qtgui_number_sink_0.set_factor(i, factor[i])
        
        self.qtgui_number_sink_0.enable_autoscale(False)
        self._qtgui_number_sink_0_win = sip.wrapinstance(self.qtgui_number_sink_0.pyqwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_number_sink_0_win, 4,0,1,1)
        

        ##################################################
        # Connections
        ##################################################

        
        self.connect((self.rtlsdr_source_0, 0), (self.sensingprocessor_hier_0, 0))    

        self.connect((self.sensingprocessor_hier_0, 0), (self.blocks_moving_average_xx_0, 0))    
        self.connect((self.sensingprocessor_hier_0, 1), (self.qtgui_time_sink_x_0_0, 1))    

        self.connect((self.blocks_moving_average_xx_0, 0), (self.qtgui_number_sink_0, 0))    
        self.connect((self.blocks_moving_average_xx_0, 0), (self.qtgui_time_sink_x_0_0, 0))    

        self.msg_connect((self.sensingprocessor_hier_0, 'msg_harddecision'), (self.zeromq_pub_msg_sink_0, 'in'))    

        logger.log("CellController  - Started")

        
    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "top_block")
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()

    # cellcontroller
    
    def get_zmq_harddecision_pub_address(self):
        return self.zmq_harddecision_pub_address

    def set_zmq_harddecision_pub_address(self, zmq_harddecision_pub_address):
        self.zmq_harddecision_pub_address = zmq_harddecision_pub_address

    # receiver
    
    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.rtlsdr_source_0.set_sample_rate(self.samp_rate)

    def get_rx_gain_if(self):
        return self.rx_gain_if

    def set_rx_gain_if(self, rx_gain_if):
        self.rx_gain_if = rx_gain_if
        Qt.QMetaObject.invokeMethod(self._rx_gain_if_line_edit, "setText", Qt.Q_ARG("QString", str(self.rx_gain_if)))
        self.rtlsdr_source_0.set_if_gain(self.rx_gain_if, 0)

    def get_rx_gain_bb(self):
        return self.rx_gain_bb

    def set_rx_gain_bb(self, rx_gain_bb):
        self.rx_gain_bb = rx_gain_bb
        Qt.QMetaObject.invokeMethod(self._rx_gain_bb_line_edit, "setText", Qt.Q_ARG("QString", str(self.rx_gain_bb)))
        self.rtlsdr_source_0.set_bb_gain(self.rx_gain_bb, 0)

    def get_rx_gain(self):
        return self.rx_gain

    def set_rx_gain(self, rx_gain):
        self.rx_gain = rx_gain
        Qt.QMetaObject.invokeMethod(self._rx_gain_line_edit, "setText", Qt.Q_ARG("QString", str(self.rx_gain)))
        self.rtlsdr_source_0.set_gain(self.rx_gain, 0)

    def get_rx_freq(self):
        return self.rx_freq

    def set_rx_freq(self, rx_freq):
        self.rx_freq = rx_freq
        Qt.QMetaObject.invokeMethod(self._rx_freq_line_edit, "setText", Qt.Q_ARG("QString", str(self.rx_freq)))
        self.rtlsdr_source_0.set_center_freq(self.rx_freq, 0)

    def get_rx_bw(self):
        return self.rx_bw

    def set_rx_bw(self, rx_bw):
        self.rx_bw = rx_bw
        self.rtlsdr_source_0.set_bandwidth(self.rx_bw, 0)

    def get_remotesensor_address(self):
        return self.remotesensor_address

    def set_remotesensor_address(self, remotesensor_address):
        self.remotesensor_address = remotesensor_address
        Qt.QMetaObject.invokeMethod(self._remotesensor_address_label, "setText", Qt.Q_ARG("QString", str(self.remotesensor_address)))

    # sensing processor
    
    def get_sensingprocessor_lambda(self):
        return self.sensingprocessor_lambda

    def set_sensingprocessor_lambda(self, sensingprocessor_lambda):
        self.sensingprocessor_lambda = sensingprocessor_lambda
        Qt.QMetaObject.invokeMethod(self._Lambda_line_edit, "setText", Qt.Q_ARG("QString", eng_notation.num_to_str(self.sensingprocessor_lambda)))
        self.sensingprocessor_hier_0.set_sensingprocessorLambda(self.sensingprocessor_lambda)



class Configuration:
    def __init__(self, config_filename):
        logger.log("Configuration - Starting")
        
        self.config_filename = config_filename;
        self.LoadConfigFile(self.config_filename)
    
        logger.log("Configuration - Started")

    def LoadConfigFile(self, config_filename):
        try:
            
            # ConfigParser initialization and configuration file read
            
            configfile = ConfigParser.RawConfigParser()
            configfile.read(config_filename)
            
            # Reading all configutarion data from config file
            
            # receiver section
            self.Load_SensorAddress(configfile)
            self.Load_SampRate(configfile)
            self.Load_RXFreq(configfile)
            self.Load_RXGain(configfile)
            self.Load_RXGainBB(configfile)
            self.Load_RXGainIF(configfile)
            self.Load_RXBW(configfile)
            
            # cellcontroller section
            self.Load_cellcontroller_listener_address(configfile)
            self.Load_cellcontroller_collector_push_address(configfile)
            self.Load_cellcontroller_id(configfile, config_filename)
            self.Load_cellcontroller_num_sectors(configfile)
            self.Load_cellcontroller_location(configfile)

            # channel controller
            self.Load_channelcontroller_listener_address(configfile)
    
            # sector controller
            self.Load_sectorcontroller_listener_address(configfile)

            # sensing section
            self.Load_sensing_start_freq(configfile)
            self.Load_sensing_stop_freq(configfile)
            self.Load_sensing_band_width(configfile)

            # SensingProcessor section
            self.Load_sensingprocessor_threshold(configfile)

            # NovaGenesis section
            self.Load_novagenesis_ng_local_address(configfile)
            self.Load_novagenesis_ng_remote_address(configfile)

            
        except Exception as inst:
            print("Problem reading configuration file")
            print inst
            raise
        
    def SaveConfigFile(self, configfile, config_filename, section, option, value):
        print(configfile, config_filename, section, option, value)
        try:
            configfile.set(section, option, value)
            with open(config_filename, 'wb') as filetowrite:
                logger.log('Saving configuration file')
                configfile.write(filetowrite)
                            
        except Exception as inst:
            print("Problem writing configuration file")
            print inst
            raise 
                
    # receiver section
    def Load_SensorAddress(self, configfile):
        self.sensor_address = configfile.get('receiver', 'sensor_address')
    def Load_SampRate(self, configfile):
        self.samp_rate = configfile.getint('receiver', 'samp_rate')
    def Load_RXGainIF(self, configfile):
        self.rx_gain_if = configfile.getfloat('receiver', 'rx_gain_if')
    def Load_RXGainBB(self, configfile):
        self.rx_gain_bb = configfile.getfloat('receiver', 'rx_gain_bb')
    def Load_RXGain(self, configfile):
        self.rx_gain = configfile.getfloat('receiver', 'rx_gain')
    def Load_RXFreq(self, configfile):
        self.rx_freq = configfile.getint('receiver', 'rx_freq')
    def Load_RXBW(self, configfile):
        self.rx_bw = configfile.getfloat('receiver', 'rx_bw')

    # cellcontroller section
    def Load_cellcontroller_listener_address(self, configfile):
        self.cellcontroller_listener_address = configfile.get('cellcontroller', 'listener_address')
    def Load_cellcontroller_collector_push_address(self, configfile):
        self.cellcontroller_collector_push_address = configfile.get('cellcontroller', 'collector_push_address')
    def Load_cellcontroller_location(self, configfile):
        self.cellcontroller_location = configfile.get('cellcontroller', 'location')
        
    def Load_cellcontroller_id(self, configfile, config_filename):
        self.cellcontroller_id = configfile.get('cellcontroller', 'id')
        if self.cellcontroller_id == '':
            cell_id = str(uuid1())
            logger.log('Generating UUID: ' + cell_id)
            self.SaveConfigFile(configfile, config_filename, 'cellcontroller', 'id' , cell_id)
        

    # channel controller
    def Load_channelcontroller_listener_address(self, configfile):
        self.channelcontroller_listener_address = configfile.get('channelcontroller', 'listener_address')
    
    # sector controller
    def Load_sectorcontroller_listener_address(self, configfile):
        self.sectorcontroller_listener_address = configfile.get('sectorcontroller', 'listener_address')
    

    # SensingProcessor section
    def Load_sensingprocessor_threshold(self, configfile):
        self.sensingprocessor_lambda = configfile.getfloat('sensingprocessor', 'threshold')

    # sensing section
    def Load_sensing_start_freq(self, configfile):
        self.sensing_start_freq = configfile.getint('sensing', 'start_freq')
    def Load_sensing_stop_freq(self, configfile):
        self.sensing_stop_freq = configfile.getint('sensing', 'stop_freq')
    def Load_cellcontroller_num_sectors(self, configfile):
        self.cellcontroller_num_sectors = configfile.getint('cellcontroller', 'num_sectors')
    def Load_sensing_band_width(self, configfile):
        self.sensing_band_width = configfile.getint('sensing', 'band_width')
        
    # NovaGenesis section
    def Load_novagenesis_ng_local_address(self, configfile):
        self.novagenesis_ng_local_address = configfile.get('novagenesis', 'ng_local_address')
    def Load_novagenesis_ng_remote_address(self, configfile):
        self.novagenesis_ng_remote_address = configfile.get('novagenesis', 'ng_remote_address')



#------------------------------------------------------------------------------


if __name__ == '__main__':
    
    logger = Logger()
    logger.log("Remote Sensor application started.")
    
    # Platform initialization stuff
    
    import ctypes
    import sys
    if sys.platform.startswith('linux'):
        try:
            x11 = ctypes.cdll.LoadLibrary('libX11.so')
            x11.XInitThreads()
        except:
            print "Warning: failed to XInitThreads()"
    
    # Options parser
    
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    parser.add_option("-c", "--config-filename", action="store", type="string", dest="config_filename", help="load configuration file")
    (options, args) = parser.parse_args()
    if(str(options.config_filename) == "None"):
        print("config-filename cannot be empty")
        quit()
    
    # Configurations load from file
    
    config = Configuration(options.config_filename);
    rtl_source = config.sensor_address
    gnuradio_listener_address = config.cellcontroller_listener_address 
    
    # Qt version check and GnuRadio TopBlock class initialization        
    
    if(StrictVersion(Qt.qVersion()) >= StrictVersion("4.5.0")):
        Qt.QApplication.setGraphicsSystem(gr.prefs().get_string('qtgui','style','raster'))
    qapp = Qt.QApplication(sys.argv)
    tb = CellController(rtl_source, gnuradio_listener_address)
    
    
    # Applying configurations to TopBlock
    
    # receiver
    tb.set_remotesensor_address(config.sensor_address)
    tb.set_rx_freq(config.rx_freq)
    tb.set_rx_gain(config.rx_gain)
    tb.set_rx_gain_bb(config.rx_gain_bb)
    tb.set_rx_gain_if(config.rx_gain_if)
    tb.set_samp_rate(config.samp_rate)
    tb.set_rx_bw(config.rx_bw)
    
    # cellcontroller
#    tb.set_zmq_harddecision_pub_address(config.cellcontroller_listener_address) 
    
    # sensing processor
    tb.set_sensingprocessor_lambda(config.sensingprocessor_lambda)

    # Starting Controllers

    # startint Sector Controller
    SectorC = SectorController.SectorController(config.sectorcontroller_listener_address)
    
    # starting Channel Controller
    ChannelC = ChannelController.ChannelController(tb, 
                                 config.channelcontroller_listener_address,        
                                 SectorC, 
                                 config.sensing_start_freq, 
                                 config.sensing_stop_freq, 
                                 config.sensing_band_width)
    
    # starting ZMQ messages collector
    collector = ZMQCollector(config.cellcontroller_id,
                             config.channelcontroller_listener_address, 
                             config.sectorcontroller_listener_address, 
                             config.cellcontroller_listener_address, 
                             config.cellcontroller_collector_push_address)
    
    # starting NovaGenesis ZMQ Interfaces   
    NGInterface = NGInterface(config, config.novagenesis_ng_local_address, config.novagenesis_ng_remote_address) 

    # Starting flow graph
    
    tb.start()
    tb.show()
    def quitting():
        tb.stop()
        tb.wait()
    qapp.connect(qapp, Qt.SIGNAL("aboutToQuit()"), quitting)
    qapp.exec_()
    tb = None #to clean up Qt widgets
    logger.log("Application terminated")
    
