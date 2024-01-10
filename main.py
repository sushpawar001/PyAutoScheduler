import csv
import datetime as dt
import time
import json
import traceback
import tkinter as tk
import tkinter.font as tkFont
from tkinter import messagebox
import ttkbootstrap as tkb
from tkinter.filedialog import askopenfilename
from ttkbootstrap.tooltip import ToolTip

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

frames = {}
timetable_struct: dict = {
    "Mon": [],
    "Tue": [],
    "Wed": [],
    "Thurs": [],
    "Fri": [],
    "Sat": [],
}

today: dt.datetime = dt.datetime.now()


def calc_college_time(
    start_time: dt.datetime, end_time: dt.datetime, minutes_lecture: float
) -> int:
    """
    Calculates the total number of college minutes between a start time and an end time,
    given the duration of each lecture in minutes.
    """

    minutesofcollege = end_time - start_time
    minutesofcollege = minutesofcollege.total_seconds() / 60.0
    return int(minutesofcollege // minutes_lecture)


def frame_expansion(frame: tkb.Frame) -> None:
    """
    Configures the widgets in the frame to expand and take full frame size
    """
    size = frame.grid_size()
    rows = size[1]
    columns = size[0]

    for col in range(columns):
        frame.columnconfigure(col, weight=2)

    for row in range(rows):
        frame.rowconfigure(row, weight=2)


def create_entry_frame() -> tkb.Frame:
    def take_info() -> None:
        """
        Stores info user given in input to the file.
        updates info in 'profs' directory.
        """
        name: str = (
            prof_entry.get().title() if prof_var.get() == "None" else prof_var.get()
        )

        year: str = ""  # Changed None to ""

        if year_var.get() == "None":
            if dept_var.get() != "None":
                year = f"{year_entry.get().upper()} {dept_var.get()}"
        else:
            year = year_var.get()

        sub = subject_entry.get()
        sub_type = subtype_var.get()
        sub_dict = {"Subject": sub, "Type": sub_type}

        workload = workload_entry.get()

        if workload:
            workload = int(workload)
            if workload < 0:
                aleart_pop_up("Workload should be greater than zero")
                return
            else:
                sub_dict["Workload"] = workload  # type: ignore

        print(f"[create_entry_frame] Name = {name}")
        print(f"[create_entry_frame] Subject = {sub}")
        print(f"[create_entry_frame] sub_dict = {sub_dict}")

        # checking all entries
        if not (name and year and sub):
            aleart_pop_up("Please fill all columns")
            return

        # adding new professor if not in dict
        if name not in profs:
            profs[name] = {year: []}
            all_profs.append(name)
            prof_OptionMenu["menu"].add_command(
                label=name, command=lambda opt=name: prof_var.set(opt)
            )

        # adding new year to professor if not in dict
        elif name in profs:
            if year not in profs[name]:
                profs[name].update({year: []})

        # adding year to option menu
        if year not in all_years_temp:
            all_years_temp.append(year)
            year_OptionMenu["menu"].add_command(
                label=year, command=lambda opt=year: year_var.set(opt)
            )

        all_subjects = get_subjects_by_year(year)

        # TODO: Workload will not be added if option is both
        # checking if subject already exists
        if sub_type == "Both":
            updated: bool = False
            for sub_type_value in ["Theory", "Practical"]:
                if (sub, sub_type_value) not in all_subjects:
                    sub_dict_copy = sub_dict.copy()
                    sub_dict_copy["Type"] = sub_type_value
                    profs[name][year].append(sub_dict_copy)
                    updated = True

            if not updated:
                teaching_prof = get_professor_by_subject(sub, "Theory")
                aleart_pop_up(
                    f"Prof. {teaching_prof} is already teaching this subject!"
                )
                return
        else:
            if (sub, sub_type) not in all_subjects:
                profs[name][year].append(sub_dict)
            else:
                teaching_prof = get_professor_by_subject(sub, sub_type)
                aleart_pop_up(
                    f"Prof. {teaching_prof} is already teaching this subject!"
                )
                return

        store_json(PROFS_FILE, profs)
        update_all_years()
        create_all_pages()
        create_menu()

    vertical_padding = 10
    horizontal_padding = 15

    entry_frame = tkb.Frame(window, padding=(20, 15))

    text1 = tk.Label(entry_frame, text="Prof:")
    text1.grid(row=0, column=0, pady=vertical_padding)
    prof_entry = tkb.Entry(entry_frame)
    prof_entry.grid(row=0, column=1, columnspan=2, pady=vertical_padding, sticky="we")

    text5 = tk.Label(entry_frame, text="Or select Prof:")
    text5.grid(row=1, column=0, pady=vertical_padding)

    # variable for managing prof entries
    prof_var: tk.StringVar = tk.StringVar()
    prof_var.set("None")
    all_profs: list = ["None"] + list(profs.keys())

    prof_OptionMenu = tkb.OptionMenu(entry_frame, prof_var, *all_profs)
    prof_OptionMenu.configure(cursor="hand2")
    prof_OptionMenu.grid(
        row=1, column=1, columnspan=2, pady=vertical_padding, sticky="NSEW"
    )

    text2 = tk.Label(entry_frame, text="Year:")
    text2.grid(row=2, column=0, pady=vertical_padding)
    year_entry = tkb.Entry(entry_frame)
    year_entry.grid(row=2, column=1, columnspan=2, pady=vertical_padding, sticky="we")

    text8 = tk.Label(entry_frame, text="Department:")
    text8.grid(row=3, column=0, pady=vertical_padding)

    ################################
    dept_var: tk.StringVar = tk.StringVar()
    dept_var.set("None")
    all_departments: list = ["None"] + get_all_departments()

    departments_OptionMenu = tkb.OptionMenu(entry_frame, dept_var, *all_departments)
    departments_OptionMenu.configure(cursor="hand2")
    departments_OptionMenu.grid(
        row=3, column=1, columnspan=2, pady=vertical_padding, sticky="NSEW"
    )
    ################################

    text5 = tk.Label(entry_frame, text="Or select Year\n& Department:")
    text5.grid(row=4, column=0, pady=vertical_padding)

    year_var: tk.StringVar = tk.StringVar()
    year_var.set("None")
    all_years_temp: list = ["None"] + get_all_years()

    year_OptionMenu = tkb.OptionMenu(entry_frame, year_var, *all_years_temp)
    year_OptionMenu.configure(cursor="hand2")
    year_OptionMenu.grid(
        row=4, column=1, columnspan=2, pady=vertical_padding, sticky="NSEW"
    )

    text3 = tk.Label(entry_frame, text="Subject:")
    text3.grid(row=5, column=0, pady=vertical_padding)
    subject_entry = tkb.Entry(entry_frame)
    subject_entry.grid(
        row=5, column=1, columnspan=2, pady=vertical_padding, sticky="we"
    )

    subtype_var: tk.StringVar = tk.StringVar(entry_frame)
    subtype_var.set("Both")

    text4 = tk.Label(entry_frame, text="Subject type:")
    text4.grid(row=6, column=0, columnspan=3, pady=vertical_padding)

    radio1 = tkb.Radiobutton(
        entry_frame, text="Theory", value="Theory", variable=subtype_var
    )
    radio1.grid(row=7, column=0, pady=vertical_padding)

    radio2 = tkb.Radiobutton(
        entry_frame, text="Practical", value="Practical", variable=subtype_var
    )
    radio2.grid(row=7, column=1, pady=vertical_padding)

    radio3 = tkb.Radiobutton(
        entry_frame, text="Both", value="Both", variable=subtype_var
    )
    radio3.grid(row=7, column=2, pady=vertical_padding)

    text6 = tk.Label(entry_frame, text="Subject Workload\n(per week):")
    text6.grid(row=8, column=0, pady=vertical_padding, padx=horizontal_padding)
    workload_entry = tkb.Entry(entry_frame)
    workload_entry.grid(
        row=8, column=1, columnspan=2, pady=vertical_padding, sticky="we"
    )

    submit_button = tkb.Button(
        entry_frame,
        text="Submit",
        command=take_info,
    )
    submit_button.grid(
        row=9, column=0, columnspan=3, pady=vertical_padding, sticky="NSEW"
    )

    # changing background all objects in frame
    # for label in entry_frame.children:
    #     if any(["radio" in label, "label" in label, "optionmenu" in label]):
    #         entry_frame.children[label].configure(background=LIGHT_GRAY_COLOR)

    frame_expansion(entry_frame)

    return entry_frame


def optional_subject_entry_frame() -> tkb.Frame:
    def update_menu_helper(sub_list, tk_var, menu):
        # Clear the current options in the second OptionMenu
        menu["menu"].delete(0, "end")

        if not sub_list:
            menu["menu"].add_command(
                label="None",
            )
            tk_var.set("None")
            return

        # Add new options based on the selected option in the first OptionMenu
        for subject in sub_list:
            menu["menu"].add_command(
                label=f"{subject['Subject']} - {subject['Type']}",
                command=lambda sub=subject: tk_var.set(
                    f"{sub['Subject']} - {sub['Type']}"
                ),
            )

        tk_var.set(f"{subject['Subject']} - {subject['Type']}")

    def update_options(*args):
        year = year_var.get()
        prof1 = prof1_var.get()
        prof2 = prof2_var.get()

        if prof1 != "None":
            sub1_list = get_all_subjects(prof1, year)
            print(f"{prof1} -> {sub1_list = }")
            update_menu_helper(sub1_list, sub1_var, sub1_OptionMenu)

        if prof2 != "None":
            sub2_list = get_all_subjects(prof2, year)
            print(f"{prof2} -> {sub2_list = }")
            update_menu_helper(sub2_list, sub2_var, sub2_OptionMenu)

    def add_options():
        year = year_var.get()
        prof1 = prof1_var.get()
        prof2 = prof2_var.get()

        subject1 = sub1_var.get()
        subject2 = sub2_var.get()

        selected_subject1, selected_subject_type1 = subject1.split(" - ")
        selected_subject2, selected_subject_type2 = subject2.split(" - ")

        global profs
        profs = read_json(PROFS_FILE)

        for sub in profs[prof1][year]:
            if sub["Subject"] == selected_subject1:
                if "Options" in sub:
                    sub["Options"].update({prof2: selected_subject2})
                else:
                    sub["Options"] = {prof2: selected_subject2}

        for sub in profs[prof2][year]:
            if sub["Subject"] == selected_subject2:
                if "Options" in sub:
                    sub["Options"].update({prof1: selected_subject1})
                else:
                    sub["Options"] = {prof1: selected_subject1}

        print(f"{selected_subject1} -> {selected_subject2}")
        store_json(PROFS_FILE, profs)

    vertical_padding = 10
    horizontal_padding = 15

    optional_entry_frame = tkb.Frame(
        window,
        padding=(20, 15),
    )

    # Options menu vars
    year_var: tk.StringVar = tk.StringVar()
    year_var.set("None")
    all_years_temp: list = ["None"] + get_all_years()

    prof1_var: tk.StringVar = tk.StringVar()
    prof2_var: tk.StringVar = tk.StringVar()
    prof1_var.set("None")
    prof2_var.set("None")
    all_profs: list = ["None"] + list(profs.keys())

    sub1_var: tk.StringVar = tk.StringVar()
    sub2_var: tk.StringVar = tk.StringVar()
    sub1_var.set("None")
    sub2_var.set("None")

    # GUI
    text1 = tk.Label(optional_entry_frame, text="Select College Year:")
    text1.grid(row=0, column=0, pady=vertical_padding)

    year_OptionMenu = tkb.OptionMenu(optional_entry_frame, year_var, *all_years_temp)
    year_OptionMenu.grid(
        row=0, column=1, pady=vertical_padding, columnspan=2, sticky="ew"
    )

    # -----
    text2 = tk.Label(optional_entry_frame, text="Professor 1:")
    text2.grid(row=1, column=0, pady=vertical_padding)

    prof1_OptionMenu = tkb.OptionMenu(
        optional_entry_frame, prof1_var, *all_profs, command=update_options
    )
    prof1_OptionMenu.grid(row=1, column=1, pady=vertical_padding, padx=5, sticky="ew")

    sub1_OptionMenu = tkb.OptionMenu(optional_entry_frame, sub1_var, "None")
    sub1_OptionMenu.grid(row=1, column=2, pady=vertical_padding, padx=5, sticky="ew")

    # -----
    text3 = tk.Label(optional_entry_frame, text="Professor 2:")
    text3.grid(row=2, column=0, pady=vertical_padding)

    prof2_OptionMenu = tkb.OptionMenu(
        optional_entry_frame, prof2_var, *all_profs, command=update_options
    )
    prof2_OptionMenu.grid(row=2, column=1, pady=vertical_padding, padx=5, sticky="ew")

    sub2_OptionMenu = tkb.OptionMenu(optional_entry_frame, sub2_var, "None")
    sub2_OptionMenu.grid(row=2, column=2, pady=vertical_padding, padx=5, sticky="ew")
    # -----

    submit_button = tkb.Button(
        optional_entry_frame,
        text="Submit",
        command=add_options,
    )
    submit_button.grid(
        row=3, column=0, columnspan=3, pady=vertical_padding, sticky="NSEW"
    )

    frame_expansion(optional_entry_frame)
    return optional_entry_frame


def view_timetable_frame(year_key) -> tkb.Frame:
    """
    Creates a timetable frame to show given year's timetable
    """

    def rewrap(event: tk.Event) -> None:
        event.widget.config(wraplength=event.width - 15)

    def add_tooltip(widget: tk.Label | tkb.Label, lec_num, day_num_of_week) -> None:
        days = {
            0: "Mon",
            1: "Tue",
            2: "Wed",
            3: "Thurs",
            4: "Fri",
            5: "Sat",
        }
        available_profs = check_professor_available(lec_num, days[day_num_of_week])
        dept_profs = get_professors_by_year(profs, year_key)

        available_profs_lec_num = "\n".join(set(available_profs) & set(dept_profs))

        ToolTip(
            widget,
            text=available_profs_lec_num
            if available_profs_lec_num
            else "No Professors Available!",
        )

    temp_var: dict = ttlist
    table_frame = tkb.Frame(window)
    vertical_pad = 10
    horizontal_pad = 20
    borderwidth = 1
    RELIEF_TYPE = "ridge"

    if not settings:
        label = tk.Label(
            table_frame,
            text="No Departments found!",
            pady=vertical_pad,
            padx=horizontal_pad,
        )
        label.grid(row=0, column=0, sticky="NSEW")
        frame_expansion(table_frame)
        return table_frame

    label = tk.Label(
        master=table_frame,
        text=f"{year_key} - Time Table",
        relief=RELIEF_TYPE,
        pady=vertical_pad * 2,
        bg=LIGHT_GRAY_COLOR,
        fg=DARK_GRAY_COLOR,
        borderwidth=borderwidth,
        font=HEADING_FONT,
    )
    label.grid(row=0, column=0, columnspan=7, sticky="NSEW")

    # creating heading label

    time_label = tkb.Label(
        master=table_frame,
        text="Time",
        relief=RELIEF_TYPE,
        anchor="center",
        padding=10,
        bootstyle="inverse-primary",
    )

    department: str = get_department_by_year(year_key)
    start_time, end_time, minutes_lecture = get_department_time(department)
    no_of_lectures = calc_college_time(start_time, end_time, minutes_lecture)

    # creating time labels
    temp_time = start_time
    time_label.grid(row=1, column=0, sticky="NSEW")
    for row in range(1, int(no_of_lectures) + 1):
        label = tk.Label(
            master=table_frame,
            text=f"{temp_time:%H:%M %p}",
            relief=RELIEF_TYPE,
            pady=vertical_pad,
            padx=horizontal_pad,
            bg=LIGHT_GRAY_COLOR,
            fg=DARK_GRAY_COLOR,
            borderwidth=borderwidth,
        )
        label.grid(row=row + 1, column=0, sticky="NSEW")
        temp_time = temp_time + dt.timedelta(minutes=minutes_lecture)

    for col, value in enumerate(temp_var[year_key]):
        label = tkb.Label(
            master=table_frame,
            text=f"{value}",
            relief=RELIEF_TYPE,
            anchor="center",
            bootstyle="inverse-primary",
        )
        label.grid(row=1, column=col + 1, sticky="NSEW")

        for row, value2 in enumerate(temp_var[year_key][value], start=2):
            label_text = (
                f"{value2['subject']}\n{value2['subtype']}\n{value2['professor']}"
            )

            label = tkb.Label(
                master=table_frame,
                text=label_text,
                relief="sunken",
                borderwidth=1,
                anchor="center",
                padding=10,
                justify="center",
                bootstyle="inverse-secondary" if "Empty Slot" in label_text else "",
                wraplength=140,
            )
            label.grid(row=row, column=col + 1, sticky="NSEW")
            label.bind("<Configure>", rewrap)

            if "Empty Slot" in label_text:
                add_tooltip(label, row - 2, col)

    frame_expansion(table_frame)

    return table_frame


def view_prof_tt_frame() -> tkb.Frame:
    prof_tt_frame = tkb.Frame(window)
    vertical_pad = 10
    horizontal_pad = 10
    borderwidth = 1
    RELIEF_TYPE = "ridge"

    if not profs:
        label = tk.Label(
            prof_tt_frame,
            text="No professors found!",
            pady=vertical_pad,
            padx=horizontal_pad,
        )
        label.grid(row=0, column=0, sticky="NSEW")
        frame_expansion(prof_tt_frame)
        return prof_tt_frame

    if not settings:
        label = tk.Label(
            prof_tt_frame,
            text="No departments found!\nPlease add department first.",
            pady=vertical_pad,
            padx=horizontal_pad,
        )
        label.grid(row=0, column=0, sticky="NSEW")
        frame_expansion(prof_tt_frame)
        return prof_tt_frame

    prof_var = tk.StringVar()
    all_profs: list = list(sorted(profs.keys()))

    if not all_profs:
        all_profs = ["None"]

    prof_var.set(all_profs[0])

    all_days: dict = list(ttlist.values())[0]
    all_days: list = list(all_days.keys())

    label = tk.Label(
        prof_tt_frame,
        text="Select Professor:",
        pady=vertical_pad,
        padx=horizontal_pad,
    )
    label.grid(row=0, column=0, columnspan=3, sticky="NSEW")

    prof_OptionMenu = tkb.OptionMenu(prof_tt_frame, prof_var, None, *all_profs)
    prof_OptionMenu.configure(cursor="hand2")

    prof_OptionMenu.grid(row=0, column=3, columnspan=4, sticky="NSEW")

    def generate_tt(*args):
        for widget in prof_tt_frame.winfo_children():
            if widget in [prof_OptionMenu, label]:
                continue
            widget.destroy()

        prof = prof_var.get()
        time_slots = get_time_slots_by_prof(prof)

        time_label_header = tk.Label(
            master=prof_tt_frame,
            text="Time",
            relief=RELIEF_TYPE,
            pady=vertical_pad,
            padx=horizontal_pad,
            bg=TEAL_COLOR,
            fg=WHITE_COLOR,
            borderwidth=borderwidth,
        )
        time_label_header.grid(row=2, column=0, sticky="NSEW")

        for col, day in enumerate(all_days):
            scheduled_lecs = get_lec_number(prof, day)
            scheduled_lecs_sorted = {}

            for key, values in scheduled_lecs.items():
                for value in values:
                    scheduled_lecs_sorted[value] = key

            scheduled_lecs_sorted = dict(sorted(scheduled_lecs_sorted.items()))

            slot_label_header = tk.Label(
                master=prof_tt_frame,
                text=day,
                relief=RELIEF_TYPE,
                pady=vertical_pad,
                padx=horizontal_pad,
                bg=TEAL_COLOR,
                fg=WHITE_COLOR,
                borderwidth=borderwidth,
            )
            slot_label_header.grid(row=2, column=col + 1, sticky="NSEW")

            for lec_num, time in enumerate(time_slots):
                slot_text = scheduled_lecs_sorted.get(lec_num, "Free Slot")

                time_label = tk.Label(
                    master=prof_tt_frame,
                    text=time,
                    relief=RELIEF_TYPE,
                    pady=vertical_pad,
                    padx=horizontal_pad,
                    bg=LIGHT_GRAY_COLOR,
                    fg=DARK_GRAY_COLOR,
                    borderwidth=borderwidth,
                )
                time_label.grid(row=lec_num + 3, column=0, sticky="NSEW")

                slot_label = tkb.Label(
                    master=prof_tt_frame,
                    text=slot_text,
                    padding=10,
                    anchor="center",
                    bootstyle="inverse-success" if slot_text == "Free Slot" else "",
                    borderwidth=borderwidth,
                    justify="center",
                )

                slot_label.grid(row=lec_num + 3, column=col + 1, sticky="NSEW")

    prof_var.trace_add("write", generate_tt)
    generate_tt()

    frame_expansion(prof_tt_frame)

    return prof_tt_frame


# TODO:Complete this
def create_professors_frame() -> tkb.Frame:
    def show_options(*args):
        years = get_years_by_department(dept_var.get())
        departments_OptionMenu.grid(columnspan=len(years) + 1)

        for widget in professors_frame.winfo_children():
            if widget in [departments_OptionMenu]:
                continue
            widget.destroy()

        for col, year in enumerate(years):
            header_label = tk.Label(
                master=professors_frame,
                text=f"{year}",
                relief=RELIEF_TYPE,
                font=SUBHEADING_FONT_BOLD,
            )
            header_label.grid(row=1, column=col + 1, sticky="NSEW")

        professor_label = tk.Label(
            master=professors_frame,
            text="Professors",
            relief=RELIEF_TYPE,
            padx=5,
            pady=5,
            font=HEADING_FONT,
        )
        professor_label.grid(row=1, column=0, sticky="NSEW")

        for row, professor in enumerate(
            get_professors_by_department(dept_var.get()), start=2
        ):
            professors_label = tk.Label(
                master=professors_frame,
                text=f"{professor}",
                relief=RELIEF_TYPE,
                padx=5,
                pady=5,
            )
            professors_label.grid(row=row, column=0, sticky="NSEW")

            for col, year in enumerate(years):  # starting from 1 because added none.
                subjects = get_all_subjects(professor, year)
                label_text = ""
                if subjects:
                    for sub in subjects:
                        label_text = f"{label_text}{sub['Subject']} ({sub['Type']})\n"
                    label_text = label_text[:-1]
                else:
                    label_text = None

                label = tk.Label(
                    master=professors_frame,
                    text=f"{label_text}",
                    relief=RELIEF_TYPE,
                    padx=5,
                    pady=5,
                )
                label.grid(row=row, column=col + 1, sticky="NSEW")

    professors_frame = tkb.Frame(window, padding=5)
    RELIEF_TYPE = "ridge"

    # early exit if no professors found
    if not profs:
        label = tk.Label(
            professors_frame,
            text="No professors found!",
        )
        label.grid(row=0, column=0, sticky="EW")
        frame_expansion(professors_frame)
        return professors_frame

    dept_var = tk.StringVar()
    all_departments: list = get_all_departments()
    dept_var.set(all_departments[0])
    departments_OptionMenu = tkb.OptionMenu(
        professors_frame, dept_var, None, *all_departments, bootstyle="outline"
    )
    departments_OptionMenu.configure(cursor="hand2")
    departments_OptionMenu.grid(row=0, column=0, columnspan=2, sticky="NSEW")

    dept_var.trace_add("write", show_options)
    show_options()
    frame_expansion(professors_frame)
    return professors_frame


def create_options_frame() -> tkb.Frame:
    def take_info() -> None:
        """
        Stores info user given in input to the file.
        updates info in 'profs' directory.
        """
        department = dept_var.get()
        start_time = start_time_entry.get()
        end_time = end_time_entry.get()
        minutes_lecture = int(lec_duration_entry.get())
        practical_slots_str = practical_slots_entry.get()
        if practical_slots_str:
            practical_slots = [int(num) for num in practical_slots_str.split(",")]
        else:
            practical_slots = []

        try:
            start_time = dt.datetime.strptime(start_time, "%H:%M")
            end_time = dt.datetime.strptime(end_time, "%H:%M")
        except Exception as error:
            print(f"Error: {error}")
            aleart_pop_up("Enter Correct Values!")
            return

        nooflectures = calc_college_time(start_time, end_time, minutes_lecture)

        start_time = dt.datetime.combine(today.date(), start_time.time())
        end_time = dt.datetime.combine(today.date(), end_time.time())

        curr_time_label.config(
            text=f"""Current College time is {start_time:%H:%M %p} to {end_time:%H:%M %p}.
        Lecture duration is {minutes_lecture} min
        Total number of lectures are {int(nooflectures)}."""
        )

        settings[department] = {
            "start_time": dt.datetime.strftime(start_time, "%H:%M"),
            "end_time": dt.datetime.strftime(end_time, "%H:%M"),
            "minutes_lecture": minutes_lecture,
            "practical_slots": practical_slots,
        }
        store_json(SETTINGS_FILE, settings)

        if ask_pop_up("Do you want to reset timetable?"):
            auto_schedule_helper()

    def show_options(*args):
        start_time, end_time, minutes_lecture = get_department_time(dept_var.get())
        nooflectures = calc_college_time(start_time, end_time, minutes_lecture)
        practical_slots = get_practical_slots_by_department(dept_var.get())

        curr_time_label.config(
            text=f"""Current College time is {start_time:%H:%M %p} to {end_time:%H:%M %p}.
            Lecture duration is {minutes_lecture} min
            Total number of lectures are {int(nooflectures)}.""",
        )

        start_time_entry.delete(0, tk.END)
        end_time_entry.delete(0, tk.END)
        lec_duration_entry.delete(0, tk.END)
        practical_slots_entry.delete(0, tk.END)

        start_time_entry.insert(0, f"{start_time:%H:%M}")
        end_time_entry.insert(0, f"{end_time:%H:%M}")
        lec_duration_entry.insert(0, minutes_lecture)
        practical_slots_str = ",".join(map(str, practical_slots))
        practical_slots_entry.insert(0, practical_slots_str)

    vertical_padding = 10
    options_frame = tkb.Frame(window, padding=(25, 20))

    if not settings:
        label = tk.Label(
            options_frame,
            text="No departments found!\nPlease create a department first",
        )
        label.grid(row=0, column=0, sticky="NSEW")
        frame_expansion(options_frame)
        return options_frame

    dept_var = tk.StringVar()
    all_departments: list = get_all_departments()
    dept_var.set(all_departments[0])

    departments_OptionMenu = tkb.OptionMenu(
        options_frame, dept_var, None, *all_departments, bootstyle="outline"
    )
    departments_OptionMenu.configure(cursor="hand2")
    departments_OptionMenu.grid(
        row=1, column=0, columnspan=2, pady=vertical_padding, sticky="NSEW"
    )

    curr_time_label = tk.Label(
        options_frame, anchor="center", justify="center", font=SUBHEADING_FONT
    )
    curr_time_label.grid(row=0, column=0, columnspan=2, pady=vertical_padding)

    text1 = tk.Label(options_frame, text="Start Time: (24hr)")
    text1.grid(row=2, column=0, pady=vertical_padding)
    start_time_entry = tkb.Entry(options_frame)
    start_time_entry.grid(row=2, column=1)

    text2 = tk.Label(options_frame, text="End Time:")
    text2.grid(row=3, column=0, pady=vertical_padding)
    end_time_entry = tkb.Entry(options_frame)
    end_time_entry.grid(row=3, column=1, pady=vertical_padding)

    text3 = tk.Label(options_frame, text="Lecture Duration: (min)")
    text3.grid(row=4, column=0, pady=vertical_padding)
    lec_duration_entry = tkb.Entry(options_frame)
    lec_duration_entry.grid(row=4, column=1, pady=vertical_padding)

    text4 = tk.Label(options_frame, text="Practical Slots: (comma separated)")
    text4.grid(row=5, column=0, pady=vertical_padding)
    practical_slots_entry = tkb.Entry(options_frame)
    practical_slots_entry.grid(row=5, column=1, pady=vertical_padding)

    dept_var.trace_add("write", show_options)
    show_options()

    submit_button = tkb.Button(options_frame, text="Submit", command=take_info)
    submit_button.grid(
        row=6, column=0, columnspan=2, pady=vertical_padding, sticky="NSEW"
    )

    frame_expansion(options_frame)

    return options_frame


def create_menu() -> None:
    """
    Creates a Menu for main GUI
    """

    menu = tk.Menu(window)
    window.config(menu=menu)

    prof_options = tk.Menu(menu)

    prof_options.add_command(
        label="Show All Professors",
        command=lambda: create_page(create_professors_frame),
    )

    prof_options.add_command(
        label="Professors' Timetable", command=lambda: create_page(view_prof_tt_frame)
    )

    prof_options.add_command(label="Delete All Professors", command=delete_all_profs)

    menu.add_cascade(label="Professors", menu=prof_options)

    options = tk.Menu(menu)

    options.add_command(
        label="Add Department", command=lambda: create_page(create_add_department_frame)
    )

    options.add_command(
        label="Department Settings", command=lambda: create_page(create_options_frame)
    )

    options.add_command(label="Import CSV", command=lambda: create_page(get_csv_frame))

    options.add_command(
        label="Add Data", command=lambda: create_page(create_entry_frame)
    )

    options.add_command(
        label="Add Optional Subjects",
        command=lambda: create_page(optional_subject_entry_frame),
    )

    options.add_command(
        label="Delete Subject", command=lambda: create_page(delete_subject_frame)
    )

    options.add_command(
        label="Export TimeTable", command=lambda: create_page(create_export_page)
    )

    menu.add_cascade(label="Options", menu=options)

    tt_menu = tk.Menu(menu)

    for year in all_years:
        tt_menu.add_command(label=year, command=lambda y=year: create_page(y))

    tt_menu.add_command(label="Clear TimeTable", command=set_default_tt)

    menu.add_cascade(label="Time Table", menu=tt_menu)

    tt_create_menu = tk.Menu(menu)

    tt_create_menu.add_command(
        label="Create TimeTable", command=lambda: create_page(create_timetable_page)
    )

    tt_create_menu.add_command(
        label="Reshchedule", command=lambda: create_page(create_reschedule_page)
    )

    menu.add_cascade(label="Create TimeTable", menu=tt_create_menu)

    settings_menu = tk.Menu(menu)
    settings_menu.add_command(
        label="Change Theme", command=lambda: create_page(change_theme_frame)
    )

    settings_menu.add_command(
        label="Statistics", command=lambda: create_page(create_stats_frame)
    )
    menu.add_cascade(label="Settings", menu=settings_menu)


def schedule_with_progress(progress_bar) -> None:
    """Uses auto_schedule_helper with a progress bar for better UX"""
    for i in range(101):
        progress_bar["value"] = i
        window.update_idletasks()  # Ensure smooth progress bar updates
        time.sleep(0.02)
    auto_schedule_helper()


def create_timetable_page() -> tkb.Frame:
    """
    Create a 'Create a timetable page'
    """
    create_timetable_frame = tkb.Frame(window, padding=(20, 20))

    text1 = tk.Label(
        create_timetable_frame,
        text="Click here to Create TimeTable:",
        background=LIGHT_GRAY_COLOR,
        foreground=DARK_GRAY_COLOR,
        font=HEADING_FONT,
    )
    text1.grid(row=0, column=0, sticky="we")

    progress_bar = tkb.Progressbar(
        create_timetable_frame,
        orient="horizontal",
        mode="determinate",
        bootstyle="success-striped",
    )
    progress_bar.grid(row=1, column=0, sticky="we")

    schedule_btn = tkb.Button(
        master=create_timetable_frame,
        text="Click Here",
        command=lambda: schedule_with_progress(progress_bar),
    )

    schedule_btn.grid(row=2, column=0, sticky="we")

    frame_expansion(create_timetable_frame)

    return create_timetable_frame


# TODO:
def create_reschedule_page() -> tkb.Frame:
    padx = 10
    pady = 15
    reschedule_frame = tkb.Frame(window)
    text1 = tk.Label(reschedule_frame, text="Prof:")
    text1.grid(row=0, column=0, sticky="NSEW", padx=padx)
    prof_entry2 = tkb.Entry(reschedule_frame)
    prof_entry2.grid(row=0, column=1, sticky="NSEW", padx=padx, pady=pady)

    text2 = tk.Label(reschedule_frame, text="Day:")
    text2.grid(row=1, column=0, sticky="NSEW", padx=padx)
    day_entry = tkb.Entry(reschedule_frame)
    day_entry.grid(row=1, column=1, sticky="NSEW", padx=padx, pady=pady)

    reschedule_btn = tkb.Button(
        master=reschedule_frame,
        text="Reschedule",
        command=lambda: reschedule(
            prof_entry2.get() or "Rajnish", day_entry.get() or "Mon"
        ),
    )
    reschedule_btn.grid(
        row=2, column=0, columnspan=2, sticky="NSEW", padx=padx, pady=pady
    )

    # changing background all objects in frame
    for label in reschedule_frame.children:
        if "radio" in label or "label" in label:
            reschedule_frame.children[label].configure(background=LIGHT_GRAY_COLOR)

    frame_expansion(reschedule_frame)

    return reschedule_frame


def create_export_page() -> tkb.Frame:
    def export_csv():
        # TODO: Not working as expected
        year_val = year_var.get()

        if year_val == "All":
            for year in all_years:
                department = get_department_by_year(year)
                time_slots = get_time_slots(department)
                export_file_csv(year, time_slots)
        else:
            department = get_department_by_year(year_val)
            time_slots = get_time_slots(department)
            export_file_csv(year_val, time_slots)

        info_pop_up("Done!")

    def export_pdf():
        year_val = year_var.get()

        if year_val == "All":
            for year in all_years:
                export_file_pdf(year)
        else:
            export_file_pdf(year_val)

        info_pop_up("Done!")

    horizontal_padding = 20
    vertical_padding = 10

    export_page_frame = tkb.Frame(window, padding=(20, 20))

    text1 = tk.Label(export_page_frame, text="Select a year & stream:")
    text1.grid(row=0, column=0, sticky="NSEW")

    year_var = tk.StringVar()
    year_options: list[str] = ["All"] + all_years if all_years else ["None"]
    year_var.set(year_options[0])

    prof_OptionMenu = tkb.OptionMenu(export_page_frame, year_var, *year_options)

    prof_OptionMenu.configure(cursor="hand2")
    prof_OptionMenu.grid(
        row=1,
        column=0,
        sticky="NSEW",
        pady=vertical_padding,
    )

    export_csv_btn = tkb.Button(
        master=export_page_frame,
        text="Export to CSV",
        command=export_csv,
    )
    export_csv_btn.grid(
        row=2,
        column=0,
        sticky="NSEW",
        pady=vertical_padding / 2,
    )

    export_pdf_btn = tkb.Button(
        master=export_page_frame,
        text="Export to PDF",
        command=export_pdf,
    )
    export_pdf_btn.grid(
        row=3,
        column=0,
        sticky="NSEW",
        pady=vertical_padding / 2,
    )

    frame_expansion(export_page_frame)

    return export_page_frame


def create_page(page):
    """
    page: function or string
    Creates a new frame from the given page
    """
    temp = frames[page]

    current_frame = frames.values()
    for frm in current_frame:
        # frm.forget()
        frm.grid_forget()

    temp.tkraise()
    temp.grid(row=0, column=0, sticky="nsew")
    # temp.grid(row=0, column=0)


def get_professor_by_subject(subject: str, subject_type=None):
    """
    Given a subject and an optional subject type,
    return the professor who teaches the subject.
    """

    for professor, subjects in profs.items():
        for year, subject_list in subjects.items():
            for subject_info in subject_list:
                if subject_info["Subject"] == subject:
                    if subject_type is None or subject_info["Type"] == subject_type:
                        return professor

    print(
        f"No professor found for the given subject {subject} and subject type {subject_type}"
    )


# TODO: Check this function is working properly [updated functionality for options]
def check_professor_available(lec_num: int, day: str) -> list:
    """
    Checks the availability of professors for a specific lecture number and day from timetable.

    Args:
     lec_num (int): The lecture number to check
     day (str): The day of the week to check availability for

    Returns:
     list: A list of professor names that are available for the given lecture number and day
    """

    busy_professors = []

    # finding which lecture at specified lec number
    for year in ttlist.keys():
        scheduled_lectures: list = ttlist[year][day]

        # number of scheduled lecture can't be less than lec number
        if len(scheduled_lectures) - 1 >= lec_num:
            busy_professors.append(scheduled_lectures[lec_num]["professor"])

    all_busy_professors = split_strip_strings(busy_professors)

    return [teacher for teacher in profs.keys() if teacher not in all_busy_professors]


def get_lec_number(professor, day) -> dict[str, list]:
    """
    Returns the lecture number [index] of the given professor on the given day.
    """
    year_subject: dict = profs.get(professor)
    # print(f"Prof. {professor} teaches = {subject}")
    lec_num = {}
    years_of_prof: list = list(year_subject.keys())

    for year in years_of_prof:
        scheduled_lecs = get_professors_from_schedule(year, day)
        indexes2 = [
            idx
            for idx in range(len(scheduled_lecs))
            # if scheduled_lecs[idx] == professor
            if professor in scheduled_lecs[idx]
        ]
        lec_num[year] = indexes2

    return lec_num


def reschedule(professor: str, day: str) -> None:
    """
    Reschedule lecture of professor on specified day
    """
    print("function reschedule ran...")

    lec_nums: dict[str, list] = get_lec_number(professor, day)

    for year in lec_nums:
        print(f"year = {year} - {lec_nums[year]}")
        for lec in lec_nums[year]:
            available = check_professor_available(lec, day)[0]
            print(f"available = {available}")
            sub = get_subject(profs, available, year, "Theory")
            ttlist[year][day][lec] = {
                "subject": sub,
                "subtype": "Theory",
                "professor": available,
            }

    create_all_tt_pages()


def store_json(file: str, read_var) -> None:
    """
    Stores data as JSON in a file.

    Args:
        file (str): The path to the JSON file.
        read_var (Any): The data to be stored as JSON.
    """

    with open(file, "w") as f:
        json.dump(read_var, f, indent=4)


def read_json(file_path: str):
    """
    Reads a JSON file and returns the loaded data.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict: The loaded JSON data.

    """

    with open(file_path, "r") as f:
        data = json.load(f)

    return data


def set_default_tt() -> None:
    """
    Sets the default timetable by creating an empty timetable structure
    for each year and day, storing it as JSON, creating all timetable pages,
    and displaying an information pop-up message.
    """

    global ttlist
    ttlist = {year: {day: [] for day in timetable_struct} for year in all_years}
    store_json(TT_FILE, ttlist)
    create_all_tt_pages()
    info_pop_up("Deleted all timetables!")


def create_all_tt_pages():
    """
    Creates timetable frames for each year
    and stores them in 'frames' dictionary.
    """
    for year in all_years:
        year_page: tkb.Frame = view_timetable_frame(year)
        frames[year] = year_page


def create_all_pages():
    """
    Creates all the necessary pages for the application,
    such as entry page, reschedule page, etc.
    The created pages are stored in 'frames' dictionary.
    """

    entry_page = create_entry_frame()
    reschedule_page = create_reschedule_page()
    timetable_page = create_timetable_page()
    prof_page = create_professors_frame()
    option_page = create_options_frame()
    export_csv_page = create_export_page()
    prof_tt_page = view_prof_tt_frame()
    add_department_page = create_add_department_frame()
    delete_subject_page = delete_subject_frame()
    optional_subject_entry_page = optional_subject_entry_frame()
    change_theme_page = change_theme_frame()
    get_csv_page = get_csv_frame()
    stats_page = create_stats_frame()

    frames[create_entry_frame] = entry_page
    frames[create_reschedule_page] = reschedule_page
    frames[create_timetable_page] = timetable_page
    frames[create_options_frame] = option_page
    frames[create_export_page] = export_csv_page
    frames[view_prof_tt_frame] = prof_tt_page
    frames[create_add_department_frame] = add_department_page
    frames[delete_subject_frame] = delete_subject_page
    frames[optional_subject_entry_frame] = optional_subject_entry_page
    frames[change_theme_frame] = change_theme_page
    frames[get_csv_frame] = get_csv_page
    frames[create_professors_frame] = prof_page
    frames[create_stats_frame] = stats_page


def get_subjects_by_year(year_to_find: str) -> list[tuple]:
    """
    Returns a list of subjects for a given year.

    Args:
        year_to_find (str): The year to find subjects for.

    Returns:
        A list of dictionaries representing the subjects found.

    Example:
        year = "FY IT"
        subjects = get_subjects_by_year(year)
        print(subjects)
    """

    all_subs: list = []

    for year in profs.values():
        if year_to_find in year.keys():
            subject_list: list[dict] = year[year_to_find]
            for subject in subject_list:
                all_subs.append((subject["Subject"], subject["Type"]))

    return all_subs


def get_subject(subs, professor, year, subtype):
    """
    Args:
    subs: profs
      professor: The name of the professor.
      year: The year of the course.
      subtype: The type of the subject.

    Returns:
      A subject that the professor teaches to given year.
    """

    subjects = subs[professor].get(year)

    if subjects:
        for subject in subjects:
            if subject["Type"] == subtype:
                subjects.append(subjects.pop(0))
                return subject["Subject"]

    return None


def get_all_subjects(professor, year):
    """
    Args:
    subs: profs
      professor: The name of the professor.
      year: The year of the course.
      subtype: The type of the subject.

    Returns:
      Subjects that the professor teaches.
    """
    subjects: list[dict] = profs[professor].get(year)

    return subjects


def get_professors_by_year(profs_dict: dict, year: str) -> list:
    """
    Given a dictionary of professors and year,
    return a list of professors that teach to the given year
    """

    professors = []
    for prof in profs_dict.keys():
        if year in profs_dict[prof].keys():
            professors.append(prof)

    return professors


def get_professors_from_schedule(year: str, day: str) -> list:
    """
    Returns a list of professors who teach on the specified day.
    Note: This function will return optional prof with '/'
    """
    today_lec: list = ttlist[year][day]
    professors = [subject["professor"] for subject in today_lec]

    return professors


def split_strip_strings(input_string_list: list[str]) -> list[str]:
    words = []

    for string in input_string_list:
        split_words: list[str] = string.split("/")
        split_words = [part.strip() for part in split_words]
        words.extend(split_words)

    return words


def auto_schedule(professors: dict[str, dict[str, list]]) -> None:
    """
    Generate a timetable schedule based on the availability of professors
    """

    if not professors:
        return aleart_pop_up("No professor available to schedule a timetable!")

    global ttlist
    ttlist = {year: {day: [] for day in timetable_struct} for year in all_years}

    for year in all_years:
        generate_year_wise_schedule(year, professors)

    create_all_tt_pages()


def generate_year_wise_schedule(
    year: str, professors: dict[str, dict[str, list]]
) -> None:
    department: str = get_department_by_year(year)
    start_time, end_time, minutes_lecture = get_department_time(department)
    no_of_lectures = calc_college_time(start_time, end_time, minutes_lecture)
    practical_slots = get_practical_slots_by_department(department)
    professors_queue = get_professors_by_year(professors, year)

    for lec_num in range(no_of_lectures):
        generate_daily_schedule(year, lec_num, professors_queue, practical_slots)


def generate_daily_schedule(
    year: str, lec_num: int, professors_queue: list, practical_slots: list
):
    queue_len = len(professors_queue)
    days = list(ttlist[year].keys())
    number_of_days = len(days)
    day_num = 0
    count = 0
    attepts = 0
    pract_attepts = 0

    def queue_next():
        professors_queue.append(professors_queue.pop(0))

    while day_num < number_of_days and count < 100:
        count += 1
        available_prof = check_professor_available(lec_num, days[day_num])
        today_lecs = get_professors_from_schedule(year, days[day_num])
        today_lecs = split_strip_strings(today_lecs)

        scheduled: bool = (
            professors_queue[0] not in today_lecs
            or lec_num > queue_len
            or attepts >= queue_len
        )
        available = professors_queue[0] in available_prof

        # logic to schedule the lectures if practicals not available in practical slot
        if lec_num in practical_slots:
            subtype = "Theory" if pract_attepts >= queue_len else "Practical"
        else:
            subtype = "Theory"

        # subtype = "Practical" if lec_num in practical_slots else "Theory"

        if available and scheduled:
            subject = get_subject(profs, professors_queue[0], year, subtype=subtype)
            if subject:
                if get_subject_workload(professors_queue[0], year, subject, subtype):
                    optional_subjects = get_optional_subjects(
                        professors_queue[0], year, subject, subtype
                    )

                    # TODO: Split this into multiple functions
                    if optional_subjects:
                        temp_sub = subject
                        temp_professor = professors_queue[0]

                        # print(optional_subjects)

                        for opt_professor, opt_subject in optional_subjects.items():
                            temp_sub += f" / {opt_subject}"
                            temp_professor += f" / {opt_professor}"

                        ttlist[year][days[day_num]].append(
                            {
                                "subject": temp_sub,
                                "subtype": subtype,
                                "professor": temp_professor,
                            }
                        )
                        # Note: Currently this does not reduce workload of all profs
                        decrease_workload(professors_queue[0], year, subject, subtype)
                        for opt_professor, opt_subject in optional_subjects.items():
                            decrease_workload(opt_professor, year, opt_subject, subtype)

                    else:
                        ttlist[year][days[day_num]].append(
                            {
                                "subject": subject,
                                "subtype": subtype,
                                "professor": professors_queue[0],
                            }
                        )
                        decrease_workload(professors_queue[0], year, subject, subtype)
                    day_num += 1
                    pract_attepts = 0

        if count >= 100:
            while day_num < number_of_days:
                # print(f"Attempt exceeded! {year} {available} {day_num =} {lec_num = }")
                ttlist[year][days[day_num]].append(
                    {
                        "subject": "Empty Slot",
                        "subtype": "Empty Slot",
                        "professor": "Empty Slot",
                    }
                )
                day_num += 1
                pract_attepts = 0

        queue_next()
        attepts += 1
        pract_attepts += 1


def get_subject_workload(
    professor: str, year: str, subject: str, subject_type: str
) -> bool:
    """
    Checks if a workload is available for a given professor,
    year, subject, and subject type.
    """
    for sub in profs[professor][year]:
        if (
            subject == sub["Subject"]
            and sub["Type"] == subject_type
            and "Workload" in sub
        ):
            if sub["Workload"] > 0:
                return True
            else:
                return False
    return True


def decrease_workload(
    professor: str, year: str, subject: str, subject_type: str
) -> None:
    """
    Decreases the workload of a professor for a given subject and year.
    If the workload value exists and is greater than 0, it decreases the workload.

    Args:
    professor (str): The name of the professor.
    year (str): The academic year.
    subject (str): The subject name.
    subject_type (str): The subject type, e.g. "Core".

    Returns:
    None
    """

    for sub in profs[professor][year]:
        if (
            subject == sub["Subject"]
            and sub["Type"] == subject_type
            and "Workload" in sub
        ):
            if sub["Workload"] > 0:
                sub["Workload"] -= 1


def get_optional_subjects(
    professor: str, year: str, subject: str, subject_type: str
) -> dict | None:
    for sub in profs[professor][year]:
        if (
            subject == sub["Subject"]
            and sub["Type"] == subject_type
            and "Options" in sub
        ):
            return sub["Options"]

    return None


def get_department_by_year(year: str) -> str:
    """
    Returns the department associated with a given year.

    Returns:
        str: The department associated with the given year.
    """

    for department in all_departments:
        if department in year:
            return department
    return ""


def get_all_years() -> list:
    """
    return all years available in prof JSON
    """
    all_years = set()

    for year in profs.values():
        all_years.update(year.keys())

    return sorted(all_years)


def update_all_years():
    """
    Updates the global variable `all_years` with the latest list of years.

    Returns:
        None
    """
    global all_years
    all_years = get_all_years()


def update_all_departments():
    """
    Updates the global variable `all_years` with the latest list of years.

    Returns:
        None
    """
    global all_departments
    all_departments = get_all_departments()


def aleart_pop_up(message):
    message_box = messagebox.showwarning(title="Warning", message=message)


def info_pop_up(message):
    message_box = messagebox.showinfo(title="Info", message=message)


def ask_pop_up(message):
    message_box = messagebox.askokcancel(title="Message", message=message)
    return message_box


def set_window_options(window):
    """
    Sets the window options for the given window.

    Args:
        window: The window to set the options for.

    Returns:
        None
    """

    window.option_add("*Font", SUBHEADING_FONT)
    window.option_add("*Label*Background", LIGHT_GRAY_COLOR)
    window.option_add("*Button*Background", TEAL_COLOR)
    window.option_add("*Button*Foreground", WHITE_COLOR)
    window.option_add("*Button*cursor", "hand2")
    window.option_add("*tearOff", False)

    # window.option_add("*Button*cursor", "hand2")


def get_time_slots(department: str) -> list[str]:
    """
    Retrieves the time slots for a given department.

    Args:
        department (str): The department to retrieve the time slots for.

    Returns:
        list[str]: A list of time slots in the format "%H:%M %p".

    """

    start_time, end_time, minutes_lecture = get_department_time(department)
    no_of_lectures = calc_college_time(start_time, end_time, minutes_lecture)
    temp_time: dt.datetime = start_time
    time_slots = []

    for _ in range(no_of_lectures):
        time_slots.append(f"{temp_time:%H:%M %p}")
        temp_time = temp_time + dt.timedelta(minutes=minutes_lecture)

    return time_slots


def get_departments_by_prof(professor: str) -> set[str]:
    """
    Retrieves the departments associated with a given professor.

    Args:
        professor (str): The name of the professor.

    Returns:
        set[str]: A set of department names.
    """

    years = profs[professor].keys()
    departments: set[str] = {get_department_by_year(year) for year in years}

    return departments


def get_time_slots_by_prof(professor: str) -> list[str]:
    """
    Retrieves max time slots for a given professor.
    """
    departments = get_departments_by_prof(professor)
    time_slots = [get_time_slots(department) for department in departments]

    return max(time_slots, key=len)


def get_practical_slots_by_department(department: str):
    """
    Retrieves the practical slots for a given department from settings.
    """

    return settings[department]["practical_slots"]


def get_department_time(department: str) -> tuple[dt.datetime, dt.datetime, int]:
    """
    Retrieves the start time, end time, and duration of a lecture
    for a given department from settings.
    """
    minutes_lecture: int = settings[department]["minutes_lecture"]
    start_time = dt.datetime.strptime(settings[department]["start_time"], "%H:%M")
    end_time = dt.datetime.strptime(settings[department]["end_time"], "%H:%M")

    start_time = dt.datetime.combine(today.date(), start_time.time())
    end_time = dt.datetime.combine(today.date(), end_time.time())

    return start_time, end_time, minutes_lecture


def export_file_csv(year: str, time_slots: list):
    """
    Exports a timetable to a CSV file for a given year and time slots.
    """
    jfile = ttlist[year]
    days = list(jfile.keys())
    header_row = ["Time"] + days

    data_rows = []
    day_subjects = jfile.values()

    for time, *values in zip(time_slots, *day_subjects):
        # * before values means receive the remaining elements as a list.
        values2 = [f"{elem['subject']} ({elem['professor']})" for elem in values]
        row = [time] + values2
        data_rows.append(row)

    with open(f"{year} timetable.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(header_row)  # Writing column headers
        writer.writerows(data_rows)  # Writing data rows


def export_file_pdf(year: str) -> None:
    """
    Exports a timetable to a PDF file for a given year.

    Args:
        year (str): The year for which the timetable is to be exported.

    Returns:
        None

    Example:
        ```
        export_file_pdf('FY IT')
        ```
    """

    styles = getSampleStyleSheet()

    # custom style for paragraphs class
    p_style = ParagraphStyle(
        name="p_style",
        alignment=1,  # Center alignment
    )

    # data to process
    year_data = ttlist[year]
    days = [list(year_data.keys())]  # days for header of PDF
    subjects = [
        list(values) for values in zip(*year_data.values())
    ]  # scheduled lectures
    data_list = days + subjects
    pdf_filename = f"{year} timtable.pdf"  # pdf name

    for elem in range(len(subjects)):
        for string in range(len(subjects[elem])):
            var = subjects[elem][string]
            var = var.replace(
                "\n", "<br/>"
            )  # reportlab paragraph processes html not string
            subjects[elem][string] = Paragraph(var, style=p_style)

    doc = SimpleDocTemplate(
        pdf_filename, pagesize=landscape(A4), title=f"{year} Timtable"
    )
    table = Table(data_list)

    horizontal_padding = 5
    vertical_padding = 5

    style = TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.black),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),  # Set vertical alignment to 'MIDDLE'
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
            ("LEFTPADDING", (0, 0), (-1, -1), horizontal_padding),
            ("RIGHTPADDING", (0, 0), (-1, -1), horizontal_padding),
            ("TOPPADDING", (0, 0), (-1, -1), vertical_padding),
            ("BOTTOMPADDING", (0, 0), (-1, -1), vertical_padding),
            ("WORDWRAP", (0, 0), (-1, -1), 1),
        ]
    )

    table.setStyle(style)

    # Add table to the document
    header = Paragraph(f"{year} TimeTable", styles["Title"])

    content = [header, Spacer(1, 10), table]
    doc.build(content)


