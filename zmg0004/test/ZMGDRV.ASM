ZMGDRV   TITLE 'ZMG0004 TEST DRIVER FOR IKJCT441'
*
*  NAME        - ZMGDRV
*
*  FUNCTION    - DRIVES IKJCT441 FROM A TSO COMMAND PROCESSOR IN A
*                (BATCH) TMP AND REPORTS EVERY RESULT WITH WTO.
*
*                OPERANDS C AND D: CLIST REGRESSION.  RUN FROM A
*                  CLIST THAT SETS TESTV=HELLOWORLD AND X1=ONE,
*                  EACH IN A TMP STEP OF ITS OWN.  C RUNS THE
*                  SEQUENCE AGAINST THE INSTALLED IKJCT441, D
*                  AGAINST THE TEST COPY ZMGT441; THE LINES MUST
*                  AGREE APART FROM THE MODULE NAME.
*                OPERAND R: REXX PATH, OUTSIDE ANY CLIST, AGAINST A
*                  STAND-IN REXX ENVIRONMENT (ENVBLOCK, IRXEXTE AND
*                  THE VARIABLE ROUTINE FAKEXCOM BELOW).
*                OPERAND O: WHICH PATH WINS INSIDE A CLIST, WITH THE
*                  STAND-IN ENVIRONMENT RECORDING THE CURRENT TOP
*                  ELEMENT (REXX) OR ANOTHER ONE (CLIST).
*
*  NOT REENTRANT.  TEST CODE, NOT SHIPPED.
*
R0       EQU   0
R1       EQU   1
R2       EQU   2
R3       EQU   3
R4       EQU   4
R5       EQU   5
R6       EQU   6
R7       EQU   7
R8       EQU   8
R9       EQU   9
R10      EQU   10
R11      EQU   11
R12      EQU   12
R13      EQU   13
R14      EQU   14
R15      EQU   15
ZMGDRV   CSECT
         STM   R14,R12,12(R13)
         LR    R12,R15
         USING ZMGDRV,R12
         LA    R11,2048(,R12)
         LA    R11,2048(,R11)
         USING ZMGDRV+4096,R11
         LR    R10,R1              R10 -> CPPL
         LA    R15,SAVE
         ST    R13,4(,R15)
         ST    R15,8(,R13)
         LR    R13,R15
         L     R1,12(,R10)         CPPLECT
         ST    R1,ECTA
         L     R2,4(,R1)           ECTIOWA
         MVC   TOPEL,0(R2)         IOSTELM NOW
         L     R2,0(,R10)          CPPLCBUF
         LH    R3,2(,R2)           OFFSET OF THE OPERANDS
         LA    R3,4(R3,R2)         FIRST OPERAND CHARACTER
         CLI   0(R3),C'C'
         BE    TESTC
         CLI   0(R3),C'D'
         BE    TESTD
         CLI   0(R3),C'R'
         BE    TESTR
         CLI   0(R3),C'O'
         BE    TESTO
         MVC   LTXT(20),=CL20'ZMGDRV BAD OPERAND'
         BAL   R14,PRT
         B     EXIT
         TITLE 'CLIST REGRESSION'
TESTC    MVC   EP,=CL8'IKJCT441'   THE INSTALLED MODULE
         BAL   R9,CSEQ
         B     EXIT
TESTD    MVC   EP,=CL8'ZMGT441'    THE TEST COPY
         BAL   R9,CSEQ
         B     EXIT
