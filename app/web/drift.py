from .blueprint import web 
from flask_login import login_required,current_user
from app.models.drift import Drift
from app.models.gift import Gift
from flask import flash, redirect, render_template, url_for, request
from app.forms.book import DriftForm
from app.view_models.book import BookViewModel
from app.libs.email import send_mail
from app.models.base import db
from app.libs.enums import PendingStatus
from app.models.user import User
from app.models.wish import Wish
from sqlalchemy import or_,desc  # or_ 或关系

from app.view_models.drift import DriftCollection



__author__ = '七月'


@web.route('/drift/<int:gid>', methods=['GET', 'POST'])
@login_required
def send_drift(gid):
    current_gift = Gift.query.get_or_404(gid)
    if current_gift.is_yourself_gift(current_user.id):
        flash('这本书是自己的(*^▽^*)，不能向自己索要哦')
        return redirect(url_for('web.book_detail', isbn=current_gift.isbn))

    can = current_user.can_send_drifts()
    if not can:
        return render_template('not_enough_beans.html', beans=current_user.beans)

    form = DriftForm(request.form)
    if request.method == 'POST' and form.validate():
        save_drift(form, current_gift)
        send_mail(current_gift.user.email, '有人想要一本书', 'email/get_gift.html',
                  wisher=current_user,
                  gift=current_gift)
        return redirect(url_for('web.pending'))

 # summary用户的简介频繁使用，且更像是一种用户的属性，所以作为用户的一个属性
    gifter = current_gift.user.summary
    return render_template('drift.html', gifter=gifter, user_beans=current_user.beans, form=form)

@web.route('/pending')
@login_required
def pending():
    # select * from drift where requester_id = ? or gifter_id = ?
    # order by create_time desc
    drifts = Drift.query.filter(
        or_(Drift.requester_id == current_user.id,
            Drift.gifter_id == current_user.id))\
        .order_by(desc(Drift.create_time)).all()

    views = DriftCollection(drifts, current_user.id)
    return render_template('pending.html', drifts=views.data)



@web.route('/drift/<int:did>/reject')   # did 表示的是 drift 的ID 号
@login_required
def reject_drift(did):
    with db.auto_commit():
        # requester_id=current_user.id 防止超权现象
        drift = Drift.query.filter(
            id==did, Drift.gifter_id==current_user.id).first_or_404()
        drift.pending = PendingStatus.Reject

        requester = User.query.get_or_404(drift.requester_id)
        requester.beans += 1

    return redirect(url_for('web.pending'))




@web.route('/drift/<int:did>/redraw')
#login_required 不能阻止有权限的用户访问其他用户的数据
@login_required   # 登陆操作并不能防止超权,用户1可以登录,取得访问视图函数,但可以更改url上编号来访问他人数据
def redraw_drift(did):
    with db.auto_commit():
        # requester_id=current_user.id 防止超权现象
        drift = Drift.query.filter_by(
            id=did, requester_id=current_user.id).first_or_404()
        drift.pending = PendingStatus.Redraw
        current_user.beans += 1

    return redirect(url_for('web.pending'))
# 用户不都是那种点击设计好的按钮来操作的


@web.route('/drift/<int:did>/mailed')
def mailed_drift(did):
    with db.auto_commit():
        # 更改鱼漂状态位成功
        drift = Drift.query.filter_by(
            id=did, gifter_id=current_user.id).first_or_404()
        drift.pending = PendingStatus.Success

        # 赠送一个鱼豆
        current_user.beans += 1

        # 完成赠送
        gift = Gift.query.get_or_404(drift.gift_id)
        gift.launched = True

        # 完成心愿
        Wish.query.filter_by(
            isbn=drift.isbn, uid=drift.requester_id, launched=False)\
            .update({Wish.launched: True})
        # 同
        # wish = Wish.query.filter_by(isbn=drift.isbn, uid=drift.requester_id, launched=False).first_or_404()
        # wish.launched = True

    return redirect(url_for('web.pending'))

def save_drift(drift_form, current_gift):
    if current_user.beans < 1:
        # TODO 自定义异常
        raise Exception()

    with db.auto_commit():
        drift = Drift()
        drift_form.populate_obj(drift)  # 实现相关字段的复制

        drift.gift_id = current_gift.id
        drift.requester_id = current_user.id
        drift.requester_nickname = current_user.nickname
        drift.gifter_nickname = current_gift.user.nickname
        drift.gifter_id = current_gift.user.id

        book = BookViewModel(current_gift.book)
        drift.book_title = book.title
        drift.book_author = book.author
        drift.book_img = book.image
        drift.isbn = book.isbn

        current_user.beans -= 1

        db.session.add(drift)