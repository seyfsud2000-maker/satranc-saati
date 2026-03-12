import os
os.environ['KIVY_AUDIO'] = 'sdl2'

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.properties import NumericProperty, StringProperty, BooleanProperty, ListProperty
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.core.audio import SoundLoader

# --- Interfeýs Dizaýny (KV) ---
KV = """
<GameScreen>:
    name: "oyun"
    BoxLayout:
        orientation: 'vertical'

        # ÝOKARKY OÝUNÇY
        RelativeLayout:
            canvas.before:
                Color:
                    rgba: root.p2_bg
                Rectangle:
                    pos: self.pos
                    size: self.size
            Button:
                background_normal: ""
                background_color: (0.15, 0.4, 0.15, 1) if root.aktif_sira == "ust" and not root.oyun_bitti else (0, 0, 0, 0)
                on_release: root.hamle_yap("ust")
            Label:
                text: root.p2_text
                font_size: "110sp"
                bold: True
                canvas.before:
                    PushMatrix
                    Rotate:
                        angle: 180
                        origin: self.center
                canvas.after:
                    PopMatrix
            Label:
                text: "Göç: " + str(root.p2_goc)
                font_size: "22sp"
                color: 0.7, 0.7, 0.7, 1
                size_hint: (None, None)
                size: self.texture_size
                pos_hint: {"top": 0.98, "right": 0.98}
                canvas.before:
                    PushMatrix
                    Rotate:
                        angle: 180
                        origin: self.center
                canvas.after:
                    PopMatrix

        # DOLANDYRYŞ PANELI
        BoxLayout:
            size_hint_y: 0.1
            spacing: 2
            canvas.before:
                Color:
                    rgba: 0.12, 0.12, 0.12, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Button:
                text: "SIFYRLA"
                bold: True
                background_normal: ""
                background_color: 0.2, 0.2, 0.2, 1
                on_release: root.reset_game()
            Button:
                text: "BAŞLAT" if root.duraklatildi else "DURDUR"
                bold: True
                background_normal: ""
                background_color: (0.2, 0.5, 0.2, 1) if root.duraklatildi else (0.6, 0.2, 0.2, 1)
                on_release: root.toggle_pause()
            Button:
                text: "SAZLAMALAR"
                bold: True
                background_normal: ""
                background_color: 0.2, 0.2, 0.2, 1
                on_release: app.root.current = "ayarlar"

        # AŞAKKY OÝUNÇY
        RelativeLayout:
            canvas.before:
                Color:
                    rgba: root.p1_bg
                Rectangle:
                    pos: self.pos
                    size: self.size
            Button:
                background_normal: ""
                background_color: (0.15, 0.4, 0.15, 1) if root.aktif_sira == "alt" and not root.oyun_bitti else (0, 0, 0, 0)
                on_release: root.hamle_yap("alt")
            Label:
                text: root.p1_text
                font_size: "110sp"
                bold: True
            Label:
                text: "Göç: " + str(root.p1_goc)
                font_size: "22sp"
                color: 0.7, 0.7, 0.7, 1
                size_hint: (None, None)
                size: self.texture_size
                pos_hint: {"top": 0.98, "right": 0.98}

<SettingsScreen>:
    name: "ayarlar"
    BoxLayout:
        orientation: 'vertical'
        canvas.before:
            Color:
                rgba: 0.05, 0.05, 0.05, 1
            Rectangle:
                pos: self.pos
                size: self.size
        BoxLayout:
            size_hint_y: 0.12
            padding: 10
            spacing: 10
            Button:
                text: "← Yza"
                size_hint_x: 0.25
                bold: True
                on_release: app.root.current = "oyun"
            Label:
                text: "Wagt Sazlamalary"
                bold: True
                font_size: "18sp"
            Button:
                text: "Düzet"
                size_hint_x: 0.25
                background_color: 0.1, 0.4, 0.6, 1
                bold: True
                on_release: root.show_custom_dialog()

        ScrollView:
            BoxLayout:
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                padding: 20
                spacing: 15
                TimeBtn:
                    text: "1 Minut"
                    on_release: root.apply_time(60, 0)
                TimeBtn:
                    text: "3 Minut | 2 Sek"
                    on_release: root.apply_time(180, 2)
                TimeBtn:
                    text: "10 Minut"
                    on_release: root.apply_time(600, 0)

<TimeBtn@Button>:
    size_hint_y: None
    height: "70dp"
    background_normal: ""
    background_color: 0.18, 0.18, 0.18, 1
    font_size: "20sp"
"""

