from .blueprint import web 
from flask import render_template, request, redirect, url_for, flash

from app.forms.auth import RegisterForm, LoginForm

from app.models.base import db,Base

from app.models.user import User

from flask_login import login_user

__author__ = '七月'


@web.route('/register', methods=['GET', 'POST'])
# def register():
#     form = RegisterForm(request.form)
    # #request.form
    # if request.methods == 'POST' and form.validate():

    # return render_template('auth/register.html',form ={'data' : {}})
    #     form = RegisterForm(request.form)
@web.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User()
        user.set_attrs(form.data)
        db.session.add(user)
        db.session.commit()
        redirect(url_for('web/login'))
    return render_template('auth/register.html', form=form)
        # form = RegisterForm(request.form)
    # if request.method == 'POST' and form.validate():
    #     with db.auto_commit():
    #         user = User()
    #         user.set_attrs(form.data)
    #         db.session.add(user)

    #     return redirect(url_for('web.login'))

    # return render_template('auth/register.html', form=form)


@web.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=True)
			
            next = request.args.get('next')
            if not next or not next.startswith('/'):
                return redirect(url_for('web.index'))
            return redirect(next)
        else:
            flash("账号不存在或者密码错误")
    return render_template('auth/login.html', form=form)


@web.route('/reset/password', methods=['GET', 'POST'])
def forget_password_request():
    return render_template('auth/forget_password_request.html')


@web.route('/reset/password/<token>', methods=['GET', 'POST'])
def forget_password(token):
    return render_template('auth/forget_password.html')


@web.route('/change/password', methods=['GET', 'POST'])
def change_password():
    return render_template('auth/change_password.html')


@web.route('/logout')
def logout():
    return render_template('auth/register.html')