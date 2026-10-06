"""Baby Computer bus monitor for a Raspberry Pi Pico W.

The monitor reads four parallel-in/serial-out adapters simultaneously:

    GP3 <- address A0-A7 adapter serial output
    GP4 <- address A8-A15 adapter serial output
    GP5 <- data D0-D7 adapter serial output
    GP6 <- VIA/control adapter serial output
    GP7 -> shared shift clock
    GP8 -> shared active-low parallel load (/PL)
    GP2 <- level-shifted W65C02 PHI2

This first version is intended for a deliberately slow W65C02 clock. It prints
the captured transactions through the Pico's USB connection.
"""

from machine import Pin
import time


# Pico connections
PHI2 = Pin(2, Pin.IN)

ADDRESS_LOW_SERIAL = Pin(3, Pin.IN)
ADDRESS_HIGH_SERIAL = Pin(4, Pin.IN)
DATA_SERIAL = Pin(5, Pin.IN)
CONTROL_SERIAL = Pin(6, Pin.IN)

SHIFT_CLOCK = Pin(7, Pin.OUT, value=0)
PARALLEL_LOAD_N = Pin(8, Pin.OUT, value=1)

SERIAL_INPUTS = (
    ADDRESS_LOW_SERIAL,
    ADDRESS_HIGH_SERIAL,
    DATA_SERIAL,
    CONTROL_SERIAL,
)


# Control-adapter bit assignments. Wire the adapter's parallel inputs so the
# resulting byte uses this layout. Names ending in _N are active-low signals.
RWB_BIT = 0
SYNC_BIT = 1
VIA_CS_N_BIT = 2
ROM_CS_N_BIT = 3
RAM_CS_N_BIT = 4
RESB_BIT = 5
IRQB_BIT = 6
RDY_BIT = 7


# A small starter table. More W65C02 opcodes can be added later.
OPCODES = {
    0x00: "BRK",
    0x20: "JSR abs",
    0x40: "RTI",
    0x4C: "JMP abs",
    0x60: "RTS",
    0x69: "ADC #imm",
    0x8D: "STA abs",
    0xA0: "LDY #imm",
    0xA2: "LDX #imm",
    0xA9: "LDA #imm",
    0xD0: "BNE rel",
    0xEA: "NOP",
    0xF0: "BEQ rel",
}


def bit_is_set(value, bit_number):
    return bool(value & (1 << bit_number))


def pulse_shift_clock():
    """Shift every adapter by one bit using their shared clock."""
    SHIFT_CLOCK.value(1)
    time.sleep_us(1)
    SHIFT_CLOCK.value(0)
    time.sleep_us(1)


def load_parallel_snapshot():
    """Copy all four stable parallel bytes into the adapters together."""
    SHIFT_CLOCK.value(0)
    PARALLEL_LOAD_N.value(0)
    time.sleep_us(1)
    PARALLEL_LOAD_N.value(1)
    time.sleep_us(1)


def read_four_adapters():
    """Return address-low, address-high, data and control bytes.

    The H input of each 74HCT165 appears first at QH. Wire bit 7 to H,
    bit 6 to G, ... and bit 0 to A. If a module uses the reverse order,
    either reverse its parallel wiring or reverse the byte in software.
    """
    load_parallel_snapshot()
    values = [0, 0, 0, 0]

    for bit_index in range(8):
        for input_index, serial_pin in enumerate(SERIAL_INPUTS):
            values[input_index] = (
                (values[input_index] << 1) | serial_pin.value()
            )

        # The last pulse is harmless and leaves every adapter ready for the
        # next parallel load.
        pulse_shift_clock()

    return values[0], values[1], values[2], values[3]


def selected_device(control):
    """Decode active-low chip-select signals from the control byte."""
    if not bit_is_set(control, VIA_CS_N_BIT):
        return "VIA"
    if not bit_is_set(control, ROM_CS_N_BIT):
        return "EEPROM"
    if not bit_is_set(control, RAM_CS_N_BIT):
        return "RAM"
    return "none"


def format_transaction(cycle, address, data, control):
    read_cycle = bit_is_set(control, RWB_BIT)
    opcode_fetch = bit_is_set(control, SYNC_BIT) and read_cycle

    direction = "R" if read_cycle else "W"
    device = selected_device(control)

    if opcode_fetch:
        decoded = OPCODES.get(data, "unknown opcode")
        detail = "OPCODE " + decoded
    else:
        detail = "data"

    return (
        "{0:06d}  A=${1:04X}  D=${2:02X}  {3}  "
        "{4:<6}  {5:<18}  CTRL={6:08b}"
    ).format(cycle, address, data, direction, device, detail, control)


def wait_for_phi2_falling_edge():
    """Poll for PHI2's falling edge; suitable only for a slow CPU clock."""
    while PHI2.value() == 0:
        pass
    while PHI2.value() == 1:
        pass


def main():
    print("Baby Computer four-channel bus monitor")
    print("Waiting for PHI2; output is sent through USB serial.")
    print("CYCLE   ADDRESS  DATA  R/W  DEVICE  INTERPRETATION      CONTROL")

    cycle = 0

    while True:
        wait_for_phi2_falling_edge()

        # The external HCT573 latches should now be holding a stable snapshot.
        address_low, address_high, data, control = read_four_adapters()
        address = (address_high << 8) | address_low

        cycle += 1
        print(format_transaction(cycle, address, data, control))


main()
