#!/usr/bin/env python

import lzma
import math
import os
from urllib.request import urlopen, Request
#from urllib.request import urlopen, build_opener, install_opener
#from urllib.request import HTTPHandler, ProxyHandler, Request


foodgroup_dict = {}
foodgroup_list = []
food_list_per_group = {}
food_list = []
food_dict = {}
nutrient_list = []
nutrient_links = {}
nutrient_dict = {}
nutrient_sr_order = []
content_list = []
content_dict = {}
lsg_list = []
lsg_dict = {}
dri_list = []
dri_dict = {}
driperkg_list = []
driperkg_dict = {}

def init(data_dir, contest):
    global contest_url
    contest_url = contest
    load_food_groups(data_dir)
    load_food_desc(data_dir)
    load_nutr_def(data_dir)
    load_nutr_data(data_dir)
    load_lsg(data_dir)
    load_dri(data_dir)
    load_driperkg(data_dir)
    global dri_count
    dri_count = len(dri_dict.keys()) + len(driperkg_dict.keys())
    print("loaded")
    #install_opener(build_opener(ProxyHandler({})))

def load_food_groups(data_dir):
    fn = os.path.join(data_dir, 'food_groups.xz')
    with lzma.open(fn, 'rt', encoding='utf8') as inputfile:
        for l in inputfile:
            a = l.strip("\n\r").split('|')
            foodgroup_list.append(tuple(a))
            foodgroup_dict[a[0]] = a[1]
            food_list_per_group[a[0]] = []
    foodgroup_dict['version'] = "3"

def load_food_desc(data_dir):
    fn = os.path.join(data_dir, 'food_desc.xz')
    with lzma.open(fn, 'rt', encoding='utf8') as inputfile:
        for l in inputfile:
            a = l.strip("\n\r").split('|')
            food_dict[a[0]] = ((a[1], a[2]))
            food_list_per_group[a[1]].append((a[0], a[2]))
            food_list.append(tuple(a))

def load_nutr_def(data_dir):
    fn = os.path.join(data_dir, 'nutr_def.xz')
    with lzma.open(fn, 'rt', encoding='utf8') as inputfile:
        for l in inputfile:
            a = l.strip("\n\r").split('|')
            #nutrient_dict = {nutrient_no : (unit, abbr, desc, digits, sr_no)}
            nutrient_dict[int(a[0])] = ((a[1], a[2], a[3], int(a[4]), int(a[5])))
            #nutrient_list = [(sr_no, nutrient_no, unit, abbr, desc, digits, links)]
            nutrient_list.append((int(a[5]), int(a[0]), a[1], a[2], a[3], int(a[4])))
            if 6 < len(a): nutrient_links[a[3]] = a[6]
    nutrient_sr_order.extend(sorted(nutrient_list))
    nutrient_links["Minerals"] = '<a href="http://en.wikipedia.org/wiki/Dietary_mineral">Minerals</a>'
    nutrient_links["Vitamins"] = '<a href="http://en.wikipedia.org/wiki/Vitamins">Vitamins</a>'
    nutrient_links["Lipids"] = '<a href="http://en.wikipedia.org/wiki/Lipid">Lipids</a>'
    nutrient_links["Amino Acids"] = '<a href="http://en.wikipedia.org/wiki/Amino_acid">Amino Acids</a>'
    nutrient_links["version"] = '3'


def load_nutr_data(data_dir):
    fn = os.path.join(data_dir, 'nutr_data.xz')
    with lzma.open(fn, 'rt', encoding='utf8') as inputfile:
        for l in inputfile:
            a = l.strip("\n\r").split('|')
            ndbno = a[0]
            nutrient_no = int(a[1])
            amount = round(float(a[2]), nutrient_dict[nutrient_no][3])
            if a[0] not in content_dict.keys(): content_dict[a[0]] = {}
            content_dict[ndbno][nutrient_no] = amount
            content_list.append((ndbno, nutrient_no, amount))

def load_lsg(data_dir):
    fn = os.path.join(data_dir, 'lsg.txt')
    with open(fn, 'r', encoding='utf8') as inputfile:
        for l in inputfile:
            a = l.strip("\n\r").split('|')
            lsg_dict[a[0]] = (a[1])
            lsg_list.append(tuple(a))

def load_dri(data_dir):
    fn = os.path.join(data_dir, 'dri.txt')
    with open(fn, 'r', encoding='utf8') as inputfile:
        for l in inputfile:
            a = l.strip("\n\r").split('|')
            nutr_no = int(a[0])
            if nutr_no not in dri_dict.keys(): dri_dict[nutr_no] = []
            for i in range(2, 8):
                if a[i]: a[i] = float(a[i])
                else: a[i] = ""
            dri_dict[nutr_no].append((a[1], a[2], a[3], a[4], a[5], a[6], a[7]))
            dri_list.append((nutr_no, a[1], a[2], a[3], a[4], a[5], a[6], a[7]))

