import csv
import datetime as dt
import json
import tkinter as tk
import tkinter.font as tkFont
from tkinter import messagebox

from PIL import ImageTk, Image
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


def frame_expansion(frame: tk.Frame) -> None:
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


def create_entry_frame() -> tk.Frame:
    def take_info() -> None:
        """
        Stores info user given in input to the file.
        updates info in 'profs' directory.
        """
        name: str = (
            prof_entry.get().capitalize()
            if prof_var.get() == "None"
            else prof_var.get()
        )

        year: str = None

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
                sub_dict["Workload"] = workload

        print(f"[create_entry_frame] Name = {name}")
        print(f"Subject = {sub}")

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
        

        # checking if subject already exists
        if sub_type == "Both":
            updated: bool = False
            for sub_type in ["Theory", "Practical"]:
                new_sub_dict = {"Subject": sub, "Type": sub_type}
                if new_sub_dict not in all_subjects:
                    profs[name][year].append(new_sub_dict)
                    updated = True

            if not updated:
                teaching_prof = get_professor_by_subject(sub, "Theory")
                aleart_pop_up(
                    f"Prof. {teaching_prof} is already teaching this subject!"
                )
                return
        else:
            if sub_dict not in all_subjects:
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

    entry_frame = tk.Frame(
        window,
        relief="solid",
        bd=1,
        padx=horizontal_padding,
        pady=vertical_padding,
        bg=LIGHT_GRAY_COLOR,
    )

    text1 = tk.Label(entry_frame, text="Prof:")
    text1.grid(row=0, column=0, pady=vertical_padding)
    prof_entry = tk.Entry(entry_frame)
    prof_entry.grid(row=0, column=1, columnspan=2, pady=vertical_padding)

    text5 = tk.Label(entry_frame, text="Or select Prof:")
    text5.grid(row=1, column=0, pady=vertical_padding)

    # variable for managing prof entries
    prof_var: tk.StringVar = tk.StringVar()
    prof_var.set("None")
    all_profs: list = ["None"] + list(profs.keys())

    prof_OptionMenu = tk.OptionMenu(entry_frame, prof_var, *all_profs)
    prof_OptionMenu.configure(relief="solid", bd=1, cursor="hand2")
    prof_OptionMenu.grid(
        row=1, column=1, columnspan=2, pady=vertical_padding, sticky="NSEW"
    )

    text2 = tk.Label(entry_frame, text="Year:")
    text2.grid(row=2, column=0, pady=vertical_padding)
    year_entry = tk.Entry(entry_frame)
    year_entry.grid(row=2, column=1, columnspan=2, pady=vertical_padding)

    text8 = tk.Label(entry_frame, text="Department:")
    text8.grid(row=3, column=0, pady=vertical_padding)

    ################################
    dept_var: tk.StringVar = tk.StringVar()
    dept_var.set("None")
    all_departments: list = ["None"] + get_all_departments()

    departments_OptionMenu = tk.OptionMenu(entry_frame, dept_var, *all_departments)
    departments_OptionMenu.configure(relief="solid", bd=1, cursor="hand2")
    departments_OptionMenu.grid(
        row=3, column=1, columnspan=2, pady=vertical_padding, sticky="NSEW"
    )
    ################################

    text5 = tk.Label(entry_frame, text="Or select Year\n& Department:")
    text5.grid(row=4, column=0, pady=vertical_padding)

    year_var: tk.StringVar = tk.StringVar()
    year_var.set("None")
    all_years_temp: list = ["None"] + get_all_years()

    year_OptionMenu = tk.OptionMenu(entry_frame, year_var, *all_years_temp)
    year_OptionMenu.configure(relief="solid", bd=1, cursor="hand2")
    year_OptionMenu.grid(
        row=4, column=1, columnspan=2, pady=vertical_padding, sticky="NSEW"
    )

    text3 = tk.Label(entry_frame, text="Subject:")
    text3.grid(row=5, column=0, pady=vertical_padding)
    subject_entry = tk.Entry(entry_frame)
    subject_entry.grid(row=5, column=1, columnspan=2, pady=vertical_padding)

    subtype_var: tk.StringVar = tk.StringVar(entry_frame)
    subtype_var.set("Both")

    text4 = tk.Label(entry_frame, text="Subject type:")
    text4.grid(row=6, column=0, columnspan=3, pady=vertical_padding)

    radio1 = tk.Radiobutton(
        entry_frame, text="Theory", value="Theory", variable=subtype_var
    )
    radio1.grid(row=7, column=0, pady=vertical_padding)

    radio2 = tk.Radiobutton(
        entry_frame, text="Practical", value="Practical", variable=subtype_var
    )
    radio2.grid(row=7, column=1, pady=vertical_padding)

    radio3 = tk.Radiobutton(
        entry_frame, text="Both", value="Both", variable=subtype_var
    )
    radio3.grid(row=7, column=2, pady=vertical_padding)

    text6 = tk.Label(entry_frame, text="Subject Workload\n(per week):")
    text6.grid(row=8, column=0, pady=vertical_padding, padx=horizontal_padding)
    workload_entry = tk.Entry(entry_frame)
    workload_entry.grid(row=8, column=1, columnspan=2, pady=vertical_padding)

    submit_button = tk.Button(
        entry_frame,
        text="Submit",
        command=take_info,
        padx=horizontal_padding,
    )
    submit_button.grid(
        row=9, column=0, columnspan=3, pady=vertical_padding, sticky="NSEW"
    )

    # changing background all objects in frame
    for label in entry_frame.children:
        if any(["radio" in label, "label" in label, "optionmenu" in label]):
            entry_frame.children[label].configure(background=LIGHT_GRAY_COLOR)

    frame_expansion(entry_frame)

    return entry_frame


