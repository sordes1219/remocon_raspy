# Import SDK packages
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
from AWSIoTPythonSDK.exception import AWSIoTExceptions
import time
import json
from logs import Applogger
import subprocess

# Init Logger
applogger = Applogger(__name__)
logger = applogger.logger

# Init AWSIoTMQTTShadowClient
myAWSIoTMQTTShadowClient = None
myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient("RaspberryPi")
myAWSIoTMQTTShadowClient.configureEndpoint("a1xfsi89ntz6zn-ats.iot.ap-northeast-1.amazonaws.com", 8883)
myAWSIoTMQTTShadowClient.configureCredentials(r"cert/rootCA.pem", r"cert/private.pem.key", r"cert/device.pem.crt")

# AWSIoTMQTTShadowClient connection configuration
myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10) # 10 sec
myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5) # 5 sec

# Function called when a shadow is deleted
def customShadowCallback_Delete(payload, responseStatus, token):
    # Display status and data from Update request
    if responseStatus == "timeout":
        logger.error("Delete request " + token + " time out!")

    if responseStatus == "accepted":
        logger.debug("~~~~~~~~~~~~~~~~~~~~~~~")
        logger.debug("Delete request with token: " + token + " accepted!")
        logger.debug("~~~~~~~~~~~~~~~~~~~~~~~\n\n")

    if responseStatus == "rejected":
        logger.error("Delete request " + token + " rejected!")

# Function called when a shadow is updated
def customShadowCallback_Update(payload, responseStatus, token):
    # Display status and data from Update request
    if responseStatus == "timeout":
        logger.error("Update request " + token + " time out!")

    if responseStatus == "accepted":
        logger.debug("~~~~~~~~~~~~~~~~~~~~~~~")
        logger.debug("Update request with token: " + token + " accepted!")
        logger.debug("~~~~~~~~~~~~~~~~~~~~~~~\n\n")

    if responseStatus == "rejected":
        logger.error("Update request " + token + " rejected!")

# Function called when a shadow-delta is updated
def customShadowCallback_DeltaUpdate(payload, responseStatus, token):

    # Display status and data from Update request
    logger.debug("~~~~~~~~~~~~~~~~~~~~~~~")
    logger.debug("DeltaUpdate payload: " + payload)
    logger.debug("~~~~~~~~~~~~~~~~~~~~~~~\n\n")

    delta = json.loads(payload)["state"]
    delta_tv =delta.get("TV")

    if delta_tv:
        if delta_tv.get("power") > 0:
            # Infrared transmission
            cmd = "python3 irrp.py -p -g17 -f codes tv:pwr_on"
            subprocess.check_call(cmd.split())

            # delite delta
            payload = {"state":{"reported":{"TV":{"power":1}}}}
            deviceShadowHandler.shadowUpdate(json.dumps(payload),customShadowCallback_Update, 5)

        if delta_tv.get("volume_up") > 0:
            # Infrared transmission
            for i in range(delta_tv.get("volume_up")):
                cmd = "python3 irrp.py -p -g17 -f codes tv:vlm_up"
                subprocess.check_call(cmd.split())

            # delite delta
            payload = {"state":{"reported":{"TV":{"volume_up":delta_tv.get("volume_up")}}}}
            deviceShadowHandler.shadowUpdate(json.dumps(payload),customShadowCallback_Update, 5)

        if delta_tv.get("volume_down") > 0:
            # Infrared transmission
            for i in range(delta_tv.get("volume_down")):
                cmd = "python3 irrp.py -p -g17 -f codes tv:vlm_down"
                subprocess.check_call(cmd.split())

            # delite delta
            payload = {"state":{"reported":{"TV":{"volume_down":delta_tv.get("volume_up")}}}}
            deviceShadowHandler.shadowUpdate(json.dumps(payload),customShadowCallback_Update, 5)

    # reset reported-shadow
    payload = {"state":{"reported":{"TV":{"power":0,"volume_up":0,"volume_down":0}}}}
    deviceShadowHandler.shadowUpdate(json.dumps(payload),customShadowCallback_Update, 5)

# Connect to AWS IoT
myAWSIoTMQTTShadowClient.connect()
logger.debug('connect to shadow')

# Create a device shadow handler, use this to update and Delete shadow document
deviceShadowHandler = myAWSIoTMQTTShadowClient.createShadowHandlerWithName('RaspberryPi', True)

# Create message payload
payload = {"state":{"reported":{"TV":{"power":0,"volume_up":0,"volume_down":0}}}}

# Delete old Shadow
deviceShadowHandler.shadowDelete(customShadowCallback_Delete, 5)

# Create New Shadow
deviceShadowHandler.shadowUpdate(json.dumps(payload),customShadowCallback_Update, 5)

# Update curent shadow JSON doc
deviceShadowHandler.shadowRegisterDeltaCallback(customShadowCallback_DeltaUpdate)

while True:
    # try:
    #     deviceShadowHandler.shadowRegisterDeltaCallback(customShadowCallback_DeltaUpdate)
    # except AWSIoTExceptions.subscribeQueueDisabledException as e:
    #     print(type(e))
    #     pass
    time.sleep(1)
