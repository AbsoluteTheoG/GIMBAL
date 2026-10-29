"""Gimbal : associe les contrôles d'un HOTAS à des touches clavier/souris
ou à une manette Xbox 360 virtuelle.

Dépendances : pygame-ce (lecture des joysticks), vgamepad (manette virtuelle,
nécessite le pilote ViGEmBus) et Pillow (image du HOTAS).
"""
import copy
import ctypes
import json
import math
import os
import shutil
import sys
import threading
import time
import tkinter as tk
import traceback
from ctypes import wintypes
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

APP_NAME = "Gimbal"  # aussi le titre de fenêtre cherché par focus_running_instance
APP_VERSION = "1.0.0"
# Version .exe (PyInstaller) : profils et réglages à côté de Gimbal.exe, pas dans le dossier temporaire.
APP_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
LOG_FILE = APP_DIR / "gimbal_error.log"


# --- Traductions --------------------------------------------------------------------

STRINGS = {
    "fr": {
        "out_key": "Touche clavier / souris", "out_pad_button": "Bouton manette",
        "out_pad_axis": "Axe manette", "out_mouse": "Mouvement souris",
        "hat_up": "haut", "hat_down": "bas", "hat_left": "gauche", "hat_right": "droite",
        "src_button": "Bouton {n}", "src_hat": "Hat {n} {dir}", "src_axis": "Axe {n}",
        "desc_key": "Touche", "desc_pad_button": "Manette · bouton", "desc_pad_axis": "Manette · axe",
        "desc_mouse": "Souris · axe",
        "short_key": "Touche", "short_pad_button": "Manette", "short_pad_axis": "Manette",
        "short_mouse": "Souris", "short_toggle": "(bascule)",
        "opt_inverted": "inversé", "opt_full_range": "course complète", "opt_deadzone": "zone morte {p}",
        "opt_toggle": "basculer", "opt_threshold": "seuil {p}",
        "status_starting": "Démarrage…", "status_engine_error": "Erreur moteur : {msg}",
        "status_paused": "Mapping en pause", "status_kb": "Sortie clavier / souris",
        "status_pad": "Manette virtuelle Xbox 360 active", "status_pad_error": "Manette virtuelle indisponible : {msg}",
        "error_title": "{app} : erreur", "error_details": "Détails dans {file}",
        "dlg_edit": "Modifier le bind", "dlg_new": "Nouveau bind", "dlg_control": "Contrôle HOTAS",
        "dlg_detect": "Détecter", "dlg_out_type": "Type de sortie", "dlg_target": "Cible",
        "dlg_capture": "Capturer une touche", "dlg_press_key": "Appuie sur une touche…", "dlg_options": "Options",
        "dlg_invert": "Inverser le sens", "dlg_centered": "Axe centré (décocher pour une manette des gaz)",
        "dlg_deadzone": "Zone morte (0 – 0.5)", "dlg_speed": "Vitesse (pixels / s)",
        "dlg_threshold": "Seuil de déclenchement (0.1 – 0.95)",
        "dlg_toggle": "Basculer (un appui = activé, un autre = désactivé)",
        "cancel": "Annuler", "ok": "OK",
        "dlg_src_placeholder": "Clique sur « Détecter » puis actionne le contrôle",
        "dlg_hint_analog": "Pendant la détection, pousse l'axe dans le sens « + » de la cible : "
                           "droite, haut (vers l'avant) ou appui.",
        "dlg_hint_digital": "Pendant la détection, appuie sur le bouton ou pousse l'axe dans le sens "
                            "qui doit déclencher la sortie.",
        "dlg_detecting": "Bouge ou appuie sur un contrôle du HOTAS…",
        "dlg_need_src": "Détecte d'abord un contrôle du HOTAS.",
        "view_choose_image": "Choisir l'image…", "view_edit_mode": "Mode placement",
        "view_add_bound": "Ajouter les contrôles déjà bindés",
        "view_hint_idle": "Clic droit sur une étiquette pour la modifier, double-clic pour éditer son bind.",
        "view_hint_edit": "Actionne un contrôle du HOTAS : son étiquette apparaît, glisse-la sur le bouton. "
                          "Tire sur les bords pour l'étirer. (Mapping en pause)",
        "view_hint_need_edit": "Active « Mode placement » pour déplacer et étirer les étiquettes.",
        "view_image_missing": "Image introuvable : {path}", "view_image_title": "Image du HOTAS",
        "filetype_images": "Images", "filetype_all": "Tous les fichiers",
        "view_empty": "Choisis une image de ton HOTAS avec « Choisir l'image… »,\n"
                      "puis active « Mode placement » et actionne les contrôles.",
        "label_free": "libre", "menu_edit": "Modifier : {out}", "menu_add": "Ajouter un bind sur ce contrôle…",
        "menu_rename": "Renommer l'étiquette…", "menu_autosize": "Taille automatique",
        "menu_remove": "Retirer l'étiquette", "rename_title": "Étiquette",
        "rename_prompt": "Texte affiché au-dessus (vide pour aucun) :",
        "toggle_on": "●  ACTIVÉ", "toggle_off": "○  DÉSACTIVÉ", "subtitle": "HOTAS → clavier, souris, manette",
        "profile": "Profil", "new_profile": "Nouveau profil…", "open_profile": "Ouvrir un profil…",
        "save_as": "Enregistrer sous…", "live_inputs": "Entrées en direct", "tab_binds": "Binds",
        "tab_view": "Vue HOTAS", "col_src": "Contrôle HOTAS", "col_out": "Sortie", "col_opts": "Options",
        "btn_add": "＋  Ajouter", "btn_edit": "Modifier", "btn_dup": "Dupliquer", "btn_del": "Supprimer",
        "fd_new": "Nouveau profil", "fd_save": "Enregistrer le profil sous", "fd_open": "Ouvrir un profil",
        "filetype_profile": "Profil HOTAS", "invalid_profile": "Ce fichier n'est pas un profil valide.",
        "no_device": "Aucun joystick détecté. Branche ton HOTAS.", "buttons": "Boutons",
        "settings": "Réglages", "theme": "Thème", "theme_system": "Système", "theme_light": "Clair",
        "theme_dark": "Sombre", "language": "Langue", "binds_count": "{n} binds",
    },
    "en": {
        "out_key": "Keyboard / mouse key", "out_pad_button": "Gamepad button",
        "out_pad_axis": "Gamepad axis", "out_mouse": "Mouse movement",
        "hat_up": "up", "hat_down": "down", "hat_left": "left", "hat_right": "right",
        "src_button": "Button {n}", "src_hat": "Hat {n} {dir}", "src_axis": "Axis {n}",
        "desc_key": "Key", "desc_pad_button": "Gamepad · button", "desc_pad_axis": "Gamepad · axis",
        "desc_mouse": "Mouse · axis",
        "short_key": "Key", "short_pad_button": "Pad", "short_pad_axis": "Pad",
        "short_mouse": "Mouse", "short_toggle": "(toggle)",
        "opt_inverted": "inverted", "opt_full_range": "full range", "opt_deadzone": "deadzone {p}",
        "opt_toggle": "toggle", "opt_threshold": "threshold {p}",
        "status_starting": "Starting…", "status_engine_error": "Engine error: {msg}",
        "status_paused": "Mapping paused", "status_kb": "Keyboard / mouse output",
        "status_pad": "Virtual Xbox 360 pad active", "status_pad_error": "Virtual pad unavailable: {msg}",
        "error_title": "{app}: error", "error_details": "Details in {file}",
        "dlg_edit": "Edit binding", "dlg_new": "New binding", "dlg_control": "HOTAS control",
        "dlg_detect": "Detect", "dlg_out_type": "Output type", "dlg_target": "Target",
        "dlg_capture": "Capture a key", "dlg_press_key": "Press a key…", "dlg_options": "Options",
        "dlg_invert": "Invert direction", "dlg_centered": "Centered axis (uncheck for a throttle)",
        "dlg_deadzone": "Deadzone (0 – 0.5)", "dlg_speed": "Speed (pixels / s)",
        "dlg_threshold": "Trigger threshold (0.1 – 0.95)",
        "dlg_toggle": "Toggle (press once = on, press again = off)",
        "cancel": "Cancel", "ok": "OK",
        "dlg_src_placeholder": "Click “Detect”, then move the control",
        "dlg_hint_analog": "While detecting, push the axis toward the target's “+” direction: "
                           "right, up (forward) or pressed.",
        "dlg_hint_digital": "While detecting, press the button or push the axis in the direction "
                            "that should trigger the output.",
        "dlg_detecting": "Move or press a HOTAS control…",
        "dlg_need_src": "Detect a HOTAS control first.",
        "view_choose_image": "Choose image…", "view_edit_mode": "Layout mode",
        "view_add_bound": "Add bound controls",
        "view_hint_idle": "Right-click a label to change it, double-click to edit its binding.",
        "view_hint_edit": "Move a HOTAS control: its label appears, drag it onto the button. "
                          "Drag the edges to resize it. (Mapping paused)",
        "view_hint_need_edit": "Turn on “Layout mode” to move and resize labels.",
        "view_image_missing": "Image not found: {path}", "view_image_title": "HOTAS image",
        "filetype_images": "Images", "filetype_all": "All files",
        "view_empty": "Pick a picture of your HOTAS with “Choose image…”,\n"
                      "then turn on “Layout mode” and move the controls.",
        "label_free": "unbound", "menu_edit": "Edit: {out}", "menu_add": "Add a binding to this control…",
        "menu_rename": "Rename label…", "menu_autosize": "Automatic size",
        "menu_remove": "Remove label", "rename_title": "Label",
        "rename_prompt": "Text shown above (empty for none):",
        "toggle_on": "●  ENABLED", "toggle_off": "○  DISABLED", "subtitle": "HOTAS → keyboard, mouse, gamepad",
        "profile": "Profile", "new_profile": "New profile…", "open_profile": "Open profile…",
        "save_as": "Save as…", "live_inputs": "Live inputs", "tab_binds": "Bindings",
        "tab_view": "HOTAS view", "col_src": "HOTAS control", "col_out": "Output", "col_opts": "Options",
        "btn_add": "＋  Add", "btn_edit": "Edit", "btn_dup": "Duplicate", "btn_del": "Delete",
        "fd_new": "New profile", "fd_save": "Save profile as", "fd_open": "Open profile",
        "filetype_profile": "HOTAS profile", "invalid_profile": "This file is not a valid profile.",
        "no_device": "No joystick detected. Plug in your HOTAS.", "buttons": "Buttons",
        "settings": "Settings", "theme": "Theme", "theme_system": "System", "theme_light": "Light",
        "theme_dark": "Dark", "language": "Language", "binds_count": "{n} bindings",
    },
}
LANGUAGES = {"fr": "Français", "en": "English"}


