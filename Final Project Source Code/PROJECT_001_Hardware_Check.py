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

#FUNCTION FOR PIR SENSOR CHECK
def pir_handler(pin):
    if pin:
        global pirhandler
        pirhandler = "PIR Sensor      Motion detected!"

def PIR_check():
    global RIGHT_BUTTON_VALUE, LEFT_BUTTON_VALUE
    lcd.clear()
    lcd.putstr("PIR Sensor      Testing...")
    sleep(1)
    lcd.clear()
    global pirhandler
    pirhandler = " "
    RIGHT_BUTTON_VALUE = False
    LEFT_BUTTON_VALUE = False
    while not RIGHT_BUTTON_VALUE and not LEFT_BUTTON_VALUE:
        lcd.clear()
        pir_sensor.irq(trigger=machine.Pin.IRQ_RISING, handler=pir_handler)
        lcd.putstr(pirhandler)
        pirhandler = "PIR Sensor"
        sleep(0.5)
    print("   PIR Sensor: Complete")

#FUNCTION FOR POTENTIOMETER CHECK
def potentiometer_check():
    global RIGHT_BUTTON_VALUE, LEFT_BUTTON_VALUE
    RIGHT_BUTTON_VALUE = False
    LEFT_BUTTON_VALUE = False
    while not RIGHT_BUTTON_VALUE and not LEFT_BUTTON_VALUE:
        reading = potentiometer.read_u16()
        voltage = reading * VOLTAGE_CONVERSION_FACTOR
        output = str((voltage*1000)/1000)
        lcd.clear()
        lcd.putstr("Potentiometer   " + output)
        sleep(0.5)
    print("   Potentiometer: Complete")

#FUNCTION FOR BUZZER CHECK
def buzzer_check():
    lcd.clear()
    lcd.putstr("Buzzer          Testing...")
    buzzer(1)
    sleep(0.25)
    buzzer(0)
    sleep(0.25)
    buzzer(1)
    sleep(0.1)
    buzzer(0)
    sleep(0.1)
    buzzer(1)
    sleep(0.1)
    buzzer(0)
    print("   Buzzer: Complete")

#FUNCTION FOR ULTRASONIC CHECK
def ultrasonic_check():
    global RIGHT_BUTTON_VALUE, LEFT_BUTTON_VALUE
    RIGHT_BUTTON_VALUE = False
    LEFT_BUTTON_VALUE = False
    while not RIGHT_BUTTON_VALUE and not LEFT_BUTTON_VALUE:
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
        lcd.clear()
        lcd.putstr("Distance:       ")
        lcd.putstr(str(distance) + " cm")
        sleep(0.5)
    print("   Ultrasonic: Complete")

#FUNCTION FOR LED STRIP CHECK
def ledstrip_check():
    lcd.clear()
    lcd.putstr("Testing RGB LED Strip...")
    sleep(0.5)
    lcd.clear()
    lcd.putstr("LED Strip: Blue Testing...")
    for i in range(NUM_LEDS):
        ar[i] = 255
    sm.put(ar,8)
    utime.sleep_ms(10)
    sleep(0.5)
    lcd.clear()
    lcd.putstr("LED Strip: Red  Testing...")
    for i in range(NUM_LEDS):
        ar[i] = 255 << 8
    sm.put(ar,8)
    utime.sleep_ms(10)
    sleep(0.5)
    lcd.clear()
    lcd.putstr("LED Strip: GreenTesting...")
    for i in range(NUM_LEDS):
        ar[i] = 255 << 16
    sm.put(ar,8)
    utime.sleep_ms(10)
    sleep(0.5)
    lcd.clear()
    lcd.putstr("LED Strip: WhiteTesting...")
    for i in range(NUM_LEDS):
        ar[i] = (255 << 16) + (255 << 8) + 255
    sm.put(ar,8)
    utime.sleep_ms(10)
    sleep(0.5)
    lcd.clear()
    lcd.putstr("LED Strip: Off  Testing...")
    for i in range(NUM_LEDS):
        ar[i] = (0)
    sm.put(ar,8)
    print("   RGB LED Strip: Complete")

#FUNCTION FOR BUTTON CHECK
def button_check():
    global RIGHT_BUTTON_VALUE, LEFT_BUTTON_VALUE
    lcd.clear()
    lcd.putstr("Right Button.   Waiting...")
    RIGHT_BUTTON_VALUE = False
    while not RIGHT_BUTTON_VALUE:
        sleep(0.1)
    lcd.clear()
    lcd.putstr("Success!")
    print("   Right Button: Complete")
    sleep(0.5)
    lcd.clear()
    lcd.putstr("Left Button.    Waiting...")
    sleep(0.5)
    LEFT_BUTTON_VALUE = False
    while not LEFT_BUTTON_VALUE:
        sleep(0.1)
    lcd.clear()
    lcd.putstr("Success!")
    print("   Left Button: Complete")

#FUNCTION FOR LED LIGHT CHECK
def led_check():
    lcd.clear()
    lcd.putstr("LED Lights      Testing...")
    sleep(0.5)
    red_led.value(1)
    lcd.clear()
    lcd.putstr("LED: Red        Testing...")
    sleep(1)
    red_led.value(0)
    yellow_led.value(1)
    lcd.clear()
    lcd.putstr("LED: Yellow     Testing...")
    sleep(1)
    yellow_led.value(0)
    green_led.value(1)
    lcd.clear()
    lcd.putstr("LED: Green      Testing...")
    sleep(1)
    green_led.value(0)
    print("   LED Lights: Complete")

while True:
    onboard_led(1)
    lcd.clear()
    lcd.putstr("Hardware Check...")
    print("---Hardware Check Results---")
    sleep(0.5)
    lcd.clear()
    button_check()
    sleep(0.5)
    ledstrip_check()
    sleep(0.5)
    led_check()
    sleep(0.5)
    PIR_check()
    sleep(0.5)
    ultrasonic_check()
    sleep(0.5)
    potentiometer_check()
    sleep(0.5)
    buzzer_check()
    print("---End of Hardware Check Results---")
    lcd.clear()
    lcd.putstr("Hardware Check  Completed!")
    sleep(3)
    lcd.clear()
    lcd.putstr("Press any buttonto restart.")
    RIGHT_BUTTON_VALUE = False
    LEFT_BUTTON_VALUE = False
    while not RIGHT_BUTTON_VALUE and not LEFT_BUTTON_VALUE:
        onboard_led(0)
        sleep(0.5)
        onboard_led(1)
        sleep(0.5)