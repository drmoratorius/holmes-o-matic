import machine, neopixel, random
from machine import Pin, PWM
from time import sleep
import time
from morutils import *

#######################################################################################
######## C O N F I G U R A T I O N ####################################################
#######################################################################################

# SG90 MOTOR
motorGpio = 32
class Servo:
    def __init__(self, pin):
        self.pwm = PWM(Pin(pin), freq=50)
        self.min_duty = 26  # Duty for 0 degrees
        self.max_duty = 128  # Duty for 180 degrees

    def angle_to_duty(self, angle):
        return int(self.min_duty + (angle / 180.0) * (self.max_duty - self.min_duty))

    def move(self, angle):
        #self.start()
        duty = self.angle_to_duty(angle)
        self.pwm.duty(duty)
        
    def stop():
        self.pwm.deinit()

    def start():
        self.pwm.init()
        
servo = Servo(motorGpio)

# NEOPIXEL
neopixelGpio = 16
initialPixelColor = (0,0,0)
defaultPixelColor = (50, 50, 50)
activePixelColor = (240, 10, 0) #(255, 100, 0)
arrowPixelColor = (0, 255, 0)

# MCP 4151
potiSckPin = 18
potiMosiPin = 23
potiCsPin = 5

# MCP 23017
mcpAddr = 0x20
sdaPin=33
sclPin=27
MCP_IODIRA = 0x00  # Controls the direction of the data I/O for port A.
MCP_IODIRB = 0x01  # Controls the direction of the data I/O for port B.
MCP_IPOLA = 0x02  # Configures the polarity on the corresponding GPIO-port bits for port A.
MCP_IPOLB = 0x03  # Configures the polarity on the corresponding GPIO-port bits for port B.
MCP_GPINTENA = 0x04  # Controls the interrupt-on-change for each pin of port A.
MCP_GPINTENB = 0x05  # Controls the interrupt-on-change for each pin of port B.
MCP_DEFVALA = 0x06  # Controls the default comparison value for interrupt-on-change for port A.
MCP_DEFVALB = 0x07  # Controls the default comparison value for interrupt-on-change for port B.
MCP_INTCONA = 0x08  # Controls how the associated pin value is compared for the interrupt-on-change for port A.
MCP_INTCONB = 0x09  # Controls how the associated pin value is compared for the interrupt-on-change for port B.
MCP_IOCON = 0x0A  # Controls the device.
MCP_GPPUA = 0x0C  # Controls the pull-up resistors for the port A pins.
MCP_GPPUB = 0x0D  # Controls the pull-up resistors for the port B pins.
MCP_INTFA = 0x0E  # Reflects the interrupt condition on the port A pins.
MCP_INTFB = 0x0F  # Reflects the interrupt condition on the port B pins.
MCP_INTCAPA = 0x10  # Captures the port A value at the time the interrupt occurred.
MCP_INTCAPB = 0x11  # Captures the port B value at the time the interrupt occurred.
MCP_GPIOA = 0x12  # Reflects the value on the port A.
MCP_GPIOB = 0x13  # Reflects the value on the port B.
MCP_OLATA = 0x14  # Provides access to the port A output latches.
MCP_OLATB = 0x15  # Provides access to the port B output latches.
mcpIrqPinNo=34

# General settings
debug = False
testProgram = False
    
crimes = [
    {
        "title": 'Harassment',
        "pixel": 0,
        "angleValue": 90
    },
    {
        "title": 'Act of Violence',
        "pixel": 1,
        "angleValue": 45
    },
    {
        "title": 'Wanted Person',
        "pixel": 2,
        "angleValue": 0
    },
#    {
#        "title": 'Theft',
#        "pixel": 3,
#        "angleValue": 2000000
#    },
#    {
#        "title": 'Homicide',
#        "pixel": 4,
#        "angleValue": 1500000 #TODO
#    },
#    {
#        "title": 'Drunkenness',
#        "pixel": 5,
#        "angleValue": 1500000 # TODO
#    },
    {
        "title": 'Protest',
        "pixel": 6,
        "angleValue": 180
    },
    {
        "title": 'Burglary',
        "pixel": 7,
        "angleValue": 135
    }
]

lastCrime = 0
prevBankAPins = []
curValues = []
inputNames = ["NC8","NC7","NC6", "NC5","NC4","NC3","BUTTON", "SWITCH"]
currentProgram = 'AUTO'
interrupt_occurred = False
manual_initialized = False

#######################################################################################
######## F U N C T I O N S ############################################################
#######################################################################################
def custom_sleep(duration):
    global interrupt_occurred
    start_time = time.ticks_ms()
    while time.ticks_ms() - start_time < duration * 1000:
        # Check for interrupt or exit condition here
        if interrupt_occurred:  # Replace with your actual condition
            interrupt_occurred = False
            break
        time.sleep_ms(10)  # Sleep for a short duration

