#---------------------------------START OF COMMON HEADER---------------------------------#
import array, rp2, machine, _thread, utime
from machine import I2C, Pin, ADC
from utime import sleep
from rp2 import PIO, StateMachine, asm_pio
from lcd_api import LcdApi
from pico_i2c_lcd import I2cLcd

#ONBOARD LED LIGHT HEADER
onboard_led = machine.Pin(25, machine.Pin.OUT) #Onboard LED is connected to GPIO 25

#I2C LCD HEADER
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16
i2c = I2C(0, sda = Pin(0), scl = Pin(1), freq = 400000) #I2C SDA is connected to GPIO 0 and I2C SCL is connected to GPIO 1
I2C_ADDR = i2c.scan()[0] #scan I2C device address
lcd = I2cLcd(i2c, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS) #LCD is 16x2

#3 LED LIGHTS HEADER
red_led = machine.Pin(13, machine.Pin.OUT) #RED LED is connected to GPIO 13 and is an OUTPUT DEVICE
yellow_led = machine.Pin(14, machine.Pin.OUT) #YELLOW LED is connected to GPIO 14 and is an OUTPUT DEVICE
green_led = machine.Pin(15, machine.Pin.OUT) #GREEN LED is connected to GPIO 15 and is an OUTPUT DEVICE

#2 BUTTONS HEADER
left_button = machine.Pin(17, machine.Pin.IN, machine.Pin.PULL_DOWN) #LEFT BUTTON is connected to GPIO 17 and is an INPUT DEVICE, with PULL_DOWN resistor enabled
right_button = machine.Pin(16, machine.Pin.IN, machine.Pin.PULL_DOWN) #RIGHT BUTTON is connected to GPIO 16 and is an INPUT DEVICE, with PULL_DOWN resistor enabled

#PIR SENSOR HEADER
pir_sensor = machine.Pin(8, machine.Pin.IN, machine.Pin.PULL_DOWN) #PIR SENSOR is connected to GPIO 8 and is an INPUT DEVICE, with PULL_DOWN resistor enabled

#POTENTIOMETER HEADER
potentiometer = ADC(0) #POTENTIOMETER is connected to ADC 0/GPIO 26
VOLTAGE_CONVERSION_FACTOR = 3.3 / (65535) #voltage conversion factor

#ULTRASONIC SENSOR HEADER
trigger = Pin(3, Pin.OUT) #ULTRASONIC TRIGGER is connected to GPIO 3 and is an OUTPUT DEVICE
echo = Pin(2, Pin.IN) #ULTRASONIC ECHO is connected to GPIO 2 and is an INPUT DEVICE

#BUZZER HEADER
buzzer = machine.Pin(19, machine.Pin.OUT) #BUZZER is connected to GPIO 5 and is an OUTPUT DEVICE

#RGB LED LIGHT STRIP HEADER
NUM_LEDS = 8 #Total number of LEDs on the LED STRIP
PIN_NUM = 12 #LED STRIP is connected to GPIO 12
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

global SETTING_READING, ULTRASONIC_READING, LEFT_BUTTON_VALUE, RIGHT_BUTTON_VALUE, PIR_VALUE
RIGHT_BUTTON_VALUE = False
LEFT_BUTTON_VALUE = True
SETTING_READING = 0
ULTRASONIC_READING = 0
PIR_VALUE = False

def ultrasonic_sensor_reading():
    global ULTRASONIC_READING
    trigger.low()
    utime.sleep_us(2)
    trigger.high()
    utime.sleep_us(5)
    trigger.low()
    while echo.value() == 0:
        signaloff = utime.ticks_us()
    while echo.value() == 1:
        signalon = utime.ticks_us()
    timepassed = signalon - signaloff
    distance = (timepassed * 0.0343) / 2
    ULTRASONIC_READING = int(distance)
    sleep(0.01)

def background_process_thread():
    global ULTRASONIC_READING, LEFT_BUTTON_VALUE, RIGHT_BUTTON_VALUE
    while True:
        ultrasonic_sensor_reading()
        if right_button.value() == 1 and RIGHT_BUTTON_VALUE == False:
            RIGHT_BUTTON_VALUE = True
            LEFT_BUTTON_VALUE = False
            buzzer(1)
            sleep(0.1)
            buzzer(0)
        sleep(0.01)
        if left_button.value() == 1 and LEFT_BUTTON_VALUE == False:
            LEFT_BUTTON_VALUE = True
            RIGHT_BUTTON_VALUE = False
            buzzer(1)
            sleep(0.1)
            buzzer(0)
        sleep(0.01)

_thread.start_new_thread(background_process_thread, ())

def setting():
    global SETTING_READING
    while RIGHT_BUTTON_VALUE == False and LEFT_BUTTON_VALUE == True:
        reading = potentiometer.read_u16()
        voltage = reading * VOLTAGE_CONVERSION_FACTOR
        output = str(int((voltage*100000)/1000))
        SETTING_READING = int(output)
        lcd.backlight_on()
        lcd.clear()
        lcd.putstr("OFF:            " + "Setting: " + str(SETTING_READING) + " cm")
        sleep(0.3)
    lcd.clear()
    lcd.putstr("ON:             " + "DETECTING MOTION")
    sleep(0.5)
    lcd.clear()
    lcd.putstr("Press left      " + "button to exit")
    sleep(0.5)
    
def pir_handler(pin):
    global PIR_VALUE
    utime.sleep_ms(100)
    if pin.value() and LEFT_BUTTON_VALUE == False and RIGHT_BUTTON_VALUE == True:
        PIR_VALUE = True
        lcd.backlight_on()
        red_led(1)
        green_led(1)
        yellow_led(1)
        pir_activation()
        
def pir_activation():
    global PIR_VALUE
    i = 0
    while i <= 10 and RIGHT_BUTTON_VALUE == True and LEFT_BUTTON_VALUE == False:
        lcd.clear()
        lcd.putstr("MOTION DETECTED Distance: " + str(ULTRASONIC_READING) + " cm")
        if ULTRASONIC_READING <= SETTING_READING:
            buzzer(1)
            for k in range(NUM_LEDS):
                ar[k] = 255 << 8
            sm.put(ar,8)
        utime.sleep(0.3)
        for k in range(NUM_LEDS):
            ar[k] = 0
        sm.put(ar,8)
        buzzer(0)
        utime.sleep(0.05)
        if i >= 6 and ULTRASONIC_READING <= SETTING_READING:
            i = 0
        i = i + 1
    PIR_VALUE = False
    red_led(0)
    green_led(0)
    yellow_led(0)
    lcd.backlight_off()

onboard_led(1)
while True:
    setting()
    while LEFT_BUTTON_VALUE == False and RIGHT_BUTTON_VALUE == True:
        pir_sensor.irq(trigger=machine.Pin.IRQ_RISING, handler=pir_handler)
        sleep(0.3)