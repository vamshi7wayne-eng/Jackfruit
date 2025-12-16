import wx
import json
import random
import platform
import os

# Optional TTS
try:
    import pyttsx3
    TTS_AVAILABLE = True
except Exception:
    TTS_AVAILABLE = False

# ---------------- SOUND -----------------
def play_correct_sound():
    if platform.system() == "Windows":
        try:
            import winsound
            winsound.Beep(1000, 150)
        except Exception:
            pass

def play_wrong_sound():
    if platform.system() == "Windows":
        try:
            import winsound
            winsound.Beep(400, 250)
        except Exception:
            pass

# ---------------- JSON LOADER -----------------
def load_question_file(path="questions.json"):
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found in working directory.")
    with open(path, "r", encoding="utf-8") as f:
        txt = f.read().strip()
        if not txt:
            raise ValueError(f"{path} is empty.")
        data = json.loads(txt)
        if not isinstance(data, dict):
            raise ValueError("JSON top-level structure must be an object with subjects as keys.")
        return data

# ---------------- APP -----------------
class FlashcardApp(wx.Frame):
    def __init__(self, questions_data):
        super().__init__(None, title="⚡ QUIZ PORTAL ⚡", size=(980, 700))
        self.questions_data = questions_data

        # state
        self.subject = None
        self.questions = []
        self.current_index = 0
        self.score = 0
        self.selected_option = None
        self.bg_enabled = True
        self.toggle = False

        # TTS engine if available
        self.tts_engine = None
        if TTS_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty("rate", 160)
            except Exception:
                self.tts_engine = None

        # UI setup
        self.panel = wx.Panel(self)
        self.panel.Bind(wx.EVT_PAINT, self.paint_background)
        self.root = wx.BoxSizer(wx.VERTICAL)
        self.panel.SetSizer(self.root)

        # animation timer
        self.anim_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.animate_bg, self.anim_timer)
        self.anim_timer.Start(350)

        self.show_home()
        self.Centre()
        self.Show()

    # ---------- BACKGROUND ----------
    def paint_background(self, event):
        dc = wx.PaintDC(self.panel)
        w, h = self.panel.GetSize()
        if not self.bg_enabled:
            dc.SetBrush(wx.Brush(wx.Colour(255, 255, 255)))
            dc.DrawRectangle(0, 0, w, h)
            return

        bg = wx.Colour(18, 18, 18) if self.toggle else wx.Colour(250, 250, 250)
        dc.SetBrush(wx.Brush(bg))
        dc.DrawRectangle(0, 0, w, h)

        text_color = wx.Colour(255, 215, 0) if not self.toggle else wx.Colour(40, 40, 40)
        dc.SetTextForeground(text_color)

        font = wx.Font(90, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        dc.SetFont(font)

        rep = "QUIZ    " * 40
        for y in range(-120, h, 140):
            dc.DrawText(rep, -200, y)

    def animate_bg(self, event):
        if self.bg_enabled:
            self.toggle = not self.toggle
            self.panel.Refresh()

    # ---------- FONTS ----------
    def font(self, size, bold=True):
        return wx.Font(size, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL,
                       wx.FONTWEIGHT_BOLD if bold else wx.FONTWEIGHT_NORMAL,
                       faceName="Segoe UI")

    # ---------- RESET ----------
    def reset(self):
        for c in self.panel.GetChildren():
            c.Destroy()
        self.root.Clear(True)

    # ---------- HOME ----------
    def show_home(self):
        self.bg_enabled = True
        self.reset()

        title = wx.StaticText(self.panel, label="⚡ QUIZ PORTAL ⚡")
        title.SetFont(wx.Font(36, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL,
                              wx.FONTWEIGHT_BOLD, faceName="Segoe UI Black"))
        title.SetForegroundColour(wx.Colour(10, 10, 10))
        self.root.Add(title, 0, wx.ALIGN_CENTER | wx.TOP, 30)

        subtitle = wx.StaticText(self.panel, label="Select Subject to Begin")
        subtitle.SetFont(self.font(16, False))
        subtitle.SetForegroundColour(wx.Colour(60, 60, 60))
        self.root.Add(subtitle, 0, wx.ALIGN_CENTER | wx.TOP, 6)

        # subject buttons as panels
        for subj in self.questions_data.keys():
            btn = wx.Panel(self.panel, size=(300, 70))
            btn.SetBackgroundColour(wx.Colour(255, 255, 255))
            s = wx.BoxSizer(wx.VERTICAL)

            lbl = wx.StaticText(btn, label=subj)
            lbl.SetFont(self.font(18, True))
            lbl.SetForegroundColour(wx.Colour(10, 10, 10))
            s.AddStretchSpacer(1)
            s.Add(lbl, 0, wx.ALIGN_CENTER)
            s.AddStretchSpacer(1)

            btn.SetSizer(s)

            # bind clicks and hover
            btn.Bind(wx.EVT_LEFT_DOWN, lambda e, s=subj: self.start_quiz(s))
            btn.Bind(wx.EVT_ENTER_WINDOW, lambda e, b=btn: (b.SetBackgroundColour(wx.Colour(255, 225, 40)), b.Refresh()))
            btn.Bind(wx.EVT_LEAVE_WINDOW, lambda e, b=btn: (b.SetBackgroundColour(wx.Colour(255, 255, 255)), b.Refresh()))

            self.root.Add(btn, 0, wx.ALIGN_CENTER | wx.TOP, 18)

        footer = wx.StaticText(self.panel, label="Designed with ♥ — Select a subject to begin")
        footer.SetFont(self.font(11, False))
        footer.SetForegroundColour(wx.Colour(100, 100, 100))
        self.root.Add(footer, 0, wx.ALIGN_CENTER | wx.TOP, 20)

        self.panel.Layout()

    # ---------- START QUIZ ----------
    def start_quiz(self, subject):
        self.subject = subject
        all_q = self.questions_data.get(subject, [])
        if not all_q:
            wx.MessageBox("No questions available for this subject.", "Error")
            return

        # pick up to 10 random questions or all if less
        n = min(10, len(all_q))
        self.questions = random.sample(all_q, n)
        self.current_index = 0
        self.score = 0
        self.selected_option = None

        self.bg_enabled = False
        self.show_quiz()

    # ---------- QUIZ UI ----------
    def show_quiz(self):
        self.reset()
        self.panel.Refresh()

        header = wx.StaticText(self.panel, label=self.subject.upper())
        header.SetFont(self.font(26, True))
        header.SetForegroundColour(wx.Colour(20, 20, 20))
        self.root.Add(header, 0, wx.ALIGN_CENTER | wx.TOP, 12)

        # question label
        q = self.questions[self.current_index]["question"]
        self.question_lbl = wx.StaticText(self.panel, label=q, style=wx.ALIGN_CENTER)
        self.question_lbl.Wrap(750)
        self.question_lbl.SetFont(self.font(20, True))
        self.question_lbl.SetForegroundColour(wx.Colour(30, 30, 30))
        self.root.Add(self.question_lbl, 0, wx.ALIGN_CENTER | wx.TOP, 12)

        # options panel
        options_panel = wx.Panel(self.panel)
        options_panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        options_sizer = wx.BoxSizer(wx.VERTICAL)

        self.option_buttons = []
        options = self.questions[self.current_index].get("options", [])

        for i in range(4):
            label = options[i] if i < len(options) else ""
            rb = wx.RadioButton(options_panel, label=label, style=wx.ALIGN_LEFT)
            rb.SetForegroundColour(wx.Colour(10, 10, 10))
            rb.SetBackgroundColour(wx.Colour(255, 255, 255))
            rb.SetFont(self.font(14, False))
            rb.Bind(wx.EVT_RADIOBUTTON, lambda e, idx=i: self.set_choice(idx))
            if not label:
                rb.Enable(False)
            self.option_buttons.append(rb)
            options_sizer.Add(rb, 0, wx.ALL | wx.ALIGN_LEFT, 8)

        options_panel.SetSizer(options_sizer)
        self.root.Add(options_panel, 0, wx.ALIGN_CENTER | wx.TOP, 12)

        # buttons
        btns = wx.BoxSizer(wx.HORIZONTAL)

        self.next_btn = wx.Button(self.panel, label="Next", size=(130, 44))
        self.next_btn.SetFont(self.font(13, True))
        self.next_btn.SetBackgroundColour(wx.Colour(200, 170, 30))
        self.next_btn.Disable()
        self.next_btn.Bind(wx.EVT_BUTTON, self.next)
        btns.Add(self.next_btn, 0, wx.ALL, 8)

        submit = wx.Button(self.panel, label="Submit", size=(130, 44))
        submit.SetFont(self.font(13, True))
        submit.SetBackgroundColour(wx.Colour(60, 150, 60))
        submit.Bind(wx.EVT_BUTTON, self.check)
        btns.Add(submit, 0, wx.ALL, 8)

        speak = wx.Button(self.panel, label="Listen", size=(100, 44))
        speak.SetFont(self.font(11, True))
        speak.Bind(wx.EVT_BUTTON, self.speak_question)
        btns.Add(speak, 0, wx.ALL | wx.LEFT, 8)

        self.root.Add(btns, 0, wx.ALIGN_CENTER | wx.TOP, 12)

        # feedback area
        feedback_box = wx.Panel(self.panel, size=(640, 70))
        feedback_box.SetBackgroundColour(wx.Colour(245, 245, 245))
        feedback_box.SetWindowStyle(wx.SIMPLE_BORDER)
        fb_sizer = wx.BoxSizer(wx.VERTICAL)
        self.feedback = wx.StaticText(feedback_box, label="")
        self.feedback.SetFont(self.font(13, False))
        self.feedback.SetForegroundColour(wx.Colour(180, 40, 50))
        fb_sizer.Add(self.feedback, 1, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 10)
        feedback_box.SetSizer(fb_sizer)
        self.root.Add(feedback_box, 0, wx.ALIGN_CENTER | wx.TOP, 14)

        # score
        self.score_lbl = wx.StaticText(self.panel, label=f"Score: {self.score}/{len(self.questions)}")
        self.score_lbl.SetFont(self.font(14, True))
        self.score_lbl.SetForegroundColour(wx.Colour(20, 20, 20))
        self.root.Add(self.score_lbl, 0, wx.ALIGN_CENTER | wx.TOP, 6)

        self.panel.Layout()

    # ---------- NAV ----------
    def set_choice(self, idx):
        self.selected_option = idx
        if self.selected_option is not None:
            self.next_btn.Enable()

    def check(self, event):
        if self.selected_option is None:
            wx.MessageBox("Choose an option first!", "Warning")
            return

        correct = self.questions[self.current_index].get("answer_index")
        if correct is None:
            wx.MessageBox("Question missing answer_index", "Error")
            return

        if self.selected_option == correct:
            self.score += 1
            play_correct_sound()
            # immediately proceed
            self.current_index += 1
            if self.current_index < len(self.questions):
                self.selected_option = None
                self.next_btn.Disable()
                self.show_quiz()  # reload UI for next question
            else:
                self.end_screen()
        else:
            right = self.questions[self.current_index]["options"][correct]
            self.feedback.SetLabel(f"Correct Answer: {right}")
            self.next_btn.Enable()
            play_wrong_sound()
            self.score_lbl.SetLabel(f"Score: {self.score}/{len(self.questions)}")

    def next(self, event):
        # Move forward without awarding point
        self.current_index += 1
        self.selected_option = None
        self.next_btn.Disable()
        if self.current_index < len(self.questions):
            self.show_quiz()
        else:
            self.end_screen()

    def end_screen(self):
        self.reset()
        self.panel.Refresh()

        txt = wx.StaticText(self.panel, label=f"QUIZ COMPLETE — SCORE {self.score}/{len(self.questions)}")
        txt.SetFont(self.font(28, True))
        txt.SetForegroundColour(wx.Colour(20, 20, 20))
        self.root.Add(txt, 0, wx.ALIGN_CENTER | wx.TOP, 100)

        restart_btn = wx.Button(self.panel, label="Restart", size=(220, 60))
        restart_btn.SetBackgroundColour(wx.Colour(255, 225, 0))
        restart_btn.SetForegroundColour(wx.Colour(10, 10, 10))
        restart_btn.SetFont(self.font(14, True))
        restart_btn.Bind(wx.EVT_BUTTON, lambda e: self.show_home())
        self.root.Add(restart_btn, 0, wx.ALIGN_CENTER | wx.TOP, 30)

        self.panel.Layout()

    # ---------- TIMER (optional extension) ----------
    # If you want a countdown per quiz, enable/implement timer logic here.

    # ---------- TTS ----------
    def speak_question(self, event):
        if not self.tts_engine:
            wx.MessageBox("Text-to-speech engine not available.", "Info")
            return
        q = self.questions[self.current_index]
        text = q.get("question", "")
        opts = q.get("options", [])
        full = text + ". " + " . ".join([f"Option {i+1}: {o}" for i, o in enumerate(opts)])
        try:
            self.tts_engine.say(full)
            self.tts_engine.runAndWait()
        except Exception:
            wx.MessageBox("TTS failed to run.", "Info")

# -------------------- RUN --------------------
if __name__ == "__main__":
    # Ensure JSON loads before starting GUI to fail fast on format issues
    try:
        data = load_question_file("questions.json")
    except Exception as exc:
        msg = f"Failed to load questions.json:\n{exc}"
        # If running from terminal, print; otherwise show a message box
        try:
            app = wx.App(False)
            wx.MessageBox(msg, "Error loading JSON", wx.OK | wx.ICON_ERROR)
            app.ExitMainLoop()
        except Exception:
            print(msg)
        raise SystemExit(1)

    app = wx.App(False)
    FlashcardApp(data)
    app.MainLoop()
