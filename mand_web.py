import tkinter as tk
from tkinter import messagebox
from openai import OpenAI
from gtts import gTTS
import os, threading, time, pygame, uuid, speech_recognition as sr, random, json

# --- API AYARI ---
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key="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" 
)

MEMORY_FILE = "mand_bot_v8_data.json"

def verileri_yukle():
    default_data = {
        "current_chat_id": None, 
        "chats": {}, 
        "stats": {"total_words": 0, "mistakes": 0, "mistake_list": []},
        "user_names": {} 
    }
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "mistake_list" not in data["stats"]: data["stats"]["mistake_list"] = []
                if "user_names" not in data: data["user_names"] = {}
                return data
        except: return default_data
    return default_data

def verileri_kaydet(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

class ToolTip:
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
    def showtip(self, text):
        if self.tipwindow or not text: return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 27
        y = y + cy + self.widget.winfo_rooty() + 27
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=text, justify="left", background="#ffffe0", relief="solid", borderwidth=1, font=("tahoma", "9", "normal"))
        label.pack(ipadx=1)
    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw: tw.destroy()

class MANDBot:
    def __init__(self, root):
        self.root = root
        self.root.title("MAND Bot v8.3 - Legendary Edition")
        self.root.geometry("1100x850")
        self.root.configure(bg="#0f172a")
        pygame.mixer.init()

        self.data = verileri_yukle()
        self.current_chat_id = self.data.get("current_chat_id")
        self.level = "A1"
        self.lv_colors = {"A1": "#22c55e", "A2": "#3b82f6", "B1": "#eab308", "B2": "#ef4444"}
        self.last_correction = ""
        self.is_talking = False
        
        # --- SIDEBAR ---
        self.sidebar = tk.Frame(root, width=280, bg="#1e293b")
        self.sidebar.pack(side="left", fill="y")
        
        tk.Label(self.sidebar, text="MAND AI DASHBOARD", font=("Arial", 14, "bold"), bg="#1e293b", fg="#94a3b8").pack(pady=20)
        
        self.stats_frame = tk.Frame(self.sidebar, bg="#334155", pady=10)
        self.stats_frame.pack(fill="x", padx=20, pady=5)
        
        self.words_label = tk.Label(self.stats_frame, text=f"Words: {self.data['stats']['total_words']}", bg="#334155", fg="white")
        self.words_label.pack()
        
        self.mistakes_label = tk.Label(self.stats_frame, text=f"Mistakes: {self.data['stats']['mistakes']} (Hover)", bg="#334155", fg="#fbbf24", font=("Arial", 10, "bold"))
        self.mistakes_label.pack()
        
        self.mistake_tip = ToolTip(self.mistakes_label)
        self.mistakes_label.bind('<Enter>', lambda e: self.mistake_tip.showtip("\n".join(self.data['stats']['mistake_list'][-10:]) if self.data['stats']['mistake_list'] else "No mistakes yet!"))
        self.mistakes_label.bind('<Leave>', lambda e: self.mistake_tip.hidetip())

        tk.Button(self.sidebar, text="+ New Chat", bg="#22c55e", fg="white", font=("Arial", 11, "bold"), command=self.new_chat, relief="flat", cursor="hand2").pack(pady=20, padx=20, fill="x")
        
        self.chat_list_frame = tk.Frame(self.sidebar, bg="#1e293b")
        self.chat_list_frame.pack(fill="both", expand=True)
        
        # --- MAIN PANEL ---
        self.main_frame = tk.Frame(root, bg="#0f172a")
        self.main_frame.pack(side="right", fill="both", expand=True)

        self.canvas = tk.Canvas(self.main_frame, width=400, height=350, bg="#0f172a", highlightthickness=0)
        self.canvas.pack(pady=10)
        self.draw_robot()

        tk.Label(self.main_frame, text="SET ENGLISH LEVEL", bg="#0f172a", fg="#94a3b8", font=("Arial", 9, "bold")).pack()
        lvl_btn_frame = tk.Frame(self.main_frame, bg="#0f172a")
        lvl_btn_frame.pack(pady=5)
        for l in ["A1", "A2", "B1", "B2"]:
            tk.Button(lvl_btn_frame, text=l, width=5, bg="#334155", fg="white", relief="flat", command=lambda x=l: self.set_level(x)).pack(side="left", padx=5)

        self.status_label = tk.Label(self.main_frame, text=f"SYSTEM: {self.level} | ONLINE", font=("Courier", 12, "bold"), bg="#0f172a", fg=self.lv_colors[self.level])
        self.status_label.pack(pady=10)

        self.text_display = tk.Label(self.main_frame, text="Ready for input...", font=("Arial", 11, "italic"), bg="#0f172a", fg="#94a3b8", wraplength=550)
        self.text_display.pack(pady=10)

        self.btn_fix = tk.Button(self.main_frame, text="⚠️ SHOW ANALYSIS", command=self.show_correction, bg="#eab308", font=("Arial", 10, "bold"), relief="flat")

        self.entry = tk.Entry(self.main_frame, font=("Arial", 14), width=40, bg="#1e293b", fg="white", insertbackground="white", relief="flat")
        self.entry.pack(pady=10, ipady=8)
        self.entry.bind("<Return>", lambda e: self.process_text())

        self.btn_record = tk.Button(self.main_frame, text=" 🎤 TRANSMIT VOICE", command=self.start_recording_thread, bg="#3b82f6", fg="white", font=("Arial", 12, "bold"), width=20, relief="flat")
        self.btn_record.pack(pady=5)

        self.recognizer = sr.Recognizer()
        self.refresh_sidebar()
        threading.Thread(target=self.auto_blink, daemon=True).start()

    def set_level(self, lvl):
        self.level = lvl
        self.status_label.config(text=f"SYSTEM: {lvl} | ONLINE", fg=self.lv_colors[lvl])

    def draw_robot(self):
        self.canvas.create_rectangle(100, 60, 300, 240, fill="#334155", outline="#94a3b8", width=4) 
        self.canvas.create_rectangle(120, 80, 280, 220, fill="#1e293b", outline="#3b82f6", width=2) 
        self.eye_l = self.canvas.create_oval(150, 110, 180, 140, fill="#3b82f6", outline="")
        self.eye_r = self.canvas.create_oval(220, 110, 250, 140, fill="#3b82f6", outline="")
        self.mouth_lines = []
        for i in range(5):
            line = self.canvas.create_rectangle(160 + (i*18), 180, 170 + (i*18), 190, fill="#3b82f6", outline="")
            self.mouth_lines.append(line)

    def set_mood(self, mood_text):
        color = "#3b82f6"
        mood_text = mood_text.lower()
        if any(word in mood_text for word in ["happy", "good", "great", "positive"]): color = "#22c55e"
        elif any(word in mood_text for word in ["sad", "angry", "bad", "negative", "upset"]): color = "#ef4444"
        self.canvas.itemconfig(self.eye_l, fill=color); self.canvas.itemconfig(self.eye_r, fill=color)
        for line in self.mouth_lines: self.canvas.itemconfig(line, fill=color)

    def ask_groq(self, prompt):
        # 1. ÖN KONTROLLER VE İSİM YAKALAMA
        if len(prompt.strip()) < 2:
            self.text_display.config(text="⚠️ Error: Input is too short!", fg="#ef4444")
            return

        # İsim Öğrenme Mantığı 
        if "my name is" in prompt.lower():
            name_part = prompt.lower().split("is")[-1].strip().capitalize()
            if len(name_part) > 1:
                self.data["user_names"][self.current_chat_id] = name_part
                verileri_kaydet(self.data)

        user_name = self.data["user_names"].get(self.current_chat_id, "Friend")

        self.status_label.config(text="PROCESSING...", fg="#eab308")
        self.btn_fix.pack_forget()
        self.data["stats"]["total_words"] += len(prompt.split())
        
        # --- SİSTEM TALİMATI: Akıllı Sohbet ve Doğal Sorular ---
        sys_msg = (f"You are MAND Bot. Level: {self.level}. Speaking to: {user_name}. "
                   "1. Answer briefly and naturally in English. "
                   "2. End with a short follow-up question ONLY if it feels natural and related to the topic. "
                   "3. NEVER ask random personal questions like 'what is your favorite fruit' out of nowhere. "
                   "Format: [Mood: mood] | [Answer] | [Fix: correction] "
                   "If input is nonsense (like 'brather'), the [Answer] must be 'INVALID_INPUT_DETECTED'.")
        
        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role":"system","content":sys_msg},{"role":"user","content":prompt}], 
                model="llama-3.1-8b-instant"
            )
            raw_res = chat_completion.choices[0].message.content
            
            # PARSING (Ayrıştırma)
            mood = "neutral"
            main_answer = raw_res
            self.last_correction = ""

            if "|" in raw_res:
                parts = raw_res.split("|")
                mood = parts[0].replace("[Mood:", "").replace("]", "").strip()
                if len(parts) >= 2: main_answer = parts[1].strip()
                if len(parts) >= 3: self.last_correction = parts[2].replace("[Fix:", "").replace("]", "").strip()

            self.set_mood(mood)

            # EKRAN VE SES YÖNETİMİ
            if "INVALID_INPUT_DETECTED" in main_answer:
                self.text_display.config(text="⚠️ I didn't recognize that. Try again?", fg="#ef4444")
            else:
                self.text_display.config(text=main_answer, fg="#94a3b8")
                self.speak(main_answer)

            # Hata Analizi Paneli
            if self.last_correction and "None" not in self.last_correction:
                self.data["stats"]["mistakes"] += 1
                self.data["stats"]["mistake_list"].append(f"- {self.last_correction[:50]}")
                self.btn_fix.pack(pady=5, before=self.entry)
            
            self.words_label.config(text=f"Words: {self.data['stats']['total_words']}")
            self.mistakes_label.config(text=f"Mistakes: {self.data['stats']['mistakes']} (Hover)")
            verileri_kaydet(self.data)

        except: self.text_display.config(text="AI Link Error.", fg="#ef4444")
        self.status_label.config(text=f"SYSTEM: {self.level} | ONLINE", fg=self.lv_colors[self.level])

    def speak(self, text):
        self.is_talking = True
        threading.Thread(target=self.animate_mouth, daemon=True).start()
        fn = f"s_{uuid.uuid4().hex[:5]}.mp3"
        try:
            gTTS(text=text, lang='en').save(fn)
            pygame.mixer.music.load(fn); pygame.mixer.music.play()
            while pygame.mixer.music.get_busy(): time.sleep(0.1)
            pygame.mixer.music.unload(); os.remove(fn)
        except: pass
        self.is_talking = False

    def animate_mouth(self):
        while self.is_talking:
            for line in self.mouth_lines:
                h = random.randint(5, 25)
                self.canvas.coords(line, self.canvas.coords(line)[0], 185-h, self.canvas.coords(line)[2], 185+h)
            time.sleep(0.1)
        for line in self.mouth_lines: self.canvas.coords(line, self.canvas.coords(line)[0], 183, self.canvas.coords(line)[2], 187)

    def record_and_process(self):
        self.status_label.config(text="LISTENING...", fg="#ef4444")
        with sr.Microphone() as source:
            try:
                self.recognizer.adjust_for_ambient_noise(source)
                audio = self.recognizer.listen(source, timeout=6)
                with open("t.wav", "wb") as f: f.write(audio.get_wav_data())
                with open("t.wav", "rb") as file:
                    tx = client.audio.transcriptions.create(file=("t.wav", file.read()), model="whisper-large-v3", response_format="text", language="en")
                self.ask_groq(tx)
                if os.path.exists("t.wav"): os.remove("t.wav")
            except: self.status_label.config(text=f"SYSTEM: {self.level} | ONLINE", fg=self.lv_colors[self.level])

    def show_correction(self):
        if self.last_correction:
            self.text_display.config(text=f"Correction: {self.last_correction}", fg="#fbbf24")
            threading.Thread(target=self.speak, args=(self.last_correction,), daemon=True).start()
            self.btn_fix.pack_forget()

    def auto_blink(self):
        while True:
            time.sleep(random.randint(4, 8))
            self.canvas.itemconfig(self.eye_l, state='hidden'); self.canvas.itemconfig(self.eye_r, state='hidden')
            time.sleep(0.1); self.canvas.itemconfig(self.eye_l, state='normal'); self.canvas.itemconfig(self.eye_r, state='normal')

    def refresh_sidebar(self):
        for w in self.chat_list_frame.winfo_children(): w.destroy()
        chat_count = 1
        for cid in list(self.data["chats"].keys()):
            tk.Button(self.chat_list_frame, text=f"Chat {chat_count}", bg="#334155", fg="white", relief="flat", command=lambda c=cid: self.load_chat(c)).pack(fill="x", padx=10, pady=2)
            chat_count += 1

    def new_chat(self):
        cid = str(uuid.uuid4())[:8]; self.data["chats"][cid] = {"history": []}
        self.current_chat_id = cid; verileri_kaydet(self.data); self.refresh_sidebar()
        self.text_display.config(text="New chat session ready.")

    def load_chat(self, cid): self.current_chat_id = cid; self.text_display.config(text=f"Chat active.")

    def process_text(self):
        if not self.current_chat_id: self.new_chat()
        t = self.entry.get()
        if t: self.entry.delete(0, tk.END); threading.Thread(target=self.ask_groq, args=(t,), daemon=True).start()

    def start_recording_thread(self):
        if not self.is_talking: threading.Thread(target=self.record_and_process, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk(); app = MANDBot(root); root.mainloop()
