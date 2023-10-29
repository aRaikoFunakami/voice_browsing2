import logging
import time
from ppadb.client import Client
# https://pypi.org/project/pure-python-adb/


def intent_googlenavigation(latitude, longitude):
	client = Client(host="127.0.0.1", port=5037)
	devices = client.devices()
	device = devices[0]

	command = f'am start -a android.intent.action.VIEW -d "google.navigation:q={latitude},{longitude}"'
	logging.info(f"command: {command}")
	output = device.shell(command)
	print(output)
	return output

def intent_chrome():
	return intent_application("com.android.chrome/com.google.android.apps.chrome.Main")

def intent_googlemap():
	return intent_application("com.google.android.apps.maps/com.google.android.maps.MapsActivity")

def intent_application(application):
	client = Client(host="127.0.0.1", port=5037)
	devices = client.devices()
	device = devices[0]
	white_list = [
		"com.android.chrome/com.google.android.apps.chrome.Main",
		"com.google.android.apps.maps/com.google.android.maps.MapsActivity",
	]
	command = f'am start -n {application}'
	logging.info(f"command: {command}")
	if application in white_list:
		output = device.shell(command)
		print(output)
		return output
	else:
		error_string = f"The application '{application}' is not in the white list!"
		logging.error(error_string)
		return error_string

if __name__ == "__main__":
	logging.basicConfig(
		format="[%(asctime)s] [%(process)d] [%(levelname)s] [%(filename)s:%(lineno)d %(funcName)s] [%(message)s]",
		level=logging.INFO,
	)
	latitude = 35.4437
	longitude = 139.6380
	intent_googlenavigation(latitude, longitude)

	time.sleep(3)
	intent_application("com.android.chrome/com.google.android.apps.chrome.Main")

