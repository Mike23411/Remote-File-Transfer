# img_viewer.py
import PySimpleGUI as sg

import os.path



# First the window layout in 2 columns


client_list_column = [

    [

        sg.FilesBrowse(),

        sg.Text("File"),

        sg.In(size=(25, 1), enable_events=True, key="-FILE-"),

    ],

    [

        sg.FolderBrowse(),

        sg.Text("Folder"),

        sg.In(size=(25, 1), enable_events=True, key="-FOLDER-"),

    ],

    [sg.Text("CLIENT")],

    [

        sg.Listbox(

            values=[], enable_events=True, size=(40, 20), key="-CLIENT LIST-"

        )

    ],
    [
        sg.Button('CLEAR', button_color='white on grey'),
    ],

]

# For now will only show the name of the file that was chosen

server_list_column = [

    [sg.Text("", size=(15, 4))],

    [sg.Text("SERVER", size=(50,1), key='SERVER TEXT')],

    [sg.Listbox(

        values=[], enable_events=True, size=(40, 20), key="-SERVER LIST-"

    )
    ],

    [sg.Button('REFRESH', button_color='white on grey', )
     ]

]

# ----- Full layout -----

layout = [

    [

        sg.Column(client_list_column),

        sg.Button('->', button_color='white on grey'),

        sg.VSeperator(),

        sg.Button('<-', button_color='white on grey'),

        sg.Column(server_list_column),

    ]

]

#def file_preview(filename):


def main():
    from client_intf import clientIntf
    client_intf = clientIntf()
    client_intf.client_setup()

    window = sg.Window("File Transfer", layout)

    client_files = {}
    client_gui_files = []
    server_files = {}
    current_folder = ""
    local_path = None

    while True:

        event, values = window.read()
        print(event)
        if event == "Exit" or event == sg.WIN_CLOSED:
            client_intf.event_handler(event)
            break

        # Folder name was filled in, make a list of files in the folder

        if event == "-FILE-":
            # Stores filename and path in client_files dictionary
            filename = values["-FILE-"]
            current_folder = filename
            client_files[os.path.basename(filename)] = filename
            client_gui_files += [os.path.basename(filename)]

            # Updates list of files
            window["-CLIENT LIST-"].update(values=client_gui_files)

        if event == 'CLEAR':
            client_files = {}
            client_gui_files = []
            window["-CLIENT LIST-"].update(client_gui_files)

        # Supposed to upload client files to server
        if event == '->':
            selected = window['-CLIENT LIST-'].get()
            print(selected)
            if selected:
                client_intf.event_handler(event, arg=selected[0])
                remote_list = [['..', True]] + client_intf.event_handler('REFRESH')
                dirs = [x[0] for x in remote_list if x[1]]
                files = [x[0] for x in remote_list if not x[1]]
                server_files = dirs + files
                window["-SERVER LIST-"].update(server_files)

        if event == '<-':
            selected = window['-SERVER LIST-'].get()
            if selected:
                client_intf.event_handler(event, selected[0])
                if local_path:
                    file_list = os.listdir(local_path)
                    client_gui_files = []
                    for file_name in file_list:
                        client_files[file_name] = folder
                        client_gui_files += [file_name]
                    window["-CLIENT LIST-"].update(client_gui_files)

        if event == "REFRESH":
            remote_list = [['..', True]] + client_intf.event_handler(event)
            dirs = [x[0] for x in remote_list if x[1]]
            files = [x[0] for x in remote_list if not x[1]]
            server_files = dirs + files
            window['SERVER TEXT'].update('SERVER: ' + client_intf.get_remote_path().__str__())
            window["-SERVER LIST-"].update(values=server_files)

        if event == "-FOLDER-":
            folder = values["-FOLDER-"]
            if folder:
                local_path = folder
                client_intf.set_local_path(local_path)
                file_list = os.listdir(folder)
                client_gui_files = []
                for file_name in file_list:
                    client_files[file_name] = folder
                    client_gui_files += [file_name]
                window["-CLIENT LIST-"].update(client_gui_files)

        if event == '-SERVER LIST-':
            selected = window["-SERVER LIST-"].get()[0]
            if selected:
                for x in remote_list:
                    if selected == x[0] and x[1]:
                        client_intf.event_handler('cdr', x[0])
                        remote_list = [['..', True]] + client_intf.event_handler('REFRESH')
                        dirs = [x[0] for x in remote_list if x[1]]
                        files = [x[0] for x in remote_list if not x[1]]
                        server_files = dirs + files
                        window['SERVER TEXT'].update('SERVER: ' + client_intf.get_remote_path().__str__())
                        window["-SERVER LIST-"].update(server_files)

        if event == '-CLIENT LIST-':
            pass

    window.close()


if __name__ == '__main__':
    main()
