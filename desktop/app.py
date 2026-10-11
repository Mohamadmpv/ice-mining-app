from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.core.window import Window
import requests

# اندازه پنجره
Window.size = (400, 700)


class IceDesktopApp(App):
    def build(self):
        self.title = "Ice Miner - Desktop"
        self.server_url = "http://127.0.0.1:8000"
        self.username = "kiyashah"

        root = BoxLayout(orientation="vertical", padding=20, spacing=10)

        # عنوان
        root.add_widget(Label(
            text="[b]⛏ Ice Mining App[/b]",
            markup=True,
            font_size=28,
            size_hint=(1, 0.1)
        ))

        # وضعیت
        self.status_label = Label(
            text="آماده",
            font_size=16,
            size_hint=(1, 0.15),
            halign="center"
        )
        root.add_widget(self.status_label)

        # آدرس سرور
        root.add_widget(Label(
            text="آدرس سرور:",
            size_hint=(1, 0.05),
            halign="center"
        ))
        self.server_input = TextInput(
            text=self.server_url,
            multiline=False,
            size_hint=(1, 0.08),
            font_size=16
        )
        root.add_widget(self.server_input)

        # نام کاربری
        root.add_widget(Label(
            text="نام کاربری:",
            size_hint=(1, 0.05),
            halign="center"
        ))
        self.username_input = TextInput(
            text=self.username,
            multiline=False,
            size_hint=(1, 0.08),
            font_size=16
        )
        root.add_widget(self.username_input)

        # دکمه چک‌این
        btn_checkin = Button(
            text="⛏ چک‌این و استخراج",
            size_hint=(1, 0.15),
            background_color=(0.2, 0.8, 0.4, 1),
            font_size=22,
            bold=True
        )
        btn_checkin.bind(on_press=self.do_checkin)
        root.add_widget(btn_checkin)

        # دکمه اطلاعات
        btn_info = Button(
            text="📊 اطلاعات من",
            size_hint=(1, 0.12),
            background_color=(0.2, 0.5, 0.9, 1),
            font_size=18
        )
        btn_info.bind(on_press=self.do_info)
        root.add_widget(btn_info)

        # دکمه ثبت‌نام (اگر کاربر جدید بود)
        btn_register = Button(
            text="📝 ثبت‌نام",
            size_hint=(1, 0.1),
            background_color=(0.9, 0.6, 0.2, 1),
            font_size=16
        )
        btn_register.bind(on_press=self.do_register)
        root.add_widget(btn_register)

        # دکمه KYC
        btn_kyc = Button(
            text="🆔 احراز هویت (KYC)",
            size_hint=(1, 0.1),
            background_color=(0.6, 0.3, 0.8, 1),
            font_size=16
        )
        btn_kyc.bind(on_press=self.do_kyc)
        root.add_widget(btn_kyc)

        # لاگ پایین صفحه
        self.log_label = Label(
            text="",
            size_hint=(1, 0.1),
            font_size=12,
            halign="center"
        )
        root.add_widget(self.log_label)

        return root

    # --- توابع کمکی ---
    def show_popup(self, title, message):
        popup = Popup(
            title=title,
            content=Label(text=message, font_size=14),
            size_hint=(0.85, 0.5)
        )
        popup.open()

    def update_status(self, text):
        self.status_label.text = text
        self.log_label.text = text

    def get_server(self):
        return self.server_input.text.strip().rstrip("/")

    def get_username(self):
        return self.username_input.text.strip()

    # --- عملیات ---
    def do_register(self, instance):
        username = self.get_username()
        if not username:
            self.show_popup("خطا", "نام کاربری را وارد کنید")
            return
        try:
            url = f"{self.get_server()}/register"
            r = requests.post(url, json={"username": username}, timeout=10)
            if r.status_code == 200:
                data = r.json()
                msg = f"ثبت‌نام موفق!\nکد معرف: {data['your_code']}"
                self.update_status(msg)
                self.show_popup("موفق ✅", msg)
            else:
                self.show_popup("خطا", r.json().get("detail", "خطای ناشناخته"))
        except Exception as e:
            self.show_popup("خطای اتصال", str(e))

    def do_kyc(self, instance):
        username = self.get_username()
        if not username:
            self.show_popup("خطا", "نام کاربری را وارد کنید")
            return
        try:
            url = f"{self.get_server()}/kyc/{username}"
            r = requests.post(url, timeout=10)
            if r.status_code == 200:
                self.update_status("KYC تایید شد ✅")
                self.show_popup("موفق ✅", "احراز هویت انجام شد")
            else:
                self.show_popup("خطا", r.json().get("detail", "خطا"))
        except Exception as e:
            self.show_popup("خطای اتصال", str(e))

    def do_checkin(self, instance):
        username = self.get_username()
        if not username:
            self.show_popup("خطا", "نام کاربری را وارد کنید")
            return
        try:
            url = f"{self.get_server()}/checkin/{username}"
            r = requests.post(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                msg = (
                    f"✅ استخراج موفق!\n\n"
                    f"دریافتی: {data['earned']} ICE\n"
                    f"موجودی کل: {data['balance']} ICE\n"
                    f"تیم: {data['team_size']} نفر"
                )
                self.update_status(f"💰 موجودی: {data['balance']} ICE")
                self.show_popup("استخراج موفق 🎉", msg)
            else:
                self.show_popup("نشد!", r.json().get("detail", "خطا"))
        except Exception as e:
            self.show_popup("خطای اتصال", str(e))

    def do_info(self, instance):
        username = self.get_username()
        if not username:
            self.show_popup("خطا", "نام کاربری را وارد کنید")
            return
        try:
            url = f"{self.get_server()}/user/{username}"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                d = r.json()
                msg = (
                    f"👤 کاربر: {d['username']}\n\n"
                    f"💰 موجودی: {d['balance']} ICE\n"
                    f"👥 تیم: {d['team_size']} نفر\n"
                    f"🔑 کد معرف: {d['referral_code']}\n"
                    f"🆔 KYC: {'✅' if d['kyc_verified'] else '❌'}\n"
                    f"⏱ وضعیت: {d['remaining']}"
                )
                self.show_popup("اطلاعات من 📊", msg)
            else:
                self.show_popup("خطا", r.json().get("detail", "خطا"))
        except Exception as e:
            self.show_popup("خطای اتصال", str(e))


if __name__ == "__main__":
    IceDesktopApp().run()