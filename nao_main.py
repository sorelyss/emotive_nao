# -*- coding: utf-8 -*-

import time
import threading
import qi
import argparse
import sys
import json
import unicodedata
import random
import requests

from image_module import ImageModule
from behaviors_module import BehaviorsModule
import sentiment_module as emotion_mod

import warnings
warnings.filterwarnings('ignore')

E_image = ''
E_audio = ''
time_beha = 6
time_dupla = 10

def getImageEmotion():
    global E_image
    sentence = img_mod.getCaption()
    if not sentence=='':
        E_image, _ = emotion_mod.text2emotion(sentence, 'en')
        print '*image text: '+sentence

def getAudioEmotion():
    global E_audio
    time.sleep(time_out-0.5)
    url = 'http://'+IP_DICTATION+'/dictation/audio.json'
    headers = {'content-Type': 'application/json'}
    try:
        audio_file = requests.get(url, headers=headers).json()
    except:
        audio_file = requests.get(url, headers=headers).json()
    mensaje = unicodedata.normalize('NFD', audio_file['message']).encode('ascii', 'ignore')
    print '*audio text: '+ mensaje
    mensaje = audio_file['message']
    if not mensaje == '':
        E_audio, _ = emotion_mod.text2emotion(mensaje, 'es')


def main():
    global E_audio, E_image, time_out, duracion_total
    # default states of variables
    time_out = 4
    start = time.time()
    behavior_mod.stopAllBehaviors()
    
    E_audio = 'anticipation'
    E_image = 'trust'
    t1= threading.Thread(target=getImageEmotion)
    t2= threading.Thread(target=getAudioEmotion)

    indice = str(random.randint(1,26))
    behavior_mod.launchBehavior("com_base_"+indice)
    t2.start()
    t1.start()

    t1.join(time_out)
    t2.join(time_out)

    behavior_mod.stopAllBehaviors()
    behavior, expression = behavior_mod.getBehavior(E_audio, E_image)
    print '**Emotions: ' +  E_audio + ' and ' + E_image
    duracion_total = time.time() - start
    behavior_mod.launchBehavior(behavior, expression)
    print("Termino y tardo:", duracion_total)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default="127.0.0.1",
                        help="Robot IP address. On robot or Local Naoqi: use '127.0.0.1'.")
    parser.add_argument("--port", type=int, default=9559,
                        help="Naoqi port number")
    parser.add_argument("--beha_name", type=str, default="comportamientos",
                        help="Behavior name")
    parser.add_argument("--ip_dictation", type=str, default="192.168.1.122",
                        help="PC IP where Dictation is running")

    args = parser.parse_args()
    session = qi.Session()
    try:
        session.connect("tcp://" + args.ip + ":" + str(args.port))
    except RuntimeError:
        print ("Can't connect to Naoqi at ip \"" + args.ip + "\" on port " + str(args.port) +".\n"
               "Please check your script arguments.")
        sys.exit(1)

    BEHA_NAME = args.beha_name
    IP_DICTATION = args.ip_dictation

    img_mod = ImageModule(session)
    sentence = img_mod.getCaption()
    behavior_mod = BehaviorsModule(session, BEHA_NAME)
    print('---- Ya puede iniciar ----')
    while True:
        try:
            url = 'http://'+IP_DICTATION+'/dictation/main.json'
            headers = {'content-Type': 'application/json'}
            main_file = requests.get(url, headers=headers).json()
            if main_file['flag']:
                break
        except KeyboardInterrupt:
            sys.exit(1)
        except Exception as e:
            print("Excepcion main thread",e)

    num_dupla = int(main_file['n'])
    time_dupla = int(main_file['t'])
    for i in range(0,num_dupla):
        url = 'http://'+IP_DICTATION+'/dictation/main.json'
        headers = {'content-Type': 'application/json'}
        main_file = requests.get(url, headers=headers).json()
        if main_file['flag'] == False:
            print('Detenido desde la interfaz....')
            img_mod.log_out()
            break
        main()
        waiting_time = time_dupla - duracion_total
        if waiting_time <= 0:
            waiting_time = 0
        else:
            time.sleep(2)
            behavior_mod.stopAllBehaviors()
            behavior_mod.standRobot()
            waiting_time -=2
            pass
        if i<num_dupla-1:
            print('--------------- Esperando '+str(waiting_time)+' segs -------------')
            time.sleep(waiting_time)
    img_mod.log_out()
