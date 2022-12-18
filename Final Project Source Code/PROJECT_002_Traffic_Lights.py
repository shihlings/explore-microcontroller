#---------------------------------START OF COMMON HEADER---------------------------------#
import array, rp2, machine, _thread, utime
from machine import I2C, Pin, ADC
from utime import sleep
from rp2 import PIO, StateMachine, asm_pio
from pico_i2c_lcd import I2cLcd

#ONBOARD LED LIGHT HEADER
onboard_led = machine.Pin(25, machine.Pin.OUT) #Onboard LED is connected to GPIO 25

#I2C LCD HEADER
i2c = I2C(0, sda = Pin(0), scl = Pin(1), freq = 400000) #I2C SDA is connected to GPIO 0 and I2C SCL is connected to GPIO 1
I2C_ADDR = i2c.scan()[0] #scan I2C device address
lcd = I2cLcd(i2c, I2C_ADDR, 2, 16) #LCD is 16x2

#3 LED LIGHTS HEADER
red_led = machine.Pin(12, machine.Pin.OUT) #RED LED is connected to GPIO 12 and is an OUTPUT DEVICE
yellow_led = machine.Pin(14, machine.Pin.OUT) #YELLOW LED is connected to GPIO 14 and is an OUTPUT DEVICE
green_led = machine.Pin(15, machine.Pin.OUT) #GREEN LED is connected to GPIO 15 and is an OUTPUT DEVICE

#2 BUTTONS HEADER
left_button = machine.Pin(21, machine.Pin.IN, machine.Pin.PULL_DOWN) #LEFT BUTTON is connected to GPIO 21 and is an INPUT DEVICE, with PULL_DOWN resistor enabled
right_button = machine.Pin(18, machine.Pin.IN, machine.Pin.PULL_DOWN) #RIGHT BUTTON is connected to GPIO 18 and is an INPUT DEVICE, with PULL_DOWN resistor enabled

#PIR SENSOR HEADER
pir_sensor = machine.Pin(28, machine.Pin.IN, machine.Pin.PULL_DOWN) #PIR SENSOR is connected to GPIO 28 and is an INPUT DEVICE, with PULL_DOWN resistor enabled

#POTENTIOMETER HEADER
potentiometer = ADC(0) #POTENTIOMETER is connected to ADC 0/GPIO 26
VOLTAGE_CONVERSION_FACTOR = 3.3 / (65535) #voltage conversion factor

#ULTRASONIC SENSOR HEADER
trigger = Pin(3, Pin.OUT) #ULTRASONIC TRIGGER is connected to GPIO 3 and is an OUTPUT DEVICE
echo = Pin(2, Pin.IN) #ULTRASONIC ECHO is connected to GPIO 2 and is an INPUT DEVICE

#BUZZER HEADER
buzzer = machine.Pin(5, machine.Pin.OUT) #BUZZER is connected to GPIO 5 and is an OUTPUT DEVICE

#RGB LED LIGHT STRIP HEADER
NUM_LEDS = 8 #Total number of LEDs on the LED STRIP
PIN_NUM = 16 #LED STRIP is connected to GPIO 16
@asm_pio(sideset_init = PIO.OUT_LOW, out_shiftdir = PIO.SHIFT_LEFT, autopull = True, pull_thresh = 24)

def ws2812():
    T1 = 2
    T2 = 5
    T3 = 3
    label("bitloop")
    out(x, 1) .side(0) [T3 - 1]
    jmp(not_x, "do_zero") .side(1) [T1 - 1]
    jmp("bitloop") .side(1) [T2 - 1]
    label("do_zero")
    nop() .side(0) [T2 - 1]
    
sm = StateMachine(0, ws2812, freq = 8000000, sideset_base = Pin(PIN_NUM))
sm.active(1)
ar = array.array("I", [0 for _ in range(NUM_LEDS)])

#---------------------------------END OF COMMON HEADER---------------------------------#

global RIGHT_BUTTON_VALUE, LEFT_BUTTON_VALUE
RIGHT_BUTTON_VALUE = False
LEFT_BUTTON_VALUE = False