def view_timetable_frame(year_key) -> tk.Frame:
    """
    Creates a timetable frame to show given year's timetable
    """
    temp_var: dict = ttlist
    table_frame = tk.Frame(window, bg=LIGHT_GRAY_COLOR)
    vertical_pad = 10
    horizontal_pad = 10
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
    time_label = tk.Label(
        master=table_frame,
        text="Time",
        relief=RELIEF_TYPE,
        pady=vertical_pad,
        padx=horizontal_pad,
        bg=TEAL_COLOR,
        fg=WHITE_COLOR,
        borderwidth=borderwidth,
    )


    department: str = get_department_by_year(year_key)
    start_time, end_time, minutes_lecture = get_department_time(department)
    no_of_lectures = calc_college_time(start_time, end_time, minutes_lecture)

    # creating time labels
    temp_time = start_time
    time_label.grid(row=1, column=0, sticky="NSEW")
    for row in range(1, int(no_of_lectures) + 1):
        # print(f"{temp_time:%H:%M %p}")
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
        label = tk.Label(
            master=table_frame,
            text=f"{value}",
            relief=RELIEF_TYPE,
            pady=vertical_pad,
            padx=horizontal_pad,
            bg=TEAL_COLOR,
            fg=WHITE_COLOR,
            borderwidth=borderwidth,
        )
        label.grid(row=1, column=col + 1, sticky="NSEW")

        for row, value2 in enumerate(temp_var[year_key][value], start=2):
            label = tk.Label(
                master=table_frame,
                text=f"{value2}",
                relief=RELIEF_TYPE,
                pady=vertical_pad,
                padx=horizontal_pad,
                bg=LIGHT_GRAY_COLOR,
                fg=DARK_GRAY_COLOR,
                borderwidth=borderwidth,
            )
            label.grid(row=row, column=col + 1, sticky="NSEW")

    frame_expansion(table_frame)

    return table_frame


