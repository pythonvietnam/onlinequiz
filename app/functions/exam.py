# -*- coding: UTF-8 -*-
from datetime import datetime, timedelta
from random import random, shuffle
from copy import deepcopy
from app import mongo

def get_exam(exam_link):
    """ Get a exam, returns dict of a exam """
    return mongo.db.exams.find_one({'link': exam_link})

def get_all_exams():
    """ Lấy danh sách kì thì còn thời hạn và kì thi đã hết thời hạn """
    alive = list(mongo.db.exams.find({'status': 'Hiện', 'deadline': {'$gt': datetime.now()}}).sort([("start_date", 1), ("deadline", 1), ("_id", 1)]))
    dead = list(mongo.db.exams.find({'status': 'Hiện', 'deadline': {'$lte': datetime.now()}}).sort([("start_date", 1), ("deadline", 1), ("_id", 1)]))
    return alive + dead

def get_all_exam_links():
    """ Returns list of links of all exams """
    """ Chú ý thuộc tính link của mỗi exam là duy nhất, được thể hiện trên address bar của browser (nên viết liền không dấu) """
    result = []
    exams = mongo.db.exams.find({'status': u"Hiện"}, {'link': 1})
    for exam in exams:
        result.append(exam['link'])
    return result
    
def get_assignment(username, exam_link):
    """ Get a assignment, returns dict of a assignments, nếu không find đc sẽ trả lại giá trị là None """
    return mongo.db.assignments.find_one({'username': username, 'exam_link': exam_link})
    
def get_random_exam_paper(exam_link):
    """ Tạo ngẫu nhiên đề thi, trả lại 1 bài làm chưa tick (asm_of_user) và 1 bài làm đã tick đúng (asm_correct) (để so sánh chấm điểm sau này)
    dựa vào kì thi nào (exam_link) thì chỉ tìm những câu hỏi cho kì thi đó (mỗi kì thi có 1 gói câu hỏi riêng, sẽ chỉ tìm những câu hỏi thuộc
    gói đó) và số câu hỏi (question_number)
    """
    
    """ Chú ý: asm_of_user và asm_correct là 1 list các câu hỏi, mỗi 1 câu hỏi được nhận vào bài làm là kiểu list,
    vị trí 0 là (question_content) nội dung câu hỏi dạng string
    vị trí 1 là (answer_content) nội dung câu trả lời dạng list, [0] là đáp án, [1] là giá trị true or false
    vị trí 2 là (type) kiểu câu hỏi radio hoặc checkbox
    """
    question_number = mongo.db.exams.find_one({'link': exam_link}, {'question_number': 1})['question_number']
    # Xác định gói câu hỏi của kì thì
    quespackage = mongo.db.exams.find_one({'link': exam_link}, {'quespackage': 1})['quespackage']
    asm_of_user = []
    asm_correct = []
    
    # Trường hợp không đủ câu hỏi cho đề thi thì raise tạm KeyError
    if mongo.db.quesbank.find({'quespackage': quespackage}).count() < question_number:
        raise KeyError
    
    while question_number > 0:
        """ Chọn ngẫu nhiên 1 câu hỏi trong ngân hàng câu hỏi và câu hỏi này phải thuộc gói câu hỏi của kì thi"""
        question = mongo.db.quesbank.find_one( {'quespackage': quespackage, 'random_point' : {'$near' : [random(), 0]} } )
        
        """ Các thành phần của 1 câu hỏi """
        question_content = question['question_content']
        answer_content_correct = question['answer_content']
        # Câu nào dạng trộn thì shuffle
        if question['shuffle'] == True:
            shuffle(answer_content_correct)

        # Tạo câu trả lời trống, chỉ lấy tên từ câu trả lời đúng, còn giá trị false hết
        answer_content = deepcopy(answer_content_correct)
        for x in answer_content:
            x[1] = False

        type = question['type']
        
        """ Kiểm tra câu hỏi vừa đc pick [question_content, answer_content, type] đã được thêm vào đề thi chưa
        vì khi pick ngẫu nhiên có thể pick lại câu hỏi đã thêm.
        Nếu chưa thì thêm vào đề (bài làm và bài giải)"""
        if question_content not in [i[0] for i in asm_of_user]:
            asm_of_user.append([question_content, answer_content, type])
            asm_correct.append([question_content, answer_content_correct, type])
            
            question_number -= 1

    return [asm_of_user, asm_correct]

