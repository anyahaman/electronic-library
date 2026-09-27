from functools import wraps

from flask import flash, redirect, url_for

from flask_login import current_user



def admin_required(f):

    @wraps(f)
    def decorated(*args, **kwargs):

        if not current_user.is_authenticated:

            flash(
                "Для выполнения данного действия необходимо пройти процедуру аутентификации"
            )

            return redirect(
                url_for("login")
            )


        if current_user.role.name != "Администратор":

            flash(
                "У вас недостаточно прав для выполнения данного действия"
            )

            return redirect(
                url_for("index")
            )


        return f(*args, **kwargs)


    return decorated




def editor_required(f):

    @wraps(f)
    def decorated(*args, **kwargs):

        if not current_user.is_authenticated:

            flash(
                "Для выполнения данного действия необходимо пройти процедуру аутентификации"
            )

            return redirect(
                url_for("login")
            )


        if current_user.role.name not in [
            "Администратор",
            "Модератор"
        ]:

            flash(
                "У вас недостаточно прав для выполнения данного действия"
            )

            return redirect(
                url_for("index")
            )


        return f(*args, **kwargs)


    return decorated