# -*- coding: UTF-8 -*-
from flask import request
from app import mongo
from model import *
from random import random, randint
from bson.objectid import ObjectId

def insert_quespackage(name):
    if name.strip() != '':
        random_loop = 100 # Tránh tạo vòng lặp vô hạn
        code = "%04d" % randint(0,9999)
        while mongo.db.quespackages.find_one({"code": code}):
            code = "%04d" % randint(0,9999)
            random_loop -= 1
            if random_loop == 1:
                return "Error Create Question Package: " + unicode(name) + u' -- Lỗi vòng lặp, vui lòng thử lại'
        quespackage = {"code": code, "name": name}
        mongo.db.quespackages.insert(quespackage)
        return "Created Question Package: " + unicode(name)
    else:
        return "Error Create Question Package: " + unicode(name) + u' -- Bạn biểu mẫu sai quy định'

def update_quespackage(packagecode, packagename):
    name = mongo.db.quespackages.find_one({"code": packagecode}, {'name': 1})['name']
    if packagename.strip() != '':
        mongo.db.quespackages.update({"code": packagecode},
                               {'$set': 
                                    {'name': packagename}
                               })
        return "Edited Question Package: " + unicode(name) + ' --> ' + unicode(packagename)
    else:
        return "Error Edit Question Package: " + unicode(packagename) + u' -- Tên không được để trống'
        
def remove_quespackage(code):
    """ Xóa Gói câu hỏi và các câu hỏi trong nó"""
    name = mongo.db.quespackages.find_one({'code': code}, {'name': 1})['name']
    if mongo.db.exams.find({'quespackage': code}).count() > 0:
        return "Error Remove Question Package: " + unicode(name) + u' -- Hiện đang có kì thi đang sử dụng gói câu hỏi này. Bạn phải xóa kì thi trước'
    else:
        mongo.db.quespackages.remove({'code': code})
        ques_removed = mongo.db.quesbank.remove({'quespackage': code})
        return "Removed Question Package: " + unicode(name) + ' -- ' + unicode(ques_removed)

def insert_question(request_form):
    quespackage = request_form['quespackage']
    question_content = request_form['question_content'].strip()
    
    answer_content = []
    for i in range(1, int(request_form['number_answer']) + 1):
        if request_form[('answer_content' + str(i))] != '' and request_form['answer_value' + str(i)] == '':
            return "Error Create Question: " + unicode(question_content) + u' -- Bạn không được để trống đáp án Đúng/Sai'
        elif request_form[('answer_content' + str(i))] != '' and request_form['answer_value' + str(i)] != '':
            answer_content.append([request_form['answer_content' + str(i)], request_form['answer_value' + str(i)] == u"Đúng"])
    
    if len(answer_content) < 2:
        return "Error Create Question: " + unicode(question_content) + u' -- Câu hỏi phải có ít nhất 2 đáp án'
    
    if [i[1] for i in answer_content].count(True) == 0:
        return "Error Create Question: " + unicode(question_content) + u' -- Phải có ít nhất 1 đáp án đúng'
    elif [i[1] for i in answer_content].count(True) == 1:
        types = "radio"
    else:
        types = "checkbox"

    random_point = [random(), 0]
    while mongo.db.quesbank.find_one({'random_point': random_point}):
        random_point = [random(), 0]
        
    shuffle = (request_form['shuffle'] == u"Có")
    
    if mongo.db.quesbank.find_one({'question_content': question_content, 'quespackage': quespackage}):
        return "Error Create Question: " + unicode(question_content) + u' -- Câu hỏi đã tồn tại'
    elif (question_content != '' and quespackage != ''):
        # Thêm câu hỏi vào quesbank
        mongo.db.quesbank.insert({"question_content": question_content, 
                            "answer_content": answer_content, 
                            "quespackage": quespackage, 
                            "random_point": random_point, 
                            "type": types,
                            "shuffle": shuffle})
        return "Created Question: " + unicode(question_content)
    else:
        return "Error Create Question: " + unicode(question_content) + u' -- Bạn phải điền đầy đủ các mục'
        