def create_assignment(username, exam_link):
    """ Tạo bài thi của thí sinh 
    Bài THI của 1 thí sinh thì bao gồm các phần: Tên thí sinh (name), bài thi của kì thi nào (exam), số điểm (point),
    số lần nộp bài (submitted), thời hạn nộp bài là bao giờ (deadline), bài LÀM của thí sinh (asm_of_user) và bài đáp án (bài giải) (asm_correct)"""
    duration = mongo.db.exams.find_one({'link': exam_link}, {'duration': 1})['duration']

    asm_of_user, asm_correct = get_random_exam_paper(exam_link)
    
    new = {'username': username, 
           'exam_link': exam_link, 
           'point': 0, 
           'deadline': datetime.now() + timedelta(seconds=duration * 60), 
           'submitted': 0, 
           'asm_of_user': asm_of_user, 
           'asm_correct': asm_correct, 
           'create_date': datetime.now(), 
           'completed_time': 0}
    mongo.db.assignments.insert(new)

def get_asm_of_user(username, exam_link):
    """ Lấy tất cả câu hỏi trong bài làm của user, trả lại list các câu hỏi, 
    mỗi câu hỏi là 1 list gồm 3 thành phần [question_content, answer_content, type] """
    return mongo.db.assignments.find_one({'username': username, 'exam_link': exam_link}, {'asm_of_user' : 1})['asm_of_user']

def update_assignment(username, exam_link, request_form):
    """
    Cập nhật bài làm. Lấy bài làm cũ của thí sinh dựa vào username và exam_link.
    Sau đó, cập nhật bài làm dựa vào request_form gửi đc đến và cập nhật số lần submit
    request_form được gửi đến là 1 list câu hỏi, trong đó mỗi câu hỏi là 1 từ điển key là nội dung câu hỏi và value là list các câu trả lời được tick 
    """
    asm_of_user = get_asm_of_user(username, exam_link)
    
    for question in asm_of_user:
        """ question này là list bao gồm 3 thành phần [question_content, answer_content, type] 
        -> question[0] là question_content
           question[1] là answer_content"""
        question_content = question[0]
        answer_content = question[1]
        re_answer = request_form.getlist(question_content) # Hàm trả lại danh sách các câu trả lời được tính, ứng với question_content (tất nhiên tập này có thể rỗng)
        
        for i in answer_content:
            if i[0] in re_answer:
                i[1] = True
            else:
                i[1] = False
        
    mongo.db.assignments.update({'username': username, 'exam_link': exam_link}, 
                                { '$set' : {'asm_of_user': asm_of_user, 
                                            'completed_time': int((datetime.now() - mongo.db.assignments.find_one({'username': username, 'exam_link': exam_link}, {'create_date': 1})['create_date'].replace(tzinfo=None)).total_seconds())},
                                  '$inc' : {'submitted': 1}
                                })

def grading(username, exam_link):
    """ Chấm điểm """
    # Lấy bài thi của 1 user dựa trên username và exam_link (kì thi nào)
    assignment = mongo.db.assignments.find_one({'username': username, 'exam_link': exam_link}, {'asm_correct': 1, 'asm_of_user': 1})
    
    # Lấy bài làm và bài giải
    asm_correct = assignment['asm_correct']
    asm_of_user = assignment['asm_of_user']
    
    # So sánh
    count = 0 # Số câu trả lời đúng
    for question in asm_correct:
        if question in asm_of_user:
            count += 1
    
    # Dựa trên tổng số câu hỏi và số câu trả lời đúng để tính điểm (làm tròn >= 0.5 -> 1.0)
    question_number = float(len(asm_correct))
    point = int(round(count / question_number * 100))

    mongo.db.assignments.update({'username': username, 'exam_link': exam_link}, { '$set' : {'point': point} })
