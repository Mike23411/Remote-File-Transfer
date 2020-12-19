Server Instructions
1. Ensure a private and public RSA key are stored on the device
2. Run server.py

Command Line Client Instructions
1. Run the rft_client.py
2. Enter the Hostname and port to connect to (Ex: 127.0.0.1:5600)
3. Enter username and password when prompted (users can be added or changed within the server.py file)
4. Once connected to the server, type "commands" in the command line to be given a list of commands
5. list files and directories by using the ls (local directory) and lsr (remote directory).
6. To navigate through directories, use the cd (local directory) and cdr (remote directory) to find the files or directories you are looking for.
7. Once you have found the file you are looking for, use the preview [file] command to preview a file 10 lines at a time, download [file] to download a file from the remote host, or upload [file] to upload a file to the remote host.

GUI Client Instruction
1. To enter the GUI, run the gui.py file
2. Enter the Hostname and port to connect to (Ex: 127.0.0.1:5600)
3. Enter username and password when prompted (users can be added or changed within the server.py file)
4. The GUI will start - click REFRESH to begin seeing server files and directories or refresh contents of the server directory
5. Navigate remote directories by clicking the directories in the list, which will always appear without file extensions at the top of the list
6. In the GUI you are given two buttons to browse through local directories, one for files and one for folders.
7. Using the browse buttons, you can find the file or folder you are looking for and import it to the client.
8. Once you have imported the files and folders you want, select a file or folder from the client side and use the arrow key to upload the selected item to the remote server.
9. Likewise you can select a file or folder from the remote server and use the arrow key on the server side to download the file to the local client.
10. Finally, you can use the clear button to clear all files and folders contained on the client. 