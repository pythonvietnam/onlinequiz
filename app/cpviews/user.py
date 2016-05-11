# -*- coding: UTF-8 -*-
from flask import request, session
from app import mongo
from model import *
from random import randint
from bson.objectid import ObjectId

def insert_group(request_form):
    if request_form['name'].strip() == '':
        return "Error Creat Group: " + unicode(request_form['name']) + u' -- Tên nhóm không đúng quy định'
    try:
        mongo.db.groups.insert({"name": request_form['name']})
        return "Created Group: " + unicode(request_form['name'])
    except:
        return "Error Creat Group: " + unicode(request_form['name']) + u' -- Tên nhóm đã tồn tại'

def update_group(id, request_form):
    if request_form['name'].strip() == '':
        return "Error Edit Group: " + unicode(request_form['name']) + u' -- Tên nhóm không đúng quy định'
    try:
        mongo.db.groups.update({'_id': id}, 
                               { '$set' : {'name': request_form['name']}})
        return "Edited Group: " + unicode(request_form['name'])
    except:
        return "Error Edit Group: " + unicode(request_form['name']) + u' -- Tên nhóm đã tồn tại'
        
def remove_group(request_form):
    name = mongo.db.groups.find_one({'_id': ObjectId(request_form['delete'])}, {'name': 1})['name']
    if mongo.db.users.find({"group": request_form['delete']}).count():
        return "Error Remove Group: " + unicode(name) + u' -- Đang có tài khoản trong Group này, hãy xóa tài khoản trước.'
    try:
        mongo.db.groups.remove({'_id': ObjectId(request_form['delete'])})
        return "Removed Group: " + unicode(name)
    except:
        return "Error Remove Group: " + unicode(name) + u' -- Lỗi chưa xác định'
        
def insert_user(request_form):
    """ Thêm user trả lại giá trị thông báo (notify) thành công hoặc ko thành công """
    
    if mongo.db.users.find_one({"username": request_form['username']}):
        return "Error Create User: " + unicode(request_form['username']) + u' -- Tài khoản đã tồn tại'
    elif len(request_form['username']) < 3:
        return "Error Create User: " + unicode(request_form['username']) + u' -- Tài khoản phải từ 3 kí tự trở lên'
    elif len(request_form['password']) < 6:
        return "Error Create User: " + unicode(request_form['username']) + u' -- Mật khẩu phải từ 6 kí tự trở lên'
    elif not mongo.db.groups.find_one({"_id": ObjectId(request_form['group'])}):
        return "Error Create User: " + unicode(request_form['username']) + u' -- Bạn chưa chọn nhóm cho tài khoản này'
    else:
        user = {"username": request_form['username'], 
                "password": request_form['password'], 
                "fullname": request_form['fullname'], 
                "email": request_form['email'], 
                "work": request_form['work'], 
                "regency": request_form['regency'], 
                "level": "Thí sinh",
                "group": request_form['group'], 
                "status": "Hoạt động"}
        mongo.db.users.insert(user)
        return "Created User: " + unicode(request_form['username'])

