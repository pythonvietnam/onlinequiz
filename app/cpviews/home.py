# -*- coding: UTF-8 -*-
from flask import request
from app import mongo, images, app
from model import *
from bson.objectid import ObjectId
from os import remove

class HomePage(Page):
    def __init__(self):
        self.link = 'home'
        self.name = u'Quản lý chung'
        self.catalogues = [('report', u'Thống kê'),
                           ('system', u'Hệ thống'),
						   ('rank', u'Xếp hạng')]
    
    def context(self):
        cata = request.args.get('c', '')
        result = {'notify': ''}
        if cata == 'report':
            result['countuser'] = mongo.db.users.find({'level': 'Thí sinh'}).count()
            result['countassignment'] = mongo.db.assignments.find().count()
            result['countquestion'] = mongo.db.quesbank.find().count()
            result['countexam'] = mongo.db.exams.find().count()
            result['countquespackage'] = mongo.db.quespackages.find().count()
            result['countnews'] = mongo.db.news.find({'topic': u'Tin tức'}).count()
            result['countguide'] = mongo.db.news.find({'topic': u'Hướng dẫn'}).count()
            return result
        elif cata == 'system':
            if request.method == 'POST':
                mongo.db.general.update({"catalog": "result"}, {"$set": {"result_on": request.form['result_on']}})
            result['result_on'] = mongo.db.general.find_one({'catalog': 'result'})['result_on']
            return result
        elif cata == 'rank':
            if request.method == 'POST':
                def id_to_fullname(id):
                    return mongo.db.users.find_one({'username': id}, {'fullname': 1})['fullname']
                result['assignments'] = mongo.db.assignments.find({'exam_link': request.form['exam']}).sort(
                                                [('point', -1), ('completed_time', 1)])
                result['id_to_fullname'] = id_to_fullname
                result['exam_link'] = request.form['exam']
            exams = mongo.db.exams.find()
            result['exams'] = exams
            return result
        else:
            result['show'] = u"Hệ thống quản trị"
            return result