*
*  CSEQ - ONE CLIST SEQUENCE AGAINST MODULE EP.  RETURN VIA R9.
*
CSEQ     MVC   TID,=CL3'C1'        RETRIEVE TESTV
         LA    R2,18
         LA    R3,NTESTV
         LA    R4,5
         SR    R5,R5
         SR    R6,R6
         BAL   R14,CALL
         BAL   R14,REPORT
         MVC   TID,=CL3'C2'        UPDATE TESTV, RETRIEVE AGAIN
         LA    R2,2
         LA    R3,NTESTV
         LA    R4,5
         LA    R5,VCHG
         LA    R6,7
         BAL   R14,CALL
         BAL   R14,REPORT
         LA    R2,18
         LA    R3,NTESTV
         LA    R4,5
         SR    R5,R5
         SR    R6,R6
         BAL   R14,CALL
         BAL   R14,REPORT
         MVC   TID,=CL3'C3'        RETRIEVE A NAME NOT DEFINED
         LA    R2,18
         LA    R3,NNOSUCH
         LA    R4,6
         SR    R5,R5
         SR    R6,R6
         BAL   R14,CALL
         BAL   R14,REPORT
         MVC   TID,=CL3'C5'        RETRIEVE/CREATE A NEW NAME
         LA    R2,1
         LA    R3,NNEWVAR
         LA    R4,6
         LA    R5,VMADE
         LA    R6,4
         BAL   R14,CALL
         BAL   R14,REPORT
         LA    R2,18
         LA    R3,NNEWVAR
         LA    R4,6
         SR    R5,R5
         SR    R6,R6
         BAL   R14,CALL
         BAL   R14,REPORT
         MVC   TID,=CL3'C6'        UPDATE WITH A LONGER VALUE
         LA    R2,2
         LA    R3,NTESTV
         LA    R4,5
         LA    R5,VLONG
         LA    R6,20
         BAL   R14,CALL
         BAL   R14,REPORT
         LA    R2,18
         LA    R3,NTESTV
         LA    R4,5
         SR    R5,R5
         SR    R6,R6
         BAL   R14,CALL
         BAL   R14,REPORT
         MVC   TID,=CL3'C4'        LOCATE ALL
         BAL   R14,LOCALL
         BR    R9
         TITLE 'REXX PATH'
TESTR    MVC   EP,=CL8'ZMGT441'
         MVC   TID,=CL3'R0'        NO CLIST, NO REXX: RC=40
         LA    R2,18
         LA    R3,NTESTV
         LA    R4,5
         SR    R5,R5
         SR    R6,R6
         BAL   R14,CALL
         BAL   R14,REPORT
         MVC   FENVTOP,TOPEL       THE EXEC STARTED WITH THIS TOP
         BAL   R14,ENVON
         MVC   TID,=CL3'R1'        LOCATE ALL: A, BB, ISPVAR, RC=20
         BAL   R14,LOCALL
         MVC   TID,=CL3'R2'        UPDATE ISPVAR, LOCATE ALL AGAIN
         LA    R2,2
         LA    R3,NISPVAR
         LA    R4,6
         LA    R5,VWORLD
         LA    R6,5
         BAL   R14,CALL
         BAL   R14,REPORT
         BAL   R14,LOCALL
         MVC   TID,=CL3'R3'        UPDATE A NEW VARIABLE
         LA    R2,2
         LA    R3,NNEWV
         LA    R4,4
         LA    R5,VCHG
         LA    R6,7
         BAL   R14,CALL
         BAL   R14,REPORT
         BAL   R14,LOCALL
         MVC   TID,=CL3'R4'        RETRIEVE: RC=40 FOR NOW
         LA    R2,18
         LA    R3,NISPVAR
         LA    R4,6
         SR    R5,R5
         SR    R6,R6
         BAL   R14,CALL
         BAL   R14,REPORT
         MVC   TID,=CL3'R5'        NAME LENGTH 0: RC=36
         LA    R2,2
         LA    R3,NISPVAR
         SR    R4,R4
         LA    R5,VWORLD
         LA    R6,5
         BAL   R14,CALL
         BAL   R14,REPORT
         MVC   TID,=CL3'R6'        STALE TOP ELEMENT: CLIST PATH, 40
         MVC   FENVTOP,=F'1'
         LA    R2,2
         LA    R3,NISPVAR
         LA    R4,6
         LA    R5,VWORLD
         LA    R6,5
         BAL   R14,CALL
         BAL   R14,REPORT
         BAL   R14,ENVOFF
         BAL   R14,FAKESUM
         B     EXIT
         TITLE 'WHICH PATH WINS INSIDE A CLIST'
TESTO    MVC   EP,=CL8'ZMGT441'
         MVC   FENVTOP,TOPEL       REXX STARTED ON TOP OF THE CLIST
         BAL   R14,ENVON
         MVC   TID,=CL3'O1'        EXPECT A FROM THE STAND-IN
         XC    TOKEN,TOKEN
         LA    R2,3
         LA    R3,0
         LA    R4,0
         SR    R5,R5
         SR    R6,R6
         BAL   R14,CALL
         BAL   R14,REPORT
         BAL   R14,LOCDONE         FINISH THE SEQUENCE
         MVC   FENVTOP,=F'1'       A CLIST CAME ON TOP OF THE EXEC
         MVC   TID,=CL3'O2'        EXPECT TESTV FROM THE CLIST
         LA    R2,18
         LA    R3,NTESTV
         LA    R4,5
         SR    R5,R5
         SR    R6,R6
         BAL   R14,CALL
         BAL   R14,REPORT
         BAL   R14,ENVOFF
         BAL   R14,FAKESUM
         B     EXIT
         TITLE 'SUBROUTINES'