def view_prof_tt_frame() -> tk.Frame:
    prof_tt_frame = tk.Frame(window, bg=LIGHT_GRAY_COLOR)
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
    all_profs: list = list(profs.keys())
    
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

    prof_OptionMenu = tk.OptionMenu(prof_tt_frame, prof_var, *all_profs)
    prof_OptionMenu.configure(relief="solid", bd=1, cursor="hand2")
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

                slot_label = tk.Label(
                    master=prof_tt_frame,
                    text=slot_text,
                    relief=RELIEF_TYPE,
                    pady=vertical_pad,
                    padx=horizontal_pad,
                    bg=LIGHT_GRAY_COLOR,
                    fg=DARK_GRAY_COLOR,
                    borderwidth=borderwidth,
                )
                slot_label.grid(row=lec_num + 3, column=col + 1, sticky="NSEW")

    prof_var.trace("w", generate_tt)
    generate_tt()

    frame_expansion(prof_tt_frame)

    return prof_tt_frame


def create_professors_frame() -> tk.Frame:
    vertical_padding = 5
    horizontal_padding = 10
    professors_frame = tk.Frame(window, bg=LIGHT_GRAY_COLOR)
    year_list = [""] + all_years
    RELIEF_TYPE = "ridge"
    border_width = 1

    # early exit if no professors found
    if not profs:
        label = tk.Label(
        professors_frame,
        text="No professors found!",
        )
        label.grid(row=0, column=0, sticky="NSEW")
        frame_expansion(professors_frame)
        return professors_frame

    for col, year in enumerate(year_list):
        header_label = tk.Label(
            master=professors_frame,
            text=f"{year}",
            relief=RELIEF_TYPE,
            padx=horizontal_padding,
            pady=vertical_padding,
            bd=border_width,
            bg=TEAL_COLOR,
            fg=WHITE_COLOR,
        )
        header_label.grid(row=0, column=col, sticky="NSEW")

    for row, professor in enumerate(profs, start=1):
        professors_label = tk.Label(
            master=professors_frame,
            text=f"{professor}",
            relief=RELIEF_TYPE,
            padx=horizontal_padding,
            bd=border_width,
            fg=DARK_GRAY_COLOR,
        )
        professors_label.grid(row=row, column=0, sticky="NSEW")

        for col, year in enumerate(year_list[1:]): # starting from 1 because added none.
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
                padx=horizontal_padding,
                pady=vertical_padding,
                bd=border_width,
                fg=DARK_GRAY_COLOR,
            )
            label.grid(row=row, column=col + 1, sticky="NSEW")

    frame_expansion(professors_frame)

    return professors_frame


def create_options_frame() -> tk.Frame:
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
            auto_schedule7(profs)

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
    horizontal_padding = 10

    options_frame = tk.Frame(
        window,
        relief="solid",
        bd=1,
        padx=horizontal_padding * 2,
        pady=vertical_padding * 2,
        bg=LIGHT_GRAY_COLOR,
    )

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

    departments_OptionMenu = tk.OptionMenu(options_frame, dept_var, *all_departments)
    departments_OptionMenu.configure(relief="solid", bd=1, cursor="hand2")
    departments_OptionMenu.grid(row=6, column=0, columnspan=2, sticky="NSEW")

    curr_time_label = tk.Label(
        options_frame,
    )
    curr_time_label.grid(row=0, column=0, columnspan=2)

    text1 = tk.Label(options_frame, text="Start Time: (24hr)")
    text1.grid(row=1, column=0, pady=vertical_padding)
    start_time_entry = tk.Entry(options_frame)
    start_time_entry.grid(row=1, column=1)

    text2 = tk.Label(options_frame, text="End Time:")
    text2.grid(row=2, column=0, pady=vertical_padding)
    end_time_entry = tk.Entry(options_frame)
    end_time_entry.grid(row=2, column=1, pady=vertical_padding)

    text3 = tk.Label(options_frame, text="Lecture Duration: (min)")
    text3.grid(row=3, column=0, pady=vertical_padding)
    lec_duration_entry = tk.Entry(options_frame)
    lec_duration_entry.grid(row=3, column=1, pady=vertical_padding, sticky="nsew")

    text4 = tk.Label(options_frame, text="Practical Slots: (comma separated)")
    text4.grid(row=4, column=0, pady=vertical_padding)
    practical_slots_entry = tk.Entry(options_frame)
    practical_slots_entry.grid(row=4, column=1, pady=vertical_padding, sticky="nsew")

    dept_var.trace("w", show_options)
    show_options()

    submit_button = tk.Button(
        options_frame, text="Submit", command=take_info, bg=TEAL_COLOR, fg=WHITE_COLOR
    )
    submit_button.grid(
        row=5, column=0, columnspan=2, pady=vertical_padding, sticky="NSEW"
    )

    frame_expansion(options_frame)

    return options_frame