def system_language():
    # Langue de l'interface Windows : identifiant principal 0x0C = français.
    return "fr" if ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF == 0x0C else "en"


LANG = system_language()  # remplacée par le réglage enregistré au démarrage de App


def tr(key, **kw):
    text = STRINGS[LANG].get(key) or STRINGS["en"][key]
    return text.format(**kw) if kw else text


def report_error(text):
    """Avec pythonw il n'y a pas de console : sans ça, une erreur au démarrage = « rien ne se passe »."""
    text = f"Python : {sys.executable}\n{text}"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"--- {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n{text}\n")
    except OSError:
        pass
    ctypes.windll.user32.MessageBoxW(None, f"{text[-1500:]}\n\n{tr('error_details', file=LOG_FILE.name)}",
                                     tr("error_title", app=APP_NAME), 0x10)


# Installé avant les imports tiers : un module manquant s'affiche aussi.
sys.excepthook = lambda exc, val, tb: report_error("".join(traceback.format_exception(exc, val, tb)))

# Dépendances embarquées (pip install --target libs pygame-ce vgamepad pillow) : l'appli
# ne dépend pas des paquets installés pour l'utilisateur et reste autonome si on la déplace.
sys.path.insert(0, str(APP_DIR / "libs"))

from PIL import Image, ImageDraw, ImageTk  # noqa: E402

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
# Indispensable : sans ça SDL ignore le joystick dès qu'une autre fenêtre (le jeu) a le focus.
os.environ["SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS"] = "1"
import pygame  # noqa: E402
import sv_ttk  # noqa: E402  (thème Sun Valley, clair / sombre)

try:
    import vgamepad as vg
except Exception:
    vg = None

PROFILES_DIR = APP_DIR / "profiles"
SETTINGS_FILE = APP_DIR / "settings.json"
POLL_HZ = 250
# Notre propre manette virtuelle remonte comme un joystick : on l'ignore pour éviter les boucles.
IGNORED_DEVICES = ("Xbox 360 Controller",)


# --- Sorties clavier / souris (SendInput) -------------------------------------

user32 = ctypes.WinDLL("user32", use_last_error=True)
ULONG_PTR = ctypes.c_size_t


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD), ("wParamH", wintypes.WORD)]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]


user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int)
user32.MapVirtualKeyW.argtypes = (wintypes.UINT, wintypes.UINT)
user32.MapVirtualKeyW.restype = wintypes.UINT

VK = {
    "BACKSPACE": 0x08, "TAB": 0x09, "ENTER": 0x0D, "PAUSE": 0x13, "CAPSLOCK": 0x14, "ESC": 0x1B,
    "SPACE": 0x20, "PAGEUP": 0x21, "PAGEDOWN": 0x22, "END": 0x23, "HOME": 0x24, "LEFT": 0x25,
    "UP": 0x26, "RIGHT": 0x27, "DOWN": 0x28, "PRINTSCREEN": 0x2C, "INSERT": 0x2D, "DELETE": 0x2E,
    "LWIN": 0x5B, "RWIN": 0x5C, "APPS": 0x5D, "NUM*": 0x6A, "NUM+": 0x6B, "NUM-": 0x6D,
    "NUM.": 0x6E, "NUM/": 0x6F, "NUMLOCK": 0x90, "SCROLLLOCK": 0x91, "LSHIFT": 0xA0,
    "RSHIFT": 0xA1, "LCTRL": 0xA2, "RCTRL": 0xA3, "LALT": 0xA4, "RALT": 0xA5,
    "OEM_1": 0xBA, "OEM_PLUS": 0xBB, "OEM_COMMA": 0xBC, "OEM_MINUS": 0xBD, "OEM_PERIOD": 0xBE,
    "OEM_2": 0xBF, "OEM_3": 0xC0, "OEM_4": 0xDB, "OEM_5": 0xDC, "OEM_6": 0xDD, "OEM_7": 0xDE,
    "OEM_8": 0xDF, "OEM_102": 0xE2,
}
VK.update({chr(c): c for c in range(0x41, 0x5B)})
VK.update({chr(c): c for c in range(0x30, 0x3A)})
VK.update({f"NUM{i}": 0x60 + i for i in range(10)})
VK.update({f"F{i}": 0x6F + i for i in range(1, 25)})
VK_NAMES = {v: k for k, v in VK.items()}

MOUSE_BUTTONS = {  # nom -> (flag appui, flag relâche, mouseData)
    "MOUSE1": (0x0002, 0x0004, 0), "MOUSE2": (0x0008, 0x0010, 0), "MOUSE3": (0x0020, 0x0040, 0),
    "MOUSE4": (0x0080, 0x0100, 1), "MOUSE5": (0x0080, 0x0100, 2),
}
WHEEL = {"WHEEL_UP": 120, "WHEEL_DOWN": -120}
KEY_NAMES = list(MOUSE_BUTTONS) + list(WHEEL) + list(VK)

# Tk donne VK_SHIFT/VK_CONTROL/VK_MENU sans distinguer gauche/droite : on passe par le keysym.
MODIFIER_KEYSYMS = {"Shift_L": "LSHIFT", "Shift_R": "RSHIFT", "Control_L": "LCTRL",
                    "Control_R": "RCTRL", "Alt_L": "LALT", "Alt_R": "RALT"}


def _send(*inputs):
    arr = (INPUT * len(inputs))(*inputs)
    user32.SendInput(len(inputs), arr, ctypes.sizeof(INPUT))


def _key_input(vk, up):
    # Les jeux lisent souvent les scancodes (DirectInput / Raw Input), pas les codes virtuels.
    sc = user32.MapVirtualKeyW(vk, 4)  # MAPVK_VK_TO_VSC_EX
    flags = 0x0008 | (0x0002 if up else 0)  # KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP
    if sc >> 8 in (0xE0, 0xE1):
        flags |= 0x0001  # KEYEVENTF_EXTENDEDKEY
    inp = INPUT(type=1)
    inp.ki = KEYBDINPUT(0, sc & 0xFF, flags, 0, 0)
    return inp


def _mouse_input(flags, data=0, dx=0, dy=0):
    inp = INPUT(type=0)
    inp.mi = MOUSEINPUT(dx, dy, data & 0xFFFFFFFF, flags, 0, 0)
    return inp


def send_key(name, up):
    if name in MOUSE_BUTTONS:
        down_flag, up_flag, data = MOUSE_BUTTONS[name]
        _send(_mouse_input(up_flag if up else down_flag, data))
    elif name in WHEEL:
        if not up:
            _send(_mouse_input(0x0800, WHEEL[name]))
    elif name in VK:
        _send(_key_input(VK[name], up))


def send_mouse_move(dx, dy):
    _send(_mouse_input(0x0001, 0, dx, dy))


def key_from_event(event):
    if event.keysym in MODIFIER_KEYSYMS:
        return MODIFIER_KEYSYMS[event.keysym]
    return VK_NAMES.get(event.keycode)


# --- Manette virtuelle ----------------------------------------------------------

PAD_BUTTONS = ["A", "B", "X", "Y", "LB", "RB", "LT", "RT", "BACK", "START", "LS", "RS",
               "DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT", "GUIDE"]
PAD_AXES = ["LX", "LY", "RX", "RY", "LT", "RT"]
XUSB_NAMES = {"LB": "LEFT_SHOULDER", "RB": "RIGHT_SHOULDER", "LS": "LEFT_THUMB", "RS": "RIGHT_THUMB"}


def xusb_button(name):
    return getattr(vg.XUSB_BUTTON, "XUSB_GAMEPAD_" + XUSB_NAMES.get(name, name))


