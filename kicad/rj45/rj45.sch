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
L Conn_02x04_Odd_Even J1
U 1 1 5B3EB509
P 2750 3500
F 0 "J1" H 2800 3700 50  0000 C CNN
F 1 "Conn_02x04_Odd_Even" H 3150 2900 50  0000 C CNN
F 2 "Pin_Headers:Pin_Header_Straight_2x04_Pitch2.54mm" H 2750 3500 50  0001 C CNN
F 3 "" H 2750 3500 50  0001 C CNN
	1    2750 3500
	0    1    1    0   
$EndComp
$Comp
L Conn_02x04_Top_Bottom J2
U 1 1 5B3EB65D
P 2650 2900
F 0 "J2" H 2700 3100 50  0000 C CNN
F 1 "Conn_02x04_Top_Bottom" H 2550 3250 50  0000 C CNN
F 2 "RJ45:RJ45" H 2650 2900 50  0001 C CNN
F 3 "" H 2650 2900 50  0001 C CNN
	1    2650 2900
	0    -1   1    0   
$EndComp
Wire Wire Line
	2550 3200 2550 3300
Wire Wire Line
	2650 3200 2650 3300
Wire Wire Line
	2750 3200 2750 3300
Wire Wire Line
	2850 3200 2850 3300
Wire Wire Line
	2850 2700 3000 2700
Wire Wire Line
	3000 2700 3000 3800
Wire Wire Line
	3000 3800 2850 3800
Wire Wire Line
	2750 2700 2750 2650
Wire Wire Line
	2750 2650 3050 2650
Wire Wire Line
	3050 2650 3050 3850
Wire Wire Line
	3050 3850 2750 3850
Wire Wire Line
	2750 3850 2750 3800
Wire Wire Line
	2550 2700 2400 2700
Wire Wire Line
	2400 2700 2400 3800
Wire Wire Line
	2400 3800 2550 3800
Wire Wire Line
	2650 2700 2650 2650
Wire Wire Line
	2650 2650 2300 2650
Wire Wire Line
	2300 2650 2300 3850
Wire Wire Line
	2300 3850 2650 3850
Wire Wire Line
	2650 3850 2650 3800
$EndSCHEMATC
