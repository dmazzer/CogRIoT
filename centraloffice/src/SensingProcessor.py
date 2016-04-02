#!/usr/bin/env python2

""" 
SensingProcessor.py: CogRIoT Cell Controller GNU Radio Sensing Algorithm 

"""
__author__ = "Daniel Mazzer"
__copyright__ = "Copyright 2016, CogRIoT Project"
__credits__ = "Inatel - Wireless and Optical Convergent Access Laboratory"
__license__ = "MIT"
__maintainer__ = "Daniel Mazzer"
__email__ = "dmazzer@gmail.com"


from gnuradio import analog
from gnuradio import blocks
from gnuradio import gr
from gnuradio.filter import firdes
import sensing

class sensingprocessor_hier(gr.hier_block2):

    def __init__(self, sensingprocessorLambda=0):
        gr.hier_block2.__init__(
            self, "Sensing Platform - Central Office",
            gr.io_signature(1, 1, gr.sizeof_gr_complex*1),
            gr.io_signaturev(2, 2, [gr.sizeof_float*1, gr.sizeof_float*1]),
        )
        self.message_port_register_hier_in("msg_harddecision")
        
        ##################################################
        # Parameters
        ##################################################
        self.sensingprocessorLambda = sensingprocessorLambda

        ##################################################
        # Blocks
        ##################################################
        self.sensing_eigenvalue_cc_0 = sensing.eigenvalue_cc()
        self.sensing_decisionmaker_ff_0 = sensing.decisionmaker_ff()
        self.blocks_multiply_const_vxx_0_1 = blocks.multiply_const_vff((0.5, ))
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_vcc((0, ))
        self.blocks_add_xx_0_0 = blocks.add_vff(1)
        self.analog_const_source_x_0_0 = analog.sig_source_f(0, analog.GR_CONST_WAVE, 0, 0, sensingprocessorLambda)

        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.sensing_decisionmaker_ff_0, 'hard_decision'), (self, 'msg_harddecision'))    
        self.connect((self.analog_const_source_x_0_0, 0), (self.sensing_decisionmaker_ff_0, 1))    
        self.connect((self.blocks_add_xx_0_0, 0), (self.blocks_multiply_const_vxx_0_1, 0))    
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.sensing_eigenvalue_cc_0, 1))    
        self.connect((self.blocks_multiply_const_vxx_0_1, 0), (self.sensing_decisionmaker_ff_0, 0))    
        self.connect((self, 0), (self.blocks_multiply_const_vxx_0, 0))    
        self.connect((self, 0), (self.sensing_eigenvalue_cc_0, 0))    
        self.connect((self.sensing_decisionmaker_ff_0, 0), (self, 0))    
        self.connect((self.sensing_decisionmaker_ff_0, 1), (self, 1))    
        self.connect((self.sensing_eigenvalue_cc_0, 1), (self.blocks_add_xx_0_0, 1))    
        self.connect((self.sensing_eigenvalue_cc_0, 0), (self.blocks_add_xx_0_0, 0))    


    def get_sensingprocessorLambda(self):
        return self.sensingprocessorLambda

    def set_sensingprocessorLambda(self, sensingprocessorLambda):
        self.sensingprocessorLambda = sensingprocessorLambda
        self.analog_const_source_x_0_0.set_offset(self.sensingprocessorLambda)

