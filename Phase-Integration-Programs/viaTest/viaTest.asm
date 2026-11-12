;   AI usage declaration: ChatGPT, VIA test program and clarification of purpose & functionality for via configuration.
;   Ref. to src: 6502 simulator - https://maksimkorzh.github.io/6502js/
;   Ref. to alt. sim.: https://www.masswerk.at/6502/assembler.html
;   To do:
;   - Create LED flashing program
;     - directs CPU to output LED flashing signal to 65C02 Versatile Interface Adapter (VIA)

!cpu w65c02

PORTB = $6000   ;   via output port (b is default)
DDRB  = $6002   ;   via configuration

* = $8000

viaInit:
    SEI         ;   set maskable interrupts as disabled
    
    ; configure all eight pins as outputs
    LDX #$FF
    STX DDRB

    LDX #$00    ;   clear x register, initializes counter

count:
    STX PORTB   ;   output updated counter. Should start at zero.
    INX         ;   increment x by 1
    JMP count   ;   repeat count

viaFault:
    JMP viaFault    ;   catch unexpected interrupts

!fill $fffa - *, $ea    ;   pad w/ NOPs
!word viaFault          ;   NMI vector
!word viaInit           ;   reset vector
!word viaFault          ;   IRQ/BRK vector