def update_question(id, request_form):
    question_content = mongo.db.quesbank.find_one({"_id": ObjectId(id)}, {'question_content': 1})['question_content']
    current_quespackage = mongo.db.quesbank.find_one({"_id": ObjectId(id)}, {'quespackage': 1})['quespackage']
    
    answer_content = []
    for i in range(1, int(request_form['number_answer']) + 1):
        if request_form[('answer_content' + str(i))] != '' and request_form['answer_value' + str(i)] == '':
            return "Error Create Question: " + unicode(question_content) + u' -- Bạn không được để trống đáp án Đúng/Sai'
        elif request_form[('answer_content' + str(i))] != '' and request_form['answer_value' + str(i)] != '':
            answer_content.append([request_form['answer_content' + str(i)], request_form['answer_value' + str(i)] == u"Đúng"])
    
    if len(answer_content) < 2:
        return "Error Create Question: " + unicode(question_content) + u' -- Câu hỏi phải có ít nhất 2 đáp án'
    
    if [i[1] for i in answer_content].count(True) == 0:
        return "Error Create Question: " + unicode(question_content) + u' -- Phải có ít nhất 1 đáp án đúng'
    elif [i[1] for i in answer_content].count(True) == 1:
        types = "radio"
    else:
        types = "checkbox"
    
    using = False
    exams = mongo.db.exams.find({'quespackage': current_quespackage}, {'link': 1})
    for exam in exams:
        if mongo.db.assignments.find({'exam_link': exam['link']}).count() > 0:
            using = True
    
    if current_quespackage == request_form['quespackage'] and using:
        return "Error Edit Question: " + unicode(question_content) + u' -- Hiện đang có bài thi đang sử dụng câu hỏi này, bạn không thể sửa câu hỏi!'
    if current_quespackage != request_form['quespackage'] and mongo.db.exams.find({'quespackage': current_quespackage}).count() > 0:
        return "Error Edit Question: " + unicode(question_content) + u' -- Hiện đang có kì thi đang sử dụng câu hỏi này, bạn không thể chuyển sang gói câu hỏi khác!'
    elif current_quespackage != request_form['quespackage'] and mongo.db.quesbank.find_one({'question_content': request_form['question_content'].strip(), 'quespackage': request_form['quespackage']}):
        return "Error Edit Question: " + unicode(question_content) + u' -- Câu hỏi đã tồn tại'
    elif (request_form['question_content'].strip() != '' and request_form['quespackage'] != ''):
        mongo.db.quesbank.update({'_id': ObjectId(id)},
                           {'$set': {'quespackage': request_form['quespackage'],
                                     'question_content': request_form['question_content'].strip(),
                                     'answer_content': answer_content,
                                     'shuffle': (request_form['shuffle'] == u'Có'),
                                     'type': types}
                            })
        return "Edited Question: " + unicode(question_content) + ' --> ' + unicode(request_form['question_content'])
    else:
        return "Error Create Question: " + unicode(question_content) + u' -- Bạn phải điền đầy đủ các mục'

def remove_question(id):
    question = mongo.db.quesbank.find_one({"_id": ObjectId(id)}, {'question_content': 1, 'quespackage': 1})
    if mongo.db.exams.find({'quespackage': question['quespackage']}).count() > 0:
        return "Error Remove Question: " + unicode(question['question_content']) + u' -- Hiện đang có kì thi đang sử dụng câu hỏi này. Bạn phải xóa kì thi trước!'
    else:
        mongo.db.quesbank.remove({"_id": ObjectId(id)})
        return "Removed Question: " + unicode(question['question_content'])
        
            
class QuestionPage(Page):
    def __init__(self):
        self.link = 'question'
        self.name = u'Câu hỏi'
        self.catalogues = [('view', u'Các gói câu hỏi'), 
                           ('create', u'Thêm câu hỏi')]
    
    def context(self):
        cata = request.args.get('c', '')
        result = {'notify': ''}
        if cata == 'view': 
            if 'edit' in request.args:
                code = request.args.get('edit')
                if request.method == 'POST' and 'delete' in request.form:
                    result['notify'] = remove_question(request.form['delete'])              
                elif request.method == 'POST' and request.form['edit'] == 'Save':
                    result['notify'] = update_quespackage(code, request.form['name'])

                result['show'] = EditForm(mongo.db.quespackages.find_one({'code': code}), 
                                          [(u'Tên', 'name', 'text')])
                    
                result['questions'] = mongo.db.quesbank.find({'quespackage': code}).sort('_id', 1)
                result['ques_num'] = result['questions'].count()
                
                return result
            
            elif request.method == 'POST':
                if 'create' in request.form:
                    result['notify'] = insert_quespackage(request.form['name'])
                elif 'delete' in request.form:
                    result['notify'] = remove_quespackage(request.form['delete'])
            collection = mongo.db.quespackages.find().sort('_id', -1)
            result['show'] = ViewForm(collection, 
                                      [(u'Chủ đề', 'name')],
                                      request.url,
                                      'code')
            return result
        elif cata == 'create':
            result['number_answer'] = 4
            if request.method == 'POST':
                if request.form['ques'] == 'Change':
                    result['number_answer'] = int(request.form['number_answer'])
                elif request.form['ques'] == 'Create':
                    result['notify'] = insert_question(request.form)
            result['quespackages'] = mongo.db.quespackages.find()
            return result
        elif cata == 'question':
            if 'id' in request.args:
                if request.method == 'POST':
                    result['notify'] = update_question(request.args.get('id', ''), request.form)
                result['quespackages'] = mongo.db.quespackages.find()
                result['question'] = mongo.db.quesbank.find_one({'_id': ObjectId(request.args.get('id', ''))})
            return result
        else:
            return result

