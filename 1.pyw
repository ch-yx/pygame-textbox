import pygame
import clr
import sys


import ctypes.wintypes
from threading import Thread

clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")
clr.AddReference("System.Runtime")


import System

from System.Windows.Forms import (
    Form,
    Application,
    TextBox,
    DockStyle,
    FormBorderStyle,
    BorderStyle,
    Timer
)
from System.Drawing import Color, Font, FontStyle, Bitmap, Imaging, Color, Rectangle
from System.Drawing.Imaging import PixelFormat
import System.Runtime

# Define some constants
WS_EX_LAYERED = 0x00080000
LWA_COLORKEY = 0x00000001
LWA_ALPHA = 0x00000002


class CustomTextBox(TextBox):
    def __init__(self, colorkey, color):
        super().__init__()

        self.BackColor = Color.FromArgb(255, *reversed(colorkey))
        self.ForeColor = Color.FromArgb(255, *reversed(color))
        self.Font = Font("Arial", 20, FontStyle.Bold)
        self.BorderStyle = BorderStyle(0)
        self.Multiline = True


class LayeredForm(Form):
    last_screen = None

    def __init__(self, colorkey, color):
        super().__init__()
        self.Width = 200
        self.Height = 100
        self.FormBorderStyle = FormBorderStyle(0)
        self.MaximizeBox = False
        self.MinimizeBox = False
        self.TopLevel = False
        self.AllowTransparency = True

        self.BackColor_ori = colorkey

        self.textbox = CustomTextBox(colorkey, color)
        self.textbox.Dock = DockStyle.Fill
        self.Controls.Add(self.textbox)

        self.Load += self.on_load
        bitmap = self.bitmap = Bitmap(self.Width, self.Height)
        self.rgbValues = System.Array.CreateInstance(
            System.Byte, bitmap.Width * bitmap.Height * 3
        )

    def on_load(self, sender, event):
        happ = self.Handle.ToInt64()
        exstyle = ctypes.windll.user32.GetWindowLongPtrA(happ, -20)
        exstyle |= WS_EX_LAYERED
        ctypes.windll.user32.SetWindowLongPtrA(happ, -20, exstyle)
        ctypes.windll.user32.SetLayeredWindowAttributes(happ, 0, 1, LWA_ALPHA)
    def on_timer_tick(self, sender, event):
        self.update_bitmap()
        if self.pygame_window_handle:
            self.update_pygame_screen()
    def update_bitmap(self):
    # 更新Bitmap以反映当前的TextBox状态
        self.textbox.DrawToBitmap(self.bitmap, self.textbox.Bounds)
        # 将Bitmap的数据复制到rgbValues数组中
        bitmap_data = self.bitmap.LockBits(
            Rectangle(0, 0, self.bitmap.Width, self.bitmap.Height),
            Imaging.ImageLockMode.ReadOnly,
            PixelFormat.Format24bppRgb,
        )
        System.Runtime.InteropServices.Marshal.Copy(
            bitmap_data.Scan0, self.rgbValues, 0, self.bitmap.Width * self.bitmap.Height * 3
        )
        self.bitmap.UnlockBits(bitmap_data)
        
    def update_pygame_screen(self):
        # 将rgbValues转换为pygame Surface
        surface = pygame.image.frombuffer(
            memoryview(self.rgbValues), (self.bitmap.Width, self.bitmap.Height), "RGB"
        )
        surface.set_colorkey(self.BackColor_ori)
        # 使用pygame的Surface更新pygame的屏幕
        self.last_screen=surface
    def run(self):
        def task():
            self.timer = Timer()
            self.timer.Interval = 1000//60   # 设置时间间隔，单位毫秒
            self.timer.Tick += self.on_timer_tick
            self.timer.Enabled = True
            Application.Run(self)
        Thread(target=task).start()

    def Close(self):
        data = self.textbox.Text
        super().Close()
        return data

    def update_layered_window(self, screen, tick):
        if self.last_screen is not None:
            screen.blit(self.last_screen, self.posinpygame)
        


def create_layered_form(pygame_window_handle, pos, colorkey, color):
    pygame_window_handle = pygame_window_handle.get_wm_info()["window"]
    app = LayeredForm(colorkey, color)
    happ = app.Handle.ToInt64()
    app.pygame_window_handle = pygame_window_handle
    app.posinpygame = pos

    ctypes.windll.user32.SetParent(happ, pygame_window_handle)

    # Set the position and size of the layered window
    ctypes.windll.user32.SetWindowPos(
        happ,
        0,  # HWND_TOP
        pos[0],
        pos[1],
        200,  # Width
        100,  # Height
        0x0040,  # SWP_SHOWWINDOW
    )
    app.run()
    return app


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
    pygame.display.set_caption("Pygame with WinForms Example")

    textbox = create_layered_form(pygame.display, (40, 80), (0, 0, 0), (255, 255, 255))
    clock = pygame.time.Clock()
    running = True
    tick = 0
    while running:
        if textbox and textbox.IsHandleCreated:
            Application.DoEvents()
        
        tick += 1
        screen.fill("blue")
        pygame.draw.rect(screen, "red", pygame.Rect(30, 30+tick%60, 60, 60))
        textbox.update_layered_window(screen, tick)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                print(textbox.Close())
            if event.type == pygame.MOUSEBUTTONDOWN:
                print(event)
                ctypes.windll.user32.SetFocus(pygame.display.get_wm_info()["window"])
            
        pygame.display.flip()

        clock.tick(60)
    pygame.quit()
    sys.exit()
