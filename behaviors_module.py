#! /usr/bin/env python
# -*- encoding: UTF-8 -*-
import qi
import argparse
import sys
import random

emotions = ['anger','disgust','fear','sadness','surprise','anticipation','trust','joy']
behaviors = ['enojarse','aburrirse', 'aterrarse', 'entristecerse', 'sorprenderse', 'p.atencion', 'aceptar', 'alegrarse'] 

class BehaviorsModule:
    def __init__(self, session, beha_name=".lastUploadedChoregrapheBehavior"):
        self.session = session
        self.behavior_mng_service = session.service("ALBehaviorManager")
        self.beha_name = beha_name + '/'
        self.tts = session.service("ALTextToSpeech")
        self.tts.setLanguage("Spanish")

    def launchBehavior(self, name_of_behavior, expression=''):
        behavior_name = self.beha_name + name_of_behavior
        if (self.behavior_mng_service.isBehaviorInstalled(behavior_name)):
            # Check that it is not already running.
            if (not self.behavior_mng_service.isBehaviorRunning(behavior_name)):
                self.behavior_mng_service.runBehavior(behavior_name, _async=True)
                self.tts.say(expression)
                print '***Corriendo ' + behavior_name
            else:
                print "Behavior is already running."
        else:
            print "Behavior not found."

    def standRobot(self):
        self.launchBehavior('start_parado')

    def stopBehavior(self, behavior_name):
        if (self.behavior_mng_service.isBehaviorRunning(behavior_name)):
            self.behavior_mng_service.stopBehavior(behavior_name)
            print('Stopped behavior: '+behavior_name)
        else:
            print "Behavior is already stopped."

    def stopAllBehaviors(self):
        self.behavior_mng_service.stopAllBehaviors()

    def getAllBehaviors(self):
        return self.behavior_mng_service.getInstalledBehaviors()
    
    def getRunningBehaviors(self):
        return self.behavior_mng_service.getRunningBehaviors()

    def getBehavior(self,E1,E2):
        indice_E1 = emotions.index(E1)
        if (emotions.index(E2)>3):
            posibles = [3, 9, 2, 5, 2, 1, 2, 5]
            expresions = [['NO NO NO','Eso me enfada','Me sacas de quicio'], ['jum no es muy interesante eso que cuentas','Soy indiferente a esta parte de la historia','Que aburrido estoy'], ['Que fue eso','Que Que','Que fue ese ruido'], [''], [''],['Que interesante','Cautivador','Cuentame mas'],['Si, claro que si',' Si Si Si','Si, estoy de acuerdo'],['Me encanta, wiii','Maravilloso, me encanto eso','Esta es la mejor parte de la historia']]
            polaridad = '_pos_' + str(random.randint(1,posibles[indice_E1]))
        else:
            posibles = [3, 1, 1, 2, 3, 4, 1, 4]
            expresions = [[''], ['Eso no fue agradable','Desapruebo ese comentario','Este tipo de cosas me molestan'], ['Noooo, no quiero ver','Quitalo quietalo quitalo','No me muestres cosas como esa'], [''], [''],[''],['Esto no puede ser pero toca aceptarlo','Bueno esta bien','Por que?'],['']]
            polaridad = '_neg_' + str(random.randint(1,posibles[indice_E1]))
        expression = random.choice(expresions[indice_E1])
        return (behaviors[indice_E1]+polaridad, expression)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default="127.0.0.1",
                        help="Robot IP address. On robot or Local Naoqi: use '127.0.0.1'.")
    parser.add_argument("--port", type=int, default=9559,
                        help="Naoqi port number")
    parser.add_argument("--beha_name", type=str, default="prueba", required=True,
                        help="Name of the behavior")
    
    args = parser.parse_args()
    session = qi.Session()
    try:
        session.connect("tcp://" + args.ip + ":" + str(args.port))
    except RuntimeError:
        print ("Can't connect to Naoqi at ip \"" + args.ip + "\" on port " + str(args.port) +".\n"
               "Please check your script arguments. Run with -h option for help.")
        sys.exit(1)

    print("Nuevo comportamiento cargado - " + args.beha_name)
    main(session, ".lastUploadedChoregrapheBehavior/" + args.beha_name)