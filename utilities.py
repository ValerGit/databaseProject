import datetime
from flask import jsonify
from flaskext.mysql import MySQL

mysql = MySQL()


def get_user_info_external(cursor, user):
    cursor.execute("SELECT * FROM User where email='%s'" % user)
    usr_info = cursor.fetchall()
    resp = {}
    if usr_info:
        all_fetched_followers = get_followers(cursor, user)
        all_fetched_followees = get_followees(cursor, user)
        all_fetched_subscr = get_subscriptions(cursor, user)
        if usr_info[0][3]:
            anon = True
        else:
            anon = False
        resp = {
            "id": usr_info[0][0],
            "email": usr_info[0][1],
            "about": usr_info[0][2],
            "isAnonymous": anon,
            "name": empty_check(usr_info[0][4]),
            "username": empty_check(usr_info[0][5]),
            "followers": all_fetched_followers,
            "following": all_fetched_followees,
            "subscriptions": all_fetched_subscr
        }
    return resp


def empty_check(value):
    if value == "":
        return None
    return value


def get_user_info_external_by_input(cursor, user):
    resp = {}
    if user:
        email = user[1]
        all_fetched_followers = get_followers(cursor, email)
        all_fetched_followees = get_followees(cursor, email)
        all_fetched_subscr = get_subscriptions(cursor, email)
        if user[3]:
            anon = True
        else:
            anon = False
        resp = {
            "id": user[0],
            "email": user[1],
            "about": user[2],
            "isAnonymous": anon,
            "name": user[4],
            "username": user[5],
            "followers": all_fetched_followers,
            "following": all_fetched_followees,
            "subscriptions": all_fetched_subscr
        }
    return resp


def get_subscriptions(cursor, user_email):
    cursor.execute("SELECT S.thread FROM Thread_Subscr S INNER JOIN Thread T ON T.id = S.thread "
                   "WHERE S.user='%s' AND T.isClosed = 0 " % user_email)
    all_subscr = cursor.fetchall()
    all_fetched_subscr = []
    for x in all_subscr:
        all_fetched_subscr.append(x[0])
    return all_fetched_subscr


def get_followers(cursor, followee):
    cursor.execute("SELECT follower FROM Following WHERE followee='%s'" % followee)
    all_folwrs = cursor.fetchall()
    all_fetched_followers = []
    for x in all_folwrs:
        all_fetched_followers.append(x[0])
    return all_fetched_followers


def get_followees(cursor, follower):
    cursor.execute("SELECT followee FROM Following WHERE follower='%s'" % follower)
    all_folwees = cursor.fetchall()
    all_fetched_followees = []
    for x in all_folwees:
        all_fetched_followees.append(x[0])
    return all_fetched_followees


def true_false_ret(value):
    if value == 0:
        return False
    return True


def get_forum_info_external(cursor, forum_short_name):
    cursor.execute("SELECT * FROM Forum WHERE short_name='%s'" % forum_short_name)
    forum_info = cursor.fetchall()[0]
    resp = {}
    if forum_info:
        forum_id = forum_info[0]
        forum_name = forum_info[1]
        forum_short_name = forum_info[2]
        user_email = forum_info[3]

        resp = {
            "id": forum_id,
            "name": forum_name,
            "short_name": forum_short_name,
            "user": user_email
        }
    return resp


def get_thread_info_external(cursor, thread_id):
    cursor.execute("SELECT * FROM Thread WHERE id='%s'" % thread_id)
    thread = cursor.fetchall()
    if not thread:
        return {}
    return get_thread_info(cursor, thread[0])


def get_thread_info_external_params(forum_short_name, since, limit, order, related):
    conn = mysql.get_db()
    cursor = conn.cursor()
    query_first = "SELECT * FROM Thread WHERE forum='%s'" % forum_short_name
    query_second = " AND date >= '%s'" % since
    query_third = " ORDER BY date %s %s" % (order, limit)
    full_query = query_first + query_second + query_third
    cursor.execute(full_query)
    thread = cursor.fetchall()
    if not thread:
        return jsonify(code=1, response="No such thread")
    end_list = []
    for x in thread:
        end_list.append(get_thread_with_params(cursor, x, related))
    return jsonify(code=0, response=end_list)


def get_thread_info(cursor, thread):
    resp = {
        "id": thread[0],
        "forum": thread[1],
        "title": thread[2],
        "isClosed": true_false_ret(thread[3]),
        "user": thread[4],
        "date": datetime.datetime.strftime(thread[5], "%Y-%m-%d %H:%M:%S"),
        "message": thread[6],
        "slug": thread[7],
        "isDeleted": true_false_ret(thread[9]),
        "likes": thread[9],
        "dislikes": thread[10],
        "points": thread[11],
        "posts": count_posts_in_thread(cursor, thread[0])
    }
    return resp


def get_post_info_by_post(post_info):
    resp = {
        "date": datetime.datetime.strftime(post_info[1], "%Y-%m-%d %H:%M:%S"),
        "dislikes": post_info[13],
        "forum": post_info[5],
        "id": post_info[0],
        "isApproved": true_false_ret(post_info[7]),
        "isDeleted": true_false_ret(post_info[11]),
        "isEdited": true_false_ret(post_info[9]),
        "isHighlighted": true_false_ret(post_info[8]),
        "isSpam": true_false_ret(post_info[10]),
        "likes": post_info[12],
        "message": post_info[3],
        "parent": zero_check(post_info[6]),
        "points": post_info[14],
        "thread": post_info[2],
        "user": post_info[4]
    }
    return resp


def zero_check(value):
    if int(value) == 0:
        return None
    return value


def get_thread_with_params(cursor, thread, related):
    user_info = thread[4]
    forum_info = thread[1]
    if related:
        if related == 'user':
            user_info = get_user_info_external(cursor, thread[4])

        elif related == 'forum':
            forum_info = get_forum_info_external(cursor, thread[1])

    resp = {
        "id": thread[0],
        "forum": forum_info,
        "title": thread[2],
        "isClosed": true_false_ret(thread[3]),
        "user": user_info,
        "date": datetime.datetime.strftime(thread[5], "%Y-%m-%d %H:%M:%S"),
        "message": thread[6],
        "slug": thread[7],
        "isDeleted": true_false_ret(thread[9]),
        "likes": thread[9],
        "dislikes": thread[10],
        "points": thread[11]
    }
    return resp


def tree_sort(posts_info, limit):
    list_of_lists = []
    limit_list = []
    counter = 0
    for x in posts_info:
        limit_list.append(get_post_info_by_post(x))
        counter += 1
        if counter == limit and limit != 0:
            list_of_lists.append(list(limit_list))
            counter = 0
            del limit_list[:]
    if limit_list:
        list_of_lists.append(list(limit_list))
    return list_of_lists


def flat_sort(posts_info):
    end_list = []
    for x in posts_info:
        end_list.append(get_post_info_by_post(x))
    return end_list


def parent_tree_sort(posts_info, limit):
    list_of_lists = []
    limit_list = []
    counter = 0
    for x in posts_info:
        if '.' not in x[15]:
            counter += 1
        limit_list.append(get_post_info_by_post(x))

        if counter == limit and limit != 0:
            list_of_lists.append(list(limit_list))
            counter = 0
            del limit_list[:]
    if limit_list:
        list_of_lists.append(list(limit_list))
    return list_of_lists


def count_posts_in_thread(cursor, thread_id):
    cursor.execute("SELECT count(id) FROM Post WHERE thread = %s AND isDeleted=0" % thread_id)
    number = cursor.fetchall()
    if not number:
        return 0
    return int(number[0][0])