def calculate_duty_ns(angle):
    if angle < 0:
        angle = 0
    elif angle > 180:
        angle = 180
    
    # Pulsdauer für 0° und 180° in ns
    min_duty_ns = 1_000_000  # 1 ms
    max_duty_ns = 2_000_000  # 2 ms
    
    # Pulsdauer pro Grad berechnen
    duty_ns_per_degree = (max_duty_ns - min_duty_ns) / 180
    
    # Pulsdauer für den gewünschten Winkel berechnen
    duty_ns = min_duty_ns + (angle * duty_ns_per_degree)
    
    return int(duty_ns)

def motor_on():
    if debug: print('(FUNC) motor_on()')
    pwm.init()
    
def motor_off():
    if debug: print('(FUNC) motor_off()')
    pwm.deinit()

def motor_set(val):
    if debug: print('(FUNC) motor_set('+str(val)+')')
    print('(FUNC) motor_set('+str(val)+')')
    #pwm.duty_ns(val)
    servo.move(val)

def set_pixel_color(no, color):
    if debug: print('(FUNC) set_pixel_color('+str(no)+', '+str(color[0])+','+str(color[1])+', '+str(color[2])+')')
    np[no] = color
    np.write()
    
def set_all_pixel_colors(color):
    if debug: print('(FUNC) set_all_pixel_colors('+str(color[0])+','+str(color[1])+', '+str(color[2])+')')
    for i in range(8): # 2 arrows
        set_pixel_color(i, color)
    
def reset_crime_wheel():
    if debug: print('(FUNC) reset_crime_wheel()')
    set_all_pixel_colors(initialPixelColor)
    motor_set(90)
    custom_sleep(1)
    motor_off()
    
def set_crime(no):
    if debug: print('(FUNC) set_crime('+str(no)+')')
    print('---> Setting crime to ' + crimes[no]['title']);
    set_all_pixel_colors(defaultPixelColor)
    set_pixel_color(crimes[no]['pixel'], activePixelColor)
    motor_set(crimes[no]['angleValue'])
    
def set_random_crime():
    global lastCrime
    if debug: print('(FUNC) set_random_crime()')
    set_pot_value(random.randint(0, 255)) # Simulate distance
    randomCrime = random.randint(0, len(crimes) - 1)
    while randomCrime == lastCrime:
        randomCrime = random.randint(0, len(crimes) - 1)
    set_crime(randomCrime)
    lastCrime = randomCrime
    
def change_arrow_status(no, newState, newColor = arrowPixelColor):
    if debug: print('(FUNC) change_arrow_status('+str(no)+', '+str(newState)+')')
    if no == 1:
        if newState == True:
            set_pixel_color(8, newColor)
        else:
            set_pixel_color(8, initialPixelColor)
    if no == 2:
        if newState == True:
            set_pixel_color(9, newColor)
        else:
            set_pixel_color(9, initialPixelColor)

def arrow_activity():
    colorOn = (100, 40, 0)
    colorOff = (100, 100, 100)
    colorDir = (240, 10, 0)
    
    for i in range(random.randint(3, 10)):
        change_arrow_status(1, True, colorOn)
        change_arrow_status(2, True, colorOn)
        custom_sleep(0.4)
        change_arrow_status(1, False)
        change_arrow_status(2, False)
        custom_sleep(0.4)
        
    arrowNo = random.randint(1, 2)
    change_arrow_status(arrowNo, True, colorDir)
    custom_sleep(0.3)

def random_crime_animation():
    motor_set(90)
    set_all_pixel_colors(defaultPixelColor)
    set_pot_value(0)
    arrow_activity()
    set_random_crime()
    
    if testProgram == True:
        custom_sleep(1)
    else:
        custom_sleep(random.randint(3, 25))
    
def debug_mode():
    set_all_pixel_colors((255, 0, 255))
    motor_set(90)
    
def set_pot_value(value):
    cs.value(0)
    spi.write(b'\x00')
    spi.write(value.to_bytes(1, 'big'))
    cs.value(1)

def random_color():
    return [random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)]

