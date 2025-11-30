import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import mss
from PIL import Image
import os

from config import UI_THEME
from screenshot import capture_screen, get_screenshot_dimensions
from ai_client import define_program as ai_define_program, generate_instructions as ai_generate_instructions

os.makedirs("./screenshots", exist_ok=True)

class AIAssistantOverlay:
    def __init__(self, root):
        self.root = root
        self.root.title("KOI Assistant")
        self.root.iconbitmap("image_koi.ico")
        self.root.geometry("280x80")
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)
        self.root.configure(bg=UI_THEME["bg_primary"])

        self.current_program = None
        self.current_location = None
        self.available_actions = []
        self.last_screenshot = None
        self.current_instructions = []
        self.highlight_window = None
        self.expanded = False

        self.main_frame = tk.Frame(self.root, bg=UI_THEME["bg_primary"])
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.setup_ui()

    def setup_ui(self):
        """Ініціалізує UI компоненти"""
        header = tk.Frame(self.main_frame, bg=UI_THEME["bg_secondary"])
        header.pack(fill=tk.X, padx=5, pady=3)

        title = tk.Label(header, text="🤖 AI", font=('Helvetica', 10, 'bold'),
                         bg=UI_THEME["bg_secondary"], fg=UI_THEME["accent"])
        title.pack(side=tk.LEFT, padx=5, pady=2)

        btn_frame = tk.Frame(header, bg=UI_THEME["bg_secondary"])
        btn_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        screenshot_btn = tk.Button(btn_frame, text="📸", 
                                   command=self.take_screenshot_threaded,
                                   bg=UI_THEME["accent"], fg="#0F2029", 
                                   font=('Helvetica', 9),
                                   padx=5, pady=2, relief=tk.FLAT, 
                                   cursor="hand2", width=3)
        screenshot_btn.pack(side=tk.LEFT, padx=2)

        self.expand_btn = tk.Button(btn_frame, text="▼", 
                                    command=self.toggle_expand,
                                    bg=UI_THEME["accent"], fg="#0F2029", 
                                    font=('Helvetica', 9),
                                    padx=5, pady=2, relief=tk.FLAT, 
                                    cursor="hand2", width=3)
        self.expand_btn.pack(side=tk.LEFT, padx=2)

        self.status_label = tk.Label(self.main_frame, text="Ready",
                                     bg=UI_THEME["bg_primary"], 
                                     fg=UI_THEME["text_primary"], 
                                     font=('Helvetica', 8))
        self.status_label.pack(pady=2)

        self.expanded_frame = tk.Frame(self.main_frame, bg=UI_THEME["bg_tertiary"])

    def toggle_expand(self):
        """Розвортає/згортає інтерфейс"""
        if self.expanded:
            self.expanded_frame.pack_forget()
            self.root.geometry("280x80")
            self.expand_btn.config(text="▼")
            self.expanded = False
        else:
            self.expanded_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            self.root.geometry("350x400")
            self.expand_btn.config(text="▲")
            self.expanded = True
            self.show_expanded_content()

    def show_expanded_content(self):
        """Відображає розширений контент"""
        for widget in self.expanded_frame.winfo_children():
            widget.destroy()

        info_frame = tk.LabelFrame(self.expanded_frame, text="Program",
                                   bg=UI_THEME["bg_secondary"], 
                                   fg=UI_THEME["accent"], 
                                   font=('Helvetica', 8, 'bold'))
        info_frame.pack(fill=tk.X, pady=5)

        self.program_label = tk.Label(info_frame, 
                                      text=self.current_program or "Not analyzed",
                                      bg=UI_THEME["bg_secondary"], 
                                      fg=UI_THEME["text_secondary"], 
                                      font=('Helvetica', 8),
                                      wraplength=320, justify=tk.LEFT)
        self.program_label.pack(anchor=tk.W, padx=5, pady=3)

        actions_frame = tk.LabelFrame(self.expanded_frame, text="Actions",
                                      bg=UI_THEME["bg_secondary"], 
                                      fg=UI_THEME["accent"], 
                                      font=('Helvetica', 8, 'bold'))
        actions_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        scrollbar = tk.Scrollbar(actions_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.actions_listbox = tk.Listbox(actions_frame, 
                                          bg=UI_THEME["bg_primary"], 
                                          fg=UI_THEME["text_primary"],
                                          font=('Helvetica', 8), height=6, 
                                          width=40,
                                          yscrollcommand=scrollbar.set, 
                                          relief=tk.FLAT, bd=0,
                                          selectbackground="#2D3338", 
                                          selectforeground=UI_THEME["accent"])
        self.actions_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.actions_listbox.yview)
        self.actions_listbox.bind('<<ListboxSelect>>', self.on_action_selected)

        for i, action in enumerate(self.available_actions, 1):
            self.actions_listbox.insert(tk.END, f"{i}. {action}")

        custom_frame = tk.Frame(self.expanded_frame, bg=UI_THEME["bg_tertiary"])
        custom_frame.pack(fill=tk.X, pady=3)

        self.custom_action_entry = tk.Entry(custom_frame, 
                                            bg=UI_THEME["bg_secondary"], 
                                            fg=UI_THEME["text_secondary"],
                                            font=('Helvetica', 8), 
                                            insertbackground=UI_THEME["accent"])
        self.custom_action_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.custom_action_entry.bind('<Return>', lambda e: self.on_custom_action())

        custom_btn = tk.Button(custom_frame, text="→", 
                              command=self.on_custom_action,
                              bg=UI_THEME["accent"], fg="#0F2029", 
                              font=('Helvetica', 8),
                              padx=5, relief=tk.FLAT, cursor="hand2")
        custom_btn.pack(side=tk.LEFT, padx=3)

        instr_frame = tk.LabelFrame(self.expanded_frame, text="Instructions",
                                    bg=UI_THEME["bg_secondary"], 
                                    fg=UI_THEME["accent"], 
                                    font=('Helvetica', 8, 'bold'))
        instr_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.instructions_text = scrolledtext.ScrolledText(instr_frame,
                                                           bg=UI_THEME["bg_primary"], 
                                                           fg=UI_THEME["text_secondary"],
                                                           font=('Courier', 8),
                                                           height=8, width=40,
                                                           wrap=tk.WORD, 
                                                           relief=tk.FLAT, bd=0,
                                                           insertbackground=UI_THEME["accent"])
        self.instructions_text.pack(fill=tk.BOTH, expand=True)
        self.instructions_text.config(state=tk.DISABLED)

        self.instructions_text.bind("<Motion>", self.on_instruction_hover)
        self.instructions_text.bind("<Leave>", self.on_instruction_leave)

        copy_btn = tk.Button(self.expanded_frame, text="📋 Copy",
                            command=self.copy_instructions,
                            bg=UI_THEME["accent"], fg="#0F2029", 
                            font=('Helvetica', 8),
                            relief=tk.FLAT, cursor="hand2")
        copy_btn.pack(pady=3)

    def take_screenshot_threaded(self):
        """Захоплює екран в окремому потоці"""
        thread = threading.Thread(target=self.take_screenshot, daemon=True)
        thread.start()

    def take_screenshot(self):
        """Захоплює екран та аналізує його"""
        try:
            self.status_label.config(text="📸 Capturing...")
            self.root.update()

            self.last_screenshot = capture_screen()
            self.status_label.config(text="🔄 Analyzing...")
            self.root.update()

            program_info = ai_define_program(self.last_screenshot)

            if program_info:
                self.current_program = program_info.get("Name", "Unknown")
                self.current_location = program_info.get("Location", "Unknown")
                self.available_actions = program_info.get("Actions", [])

                self.status_label.config(text="✅ Done")

                if self.expanded:
                    self.show_expanded_content()
                else:
                    self.toggle_expand()
            else:
                self.status_label.config(text="❌ Failed")
                messagebox.showerror("Error", "Could not analyze screenshot")

        except Exception as e:
            self.status_label.config(text="❌ Error")
            messagebox.showerror("Error", f"Screenshot error: {str(e)}")

    def on_action_selected(self, event):
        """Обробляє вибір дії зі списку"""
        if self.actions_listbox.curselection():
            index = self.actions_listbox.curselection()[0]
            action = self.available_actions[index]
            self.generate_instructions_threaded(action)

    def on_custom_action(self):
        """Обробляє користувацьку дію"""
        custom_action = self.custom_action_entry.get().strip()
        if custom_action:
            self.generate_instructions_threaded(custom_action)
            self.custom_action_entry.delete(0, tk.END)

    def generate_instructions_threaded(self, action):
        """Генерує інструкції в окремому потоці"""
        thread = threading.Thread(
            target=self.generate_instructions, 
            args=(action, self.last_screenshot), 
            daemon=True
        )
        thread.start()

    def generate_instructions(self, action, screenshot_path=None):
        """Генерує покрокові інструкції"""
        try:
            self.instructions_text.config(state=tk.NORMAL)
            self.instructions_text.delete(1.0, tk.END)
            self.instructions_text.insert(tk.END, "⏳ Generating...")
            self.instructions_text.config(state=tk.DISABLED)
            self.root.update()

            instructions_with_coords = ai_generate_instructions(
                program_name=self.current_program,
                current_location=self.current_location,
                action=action,
                screenshot_path=screenshot_path
            )

            self.current_instructions = instructions_with_coords

            self.instructions_text.config(state=tk.NORMAL)
            self.instructions_text.delete(1.0, tk.END)

            for step_data in instructions_with_coords:
                self.instructions_text.insert(tk.END, f"{step_data['action']}\n")

            self.instructions_text.config(state=tk.DISABLED)

        except Exception as e:
            self.instructions_text.config(state=tk.NORMAL)
            self.instructions_text.delete(1.0, tk.END)
            self.instructions_text.insert(tk.END, f"Error: {str(e)}")
            self.instructions_text.config(state=tk.DISABLED)

    def copy_instructions(self):
        """Копіює інструкції в буфер обміну"""
        try:
            instructions = self.instructions_text.get(1.0, tk.END)
            self.root.clipboard_clear()
            self.root.clipboard_append(instructions)
            messagebox.showinfo("✅", "Copied!")
        except Exception as e:
            messagebox.showerror("Error", f"Could not copy: {str(e)}")

    def on_instruction_hover(self, event):
        """Обробляє наведення миші на інструкцію"""
        try:
            index = self.instructions_text.index(f"@{event.x},{event.y}")
            line_num = int(index.split('.')[0]) - 1

            if line_num < len(self.current_instructions):
                step_data = self.current_instructions[line_num]
                coords = step_data.get("coordinates")

                if coords and coords.get("x") is not None and coords.get("y") is not None:
                    scaled_coords = self.scale_coordinates(coords)
                    self.show_highlight(scaled_coords)
                else:
                    self.hide_highlight()
            else:
                self.hide_highlight()
        except:
            self.hide_highlight()

    def on_instruction_leave(self, event):
        """Приховує підсвічування при виході миші"""
        self.hide_highlight()

    def scale_coordinates(self, coords):
        """Масштабує координати з розміру скріншоту на монітор"""
        try:
            if self.last_screenshot and os.path.exists(self.last_screenshot):
                img = Image.open(self.last_screenshot)
                screenshot_width, screenshot_height = img.size

                with mss.mss() as sct:
                    monitor = sct.monitors[1]
                    monitor_width = monitor['width']
                    monitor_height = monitor['height']

                scaled = {
                    "x": int(coords.get("x", 0)),
                    "y": int(coords.get("y", 0)),
                    "radius": int(coords.get("radius", 40) * 1.5)
                }

                print(f"📍 Координати: x={scaled['x']}, y={scaled['y']}, radius={scaled['radius']}")
                return scaled

            return coords

        except Exception as e:
            print(f"❌ Помилка масштабування: {e}")
            return coords

    def show_highlight(self, coords):
        """Показує круглий оверлей на координатах"""
        try:
            if self.highlight_window:
                self.highlight_window.destroy()

            x = coords.get("x", 0)
            y = coords.get("y", 0)
            radius = coords.get("radius", 40)

            print(f"🎯 Highlight: x={x}, y={y}, radius={radius}")

            highlight = tk.Toplevel(self.root)
            highlight.attributes('-topmost', True)
            highlight.attributes('-alpha', 0.6)
            highlight.overrideredirect(True)

            size = radius * 2 + 20
            highlight.geometry(f"{int(size)}x{int(size)}+{int(x - radius - 10)}+{int(y - radius - 10)}")

            canvas = tk.Canvas(highlight, bg=UI_THEME["accent"], highlightthickness=0)
            canvas.pack(fill=tk.BOTH, expand=True)

            canvas.create_oval(
                5, 5,
                size - 5, size - 5,
                outline=UI_THEME["accent"],
                width=4,
                fill=''
            )

            self.highlight_window = highlight

        except Exception as e:
            print(f"❌ Помилка при відображенні: {e}")

    def hide_highlight(self):
        if self.highlight_window:
            try:
                self.highlight_window.destroy()
                self.highlight_window = None
            except:
                pass