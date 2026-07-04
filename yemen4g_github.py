#!/usr/bin/env python3
"""
Yemen 4G Balance Indicator for Linux (GNOME/GTK)
Automatically solves the Altcha Proof-of-Work challenge to fetch balance.
"""
import sys
import threading
import requests
import hashlib
import json
import base64
import os
from bs4 import BeautifulSoup

import gi
gi.require_version('Gtk', '3.0')
try:
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import AyatanaAppIndicator3 as appindicator
except ValueError:
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3 as appindicator

gi.require_version('Notify', '0.7')
from gi.repository import Gtk, GLib, Notify
import re

CONFIG_FILE = os.path.expanduser("~/.yemen4g_config")

class Yemen4GIndicator:
    def __init__(self):
        self.session = requests.Session()
        self.config = self.load_config()
        self.last_details = "جاري الاتصال..."
        self.timer_id = None
        
        # Initialize Indicator
        self.indicator = appindicator.Indicator.new(
            "yemen-4g-indicator",
            "network-cellular-connected",
            appindicator.IndicatorCategory.APPLICATION_STATUS)
        self.indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.indicator.set_label("4G: Init...", "4G: Init...")
        
        # Build Menu
        self.menu = Gtk.Menu()
        
        self.refresh_item = Gtk.MenuItem(label="تحديث الرصيد (Refresh)")
        self.refresh_item.connect("activate", self.on_refresh)
        self.menu.append(self.refresh_item)
        
        self.details_item = Gtk.MenuItem(label="عرض التفاصيل كاملة")
        self.details_item.connect("activate", self.on_show_details)
        self.menu.append(self.details_item)
        
        self.menu.append(Gtk.SeparatorMenuItem())
        
        # Interval Submenu
        interval_item = Gtk.MenuItem(label="معدل التحديث التلقائي")
        interval_menu = Gtk.Menu()
        interval_item.set_submenu(interval_menu)
        
        self.intervals = {
            "إيقاف (يدوي فقط)": 0,
            "كل 15 دقيقة": 900,
            "كل 30 دقيقة": 1800,
            "كل 1 ساعة": 3600
        }
        
        for label, seconds in self.intervals.items():
            item = Gtk.MenuItem(label=label)
            item.connect("activate", self.on_interval_change, seconds)
            interval_menu.append(item)
            
        self.menu.append(interval_item)
        
        self.change_num_item = Gtk.MenuItem(label="تغيير رقم الهاتف")
        self.change_num_item.connect("activate", self.on_change_number)
        self.menu.append(self.change_num_item)
        
        self.quit_item = Gtk.MenuItem(label="خروج (Quit)")
        self.quit_item.connect("activate", self.on_quit)
        self.menu.append(self.quit_item)
        
        self.menu.show_all()
        self.indicator.set_menu(self.menu)
        
        Notify.init("Yemen4G")
        
        # Start fetch logic
        GLib.idle_add(self.start_fetch_background)
        self.apply_interval()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"phone": "", "interval": 900}

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f)

    def apply_interval(self):
        if self.timer_id is not None:
            GLib.source_remove(self.timer_id)
            self.timer_id = None
            
        interval = self.config.get("interval", 900)
        if interval > 0:
            self.timer_id = GLib.timeout_add_seconds(interval, self.auto_refresh)

    def on_interval_change(self, widget, seconds):
        self.config["interval"] = seconds
        self.save_config()
        self.apply_interval()
        status = "يدوي فقط" if seconds == 0 else f"كل {seconds//60} دقيقة"
        Notify.Notification.new("Yemen 4G", f"تم تغيير التحديث التلقائي إلى: {status}", "network-cellular-connected").show()

    def prompt_for_number(self):
        dialog = Gtk.Dialog(title="Yemen 4G", flags=Gtk.DialogFlags.MODAL)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                           Gtk.STOCK_OK, Gtk.ResponseType.OK)
        box = dialog.get_content_area()
        box.set_spacing(10)
        box.set_margin_top(15)
        box.set_margin_bottom(15)
        box.set_margin_start(15)
        box.set_margin_end(15)
        
        box.pack_start(Gtk.Label(label="أدخل رقم هاتف يمن فور جي:", xalign=0), False, False, 0)
        entry = Gtk.Entry()
        entry.set_text(self.config.get("phone", ""))
        box.pack_start(entry, False, False, 0)
        box.show_all()
        
        response = dialog.run()
        new_number = entry.get_text().strip() if response == Gtk.ResponseType.OK else None
        dialog.destroy()
        return new_number

    def auto_refresh(self):
        self.start_fetch_background()
        return True

    def start_fetch_background(self, *args):
        if not self.config.get("phone"):
            new_num = self.prompt_for_number()
            if not new_num:
                self.indicator.set_label("4G: No Number", "4G: No Number")
                return
            self.config["phone"] = new_num
            self.save_config()
            
        self.indicator.set_label("4G: Fetching...", "4G: Fetching...")
        threading.Thread(target=self.solve_altcha_and_fetch, daemon=True).start()
        
    def solve_altcha_and_fetch(self):
        try:
            page_url = "https://ptc.gov.ye/?page_id=9017"
            response = self.session.get(page_url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            hidden_inputs = {}
            form = soup.find('form', id='qbill_formnew')
            if form:
                for hidden in form.find_all('input', type='hidden'):
                    hidden_inputs[hidden.get('name')] = hidden.get('value', '')
            
            altcha = soup.find('altcha-widget')
            if not altcha:
                GLib.idle_add(self.update_ui, "Error", "لم يتم العثور على نظام الحماية في الموقع")
                return
                
            challenge_url = altcha.get('challengeurl', '')
            if not challenge_url.startswith('http'):
                challenge_url = "https://ptc.gov.ye" + challenge_url
                
            c_res = self.session.get(challenge_url, timeout=10)
            challenge_data = c_res.json()
            salt = challenge_data.get('salt', '')
            challenge_hash = challenge_data.get('challenge', '')
            maxnumber = challenge_data.get('maxnumber', 100000)
            
            solved_b64 = None
            for number in range(maxnumber + 1):
                test_str = salt + str(number)
                if hashlib.sha256(test_str.encode('utf-8')).hexdigest() == challenge_hash:
                    payload = challenge_data.copy()
                    payload['number'] = number
                    solved_b64 = base64.b64encode(json.dumps(payload).encode('utf-8')).decode('utf-8')
                    break
                    
            if not solved_b64:
                GLib.idle_add(self.update_ui, "Error", "فشل في حل لغز الحماية (Altcha)")
                return

            payload_post = hidden_inputs.copy()
            payload_post['phone4gidnew'] = self.config.get("phone")
            payload_post['qsubmitnew'] = 'استعلام'
            payload_post['security_token_4gbill'] = solved_b64
            
            post_res = self.session.post(page_url, data=payload_post, timeout=15)
            post_soup = BeautifulSoup(post_res.text, 'html.parser')
            
            balance = "غير معروف"
            expire_date = "غير معروف"
            
            text_list = list(post_soup.stripped_strings)
            for i, text in enumerate(text_list):
                if "الرصيد" in text or "المتاح" in text:
                    for j in range(1, 6):
                        if i + j < len(text_list):
                            match = re.search(r'(\d+(\.\d+)?)\s*(GB|MB|جيجا|ميجا)', text_list[i+j], re.IGNORECASE)
                            if match:
                                balance = match.group(0)
                                break
                    if balance != "غير معروف":
                        break
                        
            for i, text in enumerate(text_list):
                if "تاريخ" in text or "انتهاء" in text:
                    for j in range(1, 6):
                        if i + j < len(text_list):
                            match = re.search(r'(\d{2,4}[-/]\d{1,2}[-/]\d{2,4})', text_list[i+j])
                            if match:
                                expire_date = match.group(0)
                                break
                    if expire_date != "غير معروف":
                        break

            if balance == "غير معروف":
                gb_match = re.search(r'(\d+(\.\d+)?)\s*(GB|جيجا)', post_res.text, re.IGNORECASE)
                if gb_match:
                    balance = gb_match.group(0)

            details = f"رقم الهاتف: {self.config.get('phone')}\nالرصيد المتاح: {balance}\nتاريخ الانتهاء: {expire_date}"
            GLib.idle_add(self.update_ui, balance, details)
            
        except Exception as e:
            print("Error fetching details:", e)
            GLib.idle_add(self.update_ui, "Error", f"خطأ: {str(e)}")

    def update_ui(self, balance, details):
        self.indicator.set_label(f"4G: {balance}", f"4G: {balance}")
        self.last_details = details

    def on_refresh(self, widget):
        self.start_fetch_background()

    def on_change_number(self, widget):
        new_num = self.prompt_for_number()
        if new_num:
            self.config["phone"] = new_num
            self.save_config()
            self.start_fetch_background()

    def on_show_details(self, widget):
        notification = Notify.Notification.new("تفاصيل رصيد يمن فور جي", self.last_details, "network-cellular-connected")
        notification.show()

    def on_quit(self, widget):
        Gtk.main_quit()

if __name__ == "__main__":
    app = Yemen4GIndicator()
    Gtk.main()
