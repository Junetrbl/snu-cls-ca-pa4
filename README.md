# 4190.308 Computer Architecture (Fall 2020)
# Project #4: A 6-Stage Pipelined RISC-V Simulator
### Due: 11:59PM, December 16 (Wednesday)

## Introduction

The goal of this project is to understand how a pipelined processor works. You need to build a 6-stage pipelined RISC-V simulator called `snurisc6` in Python that supports the most of RV32I base instruction set.

## Processor microarchitecture

The target RISC-V processor `snurisc6` consists of six pipeline stages: IF, ID, RR, EX, MM, and WB. The following briefly summarizes the tasks performed in each stage:

* IF: Fetches an instruction from imem (instruction memory)
* ID: Decodes the instruction and prepares immediate values
* RR: Reads the register file
* EX: Performs arithmetic/logical computation and determines the branch outcome
* MM: Accesses dmem (data memory), if necessary
* WB: Writes back the result to the register file

Compared with the traditional 5-stage pipeline architecture implemented in `snurisc5`, you can see that the instruction decoding and register file reads originally performed in the ID stage has been separated into two stages, ID and RR.

The `snurisc6` processor has the following characteristics:

* The control logic is located in the ID stage as in `snurisc5`.
* If the pipeline requires to be stalled, it is detected in the ID stage. 
* The forwarding (or bypassing) detection and resolution is done at the end of the RR stage. 
* The write to the register file is done at the end of the WB stage (not in the middle of the WB stage). Therefore, when an instructions tries to read a register in the RR stage while the preceding instruction is writing a value to the same register in the WB stage at the same cycle, the value should be forwarded as well. Please note that this behavior of the register file is different from what is assumed in the textbook.
* The outcome of the conditional branch is determined at the end of the EX stage. Once the branch outcome is known, any mispredicted branch should be handled immediately.


## Problem specification

This project assignment consists of the following three parts.

### Part 1. Implementing a 6-stage pipelined RISC-V processor simulator (30 points)