def create_help_frame() -> tk.Frame:
    help_frame = tk.Frame(window, bg=LIGHT_GRAY_COLOR)
    vertical_padding = 10
    horizontal_padding = 10

    image = Image.open("img1.jpg")
    image = image.resize((300, image.height), Image.BICUBIC)

    tk_image = ImageTk.PhotoImage(image)

    image_label = tk.Label(
        help_frame, image=tk_image, borderwidth=0, highlightthickness=0
    )
    image_label.image = tk_image
    image_label.grid(row=0, column=0, sticky="NSWE")

    info_text = """Hello! Thank you for using ClassSync. Here's how to proceed:\n
1. Navigate to Options and select Add Details.
2. Provide professors' and subjects' information.
3. Move to Create Timetable, then click the button to auto-generate your timetable.
4. To see your timetable, head to the TimeTable menu and choose the desired view.
    """

    info_label = tk.Label(
        help_frame,
        text=info_text,
        wraplength=280,
        justify="left",
        foreground=DARK_GRAY_COLOR,
    )
    info_label.grid(row=0, column=1, padx=horizontal_padding * 2, pady=vertical_padding)
    frame_expansion(help_frame)

    return help_frame


def create_menu() -> None:
    """
    Creates a Menu for main GUI
    """

    menu = tk.Menu(window)
    window.config(menu=menu)

    prof_options = tk.Menu(menu)
    
    prof_options.add_command(
        label="Show All Professors", command=lambda: create_page(create_professors_frame)
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
        label="Add Data", command=lambda: create_page(create_entry_frame)
    )

    options.add_command(
        label="Department Settings", command=lambda: create_page(create_options_frame)
    )
    
    options.add_command(
        label="Delete Subject", command=lambda: create_page(delete_subject_frame)
    )

    options.add_command(
        label="Export TimeTable", command=lambda: create_page(create_export_page)
    )

    options.add_command(label="Help", command=lambda: create_page(create_help_frame))

    menu.add_cascade(label="Options", menu=options)

    tt_menu = tk.Menu(menu)

    for year in all_years:
        # print(f"create_menu = {year}")
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


def create_timetable_page() -> tk.Frame:
    """
    Create a 'Create a timetable page'
    """
    padx: int = 20
    pady: int = 10

    create_timetable_frame = tk.Frame(
        window, relief="solid", bd=1, background="#F5F5F5", pady=20, padx=20
    )
    text1 = tk.Label(
        create_timetable_frame,
        text="Click here to Create TimeTable:",
        background=LIGHT_GRAY_COLOR,
        foreground=DARK_GRAY_COLOR,
        font=HEADING_FONT,
    )
    text1.grid(row=0, column=0)

    schedule_btn = tk.Button(
        master=create_timetable_frame,
        text="Click Here",
        command=lambda: auto_schedule7(profs),
        relief="raised",
        borderwidth=2,
        background=TEAL_COLOR,
        foreground=WHITE_COLOR,
        padx=padx * 2,
        pady=pady,
    )

    schedule_btn.grid(row=1, column=0)

    frame_expansion(create_timetable_frame)

    return create_timetable_frame