def delete_all_profs():
    global profs
    profs = {}
    create_all_pages()
    info_pop_up("Deleted all professors!")


def create_add_department_frame() -> tkb.Frame:
    def take_info():
        global settings
        department_name = department_entry.get().upper()
        temp = {
            "start_time": "00:00",
            "end_time": "01:00",
            "minutes_lecture": 60,
            "practical_slots": [],
        }
        settings.update({department_name: temp})
        store_json(SETTINGS_FILE, settings)
        text2.config(text=f"Available Departments: {', '.join(get_all_departments())}")
        info_pop_up(f"Added new department: {department_name}")
        update_all_departments()
        create_all_pages()

    vertical_padding = 10
    horizontal_padding = 15

    add_department_frame = tkb.Frame(window, padding=(20, 10))

    text1 = tk.Label(add_department_frame, text="Enter Department:")
    text1.grid(row=0, column=0, pady=vertical_padding)
    department_entry = tkb.Entry(add_department_frame)
    department_entry.grid(row=1, column=0, pady=vertical_padding, sticky="NSEW")

    submit_button = tkb.Button(
        add_department_frame,
        text="Submit",
        command=take_info,
    )
    submit_button.grid(row=2, column=0, pady=vertical_padding, sticky="NSEW")

    text2 = tk.Label(
        add_department_frame,
        text=f"Available Departments: {', '.join(all_departments)}",
    )
    text2.grid(row=3, column=0, pady=vertical_padding)

    frame_expansion(add_department_frame)

    return add_department_frame


