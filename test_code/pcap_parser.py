# Imports for GUI
import threading
import tkinter as tk
import customtkinter
from tkinter import filedialog as fd

# Other imports
import os
import json
import pyshark
import queue
from mac_vendor_lookup import MacLookup
import nmap

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


class GUI(customtkinter.CTk):

    def __init__(self):
        super().__init__()

        # Initialize instance variables
        self.capture_previously_configured = False
        self.nmap_scan_ip_range = " "
        self.json_file = " "
        self.nmap_host_file = " "
        self.pcap_file = " "
        self.num_packets_capture = 1000
        self.running_capture = False
        self.perform_nmap_scan = False
        self.nmap_scan_complete = False

        self.toplevel_window = None

        self.window_setup() # call function to handle main gui setup

        self.queue = queue.Queue()

        self.results_array = [0, 0, 0, 0, 0, 0, {}]
        self.nmap_results = []

    ###################################################
    #                 Main GUI setup                  #
    ###################################################
    def window_setup(self):
        # configure window
        self.title("BONK")
        self.geometry("960x540")  # half of 1920 x 1080

        # configure grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=10)

        # create topbar
        self.topbar_frame = customtkinter.CTkFrame(self, corner_radius=0, border_width=2, border_color="orange")
        self.topbar_frame.grid(row=0)
        self.topbar_frame.pack(fill="x", ipadx=10, ipady=10)
        self.topbar_frame.grid_columnconfigure(0, weight=3)
        self.topbar_frame.grid_columnconfigure((1, 2, 3), weight=1)
        self.topbar_frame.grid_rowconfigure((0, 1, 2), weight=1)

        # Fill topbar with labels and buttons/option
        self.logo_label = customtkinter.CTkLabel(self.topbar_frame, text="Network Capture Parser",
                                                 font=customtkinter.CTkFont(family="Arial", size=25, weight="bold"))
        self.logo_label.grid(row=1, column=0)

        self.appearance_mode_label = customtkinter.CTkLabel(self.topbar_frame, text="Appearance Mode", anchor="e",
                                                            padx=10)
        self.appearance_mode_label.grid(row=0, column=6)

        self.scaling_label = customtkinter.CTkLabel(self.topbar_frame, text="UI Scaling", anchor="w", padx=10)
        self.scaling_label.grid(row=1, column=6)

        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.topbar_frame,
                                                                       values=["System", "Dark", "Light"],
                                                                       command=self.change_appearance_mode_event)

        self.appearance_mode_optionemenu.grid(row=0, column=7, padx=5)

        self.scaling_optionemenu = customtkinter.CTkOptionMenu(self.topbar_frame,
                                                               values=["80%", "90%", "100%", "110%", "120%"],
                                                               command=self.change_scaling_event)
        self.scaling_optionemenu.grid(row=1, column=7, padx=5)

        self.help_button = customtkinter.CTkButton(self.topbar_frame, text='Help', command=self.display_help_window)
        self.help_button.grid(row=2, column=7, padx=5)

        # PCAP option frame section
        self.pcap_options_frame = customtkinter.CTkFrame(self, corner_radius=5, border_width=2, border_color="orange")
        self.pcap_options_frame.grid_columnconfigure((0, 1), weight=1)
        self.pcap_options_frame.grid_rowconfigure((0, 1, 2, 3, 4), weight=1)
        self.pcap_options_frame.pack(side="left", fill='y')

        self.capture_options_label = customtkinter.CTkLabel(self.pcap_options_frame, text="Capture Options",
                                                            font=customtkinter.CTkFont(weight="bold"), anchor="center")
        self.capture_options_label.grid(row=0, columnspan=2, padx=50)

        self.pcap_option_menu = customtkinter.CTkOptionMenu(self.pcap_options_frame,
                                                            values=["Upload PCAP", "Perform Capture"],
                                                            command=self.change_pcap_option)

        self.pcap_option_menu.grid(row=1, columnspan=2, padx=50)

        self.pcap_option_button = customtkinter.CTkButton(self.pcap_options_frame, text="   Upload PCAP   ",
                                                          state=tk.NORMAL, command=self.select_pcap_file)
        self.pcap_option_button.grid(row=2, columnspan=2, padx=50)

        self.pcap_selected_option_label = customtkinter.CTkLabel(self.pcap_options_frame, text="")
        self.pcap_selected_option_label.grid(row=3, columnspan=2)

        self.pcap_file_or_num_packets = customtkinter.CTkLabel(self.pcap_options_frame, text="")
        self.pcap_file_or_num_packets.grid(row=4, columnspan=2)


        # NMAP option frame section
        self.nmap_options_frame = customtkinter.CTkFrame(self, corner_radius=5, border_width=2, border_color="orange")
        self.nmap_options_frame.grid_columnconfigure((0, 1), weight=1)
        self.nmap_options_frame.grid_rowconfigure((0,1,2,3,4), weight=1)
        self.nmap_options_frame.pack(side="left", fill='y')

        self.nmap_options_label = customtkinter.CTkLabel(self.nmap_options_frame, text="NMAP Options",
                                                          font=customtkinter.CTkFont(weight="bold"), anchor="center")
        self.nmap_options_label.grid(row=0, columnspan=2, padx=65)

        self.nmap_option_menu = customtkinter.CTkOptionMenu(self.nmap_options_frame,
                                                            values=["No NMAP", "Upload Host List", "NMAP Scan"],
                                                            command=self.change_nmap_option)

        self.nmap_option_menu.grid(row=1, columnspan=2, padx=65)

        self.nmap_command_button = customtkinter.CTkButton(self.nmap_options_frame, text="      No NMAP      ",
                                                           state=tk.DISABLED,
                                                           command=self.select_host_list_file)
        self.nmap_command_button.grid(row=2, columnspan=2, padx=65)

        self.hostlist_or_scan_label = customtkinter.CTkLabel(self.nmap_options_frame, text="")
        self.hostlist_or_scan_label.grid(row=3, columnspan=2)

        self.hostlist_file_or_ip_range_label = customtkinter.CTkLabel(self.nmap_options_frame, text="")
        self.hostlist_file_or_ip_range_label.grid(row=4, columnspan=2)

        # results frame
        self.results_frame = customtkinter.CTkFrame(self, corner_radius=5, border_width=2, border_color="orange")
        self.results_frame.grid_rowconfigure((0, 1, 2, 3, 4, 5, 6, 7, 8, 9), weight=1)
        self.results_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.results_frame.pack(side="left", fill="both", expand=1)

        self.performing_capture_label = customtkinter.CTkLabel(self.results_frame, text="",
                                                               anchor="center", font=customtkinter.CTkFont(size=15))
        self.performing_capture_label.grid(row=0, columnspan=6, pady=10)
        self.start_button = customtkinter.CTkButton(self.results_frame, text="Start", state=tk.DISABLED,
                                                    command=self.handle_start_button_click,
                                                    anchor="center")
        self.start_button.grid(row=0, columnspan=6, pady=(10, 10))

        self.progress_bar = customtkinter.CTkProgressBar(self.results_frame, corner_radius=5, orientation="horizontal",
                                                         mode='indeterminate')
        self.progress_bar.grid(row=1, columnspan=6, padx=(20, 10), pady=(10, 10), sticky="ew")

        self.hosts_label = customtkinter.CTkLabel(self.results_frame, text="", anchor="center")
        self.hosts_label.grid(row=2, column=1, padx=10)

        self.active_hosts_label = customtkinter.CTkLabel(self.results_frame, text="", anchor="center")
        self.active_hosts_label.grid(row=3, column=1, padx=10, pady=5)

        self.inactive_hosts_label = customtkinter.CTkLabel(self.results_frame, text="", anchor="center")
        self.inactive_hosts_label.grid(row=4, column=1, padx=10, pady=5)

        self.packets_label = customtkinter.CTkLabel(self.results_frame, text="", anchor="center")
        self.packets_label.grid(row=2, column=4, padx=10, pady=10)

        self.processed_packets_label = customtkinter.CTkLabel(self.results_frame, text="", anchor="center")
        self.processed_packets_label.grid(row=3, column=4, padx=10, pady=5)

        self.discarded_packets_label = customtkinter.CTkLabel(self.results_frame, text="", anchor="center")
        self.discarded_packets_label.grid(row=4, column=4, padx=10, pady=5)

        self.connections_label = customtkinter.CTkLabel(self.results_frame, text="", anchor="center")
        self.connections_label.grid(row=5, columnspan=6, pady=5)

        self.num_connections_label = customtkinter.CTkLabel(self.results_frame, text="", anchor="center")
        self.num_connections_label.grid(row=6, columnspan=6, pady=5)

        self.export_json_button = customtkinter.CTkButton(self.results_frame, text="Export to JSON for VR",
                                                          anchor="center",
                                                          command=self.handle_export_json_click,
                                                          state=tk.DISABLED)
        self.export_json_button.grid(row=7, columnspan=6, pady=(10, 10))

        self.json_file_label = customtkinter.CTkLabel(self.results_frame, text="", anchor="center")
        self.json_file_label.grid(row=8, columnspan=6, pady=(10, 10))

        self.reset_gui_button = customtkinter.CTkButton(self.results_frame, text="Reset GUI", anchor="center",
                                                        command=self.reset_gui_event)
        self.reset_gui_button.grid(row=9, columnspan=6, pady=(10, 10))

    ###################################################
    ###           GUI event functions               ###
    ###################################################

    # Changes appearance mode when user selects new mode from dropdown
    #   Allows for system, dark, or light modes
    #
    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    # Changes scaling mode when user selects new mode from dropdown
    #   Allows for 120%, 110%, 100%, 90%, or 80%
    #
    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)

    # create new help window or open existing one
    #
    def display_help_window(self):
        if self.toplevel_window is None or not self.toplevel_window.winfo_exists():
            self.toplevel_window = HelpWindow(self)  # create window if its None or destroyed
        else:
            self.toplevel_window.focus()  # if window exists focus it

    # Reset the gui to default values/states
    #
    def reset_gui_event(self):
        self.pcap_option_button.configure(state=tk.NORMAL)
        self.nmap_command_button.configure(text="      No NMAP      ", state=tk.DISABLED)

        self.performing_capture_label = customtkinter.CTkLabel(self.results_frame, text="",
                                                               anchor="center", font=customtkinter.CTkFont(size=15))
        self.performing_capture_label.grid(row=0, columnspan=6, pady=10)
        self.start_button = customtkinter.CTkButton(self.results_frame, text="Start", state=tk.DISABLED,
                                                    command=self.handle_start_button_click,
                                                    anchor="center")
        self.start_button.grid(row=0, columnspan=6, pady=(10, 10))

        self.hosts_label.configure(text="", anchor="center")
        self.active_hosts_label.configure(text="", anchor="center")
        self.inactive_hosts_label.configure(text="", anchor="center")
        self.packets_label.configure(text="", anchor="center")
        self.processed_packets_label.configure(text="", anchor="center")
        self.discarded_packets_label.configure(text="", anchor="center")
        self.connections_label.configure(text="", anchor="center")
        self.num_connections_label.configure(text="", anchor="center")
        self.pcap_selected_option_label.configure(text="")
        self.hostlist_or_scan_label.configure(text="")
        self.hostlist_file_or_ip_range_label.configure(text="")

        self.export_json_button.configure(state=tk.DISABLED)

        self.json_file_label.configure(text="", anchor="center")

        self.pcap_option_menu.set("Upload PCAP")
        self.nmap_option_menu.set("No NMAP")

        self.json_file = " "
        self.nmap_host_file = " "
        self.pcap_file = " "
        self.num_packets_capture = 1000
        self.running_capture = False
        self.perform_nmap_scan = False
        self.nmap_scan_complete = False

        self.results_array = [0, 0, 0, 0, 0, 0, {}]
        self.nmap_results = []

    # Handles switch between upload pcap and perform capture options
    #   when user selects new option from dropdown
    def change_pcap_option(self, new_pcap_option: str):
        if new_pcap_option == "Upload PCAP":
            self.pcap_option_button.configure(text="   Upload PCAP   ", command=self.select_pcap_file)
            self.pcap_file_or_num_packets.configure(text="")
            self.running_capture = False

            # See if file was already selected beforehand
            base_file = os.path.basename(os.path.normpath(self.pcap_file))

            if base_file == '.': # file was selected beforehand but incorrectly
                self.start_button.configure(state=tk.DISABLED)
                self.pcap_selected_option_label.configure(text="Select Again")
                self.pcap_file = " "  # reset pcap file path to default
            if base_file == " " or base_file == "":  # file was not selected beforehand
                self.start_button.configure(state=tk.DISABLED)
                self.pcap_selected_option_label.configure(text=" ")
                self.pcap_file = " "  # reset host list file path to default
            else:  # file was already selected
                self.start_button.configure(state=tk.NORMAL)
                self.pcap_selected_option_label.configure(font=customtkinter.CTkFont(weight="bold"), text="PCAP File:")
                self.pcap_file_or_num_packets.configure(text=base_file)
        elif new_pcap_option == "Perform Capture":
            self.pcap_option_button.configure(text="Configure Capture", command=self.configure_capture_dialog_event)

            if self.capture_previously_configured: #if they already configured the capture before
                self.start_button.configure(state=tk.NORMAL)
                self.pcap_selected_option_label.configure(font=customtkinter.CTkFont(weight="bold"), text="Num Packets:")
                self.pcap_file_or_num_packets.configure(text=self.num_packets_capture)
            else:
                self.start_button.configure(state=tk.DISABLED)
                self.pcap_selected_option_label.configure(text=" ")
                self.pcap_file_or_num_packets.configure(text=" ")

    # File select pop up window for user to select a pcap file
    #   Allows for .pcap and .pcapng files
    #
    def select_pcap_file(self):
        filetypes = (
            ('PCAP Files', '*.pcap *.pcapng'),
        )

        self.pcap_file = fd.askopenfilename(
            title='Select PCAP File',
            initialdir='/',
            filetypes=filetypes)

        base_file = os.path.basename(os.path.normpath(self.pcap_file))

        if base_file == '.':  # Check when file dialog was exited without file being selected
            self.pcap_selected_option_label.configure(font=customtkinter.CTkFont(weight="bold"), text="Select Again")
            self.pcap_file_or_num_packets.configure(text="")
        else:
            self.pcap_selected_option_label.configure(font=customtkinter.CTkFont(weight="bold"), text="PCAP File:")
            self.pcap_file_or_num_packets.configure(text=base_file)
            self.running_capture = False
            self.start_button.configure(state=tk.NORMAL)


    # Dialog popup window for configuring a network capture
    #   Allows user to input how many packets to capture
    #
    def configure_capture_dialog_event(self):
        dialog = customtkinter.CTkInputDialog(text="Type in # of packets to capture:", title="Configure Network Capture")
        packets = dialog.get_input()

        if packets.isnumeric(): # ensure input was a number
            self.num_packets_capture = int(packets)
            self.pcap_selected_option_label.configure(font=customtkinter.CTkFont(weight="bold"), text="Num Packets:")
            self.pcap_file_or_num_packets.configure(text=str(self.num_packets_capture))
            self.capture_previously_configured = True
            self.running_capture = True
            self.start_button.configure(state=tk.NORMAL)
        else:
            self.pcap_selected_option_label.configure(text="Entry invalid. Configure again.")
            self.pcap_file_or_num_packets.configure(text="")

    # Handles switch between upload host list, and perform nmap scan,
    #  and no nmap when user selects new option from dropdown
    def change_nmap_option(self, new_nmap_option: str):
        if new_nmap_option == "Upload Host List":
            self.nmap_command_button.configure(text="  Upload Host List ", command=self.select_host_list_file, state=tk.NORMAL)
            self.perform_nmap_scan = False

            # See if file was already selected beforehand
            base_file = os.path.basename(os.path.normpath(self.nmap_host_file))

            if base_file == '.': # file was selected beforehand but incorrectly
                self.hostlist_or_scan_label.configure(text="Select Again")
                self.nmap_host_file = " "  # reset host list file path to default
                self.hostlist_file_or_ip_range_label.configure(text=" ")
            if base_file == " " or base_file == "":  # file was not selected beforehand
                self.hostlist_or_scan_label.configure(text=" ")
                self.nmap_host_file = " "  # reset host list file path to default
                self.hostlist_file_or_ip_range_label.configure(text=" ")
            else:  # file was already selected
                self.hostlist_or_scan_label.configure(font=customtkinter.CTkFont(weight="bold"), text="Host List:")
                self.hostlist_file_or_ip_range_label.configure(text=base_file)
        elif new_nmap_option == "NMAP Scan":
            self.nmap_command_button.configure(text="Configure NMAP Scan", command=self.configure_nmap_scan_dialog_event,
                                               state=tk.NORMAL)

            if self.nmap_scan_ip_range != " ": # check if nmap scan was already configured before
                self.hostlist_or_scan_label.configure(font=customtkinter.CTkFont(weight="bold"), text="IP Range/CIDR:")
            else:
                self.perform_nmap_scan = True
                self.hostlist_or_scan_label.configure(text=" ")
            self.hostlist_file_or_ip_range_label.configure(text=self.nmap_scan_ip_range)
        elif new_nmap_option == "No NMAP":
            self.perform_nmap_scan = False
            self.nmap_command_button.configure(text="      No NMAP      ", state=tk.DISABLED)
            self.hostlist_or_scan_label.configure(text="")
            self.hostlist_file_or_ip_range_label.configure(text="")

    # File select pop up window for user to select a host list file
    #   Allows for .txt files
    #
    def select_host_list_file(self):

        filetypes = (
            ('host list files', '*.txt'),
        )

        self.nmap_host_file = fd.askopenfilename(
            title='Select Host List File',
            initialdir='/',
            filetypes=filetypes)

        # get the base file name from the absolute address
        base_file = os.path.basename(os.path.normpath(self.nmap_host_file))

        if base_file == '.':
            self.hostlist_or_scan_label.configure(text="Select Again")
            self.hostlist_file_or_ip_range_label.configure(text=" ")
            self.nmap_host_file = " "  # reset host list file path to default
        else:
            self.hostlist_or_scan_label.configure(font=customtkinter.CTkFont(weight="bold"), text="Host List:")
            self.hostlist_file_or_ip_range_label.configure(text=base_file)

    # Dialog popup window for configuring nmap scan
    #   Allows user to input IP range
    #
    def configure_nmap_scan_dialog_event(self):
        dialog = customtkinter.CTkInputDialog(text="Type in IP Range or CIDR Address Range:", title="Configure NMAP Scan")
        self.nmap_scan_ip_range = dialog.get_input()
        self.perform_nmap_scan = True
        self.hostlist_or_scan_label.configure(font=customtkinter.CTkFont(weight="bold"), text="IP Range/CIDR:")
        self.hostlist_file_or_ip_range_label.configure(text=self.nmap_scan_ip_range)

    # Handles user clicking the start button.
    #   Creates pcap parsing or network capturing classes,
    #   inheriting multithreading class, to run as a background
    #   task. GUI freezes up without the use of multithreading
    #
    def handle_start_button_click(self):
        # Disable buttons
        self.pcap_option_button.configure(state=tk.DISABLED)
        self.nmap_command_button.configure(state=tk.DISABLED)
        self.reset_gui_button.configure(state=tk.DISABLED)
        self.start_button.destroy()
        self.progress_bar.start()

        if self.perform_nmap_scan:
            NmapScanner(self.queue, self.nmap_scan_ip_range, self.nmap_results).start()

            self.performing_capture_label.configure(text="Running NMAP Scan")
            self.after(100, self.nmap_process_queue)

        else:
            if not self.nmap_scan_complete:
                self.nmap_results = " "

            # Replace start button with status message and begin pcap parsing or network capture
            if not self.running_capture:
                start_text = "Processing PCAP"
                PcapParser(self.queue, self.pcap_file, self.nmap_host_file, self.nmap_results, self.results_array).start()
            else:
                start_text = "Running Network Capture"
                NetworkCapture(self.queue, self.results_array, self.nmap_host_file, self.nmap_results, self.num_packets_capture).start()

            self.performing_capture_label.configure(text=start_text)
            self.after(100, self.process_queue)


    def nmap_process_queue(self):
        try:
            msg = self.queue.get_nowait()

            #Indicate that nmap scan happened
            self.nmap_scan_complete = True

            # Update results
            self.performing_capture_label.configure(text="NMAP Complete")

            self.hosts_label.configure(text="Hosts Found")

            # Take data from parsing/capture and display it for the user
            self.active_hosts_label.configure(text=str(len(self.nmap_results)))

            # clear the queue
            with self.queue.mutex:
                self.queue.queue.clear()

            #Start parse by recalling start button event function
            self.perform_nmap_scan = False
            self.handle_start_button_click()

        except queue.Empty:  # threads are still running
            self.after(100, self.nmap_process_queue)

    # Check whether parsing/capture threads have completed
    #
    def process_queue(self):
        try:
            msg = self.queue.get_nowait()

            # Stop the progress bar
            self.progress_bar.stop()

            # Update results
            self.performing_capture_label.configure(text="Parsing Complete")

            self.hosts_label.configure(text="Hosts")
            self.packets_label.configure(text="Packets")

            # Take data from parsing/capture and display it for the user
            self.active_hosts_label.configure(text=str(self.results_array[1]) + " Active")
            self.inactive_hosts_label.configure(text=str(self.results_array[2]) + " Inactive")
            self.processed_packets_label.configure(text=str(self.results_array[3]) + " Processed")
            self.discarded_packets_label.configure(text=str(self.results_array[4]) + " Discarded")

            self.connections_label.configure(text="Host Connections")
            self.num_connections_label.configure(text=str(self.results_array[5]))

            # enable the export and reset buttons
            self.export_json_button.configure(state=tk.NORMAL)
            self.reset_gui_button.configure(state=tk.NORMAL)

        except queue.Empty: # threads are still running
            self.after(100, self.process_queue)

    # Handles the user clicking the 'Export to JSON for VR' button
    #   converts the final data collected from pcap/capture to JSON format
    #
    def handle_export_json_click(self):
        self.performing_capture_label.configure(text="Exporting JSON")

        file = fd.asksaveasfile(initialfile='Untitled.json',
                                defaultextension=".json", filetypes=[("JSON Files", "*.json")])

        # get the base file name from the absolute address
        base_file = os.path.basename(os.path.normpath(file.name))

        if file.name == " " or base_file == ".":  # check that save file was actually updated
            self.json_file_label.configure(text="Select Again")
        else:
            self.json_file_label.configure(text=base_file)

            # Actually generate the JSON file for VR
            with open(file.name, "w") as outfile:  # open json file in write mode
                # dump the network object from the packet capture to the json file
                json.dump(self.results_array[6], outfile, indent=4, separators=(", ", ": "), sort_keys=True)

            self.performing_capture_label.configure(text="JSON Exported")
            self.export_json_button.configure(text="Export Again")

