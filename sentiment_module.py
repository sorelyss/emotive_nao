#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
import numpy as np
import matplotlib.pyplot as plt
from pattern.es import parse, split

from sentiment.sentiment_term import anew_word as english
from sentiment.diccionario import spanish as spanish

lemmaDict = {}
with open('sentiment/lemmatization-es.txt', 'rb') as f:
    data = f.read().decode('utf8').replace(u'\r', u'').split(u'\n')
    data = [a.split(u'\t') for a in data]

for word in data:
    if len(word) >1:
        lemmaDict[word[1]] = word[0]

def lemmatize(word):
    return lemmaDict.get(word, word)

PosNeg_adverbs = {u'muy': 1, u'mucho': 1, u'poco':-1, u'mucha': 1,
                  u'carente':-1, u'demasiado':-2, u'exceso':-2}
not_adverbs = {u'no': 1, u'nada': 1, u'No': 1, u'Nada':1}
nouns =[u'felicidad', u'alegría', u'bienestar', u'suerte', u'prosperidad', u'conteto', u'satisfacción', u'rabia',
        u'coraje', u'cólera', u'enojo', u'ira', u'furia', u'irritación', u'odio', u'resentimiento', u'rencor',
        u'tristeza', u'desconsuelo', u'aflicción', u'amargura', u'melancolía', u'pesar', u'nostalgia',
        u'desdicha', u'sorpresa', u'asombro', u'conmoción', u'susto', u'sobresalto', u'exclamación', 
        u'disgusto', u'enfado', u'amargura', u'pesadumbre', u'miedo', u'temor', u'terror', u'pavor', 
        u'pánico', u'espanto', u'horror', u'desconfianza', u'ayuda', u'calma', u'anticipación', u'anticipo', 
        u'iniciativa', u'confianza', u'seguridad', u'tranquilidad']

def similar_if_necesary(word, dictionary = spanish):
    if isinstance(word, str):
        word = unicode(word, "utf-8")
    exist = word in dictionary
    if not exist:
        word = lemmatize(word)
        exist = word in dictionary
    return exist, word

def getProbability(std_value):
    if std_value == 0:
        p = 1.0
    else:
        p = 1.0 / np.sqrt( 2.0 * np.pi * np.power(std_value, 2.0) )
    return p

def getPoint(sentence, dictionary = spanish):
    wi = []; p_v = []; p_a = []; mu_a = []; mu_v = []
    v_final = 0; a_final = 0;
    inv_exist = False
    sentence = split(parse(sentence))[0]
    for word in sentence:
        exist, word_str = similar_if_necesary(word.string, dictionary)
        if word.pos == 'RB':
            inv_exist = inv_exist or similar_if_necesary(word.string, not_adverbs)[0]
            
        if exist:
            res = dictionary.get(word_str)
            a = [res['avg'][1], res['std'][1]]
            v = [res['avg'][0], res['std'][0]]
            
            if (a[0]>4.5 and a[0]<5.5) and (v[0]>4.5 and v[0]<5.88): # Palabras neutrales con menos peso
                n_rb = -1
            else:
                n_rb = 1
            
            noun_exist = similar_if_necesary(word.string, nouns)[0]
            if word.pos == 'JJ' or noun_exist:
                quantities = [PosNeg_adverbs.get(x.string, 0) for x in word.chunk.words if x.tag=='RB'] 
                if np.sum(np.abs(quantities))>0:
                    sign = np.product( quantities/np.abs(quantities) )
                else:
                    sign = 1
                n_rb = sign * ( 2 + np.sum(np.abs(quantities)) )
            wi.append(float(n_rb))
            p_v.append(getProbability(v[1]))
            p_a.append(getProbability(a[1]))
            mu_v.append(v[0])
            mu_a.append(a[0])
    if len(wi)>0: 
        if np.min(wi)<0: # Esto hace los negativos con menor peso versus los w = 1
            wi = wi + abs(np.min(wi)) + 1

        alpha1 = p_v/np.sum(p_v)  # Solo tiene en cuenta desviacion
        alpha2 = np.multiply(wi, p_v)/np.sum(np.multiply(wi, p_v))
        alpha3 = (wi + np.transpose(p_v))/np.sum(wi + p_v)
        v_final = np.sum(alpha2 * mu_v)
        a_final = np.sum(alpha2 * mu_a)
    return (v_final, a_final), inv_exist


inverted_emotions = {'joy': 'sadness','trust': 'disgust', 'fear': 'anger','surprise': 'anticipation', 
                     'sadness': 'joy','disgust': 'trust', 'anger': 'fear','anticipation': 'surprise'}

emotions = {(7.4, 7): 'joy', 
    (7.4, 5.4): 'joy', 
    (7, 3): 'trust', 
    (4.3, 5.8): 'fear', 
    (3.5, 7.8): 'fear', 
    (6, 7.5): 'surprise', 
    (2.5, 4): 'sadness', 
    (3, 6.5): 'disgust', 
    (2.8, 7.5): 'anger', 
    (6.8, 4): 'anticipation'}
em_points = np.array(emotions.keys())

def text2emotion(texto, lang='es'):
    if lang == 'en':
        dictionary = english
    else:
        dictionary = spanish
    punto, invertir = getPoint(texto, dictionary)
    diff = em_points - punto
    index = np.argmin(np.sqrt(np.sum(np.power(diff,2), axis=1)))
    emotion = emotions[tuple(em_points[index])]
    if invertir:
        emotion = inverted_emotions[emotion]
    return emotion, punto


def plotRussell(puntos, textos=''):
    c = plt.Circle((5, 5), 4, color='blue', linewidth=1, fill=False)
    fig, ax = plt.subplots(1, 1)
    ax.set_aspect('equal')
    ax.add_patch(c)
    plt.xlim(1,9)
    plt.ylim(1,9)

    x, y = em_points.T
    plt.scatter(x,y)
    for i, label in enumerate(emotions.values()):
        ax.annotate(label,(x[i],y[i]))
    if not isinstance(puntos, list):
        puntos = [puntos]
        textos = [textos]
    for i,punto in enumerate(puntos):
        plt.scatter(*punto, color='red')
        ax.annotate(textos[i],punto, color='red')
    plt.show()
