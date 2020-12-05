#----------------------------------------------------------------
#
#  4190.308 Computer Architecture (Fall 2020)
#
#  Project #4: A 6-Stage Pipelined RISC-V Simulator
#
#  November 25, 2020
#
#  Jin-Soo Kim (jinsoo.kim@snu.ac.kr)
#  Systems Software & Architecture Laboratory
#  Dept. of Computer Science and Engineering
#  Seoul National University
#
#----------------------------------------------------------------

import sys

from consts import *
from isa import *
from components import *
from program import *
from pipe import *


#--------------------------------------------------------------------------
#   Control signal table
#--------------------------------------------------------------------------

csignals = {
    LW     : [ Y, BR_N  , OP1_RS1, OP2_IMI, OEN_1, OEN_0, ALU_ADD  , WB_MEM, REN_1, MEN_1, M_XRD, MT_W, ],
    SW     : [ Y, BR_N  , OP1_RS1, OP2_IMS, OEN_1, OEN_1, ALU_ADD  , WB_X  , REN_0, MEN_1, M_XWR, MT_W, ],
    AUIPC  : [ Y, BR_N  , OP1_PC,  OP2_IMU, OEN_0, OEN_0, ALU_ADD  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, ],
    LUI    : [ Y, BR_N  , OP1_X,   OP2_IMU, OEN_0, OEN_0, ALU_COPY2, WB_ALU, REN_1, MEN_0, M_X  , MT_X, ],
    ADDI   : [ Y, BR_N  , OP1_RS1, OP2_IMI, OEN_1, OEN_0, ALU_ADD  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, ],

    SLLI   : [ Y, BR_N  , OP1_RS1, OP2_IMI, OEN_1, OEN_0, ALU_SLL  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, ],
    SLTI   : [ Y, BR_N  , OP1_RS1, OP2_IMI, OEN_1, OEN_0, ALU_SLT  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, ],
    SLTIU  : [ Y, BR_N  , OP1_RS1, OP2_IMI, OEN_1, OEN_0, ALU_SLTU , WB_ALU, REN_1, MEN_0, M_X  , MT_X, ],
    XORI   : [ Y, BR_N  , OP1_RS1, OP2_IMI, OEN_1, OEN_0, ALU_XOR  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, ],
    SRLI   : [ Y, BR_N  , OP1_RS1, OP2_IMI, OEN_1, OEN_0, ALU_SRL  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, ],

    SRAI   : [ Y, BR_N  , OP1_RS1, OP2_IMI, OEN_1, OEN_0, ALU_SRA  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, ],
    ORI    : [ Y, BR_N  , OP1_RS1, OP2_IMI, OEN_1, OEN_0, ALU_OR   , WB_ALU, REN_1, MEN_0, M_X  , MT_X, ],
    ANDI   : [ Y, BR_N  , OP1_RS1, OP2_IMI, OEN_1, OEN_0, ALU_AND  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, ],
    ADD    : [ Y, BR_N  , OP1_RS1, OP2_RS2, OEN_1, OEN_1, ALU_ADD  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, ],
    SUB    : [ Y, BR_N  , OP1_RS1, OP2_RS2, OEN_1, OEN_1, ALU_SUB  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, ],

    SLL    : [ Y, BR_N  , OP1_RS1, OP2_RS2, OEN_1, OEN_1, ALU_SLL  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, ],
    SLT    : [ Y, BR_N  , OP1_RS1, OP2_RS2, OEN_1, OEN_1, ALU_SLT  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, ],
    SLTU   : [ Y, BR_N  , OP1_RS1, OP2_RS2, OEN_1, OEN_1, ALU_SLTU , WB_ALU, REN_1, MEN_0, M_X  , MT_X, ],
    XOR    : [ Y, BR_N  , OP1_RS1, OP2_RS2, OEN_1, OEN_1, ALU_XOR  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, ],
    SRL    : [ Y, BR_N  , OP1_RS1, OP2_RS2, OEN_1, OEN_1, ALU_SRL  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, ],

    SRA    : [ Y, BR_N  , OP1_RS1, OP2_RS2, OEN_1, OEN_1, ALU_SRA  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, ],
    OR     : [ Y, BR_N  , OP1_RS1, OP2_RS2, OEN_1, OEN_1, ALU_OR   , WB_ALU, REN_1, MEN_0, M_X  , MT_X, ],
    AND    : [ Y, BR_N  , OP1_RS1, OP2_RS2, OEN_1, OEN_1, ALU_AND  , WB_ALU, REN_1, MEN_0, M_X  , MT_X, ],
    JALR   : [ Y, BR_JR , OP1_RS1, OP2_IMI, OEN_1, OEN_0, ALU_ADD  , WB_PC4, REN_1, MEN_0, M_X  , MT_X, ],   
    JAL    : [ Y, BR_J  , OP1_RS1, OP2_IMJ, OEN_0, OEN_0, ALU_X    , WB_PC4, REN_1, MEN_0, M_X  , MT_X, ],

    BEQ    : [ Y, BR_EQ , OP1_RS1, OP2_IMB, OEN_1, OEN_1, ALU_SEQ  , WB_X  , REN_0, MEN_0, M_X  , MT_X, ],
    BNE    : [ Y, BR_NE , OP1_RS1, OP2_IMB, OEN_1, OEN_1, ALU_SEQ  , WB_X  , REN_0, MEN_0, M_X  , MT_X, ],
    BLT    : [ Y, BR_LT , OP1_RS1, OP2_IMB, OEN_1, OEN_1, ALU_SLT  , WB_X  , REN_0, MEN_0, M_X  , MT_X, ],
    BGE    : [ Y, BR_GE , OP1_RS1, OP2_IMB, OEN_1, OEN_1, ALU_SLT  , WB_X  , REN_0, MEN_0, M_X  , MT_X, ],
    BLTU   : [ Y, BR_LTU, OP1_RS1, OP2_IMB, OEN_1, OEN_1, ALU_SLTU , WB_X  , REN_0, MEN_0, M_X  , MT_X, ],

    BGEU   : [ Y, BR_GEU, OP1_RS1, OP2_IMB, OEN_1, OEN_1, ALU_SLTU , WB_X  , REN_0, MEN_0, M_X  , MT_X, ],
    ECALL  : [ Y, BR_N  , OP1_X  , OP2_X  , OEN_0, OEN_0, ALU_X    , WB_X  , REN_0, MEN_0, M_X  , MT_X, ],
    EBREAK : [ Y, BR_N  , OP1_X  , OP2_X  , OEN_0, OEN_0, ALU_X    , WB_X  , REN_0, MEN_0, M_X  , MT_X, ],
}


