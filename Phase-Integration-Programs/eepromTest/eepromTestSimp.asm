;   AI usage declaration: ChatGPT, EEPROM test program and clarification of purpose and functionality.
;   Ref. to src: 6502 simulator - https://maksimkorzh.github.io/6502js/
;   Ref. to alt. sim.: https://www.masswerk.at/6502/assembler.html
;   TODO:
;   -   Add program origin memory location
;   -   Set X register  to act as LED blinker via jmp
;   -   Pad file to fit ROM size
;   -   Compile and test using ACME cross-assembler
 
!cpu w65c02 ;   Declare CPU type
* = $8000   ;   Set origin to addr. 8000
 
reset: 
    JMP reset
    
; Pad the ROM and place the interrupt/reset vectors.
!fill $fffa - *, $ea    ;   pad w/ NOPs
!word reset             ;   IRQ/BRK vector
!word reset             ;
!word reset             ;