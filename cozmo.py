#!/usr/bin/env python3
import pygame
import pywifi
from pywifi import const
import subprocess
import platform
import pycozmo
import time

#pygame.font.init()




# for wifi
ssid_Cozmo = 'Cozmo_1054D8' # add the Cozmo number
pw_Cozmo = '322979-8178041-59' # put Cozmo WIFI password with the dashes "-" ! 
# Create a PyWiFi object
wifi = pywifi.PyWiFi()

# Get the first wireless interface
print(len(wifi.interfaces()))

interface = wifi.interfaces()[1]

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Define button properties
BUTTON_FONT_SIZE = 50
BUTTON_COLOR = RED

# Define global variables
running = True
button1_color = BUTTON_COLOR
button2_color = BUTTON_COLOR
button3_color = BUTTON_COLOR
button4_color = BUTTON_COLOR

button1_message = "Connct Wifi"
button2_message = "Connect Cozmo"
button3_message = "Button 3"
button4_message = "Quit"

#cozmo
cli = None

# Define some constants for joystick deadbands and max speeds
max_wheel_speed = 150.0
max_head_speed = 3.0
max_lift_speed = 2.0
wheel_deadband = 0.1
head_deadband = 0.05
lift_deadband = 0.05


forward_speed = 0.0 
turn_speed = 0.0
head_speed = 0.0
lift_speed = 0.0
battery_voltage = 0.0

def on_robot_state(cli, pkt: pycozmo.protocol_encoder.RobotState):
    print("Battery level: {:.01f} V".format(pkt.battery_voltage))
    global button3_message
    global battery_voltage
    battery_voltage = pkt.battery_voltage
    button3_message = "Bl: {:.01f} V".format(pkt.battery_voltage)
    global button3_color
    if pkt.battery_voltage > 1.0:
        button3_color = GREEN
    else:
        button3_color = BLUE

 #This takes a forward speed of -1.0 to 1.0 and a rotation/turning 
# speed of -1.0 to 1.0. It returns left wheel and right wheel (in 
# that order) speeds that are range -max_wheel_speed to max_wheel_speed
# The return values are converted from double to float to match
# what the pycozmo drive_wheels command exprects.
def translate_speed(fwd, turn):
    if fwd == 0.0 and turn == 0.0:
        left_wheel_speed = 0.0
        right_wheel_speed = 0.0
    elif fwd == 0.0:
        left_wheel_speed = turn*max_wheel_speed
        right_wheel_speed = -turn*max_wheel_speed
    elif turn == 0.0:
        left_wheel_speed = fwd*max_wheel_speed
        right_wheel_speed = fwd*max_wheel_speed
    else:
        avg_speed = fwd*max_wheel_speed
        turn_speed = turn*max_wheel_speed/2
        left_wheel_speed = avg_speed + turn_speed
        right_wheel_speed = avg_speed - turn_speed
    return float(left_wheel_speed), float(right_wheel_speed)
    
def win_SSID():
    results = subprocess.check_output(["netsh", "wlan", "show", "network"])
    results = results.decode("ascii")
    results = results.replace("\r","")
    results = results.replace(" ","")
    ssid = ""
    for ls in results.split("\n"):
        if ls.startswith("SSID"):
            ssid =ls.split(":")[1]
            return ssid
    return ssid
def lin_SSID():
    cssid = ""
    try:
        output = subprocess.check_output(['sudo', 'iwgetid']).decode()
        cssid = output.split('"')[1]
        return cssid
    except Exception as e:
        print("check_wifi:")
        print(e)
        return cssid

    

def check_wifi():
    global button1_message
    # Set up the Wi-Fi network credentials
    SSID = ssid_Cozmo
    PASSWORD = pw_Cozmo

 

    current_ssid = ""
    # Check if the interface is already connected to a network
    if len(current_ssid)>=0 and interface.status() == const.IFACE_CONNECTED:
        if platform.system() == "Windows":
            current_ssid =win_SSID()
        else:
            current_ssid =lin_SSID()


        #button1_message = "Con:"+ current_ssid

        if current_ssid == SSID:
            return True
        else:
            return False

    else:
        button1_message = "Not cond"
        return False