def load_driperkg(data_dir):
    fn = os.path.join(data_dir, 'driperkg.txt')
    with open(fn, 'r', encoding='utf8') as inputfile:
        for l in inputfile:
            a = l.strip("\n\r").split('|')
            nutr_no = int(a[0])
            if nutr_no not in driperkg_dict.keys():
                driperkg_dict[nutr_no] = []
            for i in range(2, 8):
                if a[i]: a[i] = float(a[i])
                else: a[i] = ""
            driperkg_dict[nutr_no].append((a[1], a[2], a[3], a[4], a[5], a[6], a[7]))
            driperkg_list.append((nutr_no, a[1], a[2], a[3], a[4], a[5], a[6], a[7]))


class Context(object):
    def __init__(self, lsg, age, weight, days=1):
        self.lsg = lsg
        self.age = age
        self.weight = weight
        self.days = days

def drival_to_str(c, val, price):
    percent = c / val
    if None != price and 0 != c:
        pv = price / percent * 100
        pv_str = str(round(pv, 2))
    else:
        pv = None
        pv_str = 'N/A'
    return (str(round(percent, 2)) + '%', pv_str, pv, percent)

def calc_dev(amount, dri):
    return math.exp(-abs(amount - dri) / dri)

def get_dri_values(amount, nutr_no, ctx, price):
    """
    returns DRI percentages for a nutrient, 
    life stage group, age, and weight
    multiplied by the number of days
    """
    ear_str, rda_str, ai_str, ul_str, pv_str = '', '', '', '', ''
    pv, dev, percent = None, None, None
    if nutr_no in dri_dict.keys():
        for ilsg, min_age, max_age, ear, rda, ai, ul in dri_dict[nutr_no]:
            if (ctx.lsg == ilsg and 
                min_age <= ctx.age and ctx.age < max_age): break
        c = amount / ctx.days * 100.0
        if ear: 
            ear_str = str(round(c / ear, 2)) + '%'
        if rda:
            rda_str, pv_str, pv, percent = drival_to_str(c, rda, price)
            dev = calc_dev(amount, rda * ctx.days)
        if ai: 
            ai_str, pv_str, pv, percent = drival_to_str(c, ai, price)
            dev = calc_dev(amount, ai * ctx.days)
        if ul:
            ul_str = str(round(c / ul, 2)) + '%'
    elif nutr_no in driperkg_dict.keys():
        for ilsg, min_age, max_age, ear, rda, ai, ul in driperkg_dict[nutr_no]:
            if (ctx.lsg == ilsg and 
                min_age <= ctx.age and ctx.age < max_age): break
        c = amount / (ctx.days * ctx.weight) * 100
        if ear: 
            ear_str = str(round(c / ear, 2)) + '%'
        if rda:
            rda_str, pv_str, pv, percent = drival_to_str(c, rda, price)
            dev = calc_dev(amount, rda * ctx.days * ctx.weight)
        if ai: 
            ai_str, pv_str, pv, percent = drival_to_str(c, ai, price)
            dev = calc_dev(amount, ai * ctx.days * ctx.weight)
        if ul:
            ul_str = str(round(c / ul, 2)) + '%'
    return (ear_str, rda_str, ai_str, ul_str, pv_str, pv, dev, percent)
    

content_section_limits = [(5000, 'Proximates'), (6300, 'Minerals'),
                          (9700, 'Vitamins'), (16000, 'Lipids'),
                          (18200, 'Amino Acids'), (20000, 'Others')]

def build_contents(context, nutrients):
    """
    builds a list of nutrient contents and DRI values
    context object is a Context class instance
    nutrients object must have a get_amount(nutr_no) method
    """
    contents = []
    section = 0
    current_section = []
    best_pv = float('inf')
    worst_pv = 0
    dev_sum = 0
    detail_dict = {k:[] for k in nutrients.keys}
    detail_list = []
    for sr_no, nutr_no, unit, abbr, desc, digits in nutrient_sr_order:
        applicable, amount, details = nutrients.get_amount(nutr_no)
        if applicable:
            (ear, rda, ai, ul,
             pvs, pv, dev, pc) = get_dri_values(amount, nutr_no, context, 
                                                nutrients.price)
            if pv:
                best_pv = min(pv, best_pv)
                worst_pv = max(pv, worst_pv)
            if dev:
                dev_sum += dev
            #print(nutr_no, pc, rda, ai)
            if pc:
                detail_list.append(nutrient_dict[nutr_no][2])
                for k in nutrients.keys:
                    if k in details:
                        detail_dict[k].append(pc*details[k]/amount)
                    else:
                        detail_dict[k].append(0)
            amount = round(amount, 3)
            if content_section_limits[section][0] <= sr_no:
                contents.append({'title' : content_section_limits[section][1],
                                 'data' : current_section})
                current_section = []
                while content_section_limits[section][0] <= sr_no: section += 1
        else: amount, ear, rda, ai, ul, pvs = 'N/A', '', '', '', '', ''
        current_section.append({'amount':amount, 'unit':unit, 'desc':desc,
                                'ear':ear, 'rda':rda, 'ai':ai, 
                                'ul':ul, 'pv':pvs})
    print('detail_list:', detail_list)
    print('detail_dict:', detail_dict)
    print('nutrients.keys', nutrients.keys)
    detail_data = [{ 'data': detail_dict[k], 'name': nutrients.get_name(k)} 
                   for k in nutrients.keys]
    contents.append({'title' : content_section_limits[section][1],
                     'data' : current_section})
    score = dev_sum / dri_count * 10
    return (contents, str(round(best_pv, 2)), str(round(worst_pv, 2)),
            str(round(score, 2)), detail_list, detail_data)