class GameScreen(Screen):
    p1_sure = NumericProperty(600)
    p2_sure = NumericProperty(600)
    p1_text = StringProperty("10:00")
    p2_text = StringProperty("10:00")
    p1_goc = NumericProperty(0)
    p2_goc = NumericProperty(0)
    aktif_sira = StringProperty("")
    duraklatildi = BooleanProperty(True)
    oyun_bitti = BooleanProperty(False)
    p1_bg = ListProperty([0.1, 0.1, 0.1, 1])
    p2_bg = ListProperty([0.1, 0.1, 0.1, 1])
    baslangic_suresi = 600
    bonus = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ses = None
        Clock.schedule_once(self.yukle_sesi, 1)
        Clock.schedule_interval(self.update_clock, 1)

    def yukle_sesi(self, dt):
        try:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'click.wav')
            if os.path.exists(path):
                self.ses = SoundLoader.load(path)
                if self.ses: self.ses.volume = 1.0
        except: pass

    def hamle_yap(self, taraf):
        if self.oyun_bitti: return
        if not self.duraklatildi and self.ses:
            self.ses.stop()
            self.ses.play()
        if self.duraklatildi: self.duraklatildi = False
        if taraf == "alt" and self.aktif_sira != "ust":
            if self.aktif_sira == "alt": self.p1_sure += self.bonus
            self.aktif_sira = "ust"
            self.p1_goc += 1
        elif taraf == "ust" and self.aktif_sira != "alt":
            if self.aktif_sira == "ust": self.p2_sure += self.bonus
            self.aktif_sira = "alt"
            self.p2_goc += 1
        self.sync_ui()

    def update_clock(self, dt):
        if not self.duraklatildi and self.aktif_sira and not self.oyun_bitti:
            if self.aktif_sira == "alt": 
                self.p1_sure -= 1
                if self.p1_sure <= 0: self.finish_game("p1")
            else: 
                self.p2_sure -= 1
                if self.p2_sure <= 0: self.finish_game("p2")
            self.sync_ui()

    def sync_ui(self):
        self.p1_text = f"{max(0, int(self.p1_sure))//60:02d}:{max(0, int(self.p1_sure))%60:02d}"
        self.p2_text = f"{max(0, int(self.p2_sure))//60:02d}:{max(0, int(self.p2_sure))%60:02d}"

    def toggle_pause(self):
        if not self.oyun_bitti:
            self.duraklatildi = not self.duraklatildi

    def finish_game(self, loser):
        self.oyun_bitti = True
        self.duraklatildi = True
        if loser == "p1": self.p1_bg = [0.8, 0, 0, 1] 
        else: self.p2_bg = [0.8, 0, 0, 1] 

    def reset_game(self):
        self.oyun_bitti = False
        self.duraklatildi = True
        self.aktif_sira = ""
        self.p1_goc = 0
        self.p2_goc = 0
        self.p1_sure = self.baslangic_suresi
        self.p2_sure = self.baslangic_suresi
        self.p1_bg = [0.1, 0.1, 0.1, 1]
        self.p2_bg = [0.1, 0.1, 0.1, 1]
        self.sync_ui()

class SettingsScreen(Screen):
    def apply_time(self, sec, bonus):
        game = self.manager.get_screen("oyun")
        game.baslangic_suresi = sec
        game.bonus = bonus
        game.reset_game()
        self.manager.current = "oyun"

    def show_custom_dialog(self):
        content = BoxLayout(orientation='vertical', padding=10, spacing=8)
        row1 = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height="45dp")
        row1.add_widget(Label(text="Minut:", bold=True))
        self.min_input = TextInput(text='5', multiline=False, input_filter='int', font_size="22sp")
        row1.add_widget(self.min_input)
        row2 = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height="45dp")
        row2.add_widget(Label(text="Bonus:", bold=True))
        self.sec_input = TextInput(text='2', multiline=False, input_filter='int', font_size="22sp")
        row2.add_widget(self.sec_input)
        btn = Button(text="TASSYKHLA", size_hint_y=None, height="50dp", background_color=(0.1, 0.6, 0.1, 1), bold=True)
        content.add_widget(row1)
        content.add_widget(row2)
        content.add_widget(btn)
        self.popup = Popup(title='Wagtyňy Düz', content=content, size_hint=(0.85, 0.28))
        btn.bind(on_release=self.set_custom_time)
        self.popup.open()

    def set_custom_time(self, instance):
        try:
            m = int(self.min_input.text) if self.min_input.text else 0
            s = int(self.sec_input.text) if self.sec_input.text else 0
            self.apply_time(m * 60, s)
            self.popup.dismiss()
        except: pass

class ChessApp(App):
    def build(self):
        Builder.load_string(KV)
        sm = ScreenManager(transition=NoTransition())
        sm.add_widget(GameScreen(name='oyun'))
        sm.add_widget(SettingsScreen(name='ayarlar'))
        return sm

if __name__ == "__main__":
    ChessApp().run()
