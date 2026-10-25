import os
import sys
import winreg

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def create_windows_shortcuts(create_desktop=True, create_startup=True):
    """
    Creates proper Unicode Windows shortcuts on Desktop and in Startup folder
    with clean Arabic names (using MoveFileW so no codepage mangling happens).
    """
    icon_path = os.path.normpath(os.path.join(BASE_DIR, "hassen_icon.ico"))
    if not os.path.exists(icon_path):
        icon_path = os.path.normpath(os.path.join(BASE_DIR, "hassen_icon.png"))

    pyw_exe = os.path.normpath(os.path.join(BASE_DIR, "venv", "Scripts", "pythonw.exe"))
    if not os.path.exists(pyw_exe):
        pyw_exe = os.path.normpath(os.path.join(BASE_DIR, "venv", "Scripts", "python.exe"))
    if not os.path.exists(pyw_exe):
        pyw_exe = sys.executable

    run_script = os.path.normpath(os.path.join(BASE_DIR, "run.py"))

    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")

        # 1. Desktop Shortcut
        if create_desktop:
            desktop_dir = shell.SpecialFolders("Desktop")
            
            # Clean any corrupted old shortcuts
            for f in os.listdir(desktop_dir):
                if ("Ø" in f and "Ù" in f) or f == "حَصِين للأطفال.lnk" or f == "Haseen Kids.lnk":
                    try:
                        os.remove(os.path.join(desktop_dir, f))
                    except Exception:
                        pass

            temp_lnk = os.path.join(desktop_dir, "Haseen_Kids_App.lnk")
            sc = shell.CreateShortcut(temp_lnk)
            sc.TargetPath = pyw_exe
            sc.Arguments = f'"{run_script}"'
            sc.WorkingDirectory = BASE_DIR
            sc.IconLocation = f"{icon_path},0"
            sc.Description = "حَصِين للأطفال | نظام الرقابة الأسرية وحماية الأجهزة"
            sc.Save()

            # Rename to Arabic using native Win32 Unicode MoveFileW
            final_lnk = os.path.join(desktop_dir, "حَصِين للأطفال.lnk")
            if os.path.exists(final_lnk):
                try:
                    os.remove(final_lnk)
                except Exception:
                    pass
            os.rename(temp_lnk, final_lnk)

        # 2. Windows Startup Folder
        if create_startup:
            startup_dir = shell.SpecialFolders("Startup")
            startup_lnk = os.path.join(startup_dir, "HaseenKids_AutoStart.lnk")
            sc2 = shell.CreateShortcut(startup_lnk)
            sc2.TargetPath = pyw_exe
            sc2.Arguments = f'"{run_script}" --minimized'
            sc2.WorkingDirectory = BASE_DIR
            sc2.IconLocation = f"{icon_path},0"
            sc2.Description = "حَصِين للأطفال | تشغيل تلقائي مع بدء تشغيل ويندوز"
            sc2.Save()

            # 3. Also register in Windows Registry Run key for resilience
            try:
                reg_key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0,
                    winreg.KEY_SET_VALUE
                )
                cmd_val = f'"{pyw_exe}" "{run_script}" --minimized'
                winreg.SetValueEx(reg_key, "HaseenKids", 0, winreg.REG_SZ, cmd_val)
                winreg.CloseKey(reg_key)
            except Exception:
                pass

        return True, "تم إنشاء اختصار سطح المكتب وتسجيل البرنامج في بدء التشغيل التلقائي بنجاح ✅"

    except Exception as e:
        return False, f"فشل إنشاء الاختصار: {str(e)}"

if __name__ == "__main__":
    ok, msg = create_windows_shortcuts()
    print("Result:", ok, msg)
