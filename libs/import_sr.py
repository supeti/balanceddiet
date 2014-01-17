#!/usr/bin/env python

import lzma
import os

tt = str.maketrans('', '', "~\n")

with open('FD_GROUP.txt', 'r', encoding='iso-8859-1') as inputfile:
    with lzma.open('food_groups.xz', 'wt', encoding='utf8') as outputfile:
        for l in inputfile:
            a = l.translate(tt).split('^')
            outputfile.write(a[0] + '|' + a[1] + "\n")

with open('FOOD_DES.txt', 'r', encoding='iso-8859-1') as inputfile:
    with lzma.open('food_desc.xz', 'wt', encoding='utf8') as outputfile:
        for l in inputfile:
            a = l.translate(tt).split('^')
            outputfile.write(a[0] + '|' + a[1] + '|' + a[2] + "\n")

nutr_links = {}
with lzma.open('nutr_def.xz', 'rt', encoding='utf8') as inputfile:
    for l in inputfile:
        a = l.strip("\n\r").split('|')
        if len(a) == 7:
            nutr_links[a[0]] = a[6]

with open('NUTR_DEF.txt', 'r', encoding='iso-8859-1') as inputfile:
    with lzma.open('nutr_def.xz', 'wt', encoding='utf8') as outputfile:
        for l in inputfile:
            a = l.translate(tt).split('^')
            if a[0] in nutr_links.keys():
                outputfile.write('|'.join(a) + '|' + nutr_links[a[0]] + "\n")
            else:
                print("new nutrient: " + l.strip("\n\r"))
                outputfile.write('|'.join(a) + "\n")
        outputfile.write('531|g|MET_CYS_G|Methionine+Cystine|3|16790|<a href="http://en.wikipedia.org/wiki/Methionine">Methionine</a> + <a href="http://en.wikipedia.org/wiki/Cysteine">Cystine</a>\n')
        outputfile.write('532|g|PHE_TYR_G|Phenylalanine+Tyrosine|3|16990|<a href="http://en.wikipedia.org/wiki/Phenylalanine">Phenylalanine</a> + <a href="http://en.wikipedia.org/wiki/Tyrosine">Tyrosine</a>\n')

amino_sums = {}
with open('NUT_DATA.txt', 'r', encoding='iso-8859-1') as inputfile:
    with lzma.open('nutr_data.xz', 'wt', encoding='utf8') as outputfile:
        for l in inputfile:
            a = l.translate(tt).split('^')
            food = a[0]
            nutrient = a[1]
            amount = a[2]
            outputfile.write(food + '|' + nutrient + '|' + amount + "\n")
            if nutrient == '506' or nutrient == '507':
                if food not in amino_sums.keys(): amino_sums[food] = {}
                asf = amino_sums[food]
                if '531' not in asf.keys():
                    asf['531'] = float(amount)
                else: asf['531'] += float(amount)
            if nutrient == '508' or nutrient == '509':
                if food not in amino_sums.keys(): amino_sums[food] = {}
                asf = amino_sums[food]
                if '532' not in asf.keys():
                    asf['532'] = float(amount)
                else: asf['532'] += float(amount)
        foods = list(amino_sums.keys())
        foods.sort()
        for food in foods:
            if '531' in amino_sums[food]:
                outputfile.write(food + '|531|' + str(amino_sums[food]['531']) + "\n")
            if '532' in amino_sums[food]:
                outputfile.write(food + '|532|' + str(amino_sums[food]['532']) + "\n")

