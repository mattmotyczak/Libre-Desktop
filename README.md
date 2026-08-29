# Librelink desktop widget app
> Manual of use and installation.

# // Intro:
A simple widget desktop app to keep track of your glucose without the need of unlocking your phone.
Any issues you come across, doubts that I havent clarified, feedback you want to give or ideas that I should add, feel free to leave them on a comment on the Discussions page! ;)

# // Install guide:
1. Download this repository as a ZIP file by going to the `Releases` section and clicking `Source code (zip)`.
   - Alternatively, clicking the big green button on the right side of your screen that says `Code`, then clicking `Download ZIP`.
2. Decompress that file on the directory that you want your app installed.
3. Execute `install_dependencies.bat`.
4. Execute `build.bat`.
   - A new folder called `/dist/` should have been created.
5. On that folder, you will find the app `LibreLinkUpWidget.exe`.
6. Run it and open config by double-clicking the widget, or right clicking on it and going into settings.
7. Load your information from Libreview.
> [!IMPORTANT]
> None of this information will go through me, they all get sent directly to Abbott's servers and back to you.
8. You may be interested in enabling "Launch app on Windows Startup" to forget about ever needing to search and open the file again.


And thats it! Congratulations on setting up your new Freestyle Libre widget.

# // Features:
   - Log-in through Libreview account.
   - Pick your desired registered patient.
   - Change unit meassures between mg/dL and mmol/L.
   - Set your high-and-low ranges to custom values.
   - Customize sizing and coloring of every tag.
      - This includes: Glucose, Name of Patient, Last Update text and Tendency Arrow.
   - Always-On-Top and Boot-With-Windows settings available.
   - Chose whether to have the window on a classic, windowed style or a modern, transparent widget format.
   - Change opacity, text shadowing style and more!

# // Known Issues:
> [!WARNING]
> When logging in, you may face an issue where the "Wait 5 minutes to try again" error never ends. To fix this, first try closing the widget entirely (Right Click Widget -> Exit App). If that doesnt work, delete the file called `config.json` (NOT config.py, thats a core function for the app).


> [!WARNING]
> When running `install_dependencies.bat`, you may come across an error that asks you to run some code manually. You can fix this by just closing the window and running the file again.
>
> This error is caused by windows being silly when handling new downloads, so its out of my bounds to control.


> [!WARNING]
> After saving, your app may freeze; but dont fret, it should go back to normal within a couple seconds.
