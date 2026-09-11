import time
import subprocess
import ctypes
from ctypes import c_void_p, c_double, c_uint32, Structure

class CGPoint(Structure):
    _fields_ = [('x', c_double), ('y', c_double)]

cg = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')
cg.CGEventCreateMouseEvent.restype = c_void_p
cg.CGEventCreateMouseEvent.argtypes = [c_void_p, c_uint32, CGPoint, c_uint32]
cg.CGEventPost.restype = None
cg.CGEventPost.argtypes = [c_uint32, c_void_p]

kCGHIDEventTap = 0
kCGEventLeftMouseDown = 1
kCGEventLeftMouseUp = 2

def click(x, y):
    pt = CGPoint(x, y)
    down = cg.CGEventCreateMouseEvent(None, kCGEventLeftMouseDown, pt, 0)
    up = cg.CGEventCreateMouseEvent(None, kCGEventLeftMouseUp, pt, 0)
    cg.CGEventPost(kCGHIDEventTap, down)
    time.sleep(0.05)
    cg.CGEventPost(kCGHIDEventTap, up)
    time.sleep(0.1)

# 1. Activate Comet
subprocess.run(['osascript', '-e', 'tell application "Comet" to activate'])
time.sleep(0.5)

# 2. Click in the input box [ GCP-Projektnummer ]
click(225.0, 718.0)
time.sleep(0.3)

# 3. Select all and type project number
script = '''
tell application "System Events"
    keystroke "a" using {command down}
    delay 0.1
    keystroke "950665954756"
end tell
'''
subprocess.run(['osascript', '-e', script])
time.sleep(0.5)

# 4. Click [ Projekt festlegen ]
click(384.0, 718.0)
time.sleep(3.0)

print("AUTOMATION_EXECUTED")
