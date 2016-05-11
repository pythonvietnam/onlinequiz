# -*- coding: UTF-8 -*-
from flask import request
from app import mongo
from model import *
from bson.objectid import ObjectId

def check_ticked(answers):
    for a in answers:
        if True in a:
            return True
    return False
    
def seconds_to_time(seconds):
    return u'%d phút %d giây' % divmod(seconds, 60)

def search_assignment(request_form):
    if request_form['group'] != u'Tất cả':
        return mod_search_assignment(request_form, request_form['group'])
    else:
        # Tất cả user và Đích danh 1 kì thi
        if request_form['username'] == '' and request_form['exam'] != u'Tất cả':
            result = mongo.db.assignments.find({'exam_link': request_form['exam']}, {'username': 1, 'exam_link': 1, '_id': 1}).sort('_id', -1)
            if result.count() == 0:
                return None
            else:
                return result
        # Đích danh 1 user và Tất cả kì thi
        elif request_form['username'] != '' and request_form['exam'] == u'Tất cả':
            result = mongo.db.assignments.find({'username': request_form['username']}, {'username': 1, 'exam_link': 1, '_id': 1}).sort('_id', -1)
            if result.count() == 0:
                return None
            else:
                return result
        # Tất cả user và Tất cả kì thi
        elif request_form['username'] == '' and request_form['exam'] == u'Tất cả':
            result = mongo.db.assignments.find({}, {'username': 1, 'exam_link': 1, '_id': 1}).sort('_id', -1)
            if result.count() == 0:
                return None
            else:
                return result
        # Đích danh 1 user và Đích danh 1 kì thi
        else:
            result = mongo.db.assignments.find({'username': request_form['username'], 'exam_link': request_form['exam']}, {'username': 1, 'exam_link': 1, '_id': 1}).sort('_id', -1)
            if result.count() == 0:
                return None
            else:
                return result
        
def mod_search_assignment(request_form, group):
    # Tất cả user và Đích danh 1 kì thi
    if request_form['username'] == '' and request_form['exam'] != u'Tất cả':
        allowed_users = mongo.db.users.find({'group': group}, {'username': 1})
    
        result = mongo.db.assignments.find({'exam_link': request_form['exam'], 
                                      'username': {'$in': [user['username'] for user in allowed_users]}}, 
                                     {'username': 1, 
                                      'exam_link': 1, 
                                      '_id': 1}).sort('_id', -1)
        if result.count() == 0:
            return None
        else:
            return result
    # Đích danh 1 user và Tất cả kì thi
    elif request_form['username'] != '' and (mongo.db.users.find_one({'username': request_form['username']}, {'group': 1})['group'] == group) and request_form['exam'] == u'Tất cả':
        result = mongo.db.assignments.find({'username': request_form['username']}, {'username': 1, 'exam_link': 1, '_id': 1}).sort('_id', -1)
        if result.count() == 0:
            return None
        else:
            return result
    # Tất cả user và Tất cả kì thi
    elif request_form['username'] == '' and request_form['exam'] == u'Tất cả':
        allowed_users = mongo.db.users.find({'group': group}, {'username': 1})
        
        result = mongo.db.assignments.find({'username': {'$in': [user['username'] for user in allowed_users]}}, 
                                     {'username': 1, 'exam_link': 1, '_id': 1}).sort('_id', -1)
        if result.count() == 0:
            return None
        else:
            return result
    # Đích danh 1 user và Đích danh 1 kì thi
    elif (mongo.db.users.find_one({'username': request_form['username']}, {'group': 1})['group'] == group):
        result = mongo.db.assignments.find({'username': request_form['username'], 'exam_link': request_form['exam']}, {'username': 1, 'exam_link': 1, '_id': 1}).sort('_id', -1)
        if result.count() == 0:
            return None
        else:
            return result
    else:
        return None
        

class AssignmentPage(Page):
    def __init__(self):
        self.link = 'assignment'
        self.name = u'Bài thi'
        self.catalogues = [('search', u'Tra cứu bài thi')]
    
    def context(self):
        cata = request.args.get('c', '')
        result = {'notify': ''}
        if cata == 'search':
            def check_mode_is_test(exam_link):
                return mongo.db.exams.find_one({'link': exam_link}, {'mode': 1})['mode'] == u"Thi thử"
            if request.method == 'POST' and request.form['search'] == u'Tìm':
                result['check_mode_is_test'] = check_mode_is_test
                
                def lookup(username, exam):
                    return username + ' - ' + mongo.db.users.find_one({'username': username})['fullname'] + ' - ' + mongo.db.exams.find_one({'link': exam})['name']
                result['lookup'] = lookup
                
                result['res'] = search_assignment(request.form)
                
            elif 'id' in request.args:
                result['assignment'] = mongo.db.assignments.find_one({'_id': ObjectId(request.args.get('id', ''))})
                result['user'] = mongo.db.users.find_one({'username': result['assignment']['username']}, {'fullname': 1, 'username': 1})
                result['examname'] = mongo.db.exams.find_one({'link': result['assignment']['exam_link']})['name']
                result['check_ticked'] = check_ticked
                result['seconds_to_time'] = seconds_to_time
                return result
                
            elif 'delete' in request.args and check_mode_is_test(mongo.db.assignments.find_one({'_id': ObjectId(request.args.get('delete', ''))}, {'exam_link': 1})['exam_link']):
                assignment = mongo.db.assignments.find_one({'_id': ObjectId(request.args.get('delete', ''))}, {'exam_link': 1, 'username': 1})
                def lookup(username, exam):
                    return username + ' - ' + mongo.db.users.find_one({'username': username})['fullname'] + ' - ' + mongo.db.exams.find_one({'link': exam})['name']
                asm = lookup(assignment['username'], assignment['exam_link'])
                
                mongo.db.assignments.remove({'_id': ObjectId(request.args.get('delete', ''))})
                result['notify'] = "Removed Assignment: " + asm
            
            result['exams'] = mongo.db.exams.find({}, {'name': 1, 'link': 1}).sort('_id', -1)
            result['groups'] = mongo.db.groups.find()
            
            return result
        else:
            return result
