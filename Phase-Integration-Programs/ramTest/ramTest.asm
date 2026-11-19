;   Status: INCOMPLETE
;
;   TODO:
;     - Assign port outputs for ram retrieval indicator
;     - Store test pattern in memory
;     - Load pattern in new register
;     - Compare register to stored value
;     - Output result to via

!cpu w65c02

;   const
PORTB = $6000   ;   via output port (b is default)
DDRB  = $6002   ;   via configuration
* = $8000


;jsr and rts
ramInit:
    SEI         ;   set maskable interrupts as disabled
    
    ; configure all eight pins as outputs
    LDX #$FF
    STX DDRB

    LDX #$00    ;   clear x register

ramTest:
    
;ramTest:
;    LDA #$AA    ;   test pattern 10101010
;    STA 

memorySuccessful:
    LDY #$FF    ;   LED pattern 11111111
    JMP viaOutput

memoryFailed:
    LDY #$EA    ;   LED pattern 11101010
    JMP viaOutput

viaOutput:
    STY PORTB   ;   Output result via LED pattern.

ramFault:
    JMP ramFault    ;   trap unexpected interrupts

;   Pad the ROM and place the interrupt/reset vectors.
!fill $fffa - *, $ea    ;   pad w/ NOPs
!word ramFault          ;   NMI vector
!word ramInit           ;   reset vector
!word ramFault          ;   IRQ/BRK vector