# --- Modèle de bind ---------------------------------------------------------------
#
# {"src": {"dev": nom, "type": "button"|"hat"|"axis", "idx": int,
#          "dir": "up"/"down"/"left"/"right" (hat) ou 1/-1 (axe), "centered": bool (axe)},
#  "out": {"type": "key"|"pad_button"|"pad_axis"|"mouse", "target": str, "speed": px/s (souris)},
#  "invert": bool, "deadzone": float, "threshold": float, "mode": "hold"|"toggle"}
#
# Un axe vers une sortie analogique donne une valeur continue ; vers une sortie
# numérique (touche, bouton), il agit comme un bouton dans le sens "dir" au-delà du seuil.

OUT_KINDS = ["key", "pad_button", "pad_axis", "mouse"]
ANALOG_OUTS = {"pad_axis", "mouse"}
HAT_DIRS = {"up": (1, 1), "down": (1, -1), "left": (0, -1), "right": (0, 1)}  # (composante, valeur)
HINTS = {
    "fr": {
        "key": {"MOUSE1": "clic gauche", "MOUSE2": "clic droit", "MOUSE3": "clic molette",
                "MOUSE4": "bouton souris 4", "MOUSE5": "bouton souris 5",
                "WHEEL_UP": "molette haut", "WHEEL_DOWN": "molette bas"},
        "pad_button": {"LB": "bumper gauche", "RB": "bumper droit", "LT": "gâchette gauche",
                       "RT": "gâchette droite", "LS": "clic stick gauche", "RS": "clic stick droit",
                       "BACK": "View", "START": "Menu"},
        "pad_axis": {"LX": "stick gauche ↔", "LY": "stick gauche ↕", "RX": "stick droit ↔",
                     "RY": "stick droit ↕", "LT": "gâchette gauche", "RT": "gâchette droite"},
        "mouse": {"X": "horizontal", "Y": "vertical"},
    },
    "en": {
        "key": {"MOUSE1": "left click", "MOUSE2": "right click", "MOUSE3": "middle click",
                "MOUSE4": "mouse button 4", "MOUSE5": "mouse button 5",
                "WHEEL_UP": "wheel up", "WHEEL_DOWN": "wheel down"},
        "pad_button": {"LB": "left bumper", "RB": "right bumper", "LT": "left trigger",
                       "RT": "right trigger", "LS": "left stick click", "RS": "right stick click",
                       "BACK": "View", "START": "Menu"},
        "pad_axis": {"LX": "left stick ↔", "LY": "left stick ↕", "RX": "right stick ↔",
                     "RY": "right stick ↕", "LT": "left trigger", "RT": "right trigger"},
        "mouse": {"X": "horizontal", "Y": "vertical"},
    },
}
DEFAULT_TARGET = {"key": "SPACE", "pad_button": "A", "pad_axis": "LX", "mouse": "X"}


def target_label(kind, name):
    hint = HINTS[LANG][kind].get(name)
    if hint is None and kind == "key" and name.startswith("OEM"):
        ch = user32.MapVirtualKeyW(VK[name], 2) & 0x7FFF  # MAPVK_VK_TO_CHAR
        hint = chr(ch).lower() if ch else None
    return f"{name} ({hint})" if hint else name


def targets(kind):
    names = {"key": KEY_NAMES, "pad_button": PAD_BUTTONS, "pad_axis": PAD_AXES, "mouse": ["X", "Y"]}[kind]
    return [target_label(kind, n) for n in names]


def describe_src(src, analog):
    t, n = src["type"], src["idx"] + 1
    if t == "button":
        what = tr("src_button", n=n)
    elif t == "hat":
        what = tr("src_hat", n=n, dir=tr("hat_" + src["dir"]))
    elif analog:
        what = tr("src_axis", n=n)
    else:
        what = tr("src_axis", n=n) + (" +" if src["dir"] > 0 else " −")
    return f"{src['dev']} · {what}"


def describe_out(out):
    return tr("desc_" + out["type"]) + " " + target_label(out["type"], out["target"])


def describe_opts(b):
    is_axis = b["src"]["type"] == "axis"
    opts = []
    if b["out"]["type"] in ANALOG_OUTS:
        if b.get("invert"):
            opts.append(tr("opt_inverted"))
        if is_axis:
            if not b["src"].get("centered", True):
                opts.append(tr("opt_full_range"))
            opts.append(tr("opt_deadzone", p=f"{b.get('deadzone', 0.05):.0%}"))
        if b["out"]["type"] == "mouse":
            opts.append(f"{b['out'].get('speed', 800):.0f} px/s")
    else:
        if b.get("mode") == "toggle":
            opts.append(tr("opt_toggle"))
        if is_axis:
            opts.append(tr("opt_threshold", p=f"{b.get('threshold', 0.5):.0%}"))
    return ", ".join(opts)


def hat_dir(h):
    return "up" if h[1] > 0 else "down" if h[1] < 0 else "right" if h[0] > 0 else "left"


def input_key(src):
    """Identifie un contrôle physique (un axe garde la même clé dans les deux sens)."""
    return (src["dev"], src["type"], src["idx"]) + ((src["dir"],) if src["type"] == "hat" else ())


def short_input(src):
    n = src["idx"] + 1
    if src["type"] == "button":
        return f"B{n}"
    if src["type"] == "hat":
        return tr("src_hat", n=n, dir=tr("hat_" + src["dir"]))
    return tr("src_axis", n=n)


def short_devices(names):
    """Partie du nom qui distingue chaque périphérique (« VKBsim Gladiator EVO L » → « L »)."""
    names = sorted(set(names))
    if len(names) < 2:
        return {n: "" for n in names}
    words = [n.split() for n in names]
    common = 0
    while all(len(w) > common + 1 for w in words) and len({w[common] for w in words}) == 1:
        common += 1
    return {n: " ".join(w[common:]) for n, w in zip(names, words)}


def short_out(b):
    kind = b["out"]["type"]
    text = tr("short_" + kind) + " " + target_label(kind, b["out"]["target"])
    return text + " " + tr("short_toggle") if b.get("mode") == "toggle" else text


def _axis(st, idx):
    return st["axes"][idx] if idx < len(st["axes"]) else 0.0


def input_active(src, st):
    """Le contrôle est-il actionné (bouton appuyé, axe sorti de sa position de repos) ?"""
    if src["type"] != "axis":
        return digital_value({"src": src}, st)
    rest = 0.0 if src.get("centered", True) else -src["dir"]
    return abs(_axis(st, src["idx"]) - rest) > 0.15


def digital_value(b, st):
    s = b["src"]
    idx = s["idx"]
    if s["type"] == "button":
        return idx < len(st["buttons"]) and st["buttons"][idx]
    if s["type"] == "hat":
        if idx >= len(st["hats"]):
            return False
        comp, val = HAT_DIRS[s["dir"]]
        return st["hats"][idx][comp] == val
    return _axis(st, idx) * s["dir"] >= b.get("threshold", 0.5)


def analog_value(b, st):
    s = b["src"]
    sign = -1.0 if b.get("invert") else 1.0
    if s["type"] != "axis":
        return sign if digital_value(b, st) else 0.0
    v = _axis(st, s["idx"]) * sign
    if not s.get("centered", True):
        v = (v + 1) / 2  # manette des gaz : butée = 0, plein gaz = 1
    elif b["out"]["target"] in ("LT", "RT"):
        v = max(v, 0.0)
    dz = b.get("deadzone", 0.05)
    if abs(v) <= dz:
        return 0.0
    return math.copysign((abs(v) - dz) / (1 - dz), v)


# --- Moteur -----------------------------------------------------------------------

