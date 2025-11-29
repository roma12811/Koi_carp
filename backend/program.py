#program.py
import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import mss
from PIL import Image
import os
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime

from ai_client import (
    image_to_base64,
    parse_program_message,
    define_program as ai_define_program,
    generate_instructions as ai_generate_instructions
)

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

client = OpenAI()
MODEL = "gpt-4o-mini"
MAX_TOKENS = 400

os.makedirs("./screenshots", exist_ok=True)


class AIAssistantOverlay:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Assistant")
        self.root.geometry("280x80")
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)
        self.root.configure(bg="#16213e")

        self.current_program = None
        self.current_location = None
        self.available_actions = []
        self.last_screenshot = None
        self.setup_ui()
        self.expanded = False

    def setup_ui(self):
        # Compact header
        header = tk.Frame(self.root, bg="#0f3460")
        header.pack(fill=tk.X, padx=5, pady=3)

        title = tk.Label(header, text="🤖 AI", font=('Helvetica', 10, 'bold'),
                         bg="#0f3460", fg="#00d4ff")
        title.pack(side=tk.LEFT, padx=5, pady=2)

        btn_frame = tk.Frame(header, bg="#0f3460")
        btn_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        screenshot_btn = tk.Button(btn_frame, text="📸", command=self.take_screenshot_threaded,
                                   bg="#00d4ff", fg="#000", font=('Helvetica', 9),
                                   padx=5, pady=2, relief=tk.FLAT, cursor="hand2", width=3)
        screenshot_btn.pack(side=tk.LEFT, padx=2)

        self.expand_btn = tk.Button(btn_frame, text="▼", command=self.toggle_expand,
                                    bg="#00d4ff", fg="#000", font=('Helvetica', 9),
                                    padx=5, pady=2, relief=tk.FLAT, cursor="hand2", width=3)
        self.expand_btn.pack(side=tk.LEFT, padx=2)

        # Status
        self.status_label = tk.Label(self.root, text="Ready",
                                     bg="#16213e", fg="#00d4ff", font=('Helvetica', 8))
        self.status_label.pack(pady=2)

        # Expanded content (hidden by default)
        self.expanded_frame = tk.Frame(self.root, bg="#16213e")

    def toggle_expand(self):
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
        # Clear previous content
        for widget in self.expanded_frame.winfo_children():
            widget.destroy()

        # Program info
        info_frame = tk.LabelFrame(self.expanded_frame, text="Program",
                                   bg="#0f3460", fg="#00d4ff", font=('Helvetica', 8))
        info_frame.pack(fill=tk.X, pady=5)

        self.program_label = tk.Label(info_frame, text=self.current_program or "Not analyzed",
                                      bg="#0f3460", fg="#eee", font=('Helvetica', 8), wraplength=320, justify=tk.LEFT)
        self.program_label.pack(anchor=tk.W, padx=5, pady=3)

        # Actions
        actions_frame = tk.LabelFrame(self.expanded_frame, text="Actions",
                                      bg="#0f3460", fg="#00d4ff", font=('Helvetica', 8))
        actions_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        scrollbar = tk.Scrollbar(actions_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.actions_listbox = tk.Listbox(actions_frame, bg="#16213e", fg="#eee",
                                          font=('Helvetica', 8), height=6, width=40,
                                          yscrollcommand=scrollbar.set, relief=tk.FLAT, bd=0)
        self.actions_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.actions_listbox.yview)
        self.actions_listbox.bind('<<ListboxSelect>>', self.on_action_selected)

        # Populate actions
        self.actions_listbox.delete(0, tk.END)
        for i, action in enumerate(self.available_actions, 1):
            self.actions_listbox.insert(tk.END, f"{i}. {action}")

        # Custom action
        custom_frame = tk.Frame(self.expanded_frame, bg="#16213e")
        custom_frame.pack(fill=tk.X, pady=3)

        self.custom_action_entry = tk.Entry(custom_frame, bg="#0f3460", fg="#eee",
                                            font=('Helvetica', 8), insertbackground="#00d4ff")
        self.custom_action_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.custom_action_entry.bind('<Return>', lambda e: self.on_custom_action())

        custom_btn = tk.Button(custom_frame, text="→", command=self.on_custom_action,
                               bg="#00d4ff", fg="#000", font=('Helvetica', 8),
                               padx=5, relief=tk.FLAT, cursor="hand2")
        custom_btn.pack(side=tk.LEFT, padx=3)

        # Instructions
        instr_frame = tk.LabelFrame(self.expanded_frame, text="Instructions",
                                    bg="#0f3460", fg="#00d4ff", font=('Helvetica', 8))
        instr_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.instructions_text = scrolledtext.ScrolledText(instr_frame,
                                                           bg="#16213e", fg="#00d4ff",
                                                           font=('Courier', 8),
                                                           height=8, width=40,
                                                           wrap=tk.WORD, relief=tk.FLAT, bd=0)
        self.instructions_text.pack(fill=tk.BOTH, expand=True)
        self.instructions_text.config(state=tk.DISABLED)

        # Copy button
        copy_btn = tk.Button(self.expanded_frame, text="📋 Copy",
                             command=self.copy_instructions,
                             bg="#00d4ff", fg="#000", font=('Helvetica', 8),
                             relief=tk.FLAT, cursor="hand2")
        copy_btn.pack(pady=3)

    def take_screenshot_threaded(self):
        thread = threading.Thread(target=self.take_screenshot, daemon=True)
        thread.start()

    def take_screenshot(self):
        try:
            self.status_label.config(text="📸 Capturing...")
            self.root.update()

            with mss.mss() as sct:
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = f"./screenshots/screenshot_{timestamp}.png"
                img.save(filepath)
                self.last_screenshot = filepath

                self.status_label.config(text="🔄 Analyzing...")
                self.root.update()

                # Using ai_client function
                program_info = ai_define_program(filepath)

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
            self.status_label.config(text=f"❌ Error")
            messagebox.showerror("Error", f"Screenshot error: {str(e)}")

    def on_action_selected(self, event):
        if self.actions_listbox.curselection():
            index = self.actions_listbox.curselection()[0]
            action = self.available_actions[index]
            self.generate_instructions_threaded(action)

    def on_custom_action(self):
        custom_action = self.custom_action_entry.get().strip()
        if custom_action:
            self.generate_instructions_threaded(custom_action)
            self.custom_action_entry.delete(0, tk.END)

    def generate_instructions_threaded(self, action):
        thread = threading.Thread(target=self.generate_instructions, args=(action, self.last_screenshot), daemon=True)
        thread.start()

    def generate_instructions(self, action, screenshot_path=None):
        try:
            self.instructions_text.config(state=tk.NORMAL)
            self.instructions_text.delete(1.0, tk.END)
            self.instructions_text.insert(tk.END, "⏳ Generating...")
            self.instructions_text.config(state=tk.DISABLED)
            self.root.update()

            # Using ai_client function
            steps = ai_generate_instructions(
                program_name=self.current_program,
                current_location=self.current_location,
                action=action,
                screenshot_path=screenshot_path
            )

            self.instructions_text.config(state=tk.NORMAL)
            self.instructions_text.delete(1.0, tk.END)

            for step in steps:
                self.instructions_text.insert(tk.END, f"{step}\n")

            self.instructions_text.config(state=tk.DISABLED)

        except Exception as e:
            self.instructions_text.config(state=tk.NORMAL)
            self.instructions_text.delete(1.0, tk.END)
            self.instructions_text.insert(tk.END, f"Error: {str(e)}")
            self.instructions_text.config(state=tk.DISABLED)

    def copy_instructions(self):
        try:
            instructions = self.instructions_text.get(1.0, tk.END)
            self.root.clipboard_clear()
            self.root.clipboard_append(instructions)
            messagebox.showinfo("✅", "Copied!")
        except Exception as e:
            messagebox.showerror("Error", f"Could not copy: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = AIAssistantOverlay(root)
    root.mainloop()