#--------------------------------------------------------------------------
#   IF: Instruction fetch stage
#--------------------------------------------------------------------------

class IF(Pipe):

    # Pipeline registers ------------------------------

    reg_pc          = WORD(0)       # IF.reg_pc

    #--------------------------------------------------


    def __init__(self):
        super().__init__()

        # Internal signals:----------------------------
        #
        #   self.pc                 # Pipe.IF.pc
        #   self.inst               # Pipe.IF.inst
        #   self.exception          # Pipe.IF.exception
        #   self.pc_next            # Pipe.IF.pc_next
        #   self.pcplus4            # Pipe.IF.pcplus4
        #
        #----------------------------------------------

    def compute(self):

        # DO NOT TOUCH -----------------------------------------------
        # Read out pipeline register values 
        self.pc     = IF.reg_pc

        # Fetch an instruction from instruction memory (imem)
        self.inst, status = Pipe.cpu.imem.access(True, self.pc, 0, M_XRD)

        # Handle exception during imem access
        if not status:
            self.exception = EXC_IMEM_ERROR
            self.inst = BUBBLE
        else:
            self.exception = EXC_NONE
        #-------------------------------------------------------------


        # Compute PC + 4 using an adder
        self.pcplus4    = Pipe.cpu.adder_pcplus4.op(self.pc, 4)

        self.pc_next    = self.pcplus4  if Pipe.ID.pc_sel == PC_4       else \
                          WORD(0)


    def update(self):
          
        IF.reg_pc         = self.pc_next

        ID.reg_pc         = self.pc
        ID.reg_inst       = self.inst
        ID.reg_exception  = self.exception

        # DO NOT TOUCH -----------------------------------------------
        Pipe.log(S_IF, self.pc, self.inst, self.log())
        #-------------------------------------------------------------


    # DO NOT TOUCH ---------------------------------------------------
    def log(self):
        return("# inst=0x%08x, pc_next=0x%08x" % (self.inst, self.pc_next))
    #-----------------------------------------------------------------


#--------------------------------------------------------------------------
#   ID: Instruction decode stage
#--------------------------------------------------------------------------