class Engine(threading.Thread):
    """Lit le HOTAS à POLL_HZ et applique les binds. Seul ce thread touche à pygame et aux sorties."""

    def __init__(self):
        super().__init__(daemon=True)
        self.enabled = True
        self.snapshot = {}          # nom du périphérique -> {"axes", "buttons", "hats"}
        self.active = frozenset()   # index des binds actuellement actifs (pour l'affichage)
        self.status = ("starting",)  # (code, *arguments), traduit par l'interface
        self._lock = threading.Lock()
        self._pending = None
        self._bindings = []
        self._pad_needed = False
        self._pad_failed = False
        self._running = True
        self._keys_down = set()
        self._pad = None
        self._pad_state = None
        self._mouse_frac = [0.0, 0.0]

    def set_bindings(self, bindings):
        with self._lock:
            self._pending = [dict(copy.deepcopy(b), _prev=False, _toggled=False) for b in bindings]

    def stop(self):
        self._running = False
        self.join(timeout=1.0)

    def run(self):
        try:
            self._loop()
        except Exception as e:
            self.status = ("engine_error", str(e))
        finally:
            self._release_all(close_pad=True)
            pygame.quit()

    def _loop(self):
        pygame.init()
        joys = {}
        was_enabled = False
        last = time.perf_counter()
        while self._running:
            for ev in pygame.event.get():
                if ev.type == pygame.JOYDEVICEADDED:
                    j = pygame.joystick.Joystick(ev.device_index)
                    joys[j.get_instance_id()] = j
                elif ev.type == pygame.JOYDEVICEREMOVED:
                    joys.pop(ev.instance_id, None)
            with self._lock:
                pending, self._pending = self._pending, None
            if pending is not None:
                self._release_all(close_pad=False)
                self._bindings = pending
                self._pad_needed = any(b["out"]["type"] in ("pad_button", "pad_axis") for b in pending)
                self._pad_failed = False
            devs = self._read(joys)
            self.snapshot = devs
            now = time.perf_counter()
            dt, last = min(now - last, 0.05), now
            if self.enabled:
                self._apply(devs, dt)
            elif was_enabled:
                self._release_all(close_pad=True)
                self.active = frozenset()
                self.status = ("paused",)
            was_enabled = self.enabled
            time.sleep(1 / POLL_HZ)

    def _read(self, joys):
        devs = {}
        for j in sorted(joys.values(), key=lambda j: j.get_instance_id()):
            try:
                name = j.get_name()
                if name.startswith(IGNORED_DEVICES):
                    continue
                key, n = name, 2
                while key in devs:
                    key, n = f"{name} #{n}", n + 1
                devs[key] = {
                    "axes": [j.get_axis(i) for i in range(j.get_numaxes())],
                    "buttons": [bool(j.get_button(i)) for i in range(j.get_numbuttons())],
                    "hats": [j.get_hat(i) for i in range(j.get_numhats())],
                }
            except pygame.error:
                pass  # débranché entre deux événements
        return devs

    def _apply(self, devs, dt):
        keys, pad_buttons, active = set(), set(), set()
        axes = dict.fromkeys(PAD_AXES, 0.0)
        mouse = [0.0, 0.0]
        for i, b in enumerate(self._bindings):
            st = devs.get(b["src"]["dev"])
            if st is None:
                continue
            kind, target = b["out"]["type"], b["out"]["target"]
            if kind in ANALOG_OUTS:
                v = analog_value(b, st)
                if v:
                    active.add(i)
                if kind == "pad_axis":
                    axes[target] += v
                else:
                    mouse[0 if target == "X" else 1] += v * b["out"].get("speed", 800) * dt
                continue
            on = digital_value(b, st)
            if b.get("mode") == "toggle":
                if on and not b["_prev"]:
                    b["_toggled"] = not b["_toggled"]
                b["_prev"] = on
                on = b["_toggled"]
            if on:
                active.add(i)
                (keys if kind == "key" else pad_buttons).add(target)
        self.active = frozenset(active)

        for k in keys - self._keys_down:
            send_key(k, up=False)
        for k in self._keys_down - keys:
            send_key(k, up=True)
        self._keys_down = keys

        # Souris : +Y = vers le haut, comme les sticks ; on garde les fractions de pixel.
        fx = self._mouse_frac[0] + mouse[0]
        fy = self._mouse_frac[1] - mouse[1]
        dx, dy = int(fx), int(fy)
        self._mouse_frac = [fx - dx, fy - dy]
        if dx or dy:
            send_mouse_move(dx, dy)

        self._update_pad(pad_buttons, axes)

    def _update_pad(self, buttons, axes):
        if not self._pad_needed:
            if self._pad is not None:
                self._release_all(close_pad=True)
            self.status = ("kb",)
            return
        if self._pad is None:
            if self._pad_failed:
                return
            try:
                if vg is None:
                    raise RuntimeError("vgamepad not installed")
                self._pad = vg.VX360Gamepad()
                self.status = ("pad",)
            except Exception as e:
                self._pad_failed = True
                self.status = ("pad_error", str(e))
                return
        for t in ("LT", "RT"):
            if t in buttons:
                axes[t] = 1.0
        for a in ("LX", "LY", "RX", "RY"):
            axes[a] = max(-1.0, min(1.0, axes[a]))
        for a in ("LT", "RT"):
            axes[a] = max(0.0, min(1.0, axes[a]))
        state = (frozenset(buttons), tuple(round(axes[a], 4) for a in PAD_AXES))
        if state == self._pad_state:
            return
        self._pad_state = state
        pad = self._pad
        pad.reset()
        for name in buttons - {"LT", "RT"}:
            pad.press_button(button=xusb_button(name))
        pad.left_joystick_float(x_value_float=axes["LX"], y_value_float=axes["LY"])
        pad.right_joystick_float(x_value_float=axes["RX"], y_value_float=axes["RY"])
        pad.left_trigger_float(value_float=axes["LT"])
        pad.right_trigger_float(value_float=axes["RT"])
        pad.update()

    def _release_all(self, close_pad):
        for k in self._keys_down:
            send_key(k, up=True)
        self._keys_down = set()
        self._mouse_frac = [0.0, 0.0]
        if self._pad is not None:
            self._pad.reset()
            self._pad.update()
            if close_pad:
                self._pad = None  # vgamepad débranche la manette virtuelle à la destruction
        self._pad_state = None


# --- Interface --------------------------------------------------------------------

PALETTES = {
    "light": {"text": "#1c1c1c", "muted": "#6b6b6b", "track": "#e1e1e1", "accent": "#005fb8",
              "center": "#a0a0a0", "chip_text": "#ffffff", "view_bg": "#e9e9e9",
              "row_active": "#c9f2d0", "row_missing": "#9a9a9a", "label_outline": "#ffffff"},
    "dark": {"text": "#fafafa", "muted": "#9a9a9a", "track": "#383838", "accent": "#57c8ff",
             "center": "#6b6b6b", "chip_text": "#1c1c1c", "view_bg": "#141414",
             "row_active": "#1f4d2c", "row_missing": "#6b6b6b", "label_outline": "#d1d5db"},
}
# Étiquettes de la vue HOTAS : mêmes couleurs dans les deux thèmes, elles sont posées sur une image.
LABEL_COLORS = {"active": "#16a34a", "bound": "#1f2937", "free": "#6b7280", "edit": "#facc15"}
TOGGLE_COLORS = {True: ("#16a34a", "#15803d"), False: ("#dc2626", "#b91c1c")}  # fond, fond survolé
HAT_ARROWS = {(0, 0): "·", (0, 1): "↑", (0, -1): "↓", (-1, 0): "←", (1, 0): "→",
              (-1, 1): "↖", (1, 1): "↗", (-1, -1): "↙", (1, -1): "↘"}
FONT = "Segoe UI"

user32.GetParent.restype = wintypes.HWND
user32.GetParent.argtypes = (wintypes.HWND,)
user32.SetWindowPos.argtypes = (wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, wintypes.UINT)


def system_theme():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
            return "light" if winreg.QueryValueEx(key, "AppsUseLightTheme")[0] else "dark"
    except OSError:
        return "light"


def set_titlebar(window, dark):
    """Barre de titre Windows 10/11 assortie au thème (DWMWA_USE_IMMERSIVE_DARK_MODE)."""
    try:
        window.update_idletasks()
        hwnd = user32.GetParent(window.winfo_id())
        value = ctypes.c_int(1 if dark else 0)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), ctypes.sizeof(value))
        # Repeint le cadre tout de suite : SWP_FRAMECHANGED | SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER.
        user32.SetWindowPos(hwnd, None, 0, 0, 0, 0, 0x0020 | 0x0002 | 0x0001 | 0x0004)
    except (AttributeError, OSError):
        pass