*
*  LOCALL - LOCATE ALL UNTIL RC 16 OR MORE (AT MOST 200 CALLS).
*  LOCDONE - THE SAME WITHOUT REPORTS, TO END A SEQUENCE.
*
LOCALL   ST    R14,LOCR14
         MVI   LOCQUIET,0
         B     LOCGO
LOCDONE  ST    R14,LOCR14
         MVI   LOCQUIET,1
LOCGO    LA    R8,200
         CLI   LOCQUIET,1          CONTINUE AN OPEN SEQUENCE?
         BE    LOCLP               YES, KEEP THE TOKEN
         XC    TOKEN,TOKEN
LOCLP    DS    0H
         LA    R2,3
         SR    R3,R3
         SR    R4,R4
         SR    R5,R5
         SR    R6,R6
         BAL   R14,CALL
         CLI   LOCQUIET,1
         BE    *+8
         BAL   R14,REPORT
         L     R15,LASTRC          RC 4, 8, 12 ONLY DESCRIBE THE
         LTR   R15,R15             VARIABLE; 16 AND UP OR A
         BM    LOCEND              NEGATIVE ONE END THE SEQUENCE
         C     R15,=F'16'
         BNL   LOCEND
         BCT   R8,LOCLP
LOCEND   DS    0H
         MVC   LTXT(30),=CL30'    TOKEN AFTER THE SEQUENCE'
         LA    R1,TOKEN
         LA    R2,LTXT+30
         BAL   R14,HEX
         CLI   LOCQUIET,1
         BE    *+8
         BAL   R14,PRT
         L     R14,LOCR14
         BR    R14
*
*  CALL - CALL MODULE EP.  R2 ECODE, R3 -> NAME, R4 NAME LENGTH,
*  R5 -> VALUE, R6 VALUE LENGTH.  TOKEN IS KEPT BETWEEN CALLS.
*
CALL     ST    R14,CALLR14
         ST    R2,PECODE
         ST    R3,PNAMEP
         ST    R4,PNAMEL
         ST    R5,PVALP
         ST    R6,PVALL
         MVC   PLIST+24(4),ECTA    PARAMETER 7 IS THE ECT ITSELF
         MVC   LASTRC,=F'-1'
         LA    R1,PLIST
         LINK  EPLOC=EP
         ST    R15,LASTRC
         CLI   PECODE+3,3          LOCATE ALL KEEPS ITS TOKEN
         BE    CALLX
         XC    TOKEN,TOKEN
CALLX    L     R14,CALLR14
         BR    R14