class ID(Pipe):


    # Pipeline registers ------------------------------

    reg_pc          = WORD(0)           # ID.reg_pc
    reg_inst        = WORD(BUBBLE)      # ID.reg_inst
    reg_exception   = WORD(EXC_NONE)    # ID.reg_exception

    #--------------------------------------------------

    
    def __init__(self):
        super().__init__()

        # Internal signals:----------------------------
        #
        #   self.pc                 # Pipe.ID.pc
        #   self.inst               # Pipe.ID.inst
        #   self.exception          # Pipe.ID.exception
        #
        #   self.rs1                # Pipe.ID.rs1
        #   self.rs2                # Pipe.ID.rs2
        #   self.rd                 # Pipe.ID.rd
        #   self.imm                # Pipe.ID.imm
        #   self.pc_sel             # Pipe.ID.pc_sel
        #   self.c_br_type          # Pipe.ID.c_br_type
        #   self.c_op1_sel          # Pipe.ID.c_op1_sel
        #   self.c_op2_sel          # Pipe.ID.c_op2_sel
        #   self.c_alu_fun          # Pipe.ID.c_alu_fun
        #   self.c_wb_sel           # Pipe.ID.c_wb_sel
        #   self.c_rf_wen           # Pipe.ID.c_rf_wen
        #   self.c_dmem_en          # Pipe.ID.c_dmem_en
        #   self.c_dmem_rw          # Pipe.ID.c_dmem_rw
        #   self.c_rs1_oen          # Pipe.ID.c_rs1_oen
        #   self.c_rs2_oen          # Pipe.ID.c_rs2_oen
        #
        #   self.MM_bubble          # Pipe.ID.MM_bubble
        #
        #----------------------------------------------


    def compute(self):

        # Readout pipeline register values
        self.pc         = ID.reg_pc
        self.inst       = ID.reg_inst
        self.exception  = ID.reg_exception

        self.rs1        = RISCV.rs1(self.inst)
        self.rs2        = RISCV.rs2(self.inst)
        self.rd         = RISCV.rd(self.inst)

        imm_i           = RISCV.imm_i(self.inst)
        imm_s           = RISCV.imm_s(self.inst)
        imm_b           = RISCV.imm_b(self.inst)
        imm_u           = RISCV.imm_u(self.inst)
        imm_j           = RISCV.imm_j(self.inst)


        # Generate control signals

        # DO NOT TOUCH------------------------------------------------
        opcode          = RISCV.opcode(self.inst)
        if opcode in [ EBREAK, ECALL ]:
            self.exception |= EXC_EBREAK
        elif opcode == ILLEGAL:
            self.exception |= EXC_ILLEGAL_INST
            self.inst = BUBBLE
            opcode = RISCV.opcode(self.inst)

        cs = csignals[opcode]
        self.c_br_type  = cs[CS_BR_TYPE]
        self.c_op1_sel  = cs[CS_OP1_SEL]
        self.c_op2_sel  = cs[CS_OP2_SEL]
        self.c_alu_fun  = cs[CS_ALU_FUN]
        self.c_wb_sel   = cs[CS_WB_SEL]
        self.c_rf_wen   = cs[CS_RF_WEN]
        self.c_dmem_en  = cs[CS_MEM_EN]
        self.c_dmem_rw  = cs[CS_MEM_FCN]
        self.c_rs1_oen  = cs[CS_RS1_OEN]
        self.c_rs2_oen  = cs[CS_RS2_OEN]

        # Any instruction with an exception becomes BUBBLE as it enters the MM stage. (except EBREAK)
        # All the following instructions after exception become BUBBLEs too.
        self.MM_bubble = (Pipe.EX.exception and (Pipe.EX.exception != EXC_EBREAK)) or (Pipe.MM.exception)
        #-------------------------------------------------------------

        # Prepare immediate values
        self.imm        = imm_i         if self.c_op2_sel == OP2_IMI      else \
                          imm_s         if self.c_op2_sel == OP2_IMS      else \
                          imm_b         if self.c_op2_sel == OP2_IMB      else \
                          imm_u         if self.c_op2_sel == OP2_IMU      else \
                          imm_j         if self.c_op2_sel == OP2_IMJ      else \
                          WORD(0)

        # Control signal to select the next PC
        self.pc_sel     = PC_4
       

    def update(self):

        RR.reg_pc               = self.pc
        RR.reg_inst             = self.inst
        RR.reg_exception        = self.exception
        RR.reg_rs1              = self.rs1
        RR.reg_rs2              = self.rs2
        RR.reg_rd               = self.rd
        RR.reg_imm              = self.imm
        RR.reg_c_alu_fun        = self.c_alu_fun
        RR.reg_c_rf_wen         = self.c_rf_wen         

        # DO NOT TOUCH -----------------------------------------------
        Pipe.log(S_ID, self.pc, self.inst, self.log())
        #-------------------------------------------------------------


    # DO NOT TOUCH ---------------------------------------------------
    def log(self):
        if self.inst in [ BUBBLE, ILLEGAL ]:
            return('# -')
        else:
            return("# inst=0x%08x, rd=%d rs1=%d rs2=%d imm=0x%08x" 
                    % (self.inst, self.rd, self.rs1, self.rs2, self.imm))
    #-----------------------------------------------------------------