def get_all_departments() -> list:
    """
    Returns a sorted list of all departments.
    """
    return sorted(list(settings.keys()))


def delete_subject_frame():
    vertical_padding = 10
    horizontal_padding = 15

    delete_subject_frame = tkb.Frame(window, padding=(25, 15))

    def update_options(*args):
        selected_prof = prof_var.get()
        selected_year = year_var.get()

        all_subs = get_all_subjects(selected_prof, selected_year)

        # Clear the current options in the second OptionMenu
        sub_OptionMenu["menu"].delete(0, "end")

        if not all_subs:
            sub_OptionMenu["menu"].add_command(
                label="None",
            )
            sub_var.set("None")
            return

        # Add new options based on the selected option in the first OptionMenu
        for subject in all_subs:
            sub_OptionMenu["menu"].add_command(
                label=f"{subject['Subject']} - {subject['Type']}",
                command=lambda sub=subject: sub_var.set(
                    f"{sub['Subject']} - {sub['Type']}"
                ),
            )

        sub_var.set(f"{subject['Subject']} - {subject['Type']}")
        # print(
        #     "[delete_subject_frame]",
        #     profs.get(selected_prof, {}).get(selected_year, []),
        # )

    def delete_subject():
        selected_prof = prof_var.get()
        selected_year = year_var.get()
        selected_sub = sub_var.get()
        selected_subject, selected_subject_type = selected_sub.split(" - ")

        for elem in profs.get(selected_prof, {}).get(selected_year, []):
            subject = elem.get("Subject")
            subject_type = elem.get("Type")
            if subject == selected_subject and subject_type == selected_subject_type:
                profs[selected_prof][selected_year].remove(elem)
                update_options()
                create_all_pages()
                store_json(PROFS_FILE, profs)

    prof_var: tk.StringVar = tk.StringVar()
    all_profs: list = list(profs.keys())

    if not all_profs:
        label = tk.Label(
            delete_subject_frame,
            text="No professors found!",
            pady=vertical_padding,
            padx=horizontal_padding,
        )
        label.grid(row=0, column=0, sticky="NSEW")
        frame_expansion(delete_subject_frame)
        return delete_subject_frame

    prof_var.set(all_profs[0])

    prof_OptionMenu = tkb.OptionMenu(
        delete_subject_frame,
        prof_var,
        *all_profs,
        command=update_options,
        bootstyle="outline",
    )
    prof_OptionMenu.configure(cursor="hand2")
    prof_OptionMenu.grid(row=0, column=0, pady=vertical_padding, sticky="NSEW")

    year_var: tk.StringVar = tk.StringVar()
    all_years_temp: list = get_all_years()
    year_var.set(all_years_temp[0])

    year_OptionMenu = tkb.OptionMenu(
        delete_subject_frame,
        year_var,
        *all_years_temp,
        command=update_options,
        bootstyle="outline",
    )
    year_OptionMenu.configure(cursor="hand2")
    year_OptionMenu.grid(row=1, column=0, pady=vertical_padding, sticky="NSEW")

    sub_var: tk.StringVar = tk.StringVar()
    sub_var.set("None")

    sub_OptionMenu = tkb.OptionMenu(
        delete_subject_frame, sub_var, "None", bootstyle="outline"
    )
    sub_OptionMenu.configure(cursor="hand2")
    sub_OptionMenu.grid(row=2, column=0, pady=vertical_padding, sticky="NSEW")
    update_options()

    submit_button = tkb.Button(
        delete_subject_frame,
        text="Submit",
        command=delete_subject,
    )
    submit_button.grid(row=3, column=0, pady=vertical_padding, sticky="NSEW")

    frame_expansion(delete_subject_frame)
    return delete_subject_frame


