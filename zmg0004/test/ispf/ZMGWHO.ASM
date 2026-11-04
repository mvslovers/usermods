ZMGWHO   TITLE 'ZMGWHO - SHOW TCB, ECT AND INPUT STACK OF THE CALLER'
*
*  TEST ONLY.  RUN AS A TSO COMMAND.  TPUTS ONE LINE:
*    T  = CURRENT TCB (PSATOLD)
*    P  = ITS PARENT TCB, G = THE PARENT OF THAT
*    L  = THE ECT OF THE SESSION (LWAPECT)
*    C  = THE ECT THE COMMAND WAS GIVEN (CPPLECT)
*    E  = ECT+X'30' (ECTENVBK) OF C
*    I  = ECTIOWA OF C (IOSRL)
*    S  = TOP INPUT STACK ELEMENT (IOSTELM)
*    N  = NUMBER OF ELEMENTS (IOSNELM)
*    F  = FIRST BYTE OF THE TOP ELEMENT (INSCODE)
*
ZMGWHO   CSECT
         STM   14,12,12(13)
         LR    12,15
         USING ZMGWHO,12
         LA    11,SAVE
         ST    13,4(,11)
         LR    13,11
         LR    2,1                 R2 -> CPPL
         L     0,X'21C'            PSATOLD
         LA    3,OT
         BAL   14,HEX
         L     7,X'21C'            PSATOLD
         L     7,X'84'(,7)         TCBOTC
         LR    0,7
         LA    3,OP
         BAL   14,HEX
         L     7,X'84'(,7)         TCBOTC OF THE PARENT
         LR    0,7
         LA    3,OG
         BAL   14,HEX
         L     1,X'224'            PSAAOLD
         L     1,X'6C'(,1)         ASCBASXB
         L     1,X'14'(,1)         ASXBLWA
         L     0,32(,1)            LWAPECT
         LA    3,OL
         BAL   14,HEX
         L     4,12(,2)            CPPLECT
         LR    0,4
         LA    3,OC
         BAL   14,HEX
         L     0,X'30'(,4)         ECTENVBK
         LA    3,OE
         BAL   14,HEX
         L     5,4(,4)             ECTIOWA
         LA    5,0(,5)
         LR    0,5
         LA    3,OI
         BAL   14,HEX
         L     6,0(,5)             IOSTELM
         LA    6,0(,6)
         LR    0,6
         LA    3,OS
         BAL   14,HEX
         LH    0,10(,5)            IOSNELM
         LA    3,ON
         BAL   14,HEX
         SLR   0,0
         IC    0,0(,6)             INSCODE
         LA    3,OF
         BAL   14,HEX
         TPUT  OUT,OUTL
         L     13,4(,13)
         LM    14,12,12(13)
         SLR   15,15
         BR    14
HEX      ST    0,HEXW
         UNPK  HEXO(9),HEXW(5)
         LA    1,HEXT
         SH    1,=H'240'
         TR    HEXO(8),0(1)
         MVC   0(8,3),HEXO
         BR    14
HEXT     DC    C'0123456789ABCDEF'
SAVE     DS    18F
HEXW     DS    F
         DS    X
HEXO     DS    CL9
OUT      DS    0C
         DC    C'WHO T='
OT       DC    CL8' '
         DC    C' P='
OP       DC    CL8' '
         DC    C' G='
OG       DC    CL8' '
         DC    C' L='
OL       DC    CL8' '
         DC    C' C='
OC       DC    CL8' '
         DC    C' E='
OE       DC    CL8' '
         DC    C' I='
OI       DC    CL8' '
         DC    C' S='
OS       DC    CL8' '
         DC    C' N='
ON       DC    CL8' '
         DC    C' F='
OF       DC    CL8' '
OUTL     EQU   *-OUT
         END   ZMGWHO
