from gpiozero import Button
from signal import pause

button1 = Button(12)
button2 = Button(20)

def button1_pressed():
    print("Button 1 Pressed")

def button2_pressed():
    print("Button 2 Pressed")

button1.when_pressed = button1_pressed
button2.when_pressed = button2_pressed

pause()  # Keeps the script running