def create_reschedule_page() -> tk.Frame:
    padx = 10
    pady = 15
    reschedule_frame = tk.Frame(window, background=LIGHT_GRAY_COLOR)
    text1 = tk.Label(reschedule_frame, text="Prof:")
    text1.grid(row=0, column=0, sticky="NSEW", padx=padx)
    prof_entry2 = tk.Entry(reschedule_frame)
    prof_entry2.grid(row=0, column=1, sticky="NSEW", padx=padx, pady=pady)

    text2 = tk.Label(reschedule_frame, text="Day:")
    text2.grid(row=1, column=0, sticky="NSEW", padx=padx)
    day_entry = tk.Entry(reschedule_frame)
    day_entry.grid(row=1, column=1, sticky="NSEW", padx=padx, pady=pady)

    reschedule_btn = tk.Button(
        master=reschedule_frame,
        text="Reschedule",
        command=lambda: reschedule(
            prof_entry2.get() or "Rajnish", day_entry.get() or "Mon"
        ),
        bg=TEAL_COLOR,
        fg=WHITE_COLOR,
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


def create_export_page() -> tk.Frame:
    def export_csv():
        year_val = year_var.get()
        department = get_department_by_year(year_val)
        time_slots = get_time_slots(department)

        if year_val == "All":
            for year in all_years:
                export_file_csv(year, time_slots)
        else:
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

    export_page_frame = tk.Frame(
        window,
        background=LIGHT_GRAY_COLOR,
        padx=horizontal_padding,
        pady=vertical_padding,
    )

    text1 = tk.Label(export_page_frame, text="Select a year & stream:")
    text1.grid(row=0, column=0, sticky="NSEW")

    year_var = tk.StringVar()
    year_options: list[str] = ["All"] + all_years if all_years else ["None"]
    year_var.set(year_options[0])

    prof_OptionMenu = tk.OptionMenu(export_page_frame, year_var, *year_options)

    prof_OptionMenu.configure(relief="solid", bd=1, cursor="hand2")
    prof_OptionMenu.grid(
        row=1,
        column=0,
        sticky="NSEW",
        pady=vertical_padding,
    )

    export_csv_btn = tk.Button(
        master=export_page_frame,
        text="Export to CSV",
        command=export_csv,
        bg=TEAL_COLOR,
        fg=WHITE_COLOR,
    )
    export_csv_btn.grid(
        row=2,
        column=0,
        sticky="NSEW",
        pady=vertical_padding / 2,
    )

    export_pdf_btn = tk.Button(
        master=export_page_frame,
        text="Export to PDF",
        command=export_pdf,
        bg=TEAL_COLOR,
        fg=WHITE_COLOR,
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

    # temp.pack(fill=tk.BOTH, expand=True)
    temp.tkraise()
    temp.grid(row=0, column=0, sticky="nsew")


def get_professor_by_subject(subject: str, subject_type=None):
    """
    Given a subject and an optional subject type,
    return the professor who teaches the subject.
    """
    subject = subject.split("\n")[0].strip()

    for professor, subjects in profs.items():
        for year, subject_list in subjects.items():
            for subject_info in subject_list:
                if subject_info["Subject"] == subject:
                    if subject_type is None or subject_info["Type"] == subject_type:
                        return professor

    print(
        f"No professor found for the given subject {subject} and subject type {subject_type}"
    )


def check_professor_available(lec_num: int, day: str) -> list:
    """
    Checks the availability of professors for a specific lecture number and day.
    """
    subjects = []

    # finding which lecture at specified lec number
    for year in ttlist.keys():
        subject = ttlist[year][day]
        if len(subject) - 1 >= lec_num:
            subjects.append(subject[lec_num])

    busy_professors = [get_professor_by_subject(subject) for subject in subjects]

    return [teacher for teacher in profs.keys() if teacher not in busy_professors]


def get_lec_number(professor, day) -> dict[str, list]:
    """
    Returns the lecture number [index] of the given professor on the given day.
    """
    subject: dict = profs.get(professor)
    # print(f"Prof. {professor} teaches = {subject}")
    lec_num = {}
    years_of_prof: list = list(subject.keys())

    for year in years_of_prof:
        scheduled_lecs = get_professors_from_schedule(year, day)
        indexes2 = [
            idx
            for idx in range(len(scheduled_lecs))
            if scheduled_lecs[idx] == professor
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
            ttlist[year][day][lec] = f"{sub}\n Theory\n ({available}) <Updated>"

    create_all_tt_pages()


def get_tt(day):
    """
    Print Time Table to console (FOR TESTING)
    """
    for x in ttlist:
        print(f"{x} = {ttlist[x][day]}")


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
        year_page: tk.Frame = view_timetable_frame(year)
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
    help_page = create_help_frame()
    prof_tt_page = view_prof_tt_frame()
    add_department_page = create_add_department_frame()
    delete_subject_page = delete_subject_frame()

    frames[create_entry_frame] = entry_page
    frames[create_reschedule_page] = reschedule_page
    frames[create_timetable_page] = timetable_page
    frames[create_professors_frame] = prof_page
    frames[create_options_frame] = option_page
    frames[create_export_page] = export_csv_page
    frames[create_help_frame] = help_page
    frames[view_prof_tt_frame] = prof_tt_page
    frames[create_add_department_frame] = add_department_page
    frames[delete_subject_frame] = delete_subject_page


def get_subjects_by_year(year_to_find: str) -> list[dict]:
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
            all_subs.extend(year[year_to_find])

    return all_subs


def get_subject(subs, professor, year, subtype):
    """
    Args:
    subs: profs
      professor: The name of the professor.
      year: The year of the course.
      subtype: The type of the subject.

    Returns:
      A subject that the professor teaches.
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
      A subjects that the professor teaches.
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
    """
    today_lec: list = ttlist[year][day]
    prof_list = []

    for subject in today_lec:
        if "Practical" in subject:
            prof_list.append(get_professor_by_subject(subject, "Practical"))
        else:
            prof_list.append(get_professor_by_subject(subject, "Theory"))

    return prof_list


def auto_schedule7(professors: dict[str, dict[str, list]]) -> None:
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


def generate_year_wise_schedule(year: str, professors: dict[str, dict[str, list]]) -> None:
    department: str = get_department_by_year(year)
    start_time, end_time, minutes_lecture = get_department_time(department)
    no_of_lectures = calc_college_time(start_time, end_time, minutes_lecture)
    practical_slots = get_practical_slots_by_department(department)
    professors_queue = get_professors_by_year(professors, year)

    for lec_num in range(no_of_lectures):           
        generate_daily_schedule(year, lec_num, professors_queue, practical_slots)


def generate_daily_schedule(year: str, lec_num: int, professors_queue: list, practical_slots: list):
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
            subject = get_subject(
                profs, professors_queue[0], year, subtype=subtype
            )
            if subject:
                if get_subject_workload(
                    professors_queue[0], year, subject, subtype
                ):
                    ttlist[year][days[day_num]].append(
                        f"{subject}\n{subtype}\n({professors_queue[0]})"
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
                sub["Workload"] -= 1
                return True
            else:
                return False
    return True


def get_department_by_year(year: str) -> str:
    """
    Returns the department associated with a given year.

    Returns:
        str: The department associated with the given year.
    """

    for department in all_departments:
        if department in year:
            return department


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
        row = [time] + values
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


def create_add_department_frame() -> tk.Frame:
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
        create_all_pages()

    vertical_padding = 10
    horizontal_padding = 15

    add_department_frame = tk.Frame(
        window,
        relief="solid",
        bd=1,
        padx=horizontal_padding,
        pady=vertical_padding,
        bg=LIGHT_GRAY_COLOR,
    )

    text1 = tk.Label(add_department_frame, text="Enter Department:")
    text1.grid(row=0, column=0, pady=vertical_padding)
    department_entry = tk.Entry(add_department_frame)
    department_entry.grid(row=1, column=0, pady=vertical_padding, sticky="NSEW")

    submit_button = tk.Button(
        add_department_frame,
        text="Submit",
        command=take_info,
        padx=horizontal_padding,
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

    delete_subject_frame = tk.Frame(window,
                                    bg=LIGHT_GRAY_COLOR,
                                    padx=horizontal_padding,
                                    pady=vertical_padding)

    def update_options(*args):
        selected_prof = prof_var.get()
        selected_year = year_var.get()
        
        all_subs = get_all_subjects(selected_prof, selected_year)

        # Clear the current options in the second OptionMenu
        sub_OptionMenu['menu'].delete(0, 'end')
        
        if not all_subs:
            sub_OptionMenu['menu'].add_command(label="None",)
            sub_var.set("None")
            return
        
        # Add new options based on the selected option in the first OptionMenu
        for subject in all_subs:
            sub_OptionMenu['menu'].add_command(
                label=f"{subject['Subject']} - {subject['Type']}",
                command=lambda sub=subject: sub_var.set(f"{sub['Subject']} - {sub['Type']}"))
        
        sub_var.set(f"{subject['Subject']} - {subject['Type']}")
        print(profs.get(selected_prof, {}).get(selected_year, []))

            
    def delete_subject():
        selected_prof = prof_var.get()
        selected_year = year_var.get()
        selected_sub = sub_var.get()
        selected_subject, selected_subject_type = selected_sub.split(' - ') 


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

    prof_OptionMenu = tk.OptionMenu(delete_subject_frame, prof_var, *all_profs, command=update_options)
    prof_OptionMenu.configure(relief="solid", bd=1, cursor="hand2")
    prof_OptionMenu.grid(
        row=0, column=0, pady=vertical_padding, sticky="NSEW"
    )

    year_var: tk.StringVar = tk.StringVar()
    all_years_temp: list = get_all_years()
    year_var.set(all_years_temp[0])

    year_OptionMenu = tk.OptionMenu(delete_subject_frame, year_var, *all_years_temp, command=update_options)
    year_OptionMenu.configure(relief="solid", bd=1, cursor="hand2")
    year_OptionMenu.grid(
        row=1, column=0, pady=vertical_padding, sticky="NSEW"
    )

    sub_var: tk.StringVar = tk.StringVar()
    sub_var.set("None")

    sub_OptionMenu = tk.OptionMenu(delete_subject_frame, sub_var, "None")
    sub_OptionMenu.configure(relief="solid", bd=1, cursor="hand2")
    sub_OptionMenu.grid(
        row=2, column=0, pady=vertical_padding, sticky="NSEW"
    )
    update_options()

    submit_button = tk.Button(
        delete_subject_frame,
        text="Submit",
        command=delete_subject,
        padx=horizontal_padding,
    )
    submit_button.grid(
        row=3, column=0, pady=vertical_padding, sticky="NSEW"
    )

    frame_expansion(delete_subject_frame)
    return delete_subject_frame



if __name__ == "__main__":
    TT_FILE: str = "timetable.json"
    PROFS_FILE: str = "professors2.json"
    SETTINGS_FILE: str = "settings2.json"

    LIGHT_GRAY_COLOR = "#F5F5F5"  # Background Color
    DARK_GRAY_COLOR = "#333333"  # Heading Text Color
    TEAL_COLOR = "#008080"  # Button Color
    WHITE_COLOR = "#FFFFFF"  # Button Text Color

    ttlist = read_json(TT_FILE)
    profs = read_json(PROFS_FILE)
    settings: dict[str, dict] = read_json(SETTINGS_FILE)

    all_years: list = get_all_years()
    all_departments: list = get_all_departments()

    window = tk.Tk()
    window.title("ClassSync")
    window.wm_attributes("-topmost", True)  # stays on top of other windows
    window.resizable(False, False)  # Prevent resizing in both dimensions

    window.minsize(250, 250)
    window.columnconfigure(0, weight=1)
    window.rowconfigure(0, weight=1)

    HEADING_FONT = tkFont.Font(family="Segoe UI", size=12, weight="bold")
    SUBHEADING_FONT = tkFont.Font(family="Segoe UI", size=10)

    set_window_options(window)
    
    if profs and settings:
        auto_schedule7(profs)

    store_json(TT_FILE, ttlist)

    create_menu()
    create_all_pages()
    create_all_tt_pages()
    create_page(create_add_department_frame)
    window.mainloop()