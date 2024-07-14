import pygame
import clr
import sys
import ctypes
import clr
clr.AddReference('System.Windows.Forms')
clr.AddReference("System.Drawing")
from ctypes.wintypes import BOOL, HWND, RECT, UINT, LPARAM, WPARAM
from System.Windows.Forms import Form, Application, TextBox, DockStyle, FormBorderStyle
from System.Drawing import Color, Font, FontStyle, Bitmap, Imaging, Color, Rectangle

from threading import Thread


WM_IME_STARTCOMPOSITION = 0x010D
WM_IME_ENDCOMPOSITION = 0x010E
class TextBox(TextBox):
    def __init__(self,*x,**y):
        super().__init__(*x,**y)
        self.Font = Font("Arial", 20, FontStyle.Bold)

class WinFormsApp(Form):
    def __init__(self):
        super().__init__()
        self.Text = 'WinForms TextBox'
        self.Width = 200
        self.Height = 100
        self.FormBorderStyle = FormBorderStyle(0)
        self.MaximizeBox = False
        self.MinimizeBox = False
        self.textbox = TextBox()
        self.textbox.Multiline = True
        self.textbox.Dock = DockStyle.Fill
        self.Controls.Add(self.textbox)
        self.TopLevel = False

    def run(self):
        Thread(target=lambda: Application.Run(self)).start()

    def Close(self):
        data = self.textbox.Text
        super().Close()
        return data

def embed_winforms_into_pygame(pygame_window_handle, pos):
    pygame_window_handle = pygame_window_handle.get_wm_info()['window']
    app = WinFormsApp()
    happ = app.Handle.ToInt64()
    ctypes.windll.user32.SetParent(happ, pygame_window_handle)
    ctypes.windll.user32.SetWindowPos(
        happ,
        0,  # HWND_TOP
        pos[0], pos[1],
        200,  # Width
        100,  # Height
        0x0040  # SWP_SHOWWINDOW
    )

    app.run()
    return app

if __name__ == "__main__":
    pygame.init()
    surface=pygame.display.set_mode((800, 600))
    pygame.display.set_caption('Pygame with WinForms Example')

    textbox = embed_winforms_into_pygame(pygame.display, (40, 80))
    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                print(textbox.Close())
            if event.type == pygame.MOUSEBUTTONDOWN:
                ctypes.windll.user32.SetFocus(pygame.display.get_wm_info()["window"])
        pygame.draw.rect(surface, (255,0,0), pygame.Rect(30, 30, 80, 80))
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()
    sys.exit()
