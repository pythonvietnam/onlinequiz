# -*- coding: UTF-8 -*-
from flask import request
from app import mongo
from model import *
from datetime import datetime
from random import randint

def insert_exam(request_form):
    """ """
    start_date = datetime.strptime(request_form['start_date'], '%Y-%m-%d')
    deadline = datetime.strptime(request_form['deadline'], '%Y-%m-%d')
    
    if start_date < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
        return "Error Create Exam: " + unicode(request_form['name']) + u' -- Ngày bắt đầu chỉ có thể là từ hiện tại trở đi'
    elif start_date >= deadline:
        return "Error Create Exam: " + unicode(request_form['name']) + u' -- Ngày bắt đầu phải nhỏ hơn ngày kết thúc'
    elif int(request_form['question_number']) > mongo.db.quesbank.find({"quespackage": request_form['quespackage']}).count():
        return "Error Create Exam: " + unicode(request_form['name']) + u' -- Số câu hỏi của kì thi nhiều hơn số câu hỏi trong gói câu hỏi bạn chọn'
    elif int(request_form['question_number']) > 0 and int(request_form['duration']) > 0:
        
        # Tạo link (mỗi kì thi chỉ có 1 link duy nhất) (giá trị để phân biệt sự khác nhau giữa các kì thi)
        random_loop = 100 # Tránh tạo vòng lặp vô hạn
        link = "%04d" % randint(0,9999)
        while mongo.db.exams.find_one({"link": link}):
            link = "%04d" % randint(0,9999)
            random_loop -= 1
            if random_loop == 1:
                return "Error Create Exam: " + unicode(request_form['name']) + u' -- Lỗi vòng lặp'
    
        exam = {"link": link, 
                "name": request_form['name'], 
                "content": request_form['content'], 
                "question_number": int(request_form['question_number']), 
                "duration": int(request_form['duration']), 
                "start_date": start_date,
                "deadline": deadline, 
                "quespackage": request_form["quespackage"], 
                "status": request_form['status'],
                "mode": request_form['mode']}
        mongo.db.exams.insert(exam)
        return "Created Exam: " + unicode(request_form['name'])
    else:
        return "Error Create Exam: " + unicode(request_form['name']) + u' -- Bạn đang cố tình nhập sai biểu mẫu?'

def update_exam(exam_link, request_form):
    name = mongo.db.exams.find_one({"link": exam_link}, {'name': 1})['name']
    mongo.db.exams.update({"link": exam_link},
                    {"$set":{"status": request_form['status'],
                             "name": request_form['name'],
                             "content": request_form['content']}
                    })
    return "Edited Exam: " + unicode(name) + ' --> ' + unicode(request_form['name'])

def remove_exam(exam_link):
    """ Xóa cả kì thi và những bài làm trong kì thi đó """
    name = mongo.db.exams.find_one({"link": exam_link}, {'name': 1})['name']
    mongo.db.exams.remove({'link': exam_link})
    asm_removed = mongo.db.assignments.remove({'exam_link': exam_link})
    return "Removed Exam: " + unicode(name) + ' -- ' + unicode(asm_removed)
    
class ExamPage(Page):
    def __init__(self):
        self.link = 'exam'
        self.name = u'Kì thi'
        self.catalogues = [('view', u'Danh sách kì thi'), 
                           ('create', u'Tạo kì thi')]
    
    def context(self):
        cata = request.args.get('c', '')
        result = {'notify': ''}
        if cata == 'view': 
            if 'edit' in request.args:
                if request.method == 'POST' and request.form['edit'] == 'Save':
                    result['notify'] = update_exam(request.args.get('edit'), request.form)
                document = mongo.db.exams.find_one({'link': request.args.get('edit', '')})
                quespackage = mongo.db.quespackages.find_one({'code': document['quespackage']})['name']
                exam_number = mongo.db.assignments.find({"exam_link": document['link']}).count()
                result['show'] = EditForm(document, 
                                          [(u'Tên kì thi', 'name', 'text'), 
                                           (u'Nội dung', 'content', 'textarea'), 
                                           (u'Gói câu hỏi', quespackage, 'readonly_direct'),
                                           (u'Số câu hỏi', 'question_number', 'readonly'),
                                           (u'Thời gian làm bài (phút)', 'duration', 'readonly'),
                                           (u'Ngày bắt đầu thi', 'start_date', 'readonly'),
                                           (u'Thời hạn nộp bài', 'deadline', 'readonly'),
                                           (u'Số bài thi hiện có', exam_number, 'readonly_direct'),
                                           (u'Chế độ', 'mode', 'readonly'),
                                           (u'Trạng thái', 'status', [u'Hiện', u'Ẩn'])])
                return result
            elif request.method == 'POST' and 'delete' in request.form:
                result['notify'] = remove_exam(request.form['delete'])
            collection_no = list(mongo.db.exams.find({'deadline': {'$lt': datetime.now()}}).sort([("start_date", 1), ("deadline", 1), ("_id", 1)]))
            collection_ok = list(mongo.db.exams.find({'deadline': {'$gt': datetime.now()}}).sort([("start_date", 1), ("deadline", 1), ("_id", 1)]))
            examview = ViewForm(collection_no + collection_ok, 
                                [(u'Kì thi', 'name'), 
                                 (u'Nội dung', 'content', '400'), 
                                 (u'Gói câu hỏi', 'quespackage'), 
                                 (u'Chế độ', 'mode'), 
                                 (u'Trạng thái', 'status')], 
                                request.url,
                                'link')
            result['show'] = examview
            return result
        elif cata == 'create':
            if request.method == 'POST':
                result['notify'] = insert_exam(request.form) 
            result['now'] = datetime.now()
            result['quespackages'] = mongo.db.quespackages.find()
            return result
        else:
            return result