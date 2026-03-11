from windows_toasts import WindowsToaster, Toast

def notify(msg: str):
    toaster = WindowsToaster('pysystemtrade')
    toast = Toast()
    toast.text_fields = [msg]
    toaster.show_toast(toast)