def auto_schedule_helper() -> None:
    """
    Auto-schedules professors based on their preferences.
    Reads in the professors data from the PROFS_FILE json.
    Runs the auto_schedule7
    function on the professors data to generate a schedule.
    """

    global profs, settings, all_years, all_departments
    profs = read_json(PROFS_FILE)
    settings = read_json(SETTINGS_FILE)
    all_years = get_all_years()
    all_departments = get_all_departments()
    auto_schedule(profs)


def change_theme_frame() -> tkb.Frame:
    theme_frame = tkb.Frame(window, padding=(15, 15))

    def change_theme(event):
        t = combo.get()
        style.theme_use(t)

    style = window.style
    combo = tkb.Combobox(theme_frame, values=tkb.Style().theme_names())
    combo.pack(pady=20)

    combo.bind("<<ComboboxSelected>>", change_theme)

    frame_expansion(theme_frame)
    return theme_frame


def create_stats_frame() -> tkb.Frame:
    stats_frame = tkb.Frame(window)

    num_of_profs = 0
    temp_var: dict = ttlist
    vertical_pad = 10
    horizontal_pad = 10
    borderwidth = 1
    RELIEF_TYPE = "ridge"

    for text_idx, text in enumerate(["Departments", "No. of Professors"]):
        header_label = tk.Label(
            master=stats_frame,
            text=text,
            relief=RELIEF_TYPE,
            pady=vertical_pad,
            padx=horizontal_pad,
            borderwidth=borderwidth,
            font=SUBHEADING_FONT_BOLD,
        )
        header_label.grid(row=0, column=text_idx, sticky="NSEW")

    # creating table headers
    for dept_idx, dept in enumerate(all_departments):
        dept_label = tk.Label(
            master=stats_frame,
            text=f"{dept}",
            relief=RELIEF_TYPE,
            pady=vertical_pad,
            padx=horizontal_pad,
            bg=LIGHT_GRAY_COLOR,
            fg=DARK_GRAY_COLOR,
            borderwidth=borderwidth,
        )
        dept_label.grid(row=dept_idx + 1, column=0, sticky="NSEW")

        prof_count = len(get_professors_by_department(dept))
        prof_count_label = tk.Label(
            master=stats_frame,
            text=f"{prof_count}",
            relief=RELIEF_TYPE,
            pady=vertical_pad,
            padx=horizontal_pad,
            bg=LIGHT_GRAY_COLOR,
            fg=DARK_GRAY_COLOR,
            borderwidth=borderwidth,
        )
        prof_count_label.grid(row=dept_idx + 1, column=1, sticky="NSEW")

    empty_lecs, total_lecs, tt_score = tt_score_calc()
    score_label = tk.Label(
        master=stats_frame,
        text=f"Total Lecture Slots: {total_lecs}\nEmpty Lecture Slots: {empty_lecs}\nTimetable Score {tt_score:.2f}%",
        relief=RELIEF_TYPE,
        pady=vertical_pad * 2,
        padx=horizontal_pad,
        bg=LIGHT_GRAY_COLOR,
        fg=DARK_GRAY_COLOR,
        borderwidth=borderwidth,
    )
    score_label.grid(row=dept_idx + 1, column=0, columnspan=2, sticky="NSEW")
    frame_expansion(stats_frame)
    return stats_frame


