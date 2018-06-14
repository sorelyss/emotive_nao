from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import qi
import argparse
import sys
import os

import cv2
import numpy as np
import tensorflow as tf

from im2txt import configuration
from im2txt import inference_wrapper
from im2txt.inference_utils import caption_generator
from im2txt.inference_utils import vocabulary

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Choose the trained model path
model_path = "./im2txt_2/model/train/model.ckpt-3000000"
vocab_path = "./im2txt_2/data/mscoco/word_counts3.txt"
#tf.logging.set_verbosity(tf.logging.INFO)

# Build the inference graph.
g = tf.Graph()
with g.as_default():
    model = inference_wrapper.InferenceWrapper()
    restore_fn = model.build_graph_from_config(configuration.ModelConfig(), model_path)
g.finalize()

# Create the vocabulary.
vocab = vocabulary.Vocabulary(vocab_path) 

sess = tf.Session(graph=g)
# Load the model from checkpoint.
restore_fn(sess)

# Prepare the caption generator. Here we are implicitly using the default
# beam search parameters. See caption_generator.py for a description of the
# available beam search parameters.
generator = caption_generator.CaptionGenerator(model, vocab)

class ImageModule:
    """Handles the image adquirement and processing"""
    def __init__(self, session):
        self.session = session
        self.video_service = session.service("ALVideoDevice")
        resolution = 4; colorSpace = 11; fps = 30;
        self.nameId = self.video_service.subscribe("python_GVM", resolution, colorSpace, fps)

    def getImage(self):
        naoImage = self.video_service.getImageRemote(self.nameId)
        w = naoImage[0]; h = naoImage[1]; nb_planes = naoImage[2]
        return np.frombuffer(naoImage[6], np.uint8).reshape(h, w, nb_planes)

    def image_processing(self, image, warp_image_path = './images/image.jpg'):
        orig = image.copy()
        (h, w) = image.shape[:2]
        ratio = h / 300.0
        w = int(w * 1/ratio)
        image = cv2.resize(image, (w,300), interpolation = cv2.INTER_AREA)
        img_HSV = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        redLower = (0,41,120)
        redUpper = (14,255,255)
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.inRange(img_HSV, redLower, redUpper)
        mask = cv2.erode(mask, kernel, iterations=1)
        kernel = np.ones((9, 9), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=1)
        cv2.imwrite('./images/imageMask.jpg', mask)
        (cnts, _) = cv2.findContours(mask.astype(np.uint8).copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        cnts = sorted(cnts, key = cv2.contourArea, reverse = True)[:10]
        screenCnt = None
        # loop over our contours
        for i,c in enumerate(cnts):
            # approximate the contour
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)

            # if our approximated contour has four points, then
            # we can assume that we have found our screen
            if len(approx) == 8:
                screenCnt = approx[:4]
                #print("countour 8pts index", i)
                break
            elif len(approx) == 4:
                screenCnt = approx
                #print("countour 4pts index", i)
                break
        try:
            if screenCnt is not None:
                pts = screenCnt.reshape(4, 2)
                rect = np.zeros((4, 2), dtype = "float32")

                s = pts.sum(axis = 1)
                rect[0] = pts[np.argmin(s)]
                rect[2] = pts[np.argmax(s)]

                diff = np.diff(pts, axis = 1)
                rect[1] = pts[np.argmin(diff)]
                rect[3] = pts[np.argmax(diff)]

                rect *= ratio
                (tl, tr, br, bl) = rect
                widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
                widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
                heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
                heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
                maxWidth = max(int(widthA), int(widthB))
                maxHeight = max(int(heightA), int(heightB))

                dst = np.array([
                [0, 0],
                [maxWidth - 1, 0],
                [maxWidth - 1, maxHeight - 1],
                [0, maxHeight - 1]], dtype = "float32")

                M = cv2.getPerspectiveTransform(rect, dst)
                warp = cv2.warpPerspective(orig, M, (maxWidth, maxHeight))
                if maxHeight>12 and maxWidth>12:
                    warp = warp[10:maxHeight-11, 10:maxWidth-11]                
                #warp = cv2.cvtColor(warp, cv2.COLOR_BGR2RGB)
                cv2.imwrite(warp_image_path, warp)
                return True
            else:
                return False
        except KeyboardInterrupt:
            sys.exit(1)
            self.log_out()
        except Exception as e:
            print("Excepcion findRectangle:", e)
            sys.exit(1)
            return False

    def getCaption(self):
        #bandera = True es que no ha encontrado rectangulo
        image = self.getImage()
        cv2.imwrite('./images/imageC.jpg', cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        rectangleFound = self.image_processing(cv2.imread('./images/imageC.jpg'))
        if rectangleFound:
            return self.captioner(open('./images/image.jpg').read())
        else:
            #print('rectangle not found')
            return ''


    def captioner(self, image):
        captions = generator.beam_search(sess, image)
        caption = captions[0]
        # Ignore begin and end words.
        sentence = [vocab.id_to_word(w) for w in caption.sentence[1:-1]]
        sentence = " ".join(sentence)
        #print("  %d) %s (p=%f)" % (0, sentence, np.exp(caption.logprob)))
        return sentence

    def log_out(self):
        if self.nameId != "":
            self.video_service.unsubscribe(self.nameId)
            print('image module exit')


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default="127.0.0.1",
                        help="Robot IP address. On robot or Local Naoqi: use '127.0.0.1'.")
    parser.add_argument("--port", type=int, default=9559,
                        help="Naoqi port number")

    args = parser.parse_args()
    #session = qi.Session()

    

                