#FUNCTION FOR READING TWO BUTTONS
def button_reader_thread():
    global RIGHT_BUTTON_VALUE, LEFT_BUTTON_VALUE
    while True:
        if right_button.value() == 1 and RIGHT_BUTTON_VALUE == False:
            RIGHT_BUTTON_VALUE = True
            buzzer(1)
            sleep(0.1)
            buzzer(0)
        sleep(0.01)
        if left_button.value() == 1 and LEFT_BUTTON_VALUE == False:
            LEFT_BUTTON_VALUE = True
            buzzer(1)
            sleep(0.1)
            buzzer(0)
        sleep(0.01)

_thread.start_new_thread(button_reader_thread, ())

onboard_led.value(1)
green_led.value(0)
yellow_led.value(0)
red_led.value(0)
utime.sleep(0.5)
for i in range(NUM_LEDS):
    ar[i] = 15 << 8
sm.put(ar,8)
while True:
    if RIGHT_BUTTON_VALUE == True:
        green_led.value(1)
        for i in range(NUM_LEDS):
            ar[i] = 15 << 16
        sm.put(ar,8)
        lcd.clear()
        lcd.putstr("Green Light.    Vertical Cross.")
        buzzer.value(1)
        utime.sleep(0.1)
        buzzer.value(0)
        utime.sleep(3)
        lcd.clear()
        lcd.putstr("Green Light.    No Crossing.")
        RIGHT_BUTTON_VALUE = False
        buzzer.value(1)
        utime.sleep(0.1)
        buzzer.value(0)
        utime.sleep(0.05)
        buzzer.value(1)
        utime.sleep(0.1)
        buzzer.value(0)
        for k in range(5):
            for i in range(NUM_LEDS):
                ar[i] = 0
            sm.put(ar,8)
            utime.sleep(0.5)
            for i in range(NUM_LEDS):
                ar[i] = 15 << 8
            sm.put(ar,8)
            utime.sleep(0.5)
        for k in range(5):
            for i in range(NUM_LEDS):
                ar[i] = 0
            sm.put(ar,8)
            utime.sleep(0.2)
            for i in range(NUM_LEDS):
                ar[i] = 15 << 8
            sm.put(ar,8)
            utime.sleep(0.2)
        for i in range(NUM_LEDS):
            ar[i] = 15 << 8
        sm.put(ar,8)
    green_led.value(1)
    lcd.clear()
    lcd.putstr("Green Light.    No Crossing.")
    utime.sleep(5)
    green_led.value(0)
    yellow_led.value(1)
    lcd.clear()
    lcd.putstr("Yellow Light.   No Crossing.")
    utime.sleep(2)
    yellow_led.value(0)
    if LEFT_BUTTON_VALUE == True:
        red_led.value(1)
        for i in range(NUM_LEDS):
            ar[i] = 15 << 16
        sm.put(ar,8)
        lcd.clear()
        lcd.putstr("Red Light.      Horizontal Cross")
        buzzer.value(1)
        utime.sleep(0.5)
        buzzer.value(0)
        utime.sleep(0.1)
        buzzer.value(1)
        utime.sleep(0.1)
        buzzer.value(0)
        utime.sleep(3)
        lcd.clear()
        lcd.putstr("Red Light.      No Crossing.")
        LEFT_BUTTON_VALUE = False
        buzzer.value(1)
        utime.sleep(0.1)
        buzzer.value(0)
        utime.sleep(0.05)
        buzzer.value(1)
        utime.sleep(0.1)
        buzzer.value(0)
        for k in range(5):
            for i in range(NUM_LEDS):
                ar[i] = 0
            sm.put(ar,8)
            utime.sleep(0.5)
            for i in range(NUM_LEDS):
                ar[i] = 15 << 8
            sm.put(ar,8)
            utime.sleep(0.5)
        for k in range(5):
            for i in range(NUM_LEDS):
                ar[i] = 0
            sm.put(ar,8)
            utime.sleep(0.2)
            for i in range(NUM_LEDS):
                ar[i] = 15 << 8
            sm.put(ar,8)
            utime.sleep(0.2)
        for i in range(NUM_LEDS):
            ar[i] = 15 << 8
        sm.put(ar,8)
    red_led.value(1)
    lcd.clear()
    lcd.putstr("Red Light.      No Crossing.")
    utime.sleep(5)
    red_led.value(0)