def tt_score_calc():
    """Calculates the timetable score (filled lectures/total lectures)"""
    empty_lecs = 0
    total_lecs = 0
    for year in ttlist:
        for day in ttlist[year]:
            for lecture in ttlist[year][day]:
                if "Empty Slot" in lecture["subject"]:
                    empty_lecs += 1
                total_lecs += 1
    filled_slots = total_lecs - empty_lecs
    tt_score = (filled_slots / total_lecs) * 100
    return empty_lecs, total_lecs, tt_score


def create_department_settings(department_name):
    """Create a new department settings in settings file."""
    if department_name not in settings:
        temp = {
            "start_time": "00:00",
            "end_time": "01:00",
            "minutes_lecture": 60,
            "practical_slots": [],
        }
        settings.update({department_name: temp})


def get_csv_frame() -> tk.Frame | tkb.Frame:
    def add_prof_new_dict(prof, year_dept) -> None:
        """
        Adds professor to new dict.
        If year-department not available then it will be added
        """
        if prof not in new_dict:
            new_dict[prof] = {}

        if year_dept not in new_dict[prof]:
            new_dict[prof][year_dept] = []

    def add_optional_prof_new_dict(
        optional_profs: list, optional_subs: list, year_dept: str
    ) -> None:
        for prof_idx, optional_prof in enumerate(optional_profs):
            subs_dicts: list = new_dict[optional_prof][year_dept]

            for sub_dict in subs_dicts:
                if sub_dict["Subject"] == optional_subs[prof_idx]:
                    opt_dict = {
                        other_prof: other_sub
                        for (other_prof, other_sub) in zip(
                            optional_profs, optional_subs
                        )
                        if other_prof != optional_prof
                    }
                    sub_dict["Options"] = opt_dict

    def import_csv_data() -> None:
        """
        Imports CSV data from a file.
        """
        try:
            csv_file_path = askopenfilename(filetypes=[("CSV Files", "*.csv")])

            with open(csv_file_path, newline="") as csvfile:
                reader = csv.DictReader(csvfile)

                # filling the new dict with the data
                for row in reader:
                    prof: str = row["Professor"].strip()
                    year_dept = f"{row['College Year']} {row['Department']}"
                    workload: str = row["Workload"]
                    subject_info = {"Type": row["Subject Type"]}

                    if workload:
                        workload = int(workload)
                        subject_info["Workload"] = workload

                    if "/" in prof:
                        optional_profs = prof.split("/")
                        optional_subs = row["Subject"].split("/")

                        for prof_idx, optional_prof in enumerate(optional_profs):
                            add_prof_new_dict(optional_prof, year_dept)
                            subject_info_copy = (
                                subject_info.copy()
                            )  # copy to modify dict
                            subject_info_copy["Subject"] = optional_subs[prof_idx]

                            new_dict[optional_prof][year_dept].append(subject_info_copy)

                        add_optional_prof_new_dict(
                            optional_profs, optional_subs, year_dept
                        )
                    else:
                        add_prof_new_dict(prof, year_dept)
                        subject_info["Subject"] = row["Subject"]
                        new_dict[prof][year_dept].append(subject_info)

                    if row["Department"] not in departments:
                        departments.append(row["Department"])
                        create_department_settings(row["Department"])

            global profs
            profs = new_dict
            store_json(PROFS_FILE, profs)
            store_json(SETTINGS_FILE, settings)
            schedule_with_progress(progress_bar)
            update_all_years()
            create_all_pages()
            create_menu()
            info_pop_up("CSV imported!")

        except Exception as e:
            traceback.print_exc()
            info_pop_up("Error: Use a correct file format!")

    vertical_padding = 10
    new_dict = {}  # dictionary to store new data
    departments = get_all_departments()

    main_frame = tkb.Frame(window, padding=(20, 20))  # main frame to center csv frame
    csv_frame = tkb.Frame(main_frame)

    text = tkb.Label(
        csv_frame,
        text="Please select a CSV file to import\nNote: Existing data will be erased.",
        anchor="center",
    )

    text.grid(row=0, column=0, pady=vertical_padding, sticky="EW")

    progress_bar = tkb.Progressbar(
        csv_frame,
        orient="horizontal",
        mode="determinate",
        bootstyle="success-striped",
    )
    progress_bar.grid(row=1, column=0, pady=vertical_padding, sticky="EW")

    submit_button = tkb.Button(
        csv_frame,
        text="Submit",
        command=import_csv_data,
    )

    submit_button.grid(row=2, column=0, ipady=vertical_padding * 0.5, sticky="EW")
    csv_frame.pack(anchor="center", expand=True)
    frame_expansion(main_frame)

    return main_frame


