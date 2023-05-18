#import evdev
# from evdev import InputDevice, categorize, ecodes
#
# #creates object 'gamepad' to store the data
# #you can call it whatever you like
# gamepad = InputDevice('/dev/input/event0') # 0 = keyboard, 1 = mouse
#
# #prints out device info at start
# print(gamepad)
#
# #evdev takes care of polling the controller in a loop
# for event in gamepad.read_loop():
#     #print(categorize(event))
#     #filters by event type
#     if event.type == ecodes.EV_REL:
#         if event.code == 0:
#             if event.value > 0:
#                 print('right')
#             else:
#                 print('left')
#         elif event.code == 1:
#             if event.value > 0:
#                 print('down')
#             else:
#                 print('up')
#         else:
#             print(event)
#         print(event.value)
#     elif event.type == ecodes.EV_KEY:
#         if event.code == 103:
#             print('up')
#         elif event.code == 105:
#             print('left')
#         elif event.code == 106:
#             print('right')
#         elif event.code == 108:
#             print('down')
#         elif event.code == 272:
#             if event.value == 1:
#                 print('LEFT CLICK!')
#             elif event.value == 0:
#                 print('UNCLICK!')
#         elif event.code == 273:
#             if event.value == 1:
#                 print('RIGHT CLICK!')
#             elif event.value == 0:
#                 print('UNCLICK!')
#         else:
#             print(event)


from evdev import InputDevice
from select import select

# A mapping of file descriptors (integers) to InputDevice instances.
devices = map(InputDevice, ('/dev/input/event0', '/dev/input/event1'))
devices = {dev.fd: dev for dev in devices}

for dev in devices.values():
    print(dev)

while True:
    r, w, x = select(devices, [], [])
    for fd in r:
        for event in devices[fd].read():
            print(event)