#--------------------------------------------------------------------------
#   RR: Register read stage
#--------------------------------------------------------------------------

class RR(Pipe):

    # Pipeline registers ------------------------------

    reg_pc              = WORD(0)           # RR.reg_pc
    reg_inst            = WORD(BUBBLE)      # RR.reg_inst
    reg_exception       = WORD(EXC_NONE)    # RR.reg_exception
    reg_rs1             = WORD(0)           # RR.reg_rs1
    reg_rs2             = WORD(0)           # RR.reg_rs2
    reg_rd              = WORD(0)           # RR.reg_rd
    reg_imm             = WORD(0)           # RR.reg_imm
    reg_c_alu_fun       = WORD(ALU_X)       # RR.reg_c_alu_fun
    reg_c_rf_wen        = WORD(REN_0)       # RR.reg_c_rf_wen

    #--------------------------------------------------


    def __init__(self):
        super().__init__()

        # Internal signals:----------------------------
        #
        #   self.pc                 # Pipe.RR.pc
        #   self.inst               # Pipe.RR.inst
        #   self.exception          # Pipe.RR.exception
        #
        #   self.rs1                # Pipe.RR.rs1
        #   self.rs2                # Pipe.RR.rs2
        #   self.rd                 # Pipe.RR.rd
        #   self.imm                # Pipe.RR.imm
        #   self.c_alu_fun          # Pipe.RR.c_alu_fun
        #   self.c_rf_wen           # Pipe.RR.c_rf_wen
        #----------------------------------------------



    def compute(self):
  
        # Readout pipeline register values
        self.pc         = RR.reg_pc
        self.inst       = RR.reg_inst
        self.exception  = RR.reg_exception

        self.rs1        = RR.reg_rs1
        self.rs2        = RR.reg_rs2
        self.rd         = RR.reg_rd
        self.imm        = RR.reg_imm
        self.c_alu_fun  = RR.reg_c_alu_fun
        self.c_rf_wen   = RR.reg_c_rf_wen

        
        # Read register file
        self.op1_data   = Pipe.cpu.rf.read(self.rs1)
        self.op2_data   = Pipe.cpu.rf.read(self.rs2)


    def update(self):

        EX.reg_pc               = self.pc
        EX.reg_inst             = self.inst
        EX.reg_exception        = self.exception
        EX.reg_rd               = self.rd
        EX.reg_op1_data         = self.op1_data
        EX.reg_op2_data         = self.op2_data
        EX.reg_c_alu_fun        = self.c_alu_fun
        EX.reg_c_rf_wen         = self.c_rf_wen         

        # DO NOT TOUCH -----------------------------------------------
        Pipe.log(S_RR, self.pc, self.inst, self.log())
        #-------------------------------------------------------------


    # DO NOT TOUCH ---------------------------------------------------
    def log(self):
        if self.inst in [ BUBBLE, ILLEGAL ]:
            return('# -')
        else:
            return("# op1=0x%08x op2=0x%08x" % (self.op1_data, self.op2_data))
    #-----------------------------------------------------------------


#--------------------------------------------------------------------------
#   EX: Execution stage
#--------------------------------------------------------------------------

