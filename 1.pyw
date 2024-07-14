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

    def on_load(self, sender, event):
        happ = self.Handle.ToInt64()
        exstyle = ctypes.windll.user32.GetWindowLongPtrA(happ, -20)
        exstyle |= WS_EX_LAYERED
        ctypes.windll.user32.SetWindowLongPtrA(happ, -20, exstyle)
        ctypes.windll.user32.SetLayeredWindowAttributes(happ, 0, 1, LWA_ALPHA)

    def run(self):
        Thread(target=lambda: Application.Run(self)).start()

    def Close(self):
        data = self.textbox.Text
        super().Close()
        return data

    def update_layered_window(self, screen, tick):
        if tick % 2:
            if self.last_screen is not None:
                screen.blit(self.last_screen, self.posinpygame)
            return
        happ = self.Handle.ToInt64()
        hdc = ctypes.windll.user32.GetDC(self.pygame_window_handle)
        # memdc = ctypes.windll.gdi32.CreateCompatibleDC(hdc)
        bitmap = Bitmap(self.Width, self.Height)

        self.textbox.DrawToBitmap(bitmap, self.textbox.Bounds)

        bitmap_data = bitmap.LockBits(
            Rectangle(0, 0, bitmap.Width, bitmap.Height),
            Imaging.ImageLockMode.ReadOnly,
            PixelFormat.Format24bppRgb,
        )
        # breakpoint()
        rgbValues = System.Array.CreateInstance(
            System.Byte, bitmap.Width * bitmap.Height * 3
        )
        System.Runtime.InteropServices.Marshal.Copy(
            bitmap_data.Scan0, rgbValues, 0, bitmap.Width * bitmap.Height * 3
        )

        surface = pygame.image.frombuffer(
            memoryview(rgbValues), (bitmap.Width, bitmap.Height), "RGB"
        )
        bitmap.UnlockBits(bitmap_data)
        surface.set_colorkey(self.BackColor_ori)

        screen.blit(surface, self.posinpygame)
        self.last_screen = surface


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
        tick += 1
        screen.fill("blue")
        pygame.draw.rect(screen, "red", pygame.Rect(30, 30, 60, 60))
        textbox.update_layered_window(screen, tick)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                print(textbox.Close())
        pygame.display.flip()

        clock.tick(60)
    pygame.quit()
    sys.exit()
