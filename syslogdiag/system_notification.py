import os
import platform


def notify(title, message):
	plt = platform.system()

	if plt == 'Linux':
		command = f'''
		notify-send "{title}" "{message}"
		'''
	else:
		return

	os.system(command)