class EX(Pipe):

    # Pipeline registers ------------------------------

    reg_pc              = WORD(0)           # EX.reg_pc
    reg_inst            = WORD(BUBBLE)      # EX.reg_inst
    reg_exception       = WORD(EXC_NONE)    # EX.reg_exception
    reg_rd              = WORD(0)           # EX.reg_rd
    reg_op1_data        = WORD(0)           # EX.reg_op1_data
    reg_op2_data        = WORD(0)           # EX.reg_op2_data
    reg_c_rf_wen        = False             # EX.reg_c_rf_wen
    reg_c_alu_fun       = WORD(ALU_X)       # EX.reg_c_alu_fun

    #--------------------------------------------------


    def __init__(self):
        super().__init__()

        # Internal signals:----------------------------
        #
        #   self.pc                 # Pipe.EX.pc
        #   self.inst               # Pipe.EX.inst
        #   self.exception          # Pipe.EX.exception
        #   self.rd                 # Pipe.EX.rd
        #   self.c_rf_wen           # Pipe.EX.c_rf_wen
        #   self.c_alu_fun          # Pipe.EX.c_alu_fun
        #   self.op1_data           # Pipe.EX.op1_data
        #   self.op2_data           # Pipe.EX.op2_data
        #
        #   self.alu_out            # Pipe.EX.alu_out
        #
        #----------------------------------------------


    def compute(self):

        # Read out pipeline register values
        self.pc                 = EX.reg_pc
        self.inst               = EX.reg_inst
        self.exception          = EX.reg_exception
        self.rd                 = EX.reg_rd
        self.c_rf_wen           = EX.reg_c_rf_wen
        self.c_alu_fun          = EX.reg_c_alu_fun
        self.op1_data           = EX.reg_op1_data
        self.op2_data           = EX.reg_op2_data

        # The second input to ALU should be put into self.alu2_data for correct log msg.
        self.alu2_data          = self.op2_data

        # Perform ALU operation
        self.alu_out = Pipe.cpu.alu.op(self.c_alu_fun, self.op1_data, self.alu2_data)


    def update(self):

        MM.reg_pc               = self.pc
        MM.reg_exception        = self.exception

        if Pipe.ID.MM_bubble:
            MM.reg_inst         = WORD(BUBBLE)
            MM.reg_c_rf_wen     = False
        else:
            MM.reg_inst         = self.inst
            MM.reg_rd           = self.rd
            MM.reg_c_rf_wen     = self.c_rf_wen
            MM.reg_alu_out      = self.alu_out


        # DO NOT TOUCH -----------------------------------------------
        Pipe.log(S_EX, self.pc, self.inst, self.log())
        #-------------------------------------------------------------


    # DO NOT TOUCH ---------------------------------------------------
    def log(self):

        ALU_OPS = {
            ALU_X       : f'# -',
            ALU_ADD     : f'# {self.alu_out:#010x} <- {self.op1_data:#010x} + {self.alu2_data:#010x}',
            ALU_SUB     : f'# {self.alu_out:#010x} <- {self.op1_data:#010x} - {self.alu2_data:#010x}',
            ALU_AND     : f'# {self.alu_out:#010x} <- {self.op1_data:#010x} & {self.alu2_data:#010x}',
            ALU_OR      : f'# {self.alu_out:#010x} <- {self.op1_data:#010x} | {self.alu2_data:#010x}',
            ALU_XOR     : f'# {self.alu_out:#010x} <- {self.op1_data:#010x} ^ {self.alu2_data:#010x}',
            ALU_SLT     : f'# {self.alu_out:#010x} <- {self.op1_data:#010x} < {self.alu2_data:#010x} (signed)',
            ALU_SLTU    : f'# {self.alu_out:#010x} <- {self.op1_data:#010x} < {self.alu2_data:#010x} (unsigned)',
            ALU_SLL     : f'# {self.alu_out:#010x} <- {self.op1_data:#010x} << {self.alu2_data & 0x1f}',
            ALU_SRL     : f'# {self.alu_out:#010x} <- {self.op1_data:#010x} >> {self.alu2_data & 0x1f} (logical)',
            ALU_SRA     : f'# {self.alu_out:#010x} <- {self.op1_data:#010x} >> {self.alu2_data & 0x1f} (arithmetic)',
            ALU_COPY1   : f'# {self.alu_out:#010x} <- {self.op1_data:#010x} (pass 1)',
            ALU_COPY2   : f'# {self.alu_out:#010x} <- {self.alu2_data:#010x} (pass 2)',
            ALU_SEQ     : f'# {self.alu_out:#010x} <- {self.op1_data:#010x} == {self.alu2_data:#010x}',
        }
        return('# -' if self.inst == BUBBLE else ALU_OPS[self.c_alu_fun]);
    #-----------------------------------------------------------------