def get_years_by_department(department):
    """Returns a list of years for a department"""
    departments_years = {year for year in all_years if department in year}
    return sorted(departments_years)


def get_professors_by_department(department: str) -> list:
    """Returns a list of professors that teaches to given department"""
    departments_years = get_years_by_department(department)
    department_profs = []
    for year in departments_years:
        department_profs.extend(get_professors_by_year(profs, year))

    return sorted(set(department_profs))


if __name__ == "__main__":
    TT_FILE: str = "timetable.json"
    PROFS_FILE: str = "professors.json"
    SETTINGS_FILE: str = "settings.json"

    LIGHT_GRAY_COLOR = "#F5F5F5"  # Background Color
    DARK_GRAY_COLOR = "#333333"  # Heading Text Color
    TEAL_COLOR = "#008080"  # Button Color
    WHITE_COLOR = "#FFFFFF"  # Button Text Color

    ttlist = read_json(TT_FILE)
    profs = read_json(PROFS_FILE)
    settings: dict[str, dict] = read_json(SETTINGS_FILE)

    all_years: list = get_all_years()
    all_departments: list = get_all_departments()

    window = tkb.Window()

    window.title("ClassSync")
    # window.wm_attributes("-topmost", True)  # stays on top of other windows
    # window.resizable(False, False)  # Prevent resizing in both dimensions

    window.minsize(450, 350)
    window.columnconfigure(0, weight=1)
    window.rowconfigure(0, weight=1)

    HEADING_FONT = tkFont.Font(family="Segoe UI", size=14, weight="bold")
    SUBHEADING_FONT = tkFont.Font(family="Segoe UI", size=12)
    SUBHEADING_FONT_BOLD = tkFont.Font(family="Segoe UI", size=12, weight="bold")

    set_window_options(window)

    if profs and settings:
        auto_schedule(profs)
        store_json(TT_FILE, ttlist)

    create_menu()
    create_all_pages()
    create_all_tt_pages()
    create_page(get_csv_frame)
    window.mainloop()