def insert_multi_user(request_form):
    number = int(request_form['number'])
    if number < 1 or number > 100:
        return u'Error Create Multi Users: -- Mỗi lần chỉ được tạo tối đa 100 users'
    elif len(request_form['username']) < 3:
        return u'Error Create Multi Users: -- Tài khoản phải từ 3 kí tự trở lên'
    elif request_form['password'] != '' and len(request_form['password']) < 6:
        return u'Error Create Multi Users: -- Mật khẩu phải từ 6 kí tự trở lên'
    elif not mongo.db.groups.find_one({"_id": ObjectId(request_form['group'])}):
        return u"Error Create Multi User: " + unicode(request_form['username']) + u' -- Bạn chưa chọn nhóm cho tài khoản này'
    else:
        user_list = []

        for i in range(number):
            
            random_loop = 100 # Tránh tạo vòng lặp vô hạn khi hết số để cấp cho user
            
            # Nếu tài khoản đã tồn tại thì randomize lại
            username = request_form['username'] + "%04d" % randint(0,9999)
            while mongo.db.users.find_one({"username": username}):
                username = request_form['username'] + "%04d" % randint(0,9999)
                random_loop -= 1
                if random_loop == 1:
                    return u'Error Create Multi Users: -- Lỗi vòng lặp, vui lòng thử lại'
            if request_form['password'] == '':
                password = str(randint(100000, 999999))
            else:
                password = request_form['password']
            user = {"username": username, 
                    "password": password, 
                    "fullname": "", 
                    "email": "", 
                    "work": request_form['work'], 
                    "regency": "", 
                    "level": "Thí sinh",
                    "group": request_form['group'], 
                    "status": "Hoạt động"}
            
            mongo.db.users.insert(user)
            user_list.append(username)
            
        return "Created Multi Users: " + str(user_list)

def update_user(username, request_form):
    """ Cập nhật user trả lại giá trị thông báo (notify) thành công hoặc ko thành công """
    
    # Điều kiện trên để tránh trường hợp thay đổi thông tin của admin hoặc mod
    user = mongo.db.users.find_one({'username': username})
    user_is_member = (user['level'] == u"Thí sinh")
    
    if request_form['password'] != '' and len(request_form['password']) < 6:
        return "Error Edit User: " + unicode(username) + u' -- Mật khẩu phải từ 6 kí tự trở lên'
    elif user_is_member:
        update_info = {'fullname': request_form['fullname'], 
                       'email': request_form['email'], 
                       'work': request_form['work'], 
                       'regency': request_form['regency'], 
                       'status': request_form['status'],
                       'group': request_form['group']}
        
        # Kiểm tra password, nếu có nhập pass thì thay đổi
        if request_form['password'] != '':
            update_info['password'] = request_form['password']
        
        mongo.db.users.update({'username': username}, 
                        { '$set' : update_info})
        return "Edited User: " + unicode(username)
    else:
        return "Error Edit User: " + unicode(username) + u' -- Bạn đang cố tình nhập sai biểu mẫu'
        
def remove_user(username):
    """ Xóa user và xóa bài thi """
    if (mongo.db.users.find_one({"username": username})['level'] == u"Thí sinh"):
        mongo.db.users.remove({"username": username})
        asm_removed = mongo.db.assignments.remove({"username": username})
        return "Removed User: " + username + ' -- ' + unicode(asm_removed)
    else:
        return "Error Remove User: " + username + u' -- Bạn đang cố tình nhập sai biểu mẫu'


