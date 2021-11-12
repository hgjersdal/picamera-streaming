# picamera-test

- `p` to take an image. Saved as img?.jpg, where ? starts at 0 and increments by one per press
- `z` to toggle between 100% crop and full screen (assuming 2560x1440 screen)
- `q` quit

For python module keyboard to work without being root:
Add user to groups tty and input.

Remove calls to ensure_root in `_nixkeyboard.py`
