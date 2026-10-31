# JC8012P4A1C_I_W_Y_CAN
JC8012P4A1C_I_W_Y addon PCB for CAN-Bus

ISOBUS / CAN interface (250 kbit/s) for the Guition JC8012P4A1C (ESP32-P4, 10.1")
display, used by [espVT](https://github.com/Meisterschulen-am-Ostbahnhof-Munchen/espVT).
The board is mounted on the back of the display board and powered from the 12 V
board net. It also supplies 5 V to the display board.

KiCad 10 project. Project-local libraries are in `lib/`.

## Connections

| Connector | Part | Purpose |
|---|---|---|
| J1 | Würth WR-PHD 610110249121 (2×5 pin header, SMT, right angled) | ribbon cable to IDC D-Sub 9 female Würth 618009221923 |
| J2 | Würth WR-FPC 68711414522 (14 pin, 0.5 mm) | FFC to FPC3 "EXTEND1" of the display board |
| J3 | Würth WR-WTB 653104131822 (4 pin, 1.25 mm) | 5 V to CN2 of the display board |

### D-Sub 9 (via ribbon cable on J1)

Pinout of the Müller-Elektronik BASIC-Terminal CAN-ISO connector. It fits the
adapter cable 481595 (D-Sub 9 male to In-Cab CPC-9 female).

| D-Sub | J1 | Signal |
|---|---|---|
| 1 | 1 | CAN_L |
| 2 | 3 | CAN_L |
| 3 | 5 | TBC_GND (see R8) |
| 4 | 7 | CAN_H |
| 5 | 9 | TBC_PWR_in (not used) |
| 6 | 2 | ECU_GND |
| 7 | 4 | CAN_H |
| 8 | 6 | TBC_PWR_out |
| 9 | 8 | ECU_PWR (12 V board net) |
| – | 10 | not used |

CAN_L (1/2) and CAN_H (4/7) are connected on the board to loop the bus through.

**Polarisation:** J1 has no shroud (an 8 mm high part is the maximum under
the cover, a box header with IDC socket would be too high). To prevent the
IDC socket from being plugged in turned by 180°, cut off pin 10 of J1 and
close position 10 of the IDC socket with a coding plug. Pins 9 and 10 are
not used. Plugged in turned, the bus TBC_PWR and ECU_PWR (12 V) would end up
on the board GND and CAN_L.

## Mechanics

- All parts on the top side (SMT only), nothing on the bottom side
- Stack height: cover 14 mm − display board 1.5 mm − M2 standoffs 3 mm −
  addon board 1.5 mm ≈ 8 mm free above the addon board
- Mounting holes M2 (2.2 mm, plated, GND) on the 58 × 46 mm grid of the
  display board standoffs S1–S4 (H1 = S1, H2 = S4, H3 = S2, H4 = S3)
- Notches for CN5 (pin header), the 100 µF capacitor next to S4 and the
  CR1220 RTC holder of the display board

### FPC3 (J2)

| Pin | Signal |
|---|---|
| 1, 2 | GND |
| 7 | CAN_RXD (GPIO5) |
| 8 | CAN_TXD (GPIO4) |
| 9 | CAN_NEN (GPIO3, 10k pull-down: transceiver active by default) |
| 13, 14 | +3V3 (VDDA, transceiver VIO) |

FFC: 14 pin, 0.5 mm pitch, **type B (contacts on opposite sides)**.
The cable leaves FPC3 towards the board edge, makes one 180° turn and enters
J2 from the edge of the addon board. Both connectors are bottom-contact ZIF
with the same orientation (opening towards the edge, pin 1 on the right
side seen from the back of the display, next to the TF card), so pin 1
connects to pin 1. A type A cable would have its contacts facing up at J2;
turning it over to make it fit reverses the pin order and swaps GND (1/2)
and 3V3 (13/14).

## Termination

ISO 11783-2 ECU Type I WEAK: split termination 750 Ω + 750 Ω with 47 nF to GND.

## TBC power output and R8

Like the BASIC-Terminal, the board supplies power for the terminating bias
circuits (TBC) on D-Sub pin 8 (TBC_PWR_out): board net minus about 0.4 V
(Schottky diode D4), limited by PTC F2 (0.14 A). Some harnesses do not start
without it.

**R8 (0 Ω, TBC_GND to GND) is not fitted (DNP) by default.** This keeps
TBC_GND isolated, which is the compatible default. If a harness needs a
TBC_GND return for its terminator, fit R8 with a 0 Ω resistor (0603).

## Power

- 12 V board net only (ECU_PWR), fuse F1 1 A slow
- Bidirectional TVS Würth 824551241 (SMDJ24CA), clamping ≤ 38.9 V
- Reverse polarity protection: dual P-MOSFET Vishay Si4948BEY (SO-8), both
  halves in parallel, 15 V gate zener. Drop-in for the KiCad symbol
  DMP6050SSD (same SO-8 pinout S1 G1 S2 G2 D2 D2 D1 D1), which is used as
  the schematic symbol.
- Buck converter Würth MagI³C 171030601: 5 V / 3 A for the transceiver and the display board