class UserPage(Page):
    def __init__(self):
        self.link = 'user'
        self.name = u'Tài khoản'
        self.catalogues = [('view', u'Tra cứu thí sinh'), 
                           ('create_one', u'Tạo 1 thí sinh'), 
                           ('create_multi', u'Tạo nhiều thí sinh'),
                           ('create_group', u'Tạo nhóm')]
    
    def context(self):
        cata = request.args.get('c', '')
        result = {'notify': ''}
        if cata == 'view': 
            if 'edit' in request.args:
                if request.method == 'POST' and request.form['edit'] == 'Save':
                    result['notify'] = update_user(request.args.get('edit'), request.form)
                    
                result['show'] = EditForm(mongo.db.users.find_one({'username': request.args.get('edit', '')}), 
                                          [(u'Tài khoản', 'username', 'readonly'), 
                                           (u'Mật khẩu', 'password', 'text'),
                                           (u'Họ Tên', 'fullname', 'text'), 
                                           (u'Đơn vị', 'work', 'text'), 
                                           (u'Chức vụ', 'regency', 'text'),
                                           (u'Email', 'email', 'text'),
                                           (u'Nhóm', 'group', [str(g['_id']) for g in mongo.db.groups.find()] ),
                                           (u'Trạng thái', 'status', [u'Hoạt động', u'Khóa'])])
                return result
            elif request.method == 'POST' and 'delete' in request.form:
                result['notify'] = remove_user(request.form['delete'])
            
            result['groups'] = mongo.db.groups.find()
            
            if 'group' in request.args:
                collection = mongo.db.users.find({'level': u'Thí sinh', 'group': request.args.get('group', '')}).sort("_id", 1)
            elif result['groups'].count():
                collection = mongo.db.users.find({'level': u'Thí sinh', 'group': str(mongo.db.groups.find()[0]['_id']) }).sort("_id", 1)
            else:
                collection = []
            
            result['show'] = ViewForm(collection, 
                                      [('Username', 'username'), 
                                       (u'Mật khẩu', 'password'), 
                                       (u'Họ Tên', 'fullname'), 
                                       (u'Các kì thi đã tham gia', 'attended'), 
                                       (u'Nhóm', 'group'), 
                                       (u'Trạng thái', 'status')], 
                                      request.url,
                                      'username')
            return result
        elif cata == 'create_one':
            if request.method == 'POST':
                result['notify'] = insert_user(request.form)
            result['groups'] = mongo.db.groups.find()
            return result
        elif cata == 'create_multi':
            if request.method == 'POST':
                result['notify'] = insert_multi_user(request.form)
            result['groups'] = mongo.db.groups.find()
            return result
        elif cata == 'create_group':
            if 'edit' in request.args:
                id = ObjectId(request.args.get('edit', ''))
                if request.method == 'POST':
                    result['notify'] = update_group(id, request.form)
                result['show'] = EditForm(mongo.db.groups.find_one({'_id': id}), 
                                          [(u'Tên nhóm', 'name', 'text')])
                return result
            elif request.method == 'POST':
                if 'create' in request.form:
                    result['notify'] = insert_group(request.form)
                elif 'delete' in request.form:
                    result['notify'] = remove_group(request.form)
            result['show'] = ViewForm(mongo.db.groups.find().sort('_id', -1), [(u'Tên nhóm', 'name')], request.url, '_id')
            return result
        elif cata == 'view_mod':
            if 'edit' in request.args:
                if request.method == 'POST' and request.form['edit'] == 'Save':
                    result['notify'] = update_manager(request.args.get('edit'), request.form)
                    
                result['show'] = EditForm(mongo.db.users.find_one({'username': request.args.get('edit', '')}), 
                                          [(u'Tài khoản', 'username', 'readonly'),  
                                           (u'Cấp độ', 'level', 'readonly'),
                                           (u'Quyền quản trị nhóm', 'group_permission', [str(g['_id']) for g in mongo.db.groups.find()] ),
                                           (u'Khả năng', 'ability', 'number'),
                                           (u'Mật khẩu', 'password', 'pass'),
                                           (u'Trạng thái', 'status', [u"Hoạt động", u"Khóa"])])
                return result
            elif request.method == 'POST' and 'delete' in request.form:
                result['notify'] = remove_manager(request.form['delete'])
            collection = mongo.db.users.find({'$or': [ {'level': u"Quản trị Đơn vị"}, {'level': u'Quản trị Tin tức'}, {'level': u'Khóa - Đơn vị'}, {'level': u'Khóa - Tin tức'} ] }).sort("_id", 1)
            result['show'] = ViewForm(collection, 
                                      [(u'Tài khoản', 'username'), 
                                       (u'Loại tài khoản', 'level'), 
                                       (u'Quyền quản lý nhóm', 'group_permission'), 
                                       (u'Khả năng', 'ability'),
                                       (u'Trạng thái', 'status')], 
                                      request.url,
                                      'username')
            return result
        elif cata == 'create_mod':
            if request.method == 'POST':
                result['notify'] = insert_manager(request.form)
            result['groups'] = mongo.db.groups.find()
            return result
        else:
            return result
