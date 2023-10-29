import logging
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


if __name__ == "__main__":
	logging.basicConfig(
		format="[%(asctime)s] [%(process)d] [%(levelname)s] [%(filename)s:%(lineno)d %(funcName)s] [%(message)s]",
		level=logging.INFO,
	)
	latitude = 35.4437
	longitude = 139.6380
	intent_googlenavigation(latitude, longitude)