# Help window class for setting up a help window with information
#   on how to use the GUI
#
class HelpWindow(customtkinter.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("700x300")
        self.title("Help")

        self.tabs = customtkinter.CTkTabview(self, width=500, segmented_button_unselected_hover_color="orange")
        self.tabs.pack(side="top", fill="both", expand=1)
        self.tabs.add("PCAP/Capture")
        self.tabs.add("NMAP")
        self.tabs.add("Results")
        self.tabs.add("Exporting to JSON")

        self.tabs.tab("PCAP/Capture").grid_columnconfigure((0,1), weight=1)
        self.tabs.tab("PCAP/Capture").grid_rowconfigure(0, weight=1)
        self.tabs.tab("PCAP/Capture").grid_rowconfigure(1, weight=5)
        self.upload_pcap_label = customtkinter.CTkLabel(self.tabs.tab("PCAP/Capture"), text="Uploading PCAPs")
        self.upload_pcap_label.grid(column=0, row=0)
        self.upload_pcap_text = customtkinter.CTkTextbox(self.tabs.tab("PCAP/Capture"))
        self.upload_pcap_text.insert("0.0", "Here is some text")
        self.upload_pcap_text.grid(column=0, row=1)
        self.perform_capture_label = customtkinter.CTkLabel(self.tabs.tab("PCAP/Capture"), text="Network Captures")
        self.perform_capture_label.grid(column=1, row=0)

class NmapScanner(threading.Thread):
    def __init__(self, queue, ip_range, nmap_results):
        super().__init__()

        self.queue = queue
        self.ip_range = ip_range
        self.nmap_results = nmap_results

    # Background task to run in the new thread
    def run(self):
        nm = nmap.PortScanner()
        nm.scan(hosts=self.ip_range, arguments='-sP')

        for host in nm.all_hosts():
            self.nmap_results.append(host)

        self.queue.put("Task finished")


# Pcap parsing class that inherits the threading class.
#   Parses a pcap file in a separate thread and returns
#   results via a pass by reference array
#
class PcapParser(threading.Thread):
    def __init__(self, queue, pcap_file, nmap_file, nmap_host_list, results_array):
        super().__init__()

        self.queue = queue
        self.results_array = results_array

        try:
            self.pcap_object = pyshark.FileCapture(pcap_file)  # get the pcap file data into a python object
        except FileNotFoundError:
            print('The file ' + pcap_file + ' could not be found or does not exist')
            exit()

        self.num_active_hosts = 0
        self.num_used_packets = 0
        self.num_discarded_packets = 0
        self.num_connections = 0

        self.inactive_host_list = []
        self.dictionary_host_list = []
        self.simple_host_list = []
        self.packet_list = []
        self.host_connections = [[]]
        self.final_data_structure = {}

        # Call helper function to create list of ips from nmap list
        self.using_nmap = False
        if nmap_file != " ":
            self.nmap_ip_list = []
            self.get_ip_list(nmap_file)
            self.using_nmap = True
        elif nmap_host_list != " ":
            self.nmap_ip_list = nmap_host_list
            self.using_nmap = True

        self.mac = MacLookup()
        #self.mac.update_vendors()  # update vendor list

    # Background task to run in the new thread
    def run(self):
        self.parse_pcap()

        if self.using_nmap:
            self.process_inactive_hosts()

        self.calculate_host_connections()

        # Update the results array that's shared between this thread and the GUI thread
        self.results_array[0] = self.num_active_hosts + len(self.inactive_host_list) # total number of hosts
        self.results_array[1] = self.num_active_hosts
        self.results_array[2] = len(self.inactive_host_list)
        self.results_array[3] = self.num_used_packets + self.num_discarded_packets # total number of packets
        self.results_array[4] = self.num_discarded_packets
        self.results_array[5] = self.num_connections
        self.results_array[6] = self.final_data_structure

        self.queue.put("Task finished")

    # Parses the pcap to gather necessary data
    # Generates dictionary host list, packet list, and simple host list
    #
    def parse_pcap(self):

        for pkt in self.pcap_object:
            try:
                simple_host_src = str(pkt.ip.src)
                simple_host_dst = str(pkt.ip.dst)

                try:  # get the summary host info for src and dst hosts
                    host_mac = str(pkt.eth.addr)

                    try:
                        vendor = self.mac.lookup(host_mac)  # get the vendor
                    except:
                        vendor = "Vendor Not Available"

                    summary_host_src = {'HostIP': simple_host_src,
                                        'HostMAC': host_mac,
                                        'Vendor': vendor}

                    summary_host_dst = {'HostIP': simple_host_dst,
                                        'HostMAC': host_mac,
                                        'Vendor': vendor}
                except AttributeError:  # no MAC address attribute available
                    summary_host_src = {'HostIP': simple_host_src,
                                        'HostMAC': "MAC Not Available",
                                        'Vendor': "Vendor Not Available"}
                    summary_host_dst = {'HostIP': simple_host_dst,
                                        'HostMAC': "MAC Not Available",
                                        'Vendor': "Vendor Not Available"}

                # create summary packet object with relevant info
                summary_pkt = {'ID': pkt.frame_info.number,
                               'ActualTime': pkt.sniff_timestamp,
                               'RelativeTime': float(pkt.frame_info.time_relative),
                               'Source': simple_host_src,
                               'Destination': simple_host_dst,
                               'Length': float(pkt.length)}

                self.num_used_packets += 1
                self.packet_list.append(
                    summary_pkt)  # append pkt to list. not using this list as of now, but might want it later

                if not self.using_nmap or ((simple_host_dst in self.nmap_ip_list) and (simple_host_src in self.nmap_ip_list)):
                    src_host_exists = False
                    for current_host in self.dictionary_host_list:
                        if current_host['HostIP'] == summary_host_src[
                            'HostIP']:  # see if the pkt belongs to the current
                            src_host_exists = True  # src host in the list
                            break

                    if not src_host_exists:  # src host has not been identified yet
                        self.dictionary_host_list.append(summary_host_src)
                        self.simple_host_list.append(simple_host_src)
                        self.num_active_hosts += 1

                    dst_host_exists = False
                    for current_host in self.dictionary_host_list:
                        if current_host['HostIP'] == summary_host_dst[
                            'HostIP']:  # see if the pkt belongs to the current
                            dst_host_exists = True  # dst host in the list
                            break

                    if not dst_host_exists:  # dst host has not been identified yet
                        self.dictionary_host_list.append(summary_host_dst)
                        self.simple_host_list.append(simple_host_dst)
                        self.num_active_hosts += 1

            except AttributeError:  # for pkts that don't have an ip (broadcast, for example)
                self.num_discarded_packets += 1

    # Analyzes the connections between active hosts
    # creates the final connections data structure by iterating over the packets
    #
    def calculate_host_connections(self):

        # Create 2D array for connections and initialize connections to 0 (nothing connected)
        rows, cols = len(self.simple_host_list), len(self.simple_host_list)
        self.host_connections = [[0 for i in range(cols)] for j in range(rows)]

        # iterate over all packets in the capture
        for pkt in self.packet_list:
            src = pkt['Source']
            dst = pkt['Destination']

            # Make sure the src and dst addresses exist in the host list
            # For example, when the pkt is being sent as a broadcast, this is when it wouldn't be included
            if (src in self.simple_host_list) and (dst in self.simple_host_list):
                source_row = self.simple_host_list.index(src)
                dst_col = self.simple_host_list.index(dst)

                self.host_connections[source_row][dst_col] += pkt['Length']  # add pkt data length to the connection
                #self.host_connections[source_column][dst_row] += pkt['Length']

                self.num_connections += 1

        self.final_data_structure = {'Hosts': self.dictionary_host_list,
                                     'Connections': self.host_connections}

    ###################################################
    ###         parse_pcap helper functions         ###
    ###################################################

    # Uses the list of IPs retrieved from a nmap scan to create a
    # list object containing those IPs
    #
    def get_ip_list(self, nmap_file):
        with open(nmap_file, 'r') as fp:
            # read all lines using readline()
            lines = fp.readlines()

        for line in lines:
            self.nmap_ip_list.append(line.replace("\n", ""))

    # Filters out active hosts from the list of all hosts.
    # This identifies the inactive hosts and labels them as such
    def process_inactive_hosts(self):
        self.inactive_host_list = self.nmap_ip_list

        # remove active hosts from the list
        for current_host in self.dictionary_host_list:
            self.inactive_host_list.remove(current_host['HostIP'])  # remove the active hosts from the inactive list

        # add inactive hosts to the dictionary host list
        for host in self.inactive_host_list:
            inactive_host_dict = {'HostIP': host,
                                  'Activity': 'inactive'}

            self.dictionary_host_list.append(inactive_host_dict)
            self.simple_host_list.append(host)

# Network capture class that inherits the threading class.
#   Performs a network capture in a separate thread and
#   returns results via a pass by reference array.
#
class NetworkCapture(threading.Thread):

    def __init__(self, queue, results_array, nmap_file, nmap_host_list, capture_length):
        super().__init__()

        self.queue = queue
        self.results_array = results_array
        self.capture_length = capture_length

        self.num_active_hosts = 0
        self.num_used_packets = 0
        self.num_discarded_packets = 0
        self.num_connections = 0

        self.dictionary_host_list = []
        self.simple_host_list = []
        self.inactive_host_list = []
        self.packet_list = []
        self.host_connections = [[]]
        self.final_data_structure = {}

        self.capture = pyshark.LiveCapture()
        self.mac = MacLookup()
        self.mac.update_vendors() # update vendor list

        # Call helper function to create list of ips from nmap list
        self.using_nmap = False
        if nmap_file != " ":
            self.nmap_ip_list = []
            self.get_ip_list(nmap_file)
            self.using_nmap = True
        elif nmap_host_list != " ":
            self.nmap_ip_list = nmap_host_list
            self.using_nmap = True

    def run(self):

        for packet in self.capture.sniff_continuously(packet_count=self.capture_length):
            self.process_packet(packet)

        if self.using_nmap:
            self.process_inactive_hosts()

        self.calculate_host_connections()

        # Update the results array that's shared between this thread and the GUI thread
        self.results_array[0] = self.num_active_hosts + len(self.inactive_host_list) # total number of hosts
        self.results_array[1] = self.num_active_hosts
        self.results_array[2] = len(self.inactive_host_list)
        self.results_array[3] = self.num_used_packets + self.num_discarded_packets # total number of packets
        self.results_array[4] = self.num_discarded_packets
        self.results_array[5] = self.num_connections
        self.results_array[6] = self.final_data_structure

        self.queue.put("Task finished")

    # Uses the list of IPs retrieved from a nmap scan to create a
    # list object containing those IPs
    #
    def get_ip_list(self, nmap_file):
        with open(nmap_file, 'r') as fp:
            # read all lines using readline()
            lines = fp.readlines()

        for line in lines:
            self.nmap_ip_list.append(line.replace("\n", ""))

    # Parses the pcap to gather necessary data
    # Generates dictionary host list, packet list, and simple host list
    #
    def process_packet(self, pkt):

        try:
            simple_host_src = str(pkt.ip.src)
            simple_host_dst = str(pkt.ip.dst)

            try:  # get the summary host info for src and dst hosts
                host_mac = str(pkt.eth.addr)

                try:
                    vendor = self.mac.lookup(host_mac)  # will need to replace with actually getting the vendor
                except:
                    vendor = "Vendor Not Available"

                summary_host_src = {'HostIP': simple_host_src,
                                    'HostMAC': host_mac,
                                    'Vendor': vendor}

                summary_host_dst = {'HostIP': simple_host_dst,
                                    'HostMAC': host_mac,
                                    'Vendor': vendor}
            except AttributeError:  # no MAC address attribute available
                summary_host_src = {'HostIP': simple_host_src,
                                    'HostMAC': "MAC Not Available",
                                    'Vendor': "Vendor Not Available"}
                summary_host_dst = {'HostIP': simple_host_dst,
                                    'HostMAC': "MAC Not Available",
                                    'Vendor': "Vendor Not Available"}

            # create summary packet object with relevant info
            summary_pkt = {'ID': pkt.frame_info.number,
                           'ActualTime': pkt.sniff_timestamp,
                           'RelativeTime': float(pkt.frame_info.time_relative),
                           'Source': simple_host_src,
                           'Destination': simple_host_dst,
                           'Length': float(pkt.length)}

            self.num_used_packets += 1
            self.packet_list.append(
                summary_pkt)  # append pkt to list. not using this list as of now, but might want it later

            if not self.using_nmap or ((simple_host_dst in self.nmap_ip_list) and (simple_host_src in self.nmap_ip_list)):
                self.append_host(summary_host_src, summary_host_dst)

        except AttributeError:  # for pkts that don't have an ip (broadcast, for example)
            self.num_discarded_packets += 1

    # Analyzes the connections between active hosts
    # creates the final connections data structure by iterating over the packets
    #
    def calculate_host_connections(self):

        # Create 2D array for connections and initialize connections to 0 (not connected)
        rows, cols = len(self.simple_host_list), len(self.simple_host_list)
        self.host_connections = [[0 for i in range(cols)] for j in range(rows)]

        # iterate over all packets in the capture
        for pkt in self.packet_list:
            src = pkt['Source']
            dst = pkt['Destination']

            # Make sure the src and dst addresses exist in the host list
            if (src in self.simple_host_list) and (dst in self.simple_host_list):
                source_column = self.simple_host_list.index(src)
                dst_row = self.simple_host_list.index(dst)

                self.host_connections[dst_row][source_column] += pkt['Length']  # add pkt data length to the connection
                self.host_connections[source_column][dst_row] += pkt['Length']

                self.num_connections += 1

        self.final_data_structure = {'Hosts': self.dictionary_host_list,
                                     'Connections': self.host_connections}

    ######################################################
    ###         network capture helper methods         ###
    ######################################################

    # Appends new host to the host list
    def append_host(self, summary_host_src, summary_host_dst):

        src_host_exists = False
        dst_host_exists = False

        host_src = summary_host_src['HostIP']
        host_dst = summary_host_dst['HostIP']

        if host_src in self.simple_host_list:  # see if the source host has already been identified
            src_host_exists = True

        if not src_host_exists:  # src host has not been identified yet
            self.dictionary_host_list.append(summary_host_src)
            self.simple_host_list.append(host_src)
            self.num_active_hosts += 1

        if host_dst in self.simple_host_list:  # see if the destination host has already been identified
            dst_host_exists = True

        if not dst_host_exists:  # dst host has not been identified yet
            self.dictionary_host_list.append(summary_host_dst)
            self.simple_host_list.append(host_dst)
            self.num_active_hosts += 1

    # Filters out active hosts from the list of all hosts.
    # This identifies the inactive hosts and labels them as such
    def process_inactive_hosts(self):
        self.inactive_host_list = self.nmap_ip_list

        # remove active hosts from the list
        for current_host in self.dictionary_host_list:
            self.inactive_host_list.remove(current_host['HostIP'])  # remove the active hosts from the inactive list

        # add inactive hosts to the dictionary host list
        for host in self.inactive_host_list:
            inactive_host_dict = {'HostIP': host,
                                  'Activity': 'inactive'}

            self.dictionary_host_list.append(inactive_host_dict)
            self.simple_host_list.append(host)


if __name__ == "__main__":
    gui = GUI()
    gui.mainloop()
