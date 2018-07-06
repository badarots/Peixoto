EESchema Schematic File Version 2
LIBS:power
LIBS:device
LIBS:switches
LIBS:relays
LIBS:motors
LIBS:transistors
LIBS:conn
LIBS:linear
LIBS:regul
LIBS:74xx
LIBS:cmos4000
LIBS:adc-dac
LIBS:memory
LIBS:xilinx
LIBS:microcontrollers
LIBS:dsp
LIBS:microchip
LIBS:analog_switches
LIBS:motorola
LIBS:texas
LIBS:intel
LIBS:audio
LIBS:interface
LIBS:digital-audio
LIBS:philips
LIBS:display
LIBS:cypress
LIBS:siliconi
LIBS:opto
LIBS:atmel
LIBS:contrib
LIBS:valves
EELAYER 25 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 1
Title ""
Date ""
Rev ""
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Comp
L Conn_01x04 J2
U 1 1 5B3EBC5E
P 2500 3550
F 0 "J2" H 2500 3750 50  0000 C CNN
F 1 "Conn_01x04" H 2700 2950 50  0000 C CNN
F 2 "Pin_Headers:Pin_Header_Straight_1x04_Pitch2.54mm" H 2500 3550 50  0001 C CNN
F 3 "" H 2500 3550 50  0001 C CNN
	1    2500 3550
	0    1    1    0   
$EndComp
Wire Wire Line
	2400 3150 2400 3350
Wire Wire Line
	2500 3150 2500 3350
$Comp
L Conn_02x02_Counter_Clockwise J1
U 1 1 5B3EBE39
P 2500 2850
F 0 "J1" H 2550 2950 50  0000 C CNN
F 1 "Conn_02x02_Counter_Clockwise" H 2600 2300 50  0000 C CNN
F 2 "RJ11:RJ11" H 2500 2850 50  0001 C CNN
F 3 "" H 2500 2850 50  0001 C CNN
	1    2500 2850
	0    1    1    0   
$EndComp
Wire Wire Line
	2500 2650 2500 2500
Wire Wire Line
	2500 2500 2300 2500
Wire Wire Line
	2300 2500 2300 3350
Wire Wire Line
	2400 2650 2400 2550
Wire Wire Line
	2400 2550 2600 2550
Wire Wire Line
	2600 2550 2600 3350
$EndSCHEMATC