class FoodNutrients(object):
    """
    provides nutrient amounts of a food item
    """
    def __init__(self, ndbno):
        self.nutrients = content_dict[ndbno]
        self.price = None
        self.keys = [ndbno]
        self.ndbno = ndbno
    def get_amount(self, nutr_no):
        """returns (applicable, amount)"""
        if nutr_no in self.nutrients.keys():
            nutrient_amount = self.nutrients[nutr_no]
            return (True, nutrient_amount, { self.ndbno: nutrient_amount })
        else:
            return (False, 0, {})
    def get_name(self, key):
        return food_dict[key][1]

def get_food_contents(ndbno, lsg, age, weight):
    """
    returns a list of (value, unit, description, EAR, RDA, AI, UL, PV=None)
    tuples for the given ndbno (food item)
    """
    context = Context(lsg, float(age), float(weight))
    nutrients = FoodNutrients(ndbno)
    contents, bpv, wpv, score, dl, details = build_contents(context, nutrients)
    return { 'contents': contents, 'bpv': bpv, 'wpv': wpv, 'score': score }

class ProductNutrients(object):
    """
    provides nutrient amounts of a product
    """
    def __init__(self, product):
        self.ingredients = product['ingredients'].values()
        self.price = float(product['price'])
        self.keys = [ingredient['ndbno'] for ingredient in self.ingredients]
        self.amounts = {ingredient['ndbno']:ingredient['amount'] 
                        for ingredient in self.ingredients}
    def get_amount(self, nutr_no):
        """returns (applicable, amount)"""
        applicable = False
        amount = 0
        details = {}
        for ingredient in self.ingredients:
            ingredient_ndbno = ingredient['ndbno']
            nutrients = content_dict[ingredient_ndbno]
            if nutr_no not in nutrients.keys(): continue
            applicable = True
            nutrient_amount = nutrients[nutr_no] * float(ingredient['amount']) * 0.01
            details[ingredient_ndbno] = nutrient_amount
            amount += nutrient_amount
        return (applicable, amount, details)
    def get_name(self, key):
        return self.amounts[key] + 'g ' + food_dict[key][1]

def get_product_contents(lsg, age, weight, product):
    """
    returns a list of (value, unit, description, EAR, RDA, AI, UL, PV=None)
    tuples for the given ndbno (food item)
    """
    context = Context(lsg, float(age), float(weight))
    nutrients = ProductNutrients(product)
    contents, bpv, wpv, score, dl, details = build_contents(context, nutrients)
    return { 'product_id': product['id'], 'contents': contents,
             'bpv': bpv, 'wpv': wpv, 'score': score, 
             'categories':dl, 'series': details }

class PlanNutrients(object):
    """
    provides nutrient amounts of a product
    """
    def __init__(self, plan):
        self.plan = plan
        self.price = 0
        self.keys = []
        self.quantities = {}
        for product in self.plan['products']:
            print('product:', product)
            quantity = product['quantity']
            name = product['name']
            self.price += float(product['price']) * float(quantity)
            self.keys.append(name)
            self.quantities[name] = quantity
    def get_amount(self, nutr_no):
        """returns (applicable, amount)"""
        applicable = False
        amount = 0
        details = {}
        for product in self.plan['products']:
            quantity = float(product['quantity'])
            product_amount = 0
            for ingredient in product['ingredients']:
                nutrients = content_dict[ingredient['ndbno']]
                if nutr_no not in nutrients.keys(): continue
                applicable = True
                m = quantity  * float(ingredient['amount']) * 0.01
                product_amount = nutrients[nutr_no] * m
                amount += product_amount
            details[product['name']] = product_amount
        return (applicable, amount, details)
    def get_name(self, key):
        return self.quantities[key] + ' ' + key

def get_plan_contents(lsg, age, weight, plan):
    """
    returns a list of (value, unit, description, EAR, RDA, AI, UL, PV=None)
    tuples for the given ndbno (food item)
    """
    context = Context(lsg, float(age), float(weight), float(plan['days']))
    nutrients = PlanNutrients(plan)
    contents, bpv, wpv, score, dl, details = build_contents(context, nutrients)
    return { 'contents': contents, 'bpv': bpv, 'wpv': wpv, 'score': score, 
             'categories':dl, 'series': details }

def get_contents(kind, args):
    """
    provides a list of nutrient contents for
    a food, a product, or a plan
    """
    print(kind, args)
    if kind == 'food_contents': return get_food_contents(**args)
    elif kind == 'product_contents': return get_product_contents(**args)
    elif kind == 'plan_contents': return get_plan_contents(**args)

def submit_plan(data):
    request = Request(contest_url, data.encode('UTF-8'))
    request.add_header('Content-Type', 'application/json;charset=utf-8')
    return urlopen(request).readall().decode()