def make_icon(color, size):
    """Icône dessinée à la volée : un manche de joystick sur fond de couleur."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((2, 2, 62, 62), 15, fill=color)
    d.rounded_rectangle((14, 46, 50, 55), 4, fill="white")  # socle
    d.rectangle((29, 24, 35, 48), fill="white")              # manche
    d.ellipse((21, 9, 43, 31), fill="white")                 # poignée
    return ImageTk.PhotoImage(img.resize((size, size), Image.LANCZOS))


def load_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


class BindingDialog(tk.Toplevel):
    def __init__(self, app, binding=None, src=None):
        super().__init__(app.root)
        self.app = app
        self.result = None
        b = copy.deepcopy(binding) if binding else {"out": {"type": "key", "target": "SPACE"}}
        if src:  # nouveau bind sur un contrôle déjà connu (depuis la vue HOTAS)
            b["src"] = copy.deepcopy(src)
            b["invert"] = src["type"] == "axis" and src["dir"] < 0
        self.src = b.get("src")
        out = b["out"]
        self.title(tr("dlg_edit") if binding else tr("dlg_new"))
        self.transient(app.root)
        self.resizable(False, False)
        set_titlebar(self, app.dark)

        f = ttk.Frame(self, padding=18)
        f.pack(fill="both", expand=True)

        ttk.Label(f, text=tr("dlg_control"), font=(FONT, 10, "bold")).grid(row=0, column=0, sticky="w", pady=6)
        self.src_var = tk.StringVar()
        ttk.Label(f, textvariable=self.src_var, width=46).grid(row=0, column=1, sticky="w", padx=10)
        self.detect_btn = ttk.Button(f, text=tr("dlg_detect"), command=self._detect)
        self.detect_btn.grid(row=0, column=2, sticky="ew")

        ttk.Label(f, text=tr("dlg_out_type"), font=(FONT, 10, "bold")).grid(row=1, column=0, sticky="w", pady=6)
        self.type_var = tk.StringVar(value=tr("out_" + out["type"]))
        type_cb = ttk.Combobox(f, textvariable=self.type_var, values=[tr("out_" + k) for k in OUT_KINDS],
                               state="readonly", width=32)
        type_cb.grid(row=1, column=1, sticky="w", padx=10)
        type_cb.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        ttk.Label(f, text=tr("dlg_target"), font=(FONT, 10, "bold")).grid(row=2, column=0, sticky="w", pady=6)
        self.target_var = tk.StringVar(value=target_label(out["type"], out["target"]))
        self.target_cb = ttk.Combobox(f, textvariable=self.target_var, state="readonly", width=32)
        self.target_cb.grid(row=2, column=1, sticky="w", padx=10)
        self.capture_btn = ttk.Button(f, text=tr("dlg_capture"), command=self._capture)
        self.capture_btn.grid(row=2, column=2, sticky="ew")

        self.hint_var = tk.StringVar()
        ttk.Label(f, textvariable=self.hint_var, foreground=app.palette["muted"],
                  wraplength=int(600 * app.scale)).grid(row=3, column=0, columnspan=3, sticky="w", pady=(8, 0))

        opts = ttk.LabelFrame(f, text=tr("dlg_options"), padding=12)
        opts.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(14, 0))
        self.invert_var = tk.BooleanVar(value=b.get("invert", False))
        self.centered_var = tk.BooleanVar(value=(self.src or {}).get("centered", True))
        self.dz_var = tk.StringVar(value=str(b.get("deadzone", 0.05)))
        self.thr_var = tk.StringVar(value=str(b.get("threshold", 0.5)))
        self.speed_var = tk.StringVar(value=str(out.get("speed", 800)))
        self.toggle_var = tk.BooleanVar(value=b.get("mode") == "toggle")

        def spin(label, var, frm, to, inc):
            row = ttk.Frame(opts)
            ttk.Label(row, text=label).pack(side="left")
            ttk.Spinbox(row, textvariable=var, from_=frm, to=to, increment=inc, width=8).pack(side="left", padx=8)
            return row

        self.opt_widgets = {
            "invert": ttk.Checkbutton(opts, text=tr("dlg_invert"), variable=self.invert_var),
            "centered": ttk.Checkbutton(opts, text=tr("dlg_centered"), variable=self.centered_var),
            "deadzone": spin(tr("dlg_deadzone"), self.dz_var, 0, 0.5, 0.01),
            "speed": spin(tr("dlg_speed"), self.speed_var, 50, 5000, 50),
            "threshold": spin(tr("dlg_threshold"), self.thr_var, 0.1, 0.95, 0.05),
            "toggle": ttk.Checkbutton(opts, text=tr("dlg_toggle"), variable=self.toggle_var),
        }

        btns = ttk.Frame(f)
        btns.grid(row=5, column=0, columnspan=3, sticky="e", pady=(16, 0))
        ttk.Button(btns, text=tr("cancel"), command=self.destroy).pack(side="right")
        ttk.Button(btns, text=tr("ok"), style="Accent.TButton", command=self._ok).pack(side="right", padx=8)

    def show(self):
        self._refresh()
        self.grab_set()
        # Pause du mapping : un bouton du HOTAS lié à ESPACE cliquerait sinon dans ce dialogue.
        self.app.dialog_open = True
        self.app.sync_enabled()
        try:
            self.wait_window()
        finally:
            self.app.dialog_open = False
            self.app.sync_enabled()
        return self.result

    def _out_type(self):
        return next(k for k in OUT_KINDS if tr("out_" + k) == self.type_var.get())

    def _refresh(self):
        kind = self._out_type()
        analog = kind in ANALOG_OUTS
        is_axis = self.src is not None and self.src["type"] == "axis"
        values = targets(kind)
        self.target_cb["values"] = values
        if self.target_var.get() not in values:
            self.target_var.set(target_label(kind, DEFAULT_TARGET[kind]))
        if kind == "key":
            self.capture_btn.grid()
        else:
            self.capture_btn.grid_remove()
        visible = {"invert": analog, "centered": analog and is_axis, "deadzone": analog and is_axis,
                   "speed": kind == "mouse", "threshold": not analog and is_axis, "toggle": not analog}
        for w in self.opt_widgets.values():
            w.pack_forget()
        for name, w in self.opt_widgets.items():
            if visible[name]:
                w.pack(anchor="w", pady=3)
        self.src_var.set(describe_src(self.src, analog) if self.src else tr("dlg_src_placeholder"))
        self.hint_var.set(tr("dlg_hint_analog") if analog else tr("dlg_hint_digital"))

    def _capture(self):
        self.capture_btn.configure(text=tr("dlg_press_key"))
        self.bind("<KeyPress>", self._on_key)
        self.focus_set()  # focus sur la fenêtre elle-même : Espace/Tab n'actionnent pas un bouton

    def _on_key(self, event):
        name = key_from_event(event)
        if name:
            self.target_var.set(target_label("key", name))
            self.unbind("<KeyPress>")
            self.capture_btn.configure(text=tr("dlg_capture"))
        return "break"

    def _detect(self):
        self.detect_btn.state(["disabled"])
        self.src_var.set(tr("dlg_detecting"))
        self.after(30, self._detect_poll, self.app.engine.snapshot, time.monotonic() + 10)

    def _detect_poll(self, base, deadline):
        if not self.winfo_exists():
            return
        found = None
        for dev, st in self.app.engine.snapshot.items():
            b0 = base.get(dev)
            if b0 is None:
                continue
            for i, (p, p0) in enumerate(zip(st["buttons"], b0["buttons"])):
                if p and not p0:
                    found = {"dev": dev, "type": "button", "idx": i}
            for i, (h, h0) in enumerate(zip(st["hats"], b0["hats"])):
                if h != h0 and h != (0, 0):
                    found = {"dev": dev, "type": "hat", "idx": i, "dir": hat_dir(h)}
            for i, (v, v0) in enumerate(zip(st["axes"], b0["axes"])):
                if abs(v - v0) > 0.5:
                    found = {"dev": dev, "type": "axis", "idx": i, "dir": 1 if v > v0 else -1,
                             "centered": abs(v0) < 0.5}
            if found:
                break
        if found or time.monotonic() > deadline:
            self.detect_btn.state(["!disabled"])
            if found:
                self.src = found
                if found["type"] == "axis":
                    self.invert_var.set(found["dir"] < 0)
                    self.centered_var.set(found["centered"])
            self._refresh()
            return
        self.after(30, self._detect_poll, base, deadline)

    @staticmethod
    def _num(var, default, lo, hi):
        try:
            return max(lo, min(hi, float(var.get().replace(",", "."))))
        except ValueError:
            return default

    def _ok(self):
        if not self.src:
            messagebox.showwarning(APP_NAME, tr("dlg_need_src"), parent=self)
            return
        kind = self._out_type()
        src = dict(self.src)
        b = {"src": src, "out": {"type": kind, "target": self.target_var.get().split(" ")[0]}}
        if src["type"] == "axis":
            src["centered"] = self.centered_var.get()
        if kind in ANALOG_OUTS:
            b["invert"] = self.invert_var.get()
            b["deadzone"] = self._num(self.dz_var, 0.05, 0.0, 0.5)
            if kind == "mouse":
                b["out"]["speed"] = self._num(self.speed_var, 800, 1, 20000)
        else:
            b["mode"] = "toggle" if self.toggle_var.get() else "hold"
            if src["type"] == "axis":
                b["threshold"] = self._num(self.thr_var, 0.5, 0.05, 0.99)
        self.result = b
        self.destroy()


class HotasView(ttk.Frame):
    """Image du HOTAS avec des étiquettes déplaçables qui montrent ce que fait chaque contrôle.

    Positions des étiquettes en coordonnées relatives à l'image (0–1), pour suivre le redimensionnement.
    """

    def __init__(self, parent, app):
        super().__init__(parent, padding=10)
        self.app = app
        self.layout = {"image": None, "labels": []}
        self.editing = False
        self._image = None          # image d'origine (PIL)
        self._photo = None          # image redimensionnée affichée
        self._rect = (0, 0, 1, 1)   # zone de l'image sur le canevas : x, y, largeur, hauteur
        self._active = set()
        self._baseline = {}
        self._drag = None

        bar = ttk.Frame(self)
        bar.pack(fill="x")
        ttk.Button(bar, text=tr("view_choose_image"), command=self._choose_image).pack(side="left")
        self.edit_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(bar, text=tr("view_edit_mode"), variable=self.edit_var, style="Switch.TCheckbutton",
                        command=self._toggle_edit).pack(side="left", padx=16)
        ttk.Button(bar, text=tr("view_add_bound"), command=self._add_bound).pack(side="left")
        self.hint_var = tk.StringVar(value=tr("view_hint_idle"))
        ttk.Label(self, textvariable=self.hint_var, foreground=app.palette["muted"]).pack(fill="x", pady=(8, 8))

        self.canvas = tk.Canvas(self, highlightthickness=0, background=app.palette["view_bg"])
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self.redraw())
        self.canvas.tag_bind("label", "<ButtonPress-1>", self._on_press)
        self.canvas.tag_bind("label", "<Double-1>", self._on_double)
        self.canvas.tag_bind("label", "<Button-3>", self._on_menu)
        self.canvas.bind("<Motion>", self._on_hover)
        self.canvas.bind("<B1-Motion>", self._on_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

    # Disposition

    def set_layout(self, layout):
        self.layout = layout
        self._image = self._photo = None
        self._active = set()
        path = layout.get("image")
        if path:
            try:
                self._image = Image.open(PROFILES_DIR / path)
                self._image.load()
            except OSError:
                self.hint_var.set(tr("view_image_missing", path=path))
        self.redraw()

    def _choose_image(self):
        path = filedialog.askopenfilename(parent=self, title=tr("view_image_title"), filetypes=[
            (tr("filetype_images"), "*.png *.jpg *.jpeg *.bmp *.gif *.webp"), (tr("filetype_all"), "*.*")])
        if not path:
            return
        # Copie dans profiles/images : le dossier de l'appli reste autonome si on le déplace.
        dest = PROFILES_DIR / "images" / Path(path).name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if Path(path).resolve() != dest.resolve():
            shutil.copy2(path, dest)
        self.layout["image"] = dest.relative_to(PROFILES_DIR).as_posix()
        self.set_layout(self.layout)
        self.app.save_profile()

    def _toggle_edit(self):
        self.editing = self.edit_var.get()
        self._baseline = {}
        self.app.sync_enabled()
        self.hint_var.set(tr("view_hint_edit") if self.editing else tr("view_hint_idle"))
        self.redraw()

    def _add_label(self, src):
        """Ajoute l'étiquette d'un contrôle s'il n'en a pas encore. Renvoie True si ajoutée."""
        labels = self.layout["labels"]
        if any(input_key(lab["src"]) == input_key(src) for lab in labels):
            return False
        # Première case libre d'une grille en haut à gauche, à faire glisser ensuite.
        for k in range(64):
            x, y = 0.12 + 0.25 * (k // 8 % 4), 0.07 + 0.12 * (k % 8)
            if not any(abs(lab["x"] - x) < 0.1 and abs(lab["y"] - y) < 0.05 for lab in labels):
                break
        labels.append({"src": src, "x": x, "y": y})
        self.redraw()  # le nouveau périphérique peut changer les préfixes L / R des autres
        return True

    def _add_bound(self):
        added = [self._add_label(copy.deepcopy(b["src"])) for b in self.app.bindings]
        if any(added):
            self.app.save_profile()
            if not self.editing:
                self.edit_var.set(True)
                self._toggle_edit()

    # Dessin

    def redraw(self):
        c = self.canvas
        c.delete("all")
        cw, ch = c.winfo_width(), c.winfo_height()
        if cw < 20 or ch < 20:
            return
        if self._image:
            iw, ih = self._image.size
            k = min(cw / iw, ch / ih)
            w, h = max(1, int(iw * k)), max(1, int(ih * k))
            x, y = (cw - w) // 2, (ch - h) // 2
            if self._photo is None or (self._photo.width(), self._photo.height()) != (w, h):
                self._photo = ImageTk.PhotoImage(self._image.resize((w, h), Image.LANCZOS))
            c.create_image(x, y, anchor="nw", image=self._photo)
        else:
            x, y, w, h = 0, 0, cw, ch
            c.create_text(cw / 2, ch / 2, fill=self.app.palette["muted"], justify="center", font=(FONT, 11),
                          text=tr("view_empty"))
        self._rect = (x, y, w, h)
        for i in range(len(self.layout["labels"])):
            self._draw_label(i)

    def _lines(self, lab):
        src = lab["src"]
        lines = [lab["caption"]] if lab.get("caption") else []
        binds = [b for b in self.app.bindings if input_key(b["src"]) == input_key(src)]
        dev = short_devices([lab["src"]["dev"] for lab in self.layout["labels"]])[src["dev"]]
        name = f"{dev} · {short_input(src)}" if dev else short_input(src)
        for b in binds:
            half = ""
            if src["type"] == "axis" and b["out"]["type"] not in ANALOG_OUTS:
                half = " +" if b["src"]["dir"] > 0 else " −"
            lines.append(f"{name}{half} → {short_out(b)}")
        if not binds:
            lines.append(f"{name} · {tr('label_free')}")
        return lines, bool(binds)

    def _fill(self, i, bound):
        return LABEL_COLORS["active" if i in self._active else "bound" if bound else "free"]

    def _draw_label(self, i):
        c, s = self.canvas, self.app.scale
        lab = self.layout["labels"][i]
        tag = f"l{i}"
        c.delete(tag)
        x0, y0, w, h = self._rect
        cx, cy = x0 + lab["x"] * w, y0 + lab["y"] * h
        lines, bound = self._lines(lab)
        pad = 4 * s
        text_opts = dict(text="\n".join(lines), fill="white", font=(FONT, 9, "bold"),
                         justify="center", tags=("label", tag))
        if "w" in lab:  # taille choisie à la main (relative à l'image) : le texte revient à la ligne
            bw, bh = lab["w"] * w, lab["h"] * h
            t = c.create_text(cx, cy, width=max(1, bw - 2 * pad), **text_opts)
            box = (cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2)
        else:  # taille automatique, ajustée au texte
            t = c.create_text(cx, cy, **text_opts)
            bx = c.bbox(t)
            box = (bx[0] - pad, bx[1] - pad, bx[2] + pad, bx[3] + pad)
        outline = LABEL_COLORS["edit"] if self.editing else self.app.palette["label_outline"]
        r = c.create_rectangle(*box, fill=self._fill(i, bound), outline=outline, width=1.5 * s,
                               dash=(4, 2) if self.editing else "", tags=("label", tag, f"bg{i}"))
        c.tag_lower(r, t)
        if self.editing:  # poignée d'étirement (tous les bords et coins fonctionnent aussi)
            c.create_rectangle(box[2] - 6 * s, box[3] - 6 * s, box[2], box[3], fill=LABEL_COLORS["edit"],
                               outline="", tags=("label", tag))

    # Boucle (appelée par App à chaque nouvel état du HOTAS)

    def tick(self, snap):
        if self.editing:
            self._detect_new(snap)
        labels = self.layout["labels"]
        active = set()
        for i, lab in enumerate(labels):
            st = snap.get(lab["src"]["dev"])
            if st and input_active(lab["src"], st):
                active.add(i)
        changed, self._active = active ^ self._active, active
        for i in changed:
            self.canvas.itemconfigure(f"bg{i}", fill=self._fill(i, self._lines(labels[i])[1]))

    def _detect_new(self, snap):
        added = False
        for dev, st in snap.items():
            base = self._baseline.setdefault(dev, st)
            for i, pressed in enumerate(st["buttons"]):
                if pressed:
                    added |= self._add_label({"dev": dev, "type": "button", "idx": i})
            for i, h in enumerate(st["hats"]):
                if h != (0, 0):
                    added |= self._add_label({"dev": dev, "type": "hat", "idx": i, "dir": hat_dir(h)})
            for i, (v, v0) in enumerate(zip(st["axes"], base["axes"])):
                if abs(v - v0) > 0.5:
                    added |= self._add_label({"dev": dev, "type": "axis", "idx": i, "dir": 1 if v > v0 else -1,
                                              "centered": abs(v0) < 0.5})
        if added:
            self.app.save_profile()

    # Souris

    def _label_at_cursor(self):
        for tag in self.canvas.gettags("current"):
            if tag[0] == "l" and tag[1:].isdigit():
                return int(tag[1:])
        return None

    EDGE_CURSORS = {"w": "size_we", "e": "size_we", "n": "size_ns", "s": "size_ns",
                    "nw": "size_nw_se", "se": "size_nw_se", "ne": "size_ne_sw", "sw": "size_ne_sw"}

    def _edges(self, i, x, y):
        """Bords de la boîte sous le curseur : "", "e", "n", "se"… (vide = milieu, on déplace)."""
        x1, y1, x2, y2 = self.canvas.coords(f"bg{i}")
        m = 6 * self.app.scale
        ns = "n" if abs(y - y1) <= m else "s" if abs(y - y2) <= m else ""
        we = "w" if abs(x - x1) <= m else "e" if abs(x - x2) <= m else ""
        return ns + we

    def _on_hover(self, event):
        if not self.editing or self._drag:
            return
        i = self._label_at_cursor()
        cursor = "" if i is None else self.EDGE_CURSORS.get(self._edges(i, event.x, event.y), "fleur")
        if self.canvas["cursor"] != cursor:
            self.canvas.configure(cursor=cursor)

    def _on_press(self, event):
        i = self._label_at_cursor()
        if i is None:
            return
        if not self.editing:
            self.hint_var.set(tr("view_hint_need_edit"))
            return
        self.canvas.tag_raise(f"l{i}")
        edges = self._edges(i, event.x, event.y)
        if edges:
            self._drag = ("resize", i, edges, list(self.canvas.coords(f"bg{i}")))
        else:
            self._drag = ("move", i, event.x, event.y)

    def _on_motion(self, event):
        if not self._drag:
            return
        if self._drag[0] == "move":
            _, i, lx, ly = self._drag
            self.canvas.move(f"l{i}", event.x - lx, event.y - ly)
            self._drag = ("move", i, event.x, event.y)
            return
        _, i, edges, box = self._drag
        min_w, min_h = 30 * self.app.scale, 16 * self.app.scale
        if "w" in edges:
            box[0] = min(event.x, box[2] - min_w)
        if "e" in edges:
            box[2] = max(event.x, box[0] + min_w)
        if "n" in edges:
            box[1] = min(event.y, box[3] - min_h)
        if "s" in edges:
            box[3] = max(event.y, box[1] + min_h)
        self._store_box(i, box, size=True)
        self._draw_label(i)

    def _store_box(self, i, box, size):
        x0, y0, w, h = self._rect
        lab = self.layout["labels"][i]
        lab["x"] = min(1.0, max(0.0, ((box[0] + box[2]) / 2 - x0) / w))
        lab["y"] = min(1.0, max(0.0, ((box[1] + box[3]) / 2 - y0) / h))
        if size:
            lab["w"], lab["h"] = (box[2] - box[0]) / w, (box[3] - box[1]) / h

    def _on_release(self, event):
        if not self._drag:
            return
        i = self._drag[1]
        if self._drag[0] == "move":
            self._store_box(i, self.canvas.coords(f"bg{i}"), size=False)
        self._drag = None
        self.app.save_profile()

    def _reset_size(self, i):
        lab = self.layout["labels"][i]
        lab.pop("w", None)
        lab.pop("h", None)
        self._draw_label(i)
        self.app.save_profile()

    def _on_double(self, event):
        i = self._label_at_cursor()
        if i is None:
            return
        src = self.layout["labels"][i]["src"]
        idx = next((j for j, b in enumerate(self.app.bindings) if input_key(b["src"]) == input_key(src)), None)
        if idx is None:
            self.app.add_bind(src)
        else:
            self.app.edit_bind(idx)

    def _on_menu(self, event):
        i = self._label_at_cursor()
        if i is None:
            return
        lab = self.layout["labels"][i]
        menu = tk.Menu(self, tearoff=False)
        for j, b in enumerate(self.app.bindings):
            if input_key(b["src"]) == input_key(lab["src"]):
                menu.add_command(label=tr("menu_edit", out=short_out(b)), command=lambda j=j: self.app.edit_bind(j))
        menu.add_command(label=tr("menu_add"), command=lambda: self.app.add_bind(lab["src"]))
        menu.add_separator()
        menu.add_command(label=tr("menu_rename"), command=lambda: self._rename(i))
        if "w" in lab:
            menu.add_command(label=tr("menu_autosize"), command=lambda: self._reset_size(i))
        menu.add_command(label=tr("menu_remove"), command=lambda: self._remove(i))
        menu.tk_popup(event.x_root, event.y_root)

    def _rename(self, i):
        lab = self.layout["labels"][i]
        text = simpledialog.askstring(tr("rename_title"), tr("rename_prompt"),
                                      initialvalue=lab.get("caption", ""), parent=self)
        if text is not None:
            lab["caption"] = text.strip()
            self._draw_label(i)
            self.app.save_profile()

    def _remove(self, i):
        del self.layout["labels"][i]
        self._active = set()
        self.redraw()
        self.app.save_profile()


class App:
    def __init__(self, root):
        global LANG
        self.root = root
        self.scale = root.winfo_fpixels("1i") / 96
        root.title(APP_NAME)
        root.geometry(f"{int(1100 * self.scale)}x{int(720 * self.scale)}")
        root.minsize(int(860 * self.scale), int(520 * self.scale))
        self.engine = Engine()
        self.engine.start()
        self.settings = load_json(SETTINGS_FILE, {})
        LANG = self.settings.get("lang") if self.settings.get("lang") in STRINGS else LANG
        self.profile_path = Path(self.settings.get("profile") or PROFILES_DIR / "default.json")
        data = load_json(self.profile_path, {})
        self.bindings = data.get("bindings", [])
        self.enabled_var = tk.BooleanVar(value=True)
        self.dialog_open = False
        self._apply_theme()
        self._build()
        self.view.set_layout(data.get("layout") or {"image": None, "labels": []})
        self._apply_bindings(save=False)
        root.protocol("WM_DELETE_WINDOW", self._close)
        self._tick()

    def sync_enabled(self):
        """Le mapping tourne si le bouton est sur ACTIVÉ, hors dialogue de bind et hors mode placement."""
        self.engine.enabled = self.enabled_var.get() and not self.dialog_open and not self.view.editing

    # Apparence

    def _apply_theme(self):
        mode = self.settings.get("theme", "system")
        theme = system_theme() if mode == "system" else mode
        sv_ttk.set_theme(theme, self.root)
        self.dark = theme == "dark"
        self.palette = PALETTES[theme]
        style = ttk.Style(self.root)
        style.configure("Treeview", rowheight=int(30 * self.scale))
        style.configure("Section.TLabel", foreground=self.palette["muted"], font=(FONT, 9, "bold"))
        style.configure("Muted.TLabel", foreground=self.palette["muted"])
        style.configure("Title.TLabel", font=(FONT + " Semibold", 15))
        self._icon = make_icon(self.palette["accent"], 64)
        self.root.iconphoto(True, self._icon)
        set_titlebar(self.root, self.dark)

    def _build(self):
        s = self.scale
        self._last_snap = None
        self._devices = set()
        self._shown_active = frozenset()

        # En-tête : nom, interrupteur, profil, réglages
        header = ttk.Frame(self.root, padding=(18, 14, 18, 12))
        header.pack(fill="x")
        self._logo = make_icon(self.palette["accent"], int(36 * s))
        ttk.Label(header, image=self._logo).pack(side="left")
        names = ttk.Frame(header)
        names.pack(side="left", padx=(10, 24))
        ttk.Label(names, text=APP_NAME, style="Title.TLabel").pack(anchor="w")
        ttk.Label(names, text=tr("subtitle"), style="Muted.TLabel").pack(anchor="w")
        # tk.Button plutôt que ttk : on veut une couleur franche, lisible d'un coup d'œil.
        self.toggle_btn = tk.Button(header, command=self._toggle_enabled, relief="flat", bd=0, cursor="hand2",
                                    highlightthickness=0, padx=int(18 * s), pady=int(7 * s),
                                    font=(FONT, 10, "bold"), fg="white", activeforeground="white")
        self.toggle_btn.pack(side="left")
        self._refresh_toggle()

        settings_btn = ttk.Menubutton(header, text="⚙", width=3)
        settings_btn.pack(side="right")
        settings_btn["menu"] = self._settings_menu(settings_btn)
        self.profile_btn = ttk.Menubutton(header)
        self.profile_btn.pack(side="right", padx=(6, 10))
        profile_menu = tk.Menu(self.profile_btn, tearoff=False)
        profile_menu.add_command(label=tr("new_profile"), command=self._new_profile)
        profile_menu.add_command(label=tr("open_profile"), command=self._open_profile)
        profile_menu.add_command(label=tr("save_as"), command=self._save_as)
        self.profile_btn["menu"] = profile_menu
        ttk.Label(header, text=tr("profile"), style="Muted.TLabel").pack(side="right")

        ttk.Separator(self.root).pack(fill="x")

        # Barre d'état (packée avant le corps pour rester visible quand la fenêtre rétrécit)
        status = ttk.Frame(self.root, padding=(18, 6))
        status.pack(side="bottom", fill="x")
        self.status_dot = ttk.Label(status, text="●")
        self.status_dot.pack(side="left")
        self.status_var = tk.StringVar()
        ttk.Label(status, textvariable=self.status_var).pack(side="left", padx=(6, 0))
        self.count_var = tk.StringVar()
        ttk.Label(status, textvariable=self.count_var, style="Muted.TLabel").pack(side="right")
        ttk.Separator(self.root).pack(side="bottom", fill="x")

        body = ttk.Frame(self.root, padding=(18, 12, 18, 10))
        body.pack(fill="both", expand=True)
        ttk.Label(body, text=tr("live_inputs").upper(), style="Section.TLabel").pack(anchor="w")
        self.monitor = tk.Canvas(body, height=40, highlightthickness=0,
                                 background=ttk.Style(self.root).lookup("TFrame", "background"))
        self.monitor.pack(fill="x", pady=(6, 12))

        self.tabs = ttk.Notebook(body)
        self.tabs.pack(fill="both", expand=True)
        binds_tab = ttk.Frame(self.tabs, padding=10)
        self.view = HotasView(self.tabs, self)
        self.tabs.add(binds_tab, text=tr("tab_binds"))
        self.tabs.add(self.view, text=tr("tab_view"))
        self.tabs.select(min(self.settings.get("tab", 0), 1))
        self.tabs.bind("<<NotebookTabChanged>>", self._on_tab)

        tools = ttk.Frame(binds_tab)
        tools.pack(fill="x", pady=(0, 10))
        ttk.Button(tools, text=tr("btn_add"), style="Accent.TButton", command=self._add).pack(side="left")
        for text, cmd in ((tr("btn_edit"), self._edit), (tr("btn_dup"), self._duplicate),
                          (tr("btn_del"), self._delete)):
            ttk.Button(tools, text=text, command=cmd).pack(side="left", padx=(8, 0))
        table = ttk.Frame(binds_tab)
        table.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(table, columns=("src", "out", "opts"), show="headings", selectmode="browse")
        for col, text, w in (("src", tr("col_src"), 360), ("out", tr("col_out"), 300), ("opts", tr("col_opts"), 220)):
            self.tree.heading(col, text=text, anchor="w")
            self.tree.column(col, width=int(w * s), anchor="w")
        self.tree.tag_configure("active", background=self.palette["row_active"])
        self.tree.tag_configure("missing", foreground=self.palette["row_missing"])
        sb = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        self.tree.bind("<Double-1>", lambda e: self._edit())
        self.tree.bind("<Delete>", lambda e: self._delete())

    def _settings_menu(self, parent):
        menu = tk.Menu(parent, tearoff=False)
        self._theme_var = tk.StringVar(value=self.settings.get("theme", "system"))
        self._lang_var = tk.StringVar(value=LANG)
        themes = tk.Menu(menu, tearoff=False)
        for key in ("system", "light", "dark"):
            themes.add_radiobutton(label=tr("theme_" + key), value=key, variable=self._theme_var,
                                   command=lambda: self._set_appearance(theme=self._theme_var.get()))
        langs = tk.Menu(menu, tearoff=False)
        for key, name in LANGUAGES.items():
            langs.add_radiobutton(label=name, value=key, variable=self._lang_var,
                                  command=lambda: self._set_appearance(lang=self._lang_var.get()))
        menu.add_cascade(label=tr("theme"), menu=themes)
        menu.add_cascade(label=tr("language"), menu=langs)
        return menu

    def _set_appearance(self, theme=None, lang=None):
        """Change le thème ou la langue : l'interface est reconstruite, le moteur continue de tourner."""
        global LANG
        if theme:
            self.settings["theme"] = theme
        if lang:
            self.settings["lang"] = LANG = lang
        save_json(SETTINGS_FILE, self.settings)
        layout = self.view.layout
        for w in self.root.winfo_children():
            w.destroy()
        self._apply_theme()
        self._build()
        self.view.set_layout(layout)
        self._apply_bindings(save=False)
        self.sync_enabled()  # le mode placement est désactivé par la reconstruction

    def _toggle_enabled(self):
        self.enabled_var.set(not self.enabled_var.get())
        self._refresh_toggle()
        self.sync_enabled()

    def _refresh_toggle(self):
        on = self.enabled_var.get()
        bg, hover = TOGGLE_COLORS[on]
        self.toggle_btn.configure(text=tr("toggle_on") if on else tr("toggle_off"), bg=bg, activebackground=hover)

    def _on_tab(self, event):
        self.settings["tab"] = self.tabs.index(self.tabs.select())
        save_json(SETTINGS_FILE, self.settings)

    # Profils

    def save_profile(self):
        save_json(self.profile_path, {"bindings": self.bindings, "layout": self.view.layout})

    def _apply_bindings(self, save=True):
        if save:
            self.save_profile()
        name = self.profile_path.stem
        self.profile_btn.configure(text=name, width=len(name) + 3)  # place pour la flèche du menu
        self.count_var.set(f"{tr('binds_count', n=len(self.bindings))}  ·  {APP_NAME} {APP_VERSION}")
        self.engine.set_bindings(self.bindings)
        self._refresh_tree()
        self.view.redraw()  # les étiquettes affichent les binds

    def _set_profile(self, path, bindings, layout):
        self.profile_path = Path(path)
        self.bindings = bindings
        self.settings["profile"] = str(self.profile_path)
        save_json(SETTINGS_FILE, self.settings)
        self.view.set_layout(layout)
        self._apply_bindings()

    def _ask_save_path(self, title):
        return filedialog.asksaveasfilename(parent=self.root, title=title, initialdir=PROFILES_DIR,
                                            defaultextension=".json",
                                            filetypes=[(tr("filetype_profile"), "*.json")])

    def _new_profile(self):
        path = self._ask_save_path(tr("fd_new"))
        if path:
            # Même image, sans étiquettes : on change rarement de HOTAS d'un jeu à l'autre.
            self._set_profile(path, [], {"image": self.view.layout.get("image"), "labels": []})

    def _save_as(self):
        path = self._ask_save_path(tr("fd_save"))
        if path:
            self._set_profile(path, self.bindings, self.view.layout)

    def _open_profile(self):
        path = filedialog.askopenfilename(parent=self.root, title=tr("fd_open"), initialdir=PROFILES_DIR,
                                          filetypes=[(tr("filetype_profile"), "*.json")])
        if not path:
            return
        data = load_json(path, None)
        if not isinstance(data, dict) or not isinstance(data.get("bindings"), list):
            messagebox.showerror(APP_NAME, tr("invalid_profile"), parent=self.root)
            return
        self._set_profile(path, data["bindings"], data.get("layout") or {"image": None, "labels": []})

    # Binds

    def _selected(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def add_bind(self, src=None):
        b = BindingDialog(self, src=src).show()
        if b:
            self.bindings.append(b)
            self._apply_bindings()
            self.tree.selection_set(str(len(self.bindings) - 1))

    def _add(self):
        self.add_bind()

    def _edit(self):
        i = self._selected()
        if i is not None:
            self.edit_bind(i)

    def edit_bind(self, i):
        b = BindingDialog(self, self.bindings[i]).show()
        if b:
            self.bindings[i] = b
            self._apply_bindings()
            self.tree.selection_set(str(i))

    def _duplicate(self):
        i = self._selected()
        if i is not None:
            self.bindings.insert(i + 1, copy.deepcopy(self.bindings[i]))
            self._apply_bindings()
            self.tree.selection_set(str(i + 1))

    def _delete(self):
        i = self._selected()
        if i is not None:
            del self.bindings[i]
            self._apply_bindings()

    def _refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for i, b in enumerate(self.bindings):
            analog = b["out"]["type"] in ANALOG_OUTS
            self.tree.insert("", "end", iid=str(i), tags=self._row_tags(i, b),
                             values=(describe_src(b["src"], analog), describe_out(b["out"]), describe_opts(b)))

    def _row_tags(self, i, b):
        if i in self._shown_active:
            return ("active",)
        return () if b["src"]["dev"] in self._devices else ("missing",)

    # Boucle d'affichage

    def _tick(self):
        snap = self.engine.snapshot
        changed = False
        if snap != self._last_snap:
            self._last_snap = snap
            self._draw_monitor(snap)
            self.view.tick(snap)
            if set(snap) != self._devices:
                self._devices = set(snap)
                changed = True
        active = self.engine.active if self.enabled_var.get() else frozenset()
        if active != self._shown_active:
            self._shown_active = active
            changed = True
        if changed:
            for i, b in enumerate(self.bindings):
                self.tree.item(str(i), tags=self._row_tags(i, b))
        code, *args = self.engine.status
        self.status_var.set(tr("status_" + code, msg=args[0]) if args else tr("status_" + code))
        ok = code in ("kb", "pad")
        self.status_dot.configure(foreground=TOGGLE_COLORS[True][0] if ok else
                                  self.palette["muted"] if code in ("paused", "starting") else TOGGLE_COLORS[False][0])
        self.root.after(40, self._tick)

    def _draw_monitor(self, snap):
        s, c, pal = self.scale, self.monitor, self.palette
        c.delete("all")
        if not snap:
            c.create_text(2 * s, 14 * s, anchor="w", fill=pal["muted"], text=tr("no_device"), font=(FONT, 10))
            c.configure(height=28 * s)
            return
        y = 0
        for name, st in snap.items():
            c.create_text(2 * s, y + 10 * s, anchor="w", text=name, fill=pal["text"], font=(FONT, 10, "bold"))
            ty = y + 32 * s
            x = 2 * s
            for i, v in enumerate(st["axes"]):  # jauges arrondies, remplies depuis le centre
                x1, x2 = x + 5 * s, x + 51 * s
                mid = (x1 + x2) / 2
                c.create_line(x1, ty, x2, ty, fill=pal["track"], width=8 * s, capstyle="round")
                end = mid + v * (x2 - x1) / 2
                if abs(end - mid) >= 1:
                    c.create_line(mid, ty, end, ty, fill=pal["accent"], width=8 * s, capstyle="butt")
                c.create_line(mid, ty - 7 * s, mid, ty + 7 * s, fill=pal["center"])
                c.create_text(mid, ty + 15 * s, text=f"A{i + 1}", fill=pal["muted"], font=(FONT, 8))
                x += 60 * s
            for i, h in enumerate(st["hats"]):
                c.create_text(x + 12 * s, ty, anchor="w", fill=pal["text"], font=(FONT, 10),
                              text=f"H{i + 1} {HAT_ARROWS.get(tuple(h), '·')}")
                x += 56 * s
            label = c.create_text(x + 16 * s, ty, anchor="w", fill=pal["muted"], font=(FONT, 9),
                                  text=tr("buttons"))
            bx = c.bbox(label)[2] + 10 * s
            pressed = [i + 1 for i, p in enumerate(st["buttons"]) if p]
            if not pressed:
                c.create_text(bx, ty, anchor="w", fill=pal["muted"], text="—")
            for n in pressed:  # pastilles
                t = c.create_text(bx + 8 * s, ty, anchor="w", text=str(n), fill=pal["chip_text"],
                                  font=(FONT, 9, "bold"))
                tb = c.bbox(t)
                c.create_line(tb[0], ty, tb[2], ty, fill=pal["accent"], width=18 * s, capstyle="round")
                c.tag_raise(t)
                bx = tb[2] + 20 * s
            y += 56 * s
        c.configure(height=y - 4 * s)

    def _close(self):
        self.engine.stop()
        self.root.destroy()


def focus_running_instance():
    """Si l'appli tourne déjà, ramène sa fenêtre devant et renvoie True."""
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    global _instance_mutex  # gardé ouvert tant que l'appli tourne
    _instance_mutex = kernel32.CreateMutexW(None, False, "Gimbal_instance")
    if ctypes.get_last_error() != 183:  # ERROR_ALREADY_EXISTS
        return False
    user32.FindWindowW.restype = wintypes.HWND
    hwnd = user32.FindWindowW(None, APP_NAME)
    if not hwnd:
        return False  # instance sans fenêtre (en train de démarrer ou bloquée) : on démarre quand même
    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    user32.SetForegroundWindow(hwnd)
    return True


def main():
    if focus_running_instance():
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass
    root = tk.Tk()
    root.report_callback_exception = lambda exc, val, tb: report_error(
        "".join(traceback.format_exception(exc, val, tb)))
    App(root)
    root.lift()
    root.focus_force()
    root.mainloop()


if __name__ == "__main__":
    main()
