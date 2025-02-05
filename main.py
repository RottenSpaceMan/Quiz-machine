import tkinter as tk
from tkinter import ttk
import random
import json

# Loading from JSON
with open("students.json") as f:
    students = json.load(f)
with open("questions.json") as f:
    quiz_questions = json.load(f)

class TeamInputDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Enter Number of Teams")
        self.geometry("1280x720")
        self.parent = parent

        self.label = ttk.Label(self, text="Number of Teams:")
        self.label.pack(pady=10)

        self.team_count_var = tk.IntVar(value=4)
        self.entry = ttk.Entry(self, textvariable=self.team_count_var)
        self.entry.pack(pady=5)

        self.confirm_button = ttk.Button(self, text="Confirm", command=self.on_confirm)
        self.confirm_button.pack(pady=10)

    def on_confirm(self):
        self.parent.num_teams = self.team_count_var.get()
        self.destroy()
        self.parent.show_student_assignment()

class StudentAssignmentDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Assign Students to Teams")
        self.geometry("1080x720")
        self.parent = parent

        self.team_vars = {}
        self.student_team = {}

        self.label = ttk.Label(self, text="Assign each student to a team:")
        self.label.pack(pady=10)

        self.student_frame = ttk.Frame(self)
        self.student_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Adding a canvas and scrollbar
        self.canvas = tk.Canvas(self.student_frame)
        self.scrollbar = ttk.Scrollbar(self.student_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        for student_id, student_name in students.items():
            frame = ttk.Frame(self.scrollable_frame)
            frame.pack(fill="x", pady=5)

            label = ttk.Label(frame, text=student_name)
            label.pack(side="left", padx=5)

            team_var = tk.StringVar(value="None")
            self.team_vars[student_id] = team_var

            options = ["None"] + [f"Team {i+1}" for i in range(self.parent.num_teams)]
            dropdown = ttk.OptionMenu(frame, team_var, *options)
            dropdown.pack(side="right", padx=5)

        self.confirm_button = ttk.Button(self, text="Confirm", command=self.on_confirm)
        self.confirm_button.pack(pady=10)

    def on_confirm(self):
        self.parent.student_team = {student_id: var.get() for student_id, var in self.team_vars.items() if var.get() != "None"}
        self.destroy()
        self.parent.create_quiz_app()

class QuizApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.num_teams = 4  # Default number of teams
        self.student_team = {}
        self.withdraw()  # Hide the main window initially
        self.team_input_dialog = TeamInputDialog(self)
        self.wait_window(self.team_input_dialog)  # Wait for the dialog to close

    def show_student_assignment(self):
        self.student_assignment_dialog = StudentAssignmentDialog(self)
        self.wait_window(self.student_assignment_dialog)  # Wait for the dialog to close

    def create_quiz_app(self):
        self.title("Quiz App")
        self.geometry("1080x720")
        self.team_names = [f"Team {i+1}" for i in range(self.num_teams)]
        self.team_scores = {team: 0 for team in self.team_names}
        self.current_question = None  # will hold a tuple (question, answer)
        self.current_team_index = 0
        self.skipped_teams = set()
        self.answer_visible = False
        self.create_widgets()
        self.deiconify()  # Show the main window

    def create_widgets(self):
        # --- TEAM SCORE SETTER SECTION ---
        self.score_setter_frame = ttk.LabelFrame(self, text="Set Team Score")
        self.score_setter_frame.pack(side="top", fill="x", padx=10, pady=5)

        self.team_var = tk.StringVar(value=self.team_names[0])
        # Create radio buttons for each team
        for team in self.team_names:
            rb = ttk.Radiobutton(
                self.score_setter_frame, text=team, variable=self.team_var, value=team
            )
            rb.pack(side="left", padx=5)

        # Add entry to show and set team score
        self.score_var = tk.StringVar(value="0")
        self.score_entry = ttk.Entry(self.score_setter_frame, textvariable=self.score_var, width=5)
        self.score_entry.pack(side="left", padx=5)

        self.set_score_button = ttk.Button(self.score_setter_frame, text="Set Score", command=self.set_team_score)
        self.set_score_button.pack(side="left", padx=5)

        # --- TEAM ASSIGNMENT SECTION ---
        self.team_frame = ttk.LabelFrame(self, text="Team Selection")
        self.team_frame.pack(side="top", fill="x", padx=10, pady=5)

        # --- QUIZ CONTROL SECTION ---
        self.quiz_frame = ttk.LabelFrame(self, text="Quiz")
        self.quiz_frame.pack(side="top", fill="both", expand=True, padx=10, pady=5)

        # Display the current question
        self.question_label = ttk.Label(self.quiz_frame, text="Press Start to get a question", wraplength=500, font=("Helvetica", 16))
        self.question_label.pack(pady=10)

        # Display the randomly selected student for the current team
        self.student_label = ttk.Label(self.quiz_frame, text="Student: N/A")
        self.student_label.pack(pady=10)

        # Display the answer (initially hidden)
        self.answer_label = ttk.Label(self.quiz_frame, text="", wraplength=500)
        self.answer_label.pack(pady=10)

        # Buttons for controlling the quiz
        self.control_frame = ttk.Frame(self.quiz_frame)
        self.control_frame.pack(pady=10)

        self.start_button = ttk.Button(self.control_frame, text="Start Question", command=self.start_question)
        self.start_button.pack(side="left", padx=5)

        self.random_question_button = ttk.Button(self.control_frame, text="Random Question", command=self.random_question)
        self.random_question_button.pack(side="left", padx=5)

        self.random_student_button = ttk.Button(self.control_frame, text="Random Student", command=self.random_student)
        self.random_student_button.pack(side="left", padx=5)

        self.check_answer_button = ttk.Button(self.control_frame, text="Show Answer", command=self.toggle_answer)
        self.check_answer_button.pack(side="left", padx=5)

        self.correct_button = ttk.Button(self.control_frame, text="Correct", command=self.mark_correct)
        self.correct_button.pack(side="left", padx=5)

        self.skip_button = ttk.Button(self.control_frame, text="Skip", command=self.skip_question)
        self.skip_button.pack(side="left", padx=5)

        # --- LEADERBOARD SECTION ---
        self.score_frame = ttk.LabelFrame(self, text="Leaderboard")
        self.score_frame.pack(side="bottom", fill="x", padx=10, pady=5)

        self.score_text = tk.Text(self.score_frame, height=5, state="disabled")
        self.score_text.pack(fill="x")

        # Adding a reset button
        self.reset_button = ttk.Button(self.score_frame, text="Reset Quiz", command=self.reset_quiz)
        self.reset_button.pack(pady=10)

    def set_team_score(self):
        team = self.team_var.get()
        try:
            score = int(self.score_var.get())
            self.team_scores[team] = score
            self.update_leaderboard()
        except ValueError:
            pass  # Ignore invalid input

    def start_question(self):
        if not quiz_questions:
            self.end_quiz()
            return
        # Randomly select a question (pop it so it isn’t repeated)
        qid = random.choice(list(quiz_questions.keys()))
        self.current_question = quiz_questions.pop(qid)
        self.question_label.config(text=self.current_question["question"])
        self.answer_label.config(text="")
        self.answer_visible = False
        self.check_answer_button.config(text="Show Answer")
        self.random_student()

    def random_question(self):
        if not quiz_questions:
            self.end_quiz()
            return
        qid = random.choice(list(quiz_questions.keys()))
        self.current_question = quiz_questions.pop(qid)
        self.question_label.config(text=self.current_question["question"], font=("Helvetica", 16))
        self.answer_label.config(text="")
        self.answer_visible = False
        self.check_answer_button.config(text="Show Answer")

    def random_student(self):
        current_team = self.team_var.get()
        assigned_students = [student for student, team in self.student_team.items() if team == current_team]
        if assigned_students:
            selected_student = random.choice(assigned_students)
            self.student_label.config(text=f"Student: {students[selected_student]}", font=("Helvetica", 16))
        else:
            self.student_label.config(text="Student: N/A", font=("Helvetica", 16))

    def toggle_answer(self):
        if self.current_question:
            if self.answer_visible:
                self.answer_label.config(text="")
                self.check_answer_button.config(text="Show Answer")
            else:
                self.answer_label.config(text=f"Answer: {self.current_question['answer']}")
                self.check_answer_button.config(text="Hide Answer")
            self.answer_visible = not self.answer_visible

    def mark_correct(self):
        team = self.team_var.get()
        self.team_scores[team] += 1
        self.update_leaderboard()
        self.next_team()
        self.start_question()

    def skip_question(self):
        current_team = self.team_var.get()
        self.skipped_teams.add(current_team)
        self.next_team()
        if len(self.skipped_teams) == len(self.team_names):
            self.skipped_teams.clear()
            self.question_label.config(text="Question Skipped!")
            self.current_question = None
            self.start_question()

    def next_team(self):
        self.current_team_index = (self.current_team_index + 1) % len(self.team_names)
        self.team_var.set(self.team_names[self.current_team_index])
        self.student_label.config(text="Student: N/A")
        if self.current_team_index == 0 and self.current_question is None:
            self.start_question()

    def update_leaderboard(self):
        leaderboard = "Leaderboard:\n"
        for team, score in self.team_scores.items():
            leaderboard += f"{team}: {score}\n"
        self.score_text.config(state="normal")
        self.score_text.delete("1.0", tk.END)
        self.score_text.insert(tk.END, leaderboard)
        self.score_text.config(state="disabled")

    def end_quiz(self):
        self.update_leaderboard()
        self.question_label.config(text="Quiz Finished!")

    def reset_quiz(self):
        self.num_teams = 4
        self.student_team = {}
        self.team_scores = {team: 0 for team in self.team_names}
        self.current_question = None
        self.current_team_index = 0
        self.skipped_teams = set()
        self.withdraw()
        self.team_input_dialog = TeamInputDialog(self)
        self.wait_window(self.team_input_dialog)

if __name__ == "__main__":
    app = QuizApp()
    app.mainloop()