Your first task is to implement ``snurisc6``, a 6-stage pipelined RISC-V processor simulator in Python. The reference 5-stage pipelined RISC-V processor simulator is available in the ``pipe5`` directory of [the PyRISC Project](https://github.com/snu-csl/pyrisc). The requirements for implementing ``snurisc6`` are summarized below:

* ``snurisc6`` should accept the same RISC-V executable file accepted by the reference ``snurisc5`` simulator.
* ``snurisc6`` and ``snurisc5`` should produce the same results (in terms of register values and memory states).
* Data forwarding should be fully implemented wherever necessary.
* In case data forwarding cannot solve the dependency among instructions (e.g., load-use hazard), the pipeline should be stalled.
* You should minimize the number of stalled cycles.


### Part 2. Implementing the "always-taken" branch prediction scheme (40 points)

By default, the "__always-not-taken__" branch prediction scheme is used in ``snurisc5``, i.e., the instructions next to the conditional branch instruction are fetched immediately at the next cycle assuming that the branch will not be taken. 

Instead, your second task is to implement the "__always-taken__" branch prediction scheme in ``snurisc6``. In the __always-taken__ branch prediction scheme, the next instructions in the branch target are immediately fetched after the branch instruction predicting that the branch will be taken. Similar to the __always-not-taken__ prediction scheme, any instructions that are incorrectly fetched should be cancelled (by converting them into BUBBLEs) when the prediction was wrong. From the literature, the __always-taken__ branch prediction scheme is known to outperform the __always-not-taken__ scheme, resulting in an accuracy of about 60%. Here are more detailed descriptions for implementing the __always-taken__ branch prediction scheme.

* The branch prediction should be performed in the IF stage in order to fetch the next instruction immediately. This means that we need to put an additional logic in the IF stage to identify whether the fetched instruction is one of the conditional branch instructions (i.e., ``beq``, ``bne``, ``bge``, ``bgeu``, ``blt``, ``bltu``).
* When the current instruction is a branch instruction, it is required to compute the branch target address in the IF stage. This can be done by extracting the offset value from the instruction word and then adding it to the current ``pc``. You can use the adder named ``Pipe.cpu.adder_brtarget`` for this purpose which was originally used for calculating the branch target address in the EX stage.
* The branch outcome is determined in the EX stage. If the prediction was right, there is nothing we need to do. However, if the prediction was wrong (i.e., the branch was NOT taken), we need to cancel the incorrectly fetched instructions. At the time we know the prediction was wrong in the EX stage, three instructions from the branch target address are already fetched and running in the IF, ID, and RR stages of the pipeline. Therefore, these three instructions should be converted to BUBBLEs.
* Finally, when the prediction was wrong, we need to forward the correct value for the next ``pc``. This value should be the address of the original branch instruction plus 4. 
* We can use the same prediction scheme for the ``jal`` instruction. The target address of the ``jal`` instruction is given by the ``pc`` + 20-bit offset (21-bit after adjustment). So, we can use the same adder to compute the target address. For the ``jal`` instruction, the difference is that we are never wrong about the prediction.
* The handling of the ``jalr`` instruction is a little bit tricky, as its target address is given by the ``rs1`` + 12-bit offset. In order to compute the target address in the IF stage for the ``jalr`` instruction, we need another read port in the register file (due to structural hazard). Also, it requires another forwarding path from later stages to the IF stage and pipeline stalls for the possible dependency with the preceding instructions on the ``rs1`` register. To make the problem simpler, the ``jalr`` instruction is handled in the same way as in ``snurisc5``; the instructions next to the ``jalr`` instruction are fetched until we have the target address in the EX stage and then the incorrectly fetched instructions are converted into BUBBLEs while the target address is forward to the next ``pc`` value immediately.

* Example 1: Taken branch

```
                         C0  C1  C2  C3  C4  C5  C6  C7  C8  C9  C10 C11 C12 (cycle)
    beq  t0, t0, L1      IF  ID  RR  EX  MM  WB
    add  t1, t2, t3
    addi t1, t1, -1
    sub  t4, t1, t2
    ...
    ...
L1: sub  t5, t6, t3          IF  ID  RR  EX  MM  WB
    xori t5, t5, 1               IF  ID  RR  EX  MM  WB
    add  t6, t6, t5                  IF  ID  RR  EX  MM  WB
    addi t6, t6, 10                      IF  ID  RR  EX  MM  WB
```

* Example 2: Not-taken branch

```
                         C0  C1  C2  C3  C4  C5  C6  C7  C8  C9  C10 C11 C12 (cycle)
    bne  t0, t0, L1      IF  ID  RR  EX  MM  WB
    add  t1, t2, t3                      IF  ID  RR  EX  MM  WB
    addi t1, t1, -1                          IF  ID  RR  EX  MM  WB
    sub  t4, t1, t2                              IF  ID  RR  EX  MM  WB
    ...
    ...
L1: sub  t5, t6, t3          IF  ID  RR  -   -   -
    xori t5, t5, 1               IF  ID  -   -   -   -
    add  t6, t6, t5                  IF  -   -   -   -   -
    addi t6, t6, 10                      
```

* Example 3: ``jal`` instruction

```
                         C0  C1  C2  C3  C4  C5  C6  C7  C8  C9  C10 C11 C12 (cycle)
    jal  ra, L1          IF  ID  RR  EX  MM  WB
    add  t1, t2, t3
    addi t1, t1, -1
    sub  t4, t1, t2
    ...
    ...
L1: sub  t5, t6, t3          IF  ID  RR  EX  MM  WB
    xori t5, t5, 1               IF  ID  RR  EX  MM  WB
    add  t6, t6, t5                  IF  ID  RR  EX  MM  WB
    addi t6, t6, 10                      IF  ID  RR  EX  MM  WB
```

* Example 4: ``jalr`` instruction (assuming ``ra`` contains the address of ``L1``)

```
                         C0  C1  C2  C3  C4  C5  C6  C7  C8  C9  C10 C11 C12 (cycle)
    jalr x0, 0(ra)       IF  ID  RR  EX  MM  WB
    add  t1, t2, t3          IF  ID  RR  -   -   -
    addi t1, t1, -1              IF  ID  -   -   -   -
    sub  t4, t1, t2                  IF  -   -   -   -   -
    ...
    ...
L1: sub  t5, t6, t3                      IF  ID  RR  EX  MM  WB
    xori t5, t5, 1                           IF  ID  RR  EX  MM  WB
    add  t6, t6, t5                              IF  ID  RR  EX  MM  WB
    addi t6, t6, 10                                  IF  ID  RR  EX  MM  WB
```

If you complete Part 1 with the default __always-not-taken__ branch prediction, you will get only 30 points in this project assignment. If you complete both Part 1 and Part 2, you will get 70 points.


### Part 3: Design document (30 points)

You need to prepare and submit the design document (in PDF file) for the `snurisc6` processor. If you design the 6-stage RISC-V pipeline correctly with satisfying all the above requirements, you will get 30 points even if your implementation does not work. Your design document should answer the following questions:

1. What does the overall pipeline architecture look like? (10 points)

 * We provide you with the `snurisc6-design.pdf` file that has an empty diagram of pipeline stages and hardware components. You need to complete this diagram according to your pipeline design. A hand-drawn diagram is OK. You don't have to spend a lot of time to make it fancy. Please take a picture of your diagram and attach it in your design document.

2. About Part 1: When do data hazards occur and how do you deal with them? (10 points)

 * Show all the possible cases when data hazards can occur and your solutions to them.
 * What hardware has been added to detect and resolve data hazards and how does it work?

3. About Part 2: When do control hazards occur and how do you deal with them with the __always-taken__ branch prediction scheme? (10 points)

 * Again, show all the possible cases when control hazards can occur and your solutions to them.
 * What hardware has been added to detect and resolve control hazards and how does it work?


### Getting started

We provide you with the skeleton code that can be downloaded from https://github.com/snu-csl/ca-pa4. To download the skeleton code, please take the following step:

```
$ git clone https://github.com/snu-csl/ca-pa4.git
```

Note that the `snurisc6` simulator is based on the reference 5-stage pipelined simulator (`snurisc5`) available in [the PyRISC project](https://github.com/snu-csl/pyrisc). We have slightly changed the simulator structure so that you only need to modify the ``stages.py`` file. Currently, `snurisc6` just supports  some of ALU operations without implementing any hazard detection and control logic. Please refer to the `snurisc6-skel.pdf` file for the current pipeline structure of the `snurisc6` simulator.

Your task is to make it work correctly for any combination of instructions. You may find the [GUIDE.md](https://github.com/snu-csl/pyrisc/blob/master/pipe5/GUIDE.md) file in the PyRISC project useful, which describes the overall architecture and implementation details of the `snurisc5` simulator.

In the PyRISC project, several RISC-V executable files are available such as `fib`, `sum100`, `forward`, `branch`, and `loaduse`. You can test your simulator with these programs. Also, it is highly recommended to write your own test programs to see how your simulator works in a particular situation. Note that, for the given RISC-V executable file, `snurisc` (ISA simulator), `snurisc5` (5-stage implementation), and your `snurisc6` (6-stage implementation) all should have the same results in terms of register values and memory states. The only difference will be the number of cycles you need to execute the program.

The following example shows how you can run the executable file `sum100` on the `snurisc6` simulator (We assume that `pyrisc` is also downloaded in the same directory as `ca-pa4`).

```
$ cd ca-pa4
$ ./snurisc6.py -l 4 ../pyrisc/asm/sum100   
or
$ python3 ./snurisc6.py -l 4 ../pyrisc/asm/sum100
Loading file ../pyrisc/asm/sum100
--------------------------------------------------
0 [IF] 0x80000000: addi   t0, zero, 1            
0 [ID] 0x00000000: BUBBLE                        
0 [RR] 0x00000000: BUBBLE                        
0 [EX] 0x00000000: BUBBLE                        
0 [MM] 0x00000000: BUBBLE                        
0 [WB] 0x00000000: BUBBLE                        
--------------------------------------------------
1 [IF] 0x80000004: addi   t1, zero, 100          
1 [ID] 0x80000000: addi   t0, zero, 1            
1 [RR] 0x00000000: BUBBLE                        
1 [EX] 0x00000000: BUBBLE                        
1 [MM] 0x00000000: BUBBLE                        
1 [WB] 0x00000000: BUBBLE                        
--------------------------------------------------
2 [IF] 0x80000008: addi   t6, zero, 0            
2 [ID] 0x80000004: addi   t1, zero, 100          
2 [RR] 0x80000000: addi   t0, zero, 1            
2 [EX] 0x00000000: BUBBLE                        
2 [MM] 0x00000000: BUBBLE                        
2 [WB] 0x00000000: BUBBLE                        
--------------------------------------------------
...

(cycles omitted)

...
--------------------------------------------------
11 [IF] 0x8000002c: (illegal)                     
11 [ID] 0x80000028: BUBBLE                        
11 [RR] 0x80000024: BUBBLE                        
11 [EX] 0x80000020: BUBBLE                        
11 [MM] 0x8000001c: BUBBLE                        
11 [WB] 0x80000018: ebreak                        
Execution completed
Registers
=========
zero ($0): 0x00000000    ra ($1):   0x00000000    sp ($2):   0x00000000    gp ($3):   0x00000000    
tp ($4):   0x00000000    t0 ($5):   0x00000000    t1 ($6):   0x00000000    t2 ($7):   0x00000000    
s0 ($8):   0x00000000    s1 ($9):   0x00000000    a0 ($10):  0x00000000    a1 ($11):  0x00000000    
a2 ($12):  0x00000000    a3 ($13):  0x00000000    a4 ($14):  0x00000000    a5 ($15):  0x00000000    
a6 ($16):  0x00000000    a7 ($17):  0x00000000    s2 ($18):  0x00000000    s3 ($19):  0x00000000    
s4 ($20):  0x00000000    s5 ($21):  0x00000000    s6 ($22):  0x00000000    s7 ($23):  0x00000000    
s8 ($24):  0x00000000    s9 ($25):  0x00000000    s10 ($26): 0x00000000    s11 ($27): 0x00000000    
t3 ($28):  0x00000000    t4 ($29):  0x00000000    t5 ($30):  0x00000000    t6 ($31):  0x00000000    
Memory 0x80010000 - 0x8001ffff
==============================
7 instructions executed in 12 cycles. CPI = 1.714
Data transfer:    0 instructions (0.00%)
ALU operation:    5 instructions (71.43%)
Control transfer: 2 instructions (28.57%)
```

## Restrictions

* You should not change any files other than `stages.py`. 

* Your `stages.py` file should not contain any `print()` function even in comment lines. Please remove them before you submit your code to the server.

* Your simulator should minimize the number of stalled cycles.

* Your code should finish within a reasonable number of cycles. If your simulator runs beyond the predefined threshold, you will get the `TIMEOUT` error.

* __The number of submissions to the `sys` server will be limited to 50 times__.


## Hand in instructions

* Submit only the `stages.py` file to the submission server.

* Also, submit the design document (in PDF file only) to the submission server.

## Logistics

* You will work on this project alone.

* Only the upload submitted before the deadline will receive the full credit. 25% of the credit will be deducted for every single day delay.

* You can use up to 4 slip days during this semester. If your submission is delayed by 1 day and if you decided to use 1 slip day, there will be no penalty. In this case, you should explicitly declare the number of slip days you want to use in the QnA board of the submission server after each submission.

* Any attempt to copy others' work will result in heavy penalty (for both the copier and the originator). Don't take a risk.


This is the final project. I hope you enjoyed!



---
[Jin-Soo Kim](mailto:jinsoo.kim_AT_snu.ac.kr)  
[Systems Software and Architecture Laboratory](http://csl.snu.ac.kr)  
[Dept. of Computer Science and Engineering](http://cse.snu.ac.kr)  
[Seoul National University](http://www.snu.ac.kr)