#--------------------------------------------------------------------------
#   MM: Memory access stage
#--------------------------------------------------------------------------

class MM(Pipe):

    # Pipeline registers ------------------------------

    reg_pc              = WORD(0)           # MM.reg_pc
    reg_inst            = WORD(BUBBLE)      # MM.reg_inst
    reg_exception       = WORD(EXC_NONE)    # MM.reg_exception
    reg_rd              = WORD(0)           # MM.reg_rd
    reg_c_rf_wen        = False             # MM.reg_c_rf_wen
    reg_alu_out         = WORD(0)           # MM.reg_alu_out

    #--------------------------------------------------

    def __init__(self):
        super().__init__()

        # Internal signals:----------------------------
        #
        #   self.pc                 # Pipe.MW.pc
        #   self.inst               # Pipe.MW.inst
        #   self.exception          # Pipe.MW.exception
        #   self.rd                 # Pipe.MW.rd
        #   self.c_rf_wen           # Pipe.MW.c_rf_wen
        #   self.alu_out            # Pipe.MW.alu_out
        #
        #----------------------------------------------

    def compute(self):

        # Read out pipeline register values
        self.pc             = MM.reg_pc
        self.inst           = MM.reg_inst
        self.exception      = MM.reg_exception
        self.rd             = MM.reg_rd
        self.c_rf_wen       = MM.reg_c_rf_wen
        self.alu_out        = MM.reg_alu_out  

        # Nothing to do for now

        # The value to be written into the register file should be put into self.wbdata for logging
        self.wbdata         = self.alu_out
    

    def update(self):
        
        WB.reg_pc           = self.pc
        WB.reg_inst         = self.inst
        WB.reg_exception    = self.exception
        WB.reg_c_rf_wen     = self.c_rf_wen
        WB.reg_wbdata       = self.wbdata

        # DO NOT TOUCH -----------------------------------------------
        Pipe.log(S_MM, self.pc, self.inst, self.log())
        #-------------------------------------------------------------

    
    # DO NOT TOUCH ---------------------------------------------------
    def log(self):
        if not self.c_rf_wen:
            return('# -')
        else:
            return('# rd=%d wbdata=0x%08x' % (self.rd, self.wbdata))
    #-----------------------------------------------------------------


#--------------------------------------------------------------------------
#   WB: Write back stage
#--------------------------------------------------------------------------

class WB(Pipe):

    # Pipeline registers ------------------------------

    reg_pc              = WORD(0)           # WB.reg_pc
    reg_inst            = WORD(BUBBLE)      # WB.reg_inst
    reg_exception       = WORD(EXC_NONE)    # WB.reg_exception
    reg_rd              = WORD(0)           # WB.reg_rd
    reg_c_rf_wen        = False             # WB.reg_c_rf_wen
    reg_wbdata          = WORD(0)           # WB.reg_wbdata

    #--------------------------------------------------

    def __init__(self):
        super().__init__()

        # Internal signals:----------------------------
        #
        #   self.pc                 # Pipe.WB.pc
        #   self.inst               # Pipe.WB.inst
        #   self.exception          # Pipe.WB.exception
        #   self.rd                 # Pipe.WB.rd
        #   self.c_rf_wen           # Pipe.WB.c_rf_wen
        #   self.wbdata             # Pipe.WB.wbdata
        #
        #----------------------------------------------

    def compute(self):

        # Read out pipeline register values
        self.pc             = WB.reg_pc
        self.inst           = WB.reg_inst
        self.exception      = WB.reg_exception
        self.rd             = WB.reg_rd
        self.c_rf_wen       = WB.reg_c_rf_wen
        self.wbdata         = WB.reg_wbdata  

        # nothing to compute here


    def update(self):
    
        if self.c_rf_wen:
            Pipe.cpu.rf.write(self.rd, self.wbdata)


        # DO NOT TOUCH -----------------------------------------------
        Pipe.log(S_WB, self.pc, self.inst, self.log())

        if (self.exception):
            return False
        else:
            return True
        # ------------------------------------------------------------


    # DO NOT TOUCH ---------------------------------------------------
    def log(self):
        if self.inst == BUBBLE or (not self.c_rf_wen):
            return('# -')
        else:
            return('# R[%d] <- 0x%08x' % (self.rd, self.wbdata))
    #-----------------------------------------------------------------


