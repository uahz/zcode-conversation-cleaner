"""PrintWindow 截图脚本（即使窗口被遮挡也能抓取）。"""
import ctypes, time, sys
from ctypes import wintypes
from PIL import Image
import pygetwindow as gw

user32 = ctypes.WinDLL('user32', use_last_error=True)
gdi32  = ctypes.WinDLL('gdi32',  use_last_error=True)


class BMIH(ctypes.Structure):
    _fields_ = [
        ('biSize', wintypes.DWORD), ('biWidth', wintypes.LONG),
        ('biHeight', wintypes.LONG), ('biPlanes', wintypes.WORD),
        ('biBitCount', wintypes.WORD), ('biCompression', wintypes.DWORD),
        ('biSizeImage', wintypes.DWORD), ('biXPelsPerMeter', wintypes.LONG),
        ('biYPelsPerMeter', wintypes.LONG), ('biClrUsed', wintypes.DWORD),
        ('biClrImportant', wintypes.DWORD),
    ]


class BMI(ctypes.Structure):
    _fields_ = [('bmiHeader', BMIH), ('bmiColors', wintypes.DWORD * 3)]


def capture(hwnd, out):
    r = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    W, H = r.right - r.left, r.bottom - r.top
    if W <= 0 or H <= 0:
        return False
    hdc = user32.GetWindowDC(hwnd)
    mem = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, W, H)
    gdi32.SelectObject(mem, bmp)
    user32.PrintWindow(hwnd, mem, 2)  # PW_RENDERFULLCONTENT
    bmi = BMI()
    bmi.bmiHeader.biSize = ctypes.sizeof(BMIH)
    bmi.bmiHeader.biWidth = W
    bmi.bmiHeader.biHeight = -H  # top-down
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = 0
    buf = ctypes.create_string_buffer(W * H * 4)
    gdi32.GetDIBits(mem, bmp, 0, H, buf, ctypes.byref(bmi), 0)
    Image.frombuffer('RGBA', (W, H), buf.raw, 'raw', 'BGRA', 0, 1).save(out)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mem)
    user32.ReleaseDC(hwnd, hdc)
    return True


if __name__ == "__main__":
    out = sys.argv[1]
    for _ in range(60):
        wins = [w for w in gw.getAllWindows() if 'Zcode' in (w.title or '')]
        if wins:
            break
        time.sleep(0.4)
    print('found', len(wins))
    if wins:
        print('capturing', wins[0].title, wins[0].box)
        ok = capture(wins[0]._hWnd, out)
        print('ok' if ok else 'fail')
    else:
        print('no Zcode window found')
        sys.exit(1)
