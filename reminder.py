import uuid
import re

import click
import faker

from flask import Flask, render_template, request, redirect, flash, url_for
from flask.ext.sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///reminder.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["SECRET_KEY"] = str(uuid.uuid4())

db = SQLAlchemy(app)


class DatabaseError(Exception):
    pass


class InvalidDatabaseInputError(DatabaseError):
    pass


class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String())
    email = db.Column(db.String(120))

    def __init__(self, text, email):
        self.text = text
        self.email = email
        self.validate_input()

    def validate_input(self):
        if not re.match(r"(\w+\@\w+\.\w{2,})", self.email):
            raise InvalidDatabaseInputError(
                str(self.email) + " is not a valid email address.")

    def __repr__(self):
        short = self.text[:24]
        return "<Reminder for: {self.email}> ({short}...)".format(**locals())


def initialize_db():
    db.drop_all()
    db.create_all()
    print("Initialized the database.")


def create_db_test_entries():
    fake = faker.Faker()
    domains = ["gmx.de", "yahoo.com", "web.com", "gmail.com", "twisted.org"]
    for i in range(5):
        name = fake.name().replace(" ", "").replace(".", "").lower()
        mail = name + "@" + domains[i]
        db.session.add(Reminder(email=mail, text=fake.text()))
    db.session.commit()
    print("Created some test entries.")


@app.route("/")
def show_reminders():
    return render_template("show_reminders.html",
                           reminders=Reminder.query.all())


@app.route("/add/", methods=["GET", "POST"])
def add_reminder():
    try:
        email = request.form.get("email")
        text = request.form.get("text")
        if (email and text):
            reminder = Reminder(email=email, text=text)
            db.session.add(reminder)
            db.session.commit()
            flash("Added reminder with id: {0}".format(reminder.id))
    except DatabaseError as err:
        flash(str(err), "error")
    return redirect(url_for("show_reminders"))


@app.route("/add/some/", methods=["GET", "POST"])
def add_some_reminders():
    create_db_test_entries()
    flash("Added some reminders")
    return redirect(url_for("show_reminders"))


@app.route("/delete/", methods=["GET", "POST"])
def delete_reminder():
    reminder_id = request.form.get("reminder_id")
    if reminder_id:
        reminder = Reminder.query.filter_by(id=reminder_id).first()
        db.session.delete(reminder)
        db.session.commit()
        flash("Deleted reminder with id: {0}".format(reminder_id))
        return redirect(url_for("show_reminders"))
    flash("Could not find reminder with id: {0}".format(reminder_id))
    return redirect(url_for("show_reminders"))


@app.route("/delete/all/", methods=["GET", "POST"])
def delete_all_reminders():
    for reminder in Reminder.query.all():
        db.session.delete(reminder)
    db.session.commit()
    return redirect(url_for("show_reminders"))


@click.command()
@click.option("--initdb", is_flag=True)
@click.option("--testdb", is_flag=True)
@click.option("--run", is_flag=True)
def cli(initdb, testdb, run):
    if initdb:
        initialize_db()
    if testdb:
        create_db_test_entries()
    if run:
        app.run(debug=True)


if __name__ == "__main__":
    cli()
