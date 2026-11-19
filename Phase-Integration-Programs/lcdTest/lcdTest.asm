;   to do:
;   - v1: print out a singular character on LCD screen
;   - v2: print out entire string of characters on screen

!cpu w65c02

;   const
PORTB = $6000   ;   via output port for display
PORTA = $6001   ;   via output port for display enable
DDRB = $6002    ;   config via output port b
DDRA = $6003    ;   config via output port a

* = $8000

viaInit:
    SEI         ;   set maskable interrupts as disabled
    
    ; config all eight pins as outputs
    LDX #$FF
    STX DDRB

    ;   config pins 5-7 (designated to RS, RW, E) as outputs
    LDX #$E0
    STX DDRA

    LDX #$00    ;   clear x register, initializes counter

lcdInit:
    ;   CLR DISPLAY
 
    LDA #$00
    STA PORTA
    LDA #$3F
    STA PORTB

lcdFault:
    JMP lcdFault    ;   trap unexpected interrupts

;   Pad the ROM and place the interrupt/reset vectors.
!fill $fffa - *, $ea    ;   pad w/ NOPs
!word lcdFault          ;   NMI vector
!word lcdInit           ;   reset vector
!word lcdFault          ;   IRQ/BRK vector