*
*  REPORT - ONE LINE: TID EP RC NAME=VALUE
*
REPORT   ST    R14,REPR14
         MVI   LTXT,C' '
         MVC   LTXT+1(L'LTXT-1),LTXT
         MVC   LTXT(3),TID
         MVC   LTXT+4(8),EP
         MVC   LTXT+13(3),=C'RC='
         L     R1,LASTRC
         CVD   R1,DWORK
         UNPK  LTXT+16(3),DWORK+6(2)
         OI    LTXT+18,X'F0'
         L     R1,LASTRC           RC 0-12: NAME AND VALUE ARE SET
         LTR   R1,R1
         BM    REPOUT
         C     R1,=F'16'
         BNL   REPOUT
         L     R1,PNAMEL           NAME
         LTR   R1,R1
         BNP   REPVAL
         CH    R1,=H'16'
         BNH   *+8
         LA    R1,16
         BCTR  R1,0
         L     R2,PNAMEP
         EX    R1,MVNAME
REPVAL   MVI   LTXT+37,C'='
         L     R1,PVALL            VALUE
         LTR   R1,R1
         BNP   REPOUT
         CH    R1,=H'20'
         BNH   *+8
         LA    R1,20
         BCTR  R1,0
         L     R2,PVALP
         EX    R1,MVVAL
REPOUT   BAL   R14,PRT
         L     R14,REPR14
         BR    R14
MVNAME   MVC   LTXT+21(0),0(R2)
MVVAL    MVC   LTXT+38(0),0(R2)
*
*  ENVON / ENVOFF - INSTALL AND REMOVE THE STAND-IN ENVIRONMENT
*
ENVON    L     R1,ECTA
         MVC   OLDENV,X'30'(R1)
         LA    R0,FENV
         ST    R0,X'30'(,R1)
         BR    R14
ENVOFF   L     R1,ECTA
         MVC   X'30'(4,R1),OLDENV
         BR    R14
*
*  FAKESUM - REPORT THE CALLS THE STAND-IN SAW AND ITS CHECKS
*
FAKESUM  ST    R14,SUMR14
         MVI   LTXT,C' '
         MVC   LTXT+1(L'LTXT-1),LTXT
         MVC   LTXT(18),=C'FAKEXCOM CALLS/BAD'
         LA    R1,FKCALLS
         LA    R2,LTXT+20
         BAL   R14,HEX
         LA    R1,FKBAD
         LA    R2,LTXT+30
         BAL   R14,HEX
         BAL   R14,PRT
         L     R14,SUMR14
         BR    R14
*
*  HEX - R1 -> FULLWORD, R2 -> 8 BYTES OF TEXT
*
HEX      UNPK  HWORK(9),0(5,R1)
         TR    HWORK(8),HTAB-240
         MVC   0(8,R2),HWORK
         BR    R14
*
*  PRT - WTO THE LINE IN LTXT AND CLEAR IT
*
PRT      ST    R14,PRTR14
         LA    R1,WLIST
         SR    R0,R0
         SVC   35
         MVI   LTXT,C' '
         MVC   LTXT+1(L'LTXT-1),LTXT
         L     R14,PRTR14
         BR    R14
EXIT     L     R13,4(,R13)
         LM    R14,R12,12(R13)
         SR    R15,R15
         BR    R14
         TITLE 'STAND-IN VARIABLE ROUTINE'
*
*  FAKEXCOM - IRXEXCOM CONTRACT OVER A SMALL TABLE.  CHECKS THE
*  CALL: PARAMETER 1 IS C'IRXEXCOM', R0 IS THE ENVBLOCK, THE 4TH
*  ENTRY ENDS THE LIST.  SUPPORTS 'S' AND 'N'; ANY REQUEST OTHER
*  THAN 'N' RESTARTS THE 'N' SEQUENCE.
*
FAKEXCOM STM   R14,R12,12(R13)
         BALR  R9,0
         USING *,R9
         L     R12,FKBASE
         B     FKBASEX
FKBASE   DC    A(ZMGDRV)
FKBASEX  DS    0H
         DROP  R9
         LA    R11,2048(,R12)
         LA    R11,2048(,R11)
         L     R2,FKCALLS
         LA    R2,1(,R2)
         ST    R2,FKCALLS
         L     R2,0(,R1)           PARAMETER 1
         CLC   0(8,R2),=C'IRXEXCOM'
         BNE   FKBADC
         C     R0,=A(FENV)
         BNE   FKBADC
         TM    12(R1),X'80'        4TH ENTRY IS THE LAST
         BO    FKOK
FKBADC   L     R2,FKBAD
         LA    R2,1(,R2)
         ST    R2,FKBAD
FKOK     L     R3,12(,R1)          R3 -> SHVBLOCK
         LA    R3,0(,R3)
         MVI   9(R3),0             SHVRET
         CLI   8(R3),C'N'
         BE    FKNEXT
         XC    FKITER,FKITER       ANYTHING ELSE RESTARTS 'N'
         CLI   8(R3),C'S'
         BE    FKSTORE
         MVI   9(R3),X'80'         SHVBADF
         B     FKRET
FKSTORE  L     R4,X'14'(,R3)       SHVNAML
         LTR   R4,R4
         BNP   FKBADN
         CH    R4,=H'8'
         BH    FKBADN
         L     R5,X'10'(,R3)       SHVNAMA
         LA    R6,FKTAB
         L     R7,FKCOUNT
         LTR   R7,R7
         BZ    FKADD
FKFIND   CH    R4,0(,R6)
         BNE   FKFNEXT
         BCTR  R4,0
         EX    R4,FKCLC
         LA    R4,1(,R4)
         BE    FKSET
FKFNEXT  LA    R6,FKSLOT(,R6)
         BCT   R7,FKFIND
FKADD    L     R7,FKCOUNT          ADD A SLOT
         CH    R7,=H'6'
         BNL   FKBADN
         LA    R7,1(,R7)
         ST    R7,FKCOUNT
         STH   R4,0(,R6)
         MVC   2(8,R6),=CL8' '
         BCTR  R4,0
         EX    R4,FKMVN
         MVI   9(R3),X'01'         SHVNEWV
FKSET    L     R4,X'1C'(,R3)       SHVVALL
         CH    R4,=H'16'
         BNH   *+8
         LA    R4,16
         STH   R4,10(,R6)
         LTR   R4,R4
         BZ    FKRET
         L     R5,X'18'(,R3)       SHVVALA
         BCTR  R4,0
         EX    R4,FKMVV
         B     FKRET
FKBADN   MVI   9(R3),X'08'         SHVBADN
         B     FKRET
FKNEXT   L     R7,FKITER
         C     R7,FKCOUNT
         BL    FKNGO
         XC    FKITER,FKITER
         MVI   9(R3),X'02'         SHVLVAR
         B     FKRET
FKNGO    LA    R6,FKSLOT
         MR    R6,R6               R7 * SLOT SIZE (R6/R7 PAIR)
         LA    R6,FKTAB(R7)
         L     R7,FKITER
         LA    R7,1(,R7)
         ST    R7,FKITER
         LH    R4,0(,R6)           NAME LENGTH
         C     R4,4(,R3)           FITS SHVUSER?
         BH    FKTRUNC
         ST    R4,X'14'(,R3)       SHVNAML
         L     R5,X'10'(,R3)
         BCTR  R4,0
         EX    R4,FKGETN
         LH    R4,10(,R6)          VALUE LENGTH
         C     R4,X'0C'(,R3)       FITS SHVBUFL?
         BH    FKTRUNC
         ST    R4,X'1C'(,R3)       SHVVALL
         LTR   R4,R4
         BZ    FKRET
         L     R5,X'18'(,R3)
         BCTR  R4,0
         EX    R4,FKGETV
         B     FKRET
FKTRUNC  MVI   9(R3),X'04'         SHVTRUNC
FKRET    LM    R14,R12,12(R13)
         SR    R15,R15
         BR    R14
FKCLC    CLC   2(0,R6),0(R5)
FKMVN    MVC   2(0,R6),0(R5)
FKMVV    MVC   12(0,R6),0(R5)
FKGETN   MVC   0(0,R5),2(R6)
FKGETV   MVC   0(0,R5),12(R6)
         TITLE 'DATA'
SAVE     DS    18F
DWORK    DS    D
ECTA     DS    A
TOPEL    DS    A
OLDENV   DS    A
LASTRC   DS    F
EP       DS    CL8
TID      DS    CL3
LOCQUIET DS    X
LOCR14   DS    A
CALLR14  DS    A
REPR14   DS    A
SUMR14   DS    A
PRTR14   DS    A
HWORK    DS    CL9
HTAB     DC    C'0123456789ABCDEF'
WLIST    DC    AL2(4+L'LTXT),AL2(0)
LTXT     DC    CL64' '
PLIST    DC    A(PECODE,PNAMEP,PNAMEL,PVALP,PVALL,TOKEN,0)
         DC    X'80',AL3(PRCODE)
PECODE   DS    F
PNAMEP   DS    A
PNAMEL   DS    F
PVALP    DS    A
PVALL    DS    F
TOKEN    DC    F'0'
PRCODE   DS    F
NTESTV   DC    C'TESTV'
NNOSUCH  DC    C'NOSUCH'
NISPVAR  DC    C'ISPVAR'
NNEWV    DC    C'NEWV'
VHELLO   DC    C'HELLOWORLD'
VCHG     DC    C'CHANGED'
VWORLD   DC    C'WORLD'
NNEWVAR  DC    C'NEWVAR'
VMADE    DC    C'MADE'
VLONG    DC    C'ABCDEFGHIJKLMNOPQRST'
*
*  STAND-IN REXX ENVIRONMENT
*
         DS    0F
FENV     DC    CL8'ENVBLOCK',CL4'0100',F'320'
         DC    A(0,0,0,FEXTE)      PARMBLOCK, USER, WORKBLOK, IRXEXTE
         DC    68F'0'              UP TO +X'130'
FENVTOP  DC    F'0'                +X'130'
         DC    XL12'00'
FEXTE    DC    F'4',A(0,0,0,FAKEXCOM)  IRXEXCOM AT +X'10'
FKCALLS  DC    F'0'
FKBAD    DC    F'0'
FKITER   DC    F'0'
FKCOUNT  DC    F'3'
FKSLOT   EQU   28                  H NAMELEN, CL8 NAME, H VALLEN, CL16
FKTAB    DC    H'1',CL8'A',H'1',CL16'1'
         DC    H'2',CL8'BB',H'2',CL16'22'
         DC    H'6',CL8'ISPVAR',H'5',CL16'HELLO'
         DC    3XL28'00'
         LTORG
         END   ZMGDRV