# Always receives an array of values: [['SP1', True], ['SP2', False]]...
def input_callback(changes):
    global currentProgram, interrupt_occurred
    eventSource = changes[0][0]
    eventValue = changes[0][1]
    
    if eventSource == 'SWITCH':
        if eventValue == True:
            currentProgram = 'MANUAL'
            print('Switched to **MANUAL**')
            interrupt_occurred = True
        else:
            currentProgram = 'AUTO'
            print('Switched to **AUTO**')
            interrupt_occurred = True
            manual_initialized = False
            
    if eventSource == 'BUTTON' and eventValue == True:
        if currentProgram == 'MANUAL':
            manual_initialized = True
            print('Pressed button in manual mode!')
            set_pixel_color(0, [255, 0, 0])
            custom_sleep(0.5)
            set_pixel_color(1, [255, 0, 0])
            custom_sleep(0.5)
            set_pixel_color(2, [255, 0, 0])
            custom_sleep(0.5)
            set_pixel_color(3, [255, 0, 0])
            custom_sleep(0.5)
            set_pixel_color(4, [255, 0, 0])
            custom_sleep(0.5)
            set_pixel_color(5, [255, 0, 0])
            custom_sleep(0.5)
            set_pixel_color(6, [255, 0, 0])
            custom_sleep(0.5)
            set_pixel_color(7, [255, 0, 0])
            
            custom_sleep(1)
            set_all_pixel_colors([0,0,0])
            
            for j in range (20):
                for i in range(10): # 2 arrows
                    set_pixel_color(i, random_color())
                    custom_sleep(0.05)
             
            custom_sleep(2)
            set_all_pixel_colors([0,0,0])
            custom_sleep(1)
            change_arrow_status(1, True)
            change_arrow_status(2, True)
            set_all_pixel_colors([200, 50, 10])        
            manual_initialized = True            
            interrupt_occurred = True
    
def SP_mcpCallback(pin):
    global prevBankAPins
    changes = []
    curValues = UTIL_convertBinaryValue(i2c.readfrom_mem(mcpAddr, MCP_GPIOB, 1))
    changedOffsets = UTIL_compare_bool_arrays(prevBankAPins, curValues)
    if len(changedOffsets):
        for offset in changedOffsets:
            print('INPUT ' + inputNames[offset] + ' changed to ' + str(curValues[offset]))
            changes.append([inputNames[offset], curValues[offset]])
        prevBankAPins = curValues
    if len(changes):
        input_callback(changes)
        
#######################################################################################
######## P R O G R A M ################################################################
#######################################################################################
    
# MCP 4151 INIT (SPI)
cs = machine.Pin(potiCsPin, machine.Pin.OUT)
spi = machine.SPI(1, baudrate=1000000, polarity=0, phase=0, sck=machine.Pin(potiSckPin), mosi=machine.Pin(potiMosiPin))

# NEOPIXEL INIT
np = neopixel.NeoPixel(machine.Pin(neopixelGpio), 10) # + 2 arrows
set_all_pixel_colors([0,0,0])

# MCP 23017 INIT
i2c = machine.I2C(0, scl=machine.Pin(sclPin), sda=machine.Pin(sdaPin), )
i2cdevices = i2c.scan()
print('[.] Configuring MCP23017 for program...')
i2c.writeto_mem(mcpAddr, MCP_IODIRB, b'\xFF')  # Bank B -> all input
print('[.] Set Bank B to input')
i2c.writeto_mem(mcpAddr, MCP_GPPUB, b'\xFF')
print('[.] Set Bank B all pull-up resistors on')
i2c.writeto_mem(mcpAddr, MCP_GPINTENB, b'\xFF')
print('[.] Set Bank B IRQ mode')
i2c.writeto_mem(mcpAddr, MCP_IODIRA, b'\x00')  # Bank A -> all output
print('[.] Set Bank A to output')
i2c.writeto_mem(mcpAddr, MCP_GPIOA, b'\x00')
print('[.] Set Bank A all outputs to 0')
print('[*] Reading current value of bank B')
curValues = UTIL_convertBinaryValue(i2c.readfrom_mem(mcpAddr, MCP_GPIOB, 1))
prevBankAPins = curValues
mcpIrqPin = machine.Pin(mcpIrqPinNo, machine.Pin.IN)
mcpIrqPin.irq(trigger=machine.Pin.IRQ_FALLING | machine.Pin.IRQ_RISING, handler=SP_mcpCallback)


# Bootup sequence
i2c.writeto_mem(mcpAddr, MCP_GPIOA, b'\xFF')
i2c.writeto_mem(mcpAddr, MCP_GPIOA, bytearray([0b10000000]))
sleep(1)
i2c.writeto_mem(mcpAddr, MCP_GPIOA, bytearray([0b11000000]))
sleep(1)
i2c.writeto_mem(mcpAddr, MCP_GPIOA, bytearray([0b11110000]))
sleep(1)
i2c.writeto_mem(mcpAddr, MCP_GPIOA, bytearray([0b11111000]))
sleep(1)
i2c.writeto_mem(mcpAddr, MCP_GPIOA, bytearray([0b11111100]))
sleep(0.3)
i2c.writeto_mem(mcpAddr, MCP_GPIOA, bytearray([0b11111110]))
sleep(0.3)
i2c.writeto_mem(mcpAddr, MCP_GPIOA, bytearray([0b11111111]))

while True:
    if currentProgram == 'AUTO':
        random_crime_animation()
        custom_sleep(2)
    else:
        print('Manual')
        if manual_initialized == False:
            change_arrow_status(1, True)
            change_arrow_status(2, True)
            set_all_pixel_colors([200, 50, 10])        
            manual_initialized = True
        custom_sleep(1)