def connect_wifi():
    global button1_message
    # Set up the Wi-Fi network credentials
    SSID = ssid_Cozmo
    PASSWORD = pw_Cozmo


    # Get the first wireless interface
    global interface
    print("wifi scanning")
    # Scan for available Wi-Fi networks
    interface.scan()
    networks = interface.scan_results()

    # Find the network you want to connect to
    target_network = None
    for network in networks:
        if network.ssid == SSID:
            target_network = network
            break
    print("build wifi profile")
    # If the target network is found, create a Profile object and connect to the network
    if target_network:
        profile = pywifi.Profile()
        profile.ssid = SSID
        profile.auth = const.AUTH_ALG_OPEN
        profile.akm.append(const.AKM_TYPE_WPA2PSK)
        profile.cipher = const.CIPHER_TYPE_CCMP
        profile.key = PASSWORD
        interface.disconnect()
        print("disconnect wifi")
        time.sleep(1)
        interface.remove_all_network_profiles()
        print("remove_all_network_profiles wifi")
        time.sleep(1)
        new_profile = interface.add_network_profile(profile)
        interface.connect(new_profile)
        print("connect new wifi")
        time.sleep(1)

        button1_message = "Cond:" + SSID
        print("connected to "+SSID)
        return True
    else:
        button1_message = "not fnd:"+ SSID
        print("Not find: "+SSID)
        return False



# Define button click functions
def button1_click():
    print("Button 1 clicked")
    global button1_message
    button1_message = "Connect..."
    global button1_color
    if check_wifi():
        print("connected")
        button1_color = GREEN  # Set the color of button4 to green
    else:
        print("try to connect")
        button1_color = BLUE  # Set the color of button4 to green
        if connect_wifi():
            button1_color = GREEN  # Set the color of button4 to green
        else:
            button1_color = RED  # Set the color of button4 to green
        

    

def button2_click():
    print("Button 2 clicked")
    global button2_color
    global run_cozmo
    global forward_speed 
    global turn_speed
    global head_speed
    global lift_speed
 
    if check_wifi():
        ### ------ Cozmo Initialization ------
        global cli
        cli = None
        # Connect to cozmo
        cli = pycozmo.client.Client(
        protocol_log_messages=None,
        auto_initialize=True,
        enable_animations=True,
        enable_procedural_face=True)
        cli.start()
        cli.connect()
        cli.wait_for_robot()
        #cli.enable_camera(enable=True, color=True)
        cli.set_lift_height(1)
        cli.set_head_angle(1)
        cli.add_handler(pycozmo.protocol_encoder.RobotState, on_robot_state, one_shot=True)
        forward_speed = 0.0
        turn_speed = 0.0
        head_speed = 0.0
        lift_speed = 0.0
        expression = -1
        make_sound = False    
        button2_color = GREEN  # Set the color of button4 to green
        run_cozmo = True
    else:
        button2_color = RED  # Set the color of button4 to green
        run_cozmo = False

  
def button3_click():
    print("Button 3 clicked")
    global button3_message
    global battery_voltage

    print("Battery level: {:.01f} V".format(battery_voltage))
    
    button3_message = "Bl: {:.01f} V".format(battery_voltage)
    global button3_color
    if battery_voltage > 1.0:
        button3_color = GREEN
    else:
        button3_color = BLUE

def button4_click():
    global running
    global button4_color
    button4_color = GREEN  # Set the color of button4 to green
    running = False

# Initialize Pygame
pygame.init()

# Create the font for the button labels
#button_font = pygame.font.SysFont(None, BUTTON_FONT_SIZE)
button_font = pygame.font.SysFont("freesansbold.ttf" , BUTTON_FONT_SIZE)


# Initialize the joysticks.

pygame.joystick.init()
run_cozmo = False

# Create the screen
#screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)

# Define the buttons
button1 = pygame.Rect(0, 0, 0, 0)
button2 = pygame.Rect(0, 0, 0, 0)
button3 = pygame.Rect(0, 0, 0, 0)
button4 = pygame.Rect(0, 0, 0, 0)


def main():
    global running
    global button1_color
    global button2_color
    global button3_color
    global button4_color
    global forward_speed 
    global turn_speed
    global head_speed
    global lift_speed
    old_forward_speed=0.0 
    old_turn_speed=0.0
    old_head_speed=0.0
    old_lift_speed=0.0
    old_axis = -1
    
    
    while running:
# Initializing our joysticks every time so we can get the values in the event queue
            # and handle hot swapping
        for i in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(i)
            joystick.init()
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                    button4_click()
            elif event.type == pygame.JOYBUTTONDOWN:
                print(f"Joystick button {event.button} pressed")
                if event.button == 7:
                    button2_click()
                if event.button == 6:
                    button4_click()
            elif event.type == pygame.JOYAXISMOTION:
                #print("Axis {} value: {:>6.3f}".format(event.axis, event.value))
                if event.axis == 1:
                    if -wheel_deadband < event.value < wheel_deadband:
                        forward_speed = 0.0
                    else:
                        forward_speed = -event.value
                elif event.axis == 0:
                    if -wheel_deadband < event.value < wheel_deadband:
                        turn_speed = 0.0
                    else:
                        turn_speed = event.value
                elif event.axis == 3:
                    print()
                  #  if -head_deadband < event.value < head_deadband:
                  #      head_speed = 0.0
                  #  else:
                  #      head_speed = -event.value * max_head_speed
                elif event.axis == 4:
                    print()
                   # if -lift_deadband < event.value < lift_deadband:
                   #     lift_speed = 0.0
                   # else:
                    #    lift_speed = -event.value * max_lift_speed
                elif event.axis == 5:
                    print("old_axis {} axis: {:>6.3f}".format(old_axis, event.value))

                    if old_axis < event.value:
                        lift_speed = 0.3
                    else:
                        lift_speed = 0.0

                    old_axis = event.value
                elif event.axis == 2:
                    if old_axis < event.value:
                        lift_speed = -0.3
                    else:
                        lift_speed = 0.0
                    old_axis = event.value



            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Check if the left mouse button was clicked
                if event.button == 1:
                    # Check if the click is inside one of the buttons
                    if button1.collidepoint(event.pos):
                        button1_click()
                    elif button2.collidepoint(event.pos):
                        button2_click()
                    elif button3.collidepoint(event.pos):
                        button3_click()
                    elif button4.collidepoint(event.pos):
                        button4_click()
                   ### All our Cozmo control calls based on the user inputs
            if(run_cozmo):
                global cli
                # Move head
                if old_head_speed != head_speed:
                    cli.move_head(head_speed)
                    old_head_speed = head_speed
                # Move arm
                if old_lift_speed != lift_speed:
                    print("lift speed:"+str(lift_speed))
                    cli.move_lift(lift_speed)
                    old_lift_speed = lift_speed
                    
                # Translate x-y speed to left wheel, right wheel speed
                if old_forward_speed != forward_speed or old_turn_speed != turn_speed:
                    lwheel,rwheel = translate_speed(forward_speed,turn_speed)
                    # Feed the wheel speeds to cozmo
                    cli.drive_wheels(lwheel, rwheel)
                else:
                    lwheel,rwheel = translate_speed(0.0,0.0)
                    # Feed the wheel speeds to cozmo
                    cli.drive_wheels(lwheel, rwheel)
                
        # Get the dimensions of the window
        window_width, window_height = screen.get_size()
        
        # Calculate the dimensions of the buttons
        button_width =int( window_width / 2)
        button_height =int( window_height / 2)
        
        # Set the positions and dimensions of the buttons
        button1.x = 0
        button1.y = 0
        button1.width = button_width
        button1.height = button_height
        
        button2.x = button_width
        button2.y = 0
        button2.width = button_width
        button2.height = button_height
        
        button3.x = 0
        button3.y = button_height
        button3.width = button_width
        button3.height = button_height
        
        button4.x = button_width
        button4.y = button_height
        button4.width = button_width
        button4.height = button_height
        # Fill the background color
        
        screen.fill(BLACK)
        if check_wifi():
            button1_color = GREEN  # Set the color of button4 to green
        else:
            button1_color = RED  # Set the color of button4 to green

        # Draw the buttons
        pygame.draw.rect(screen, button1_color, button1)
        pygame.draw.rect(screen, BLUE, button1,2)
        pygame.draw.rect(screen, button2_color, button2)
        pygame.draw.rect(screen, BLUE, button2,2)
        pygame.draw.rect(screen, button3_color, button3)
        pygame.draw.rect(screen, BLUE, button3,2)
        pygame.draw.rect(screen, button4_color, button4)
        pygame.draw.rect(screen, BLUE, button4,2)

        # Add the labels to the buttons
        global button1_message
        global button2_message
        global button3_message
        global button4_message
        button4_message = "Quit"
        button1_label = button_font.render(button1_message, True, WHITE)
        button2_label = button_font.render(button2_message, True, WHITE)
        button3_label = button_font.render(button3_message, True, WHITE)
        button4_label = button_font.render(button4_message, True, WHITE)

        screen.blit(button1_label, (int(button1.x + button_width/2 - button1_label.get_width()/2), int(button1.y + button_height/2 - button1_label.get_height()/2)))
        screen.blit(button2_label, (int(button2.x + button_width/2 - button2_label.get_width()/2), int(button2.y + button_height/2 - button2_label.get_height()/2)))
        screen.blit(button3_label, (int(button3.x + button_width/2 - button3_label.get_width()/2), int(button3.y + button_height/2 - button3_label.get_height()/2)))
        screen.blit(button4_label, (int(button4.x + button_width/2 - button4_label.get_width()/2), int(button4.y + button_height/2 - button4_label.get_height()/2)))

        # Update the screen
        pygame.display.update()

if __name__ == "__main__":
    main()

# Quit Pygame
pygame.quit()

