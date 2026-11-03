# Variant 2 of the frame with the keypad chamber, see make_frame.py.
# Run:  freecadcmd make_frame_keypad.py      (FreeCAD 1.1)
# Output: frame_keypad.step, frame_keypad.stl
import os
os.environ["FRAME_VARIANT"] = "keypad"
__file__ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "make_frame.py")
exec(compile(open(__file__, encoding="utf-8").read(), __file__, "exec"))
