from flask import Flask
from flask import request
from flask import jsonify
from datetime import datetime
import json
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///store.sqlite'

db = SQLAlchemy(app)

class Entry(db.Model):
    key = db.Column(db.String(20), unique=True, nullable=False, primary_key=True)
    value = db.Column(db.Text)
    created = db.Column(db.DateTime, nullable=False)
    last_accessed = db.Column(db.DateTime)
    last_changed = db.Column(db.DateTime)

    def __repr__(self):
        return '<Entry {}>'.format(self.key)

    def response(self):
        response = {}
        response['key'] = self.key
        response['created'] = self.created.strftime('%FT%T%z')

        try:
            response['value'] = json.loads(self.value)
        except json.decoder.JSONDecodeError:
            response['value'] = self.value

        if self.last_accessed is None:
            response['last_accessed'] = ''
        else:
            response['last_accessed'] = self.last_accessed.strftime('%FT%T%z')

        if self.last_changed is None:
            response['last_changed'] = ''
        else:
            response['last_changed'] = self.last_changed.strftime('%FT%T%z')

        return response

    def update(self, new):
        if 'value' in new:
            self.value = new['value']


@app.route('/entries', methods=['POST'])
def add_entry():
    data = request.get_json(force=True)
    entry = Entry(
        key=data['key'],
        value=json.dumps(data['value']),
        created=datetime.now()
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify(entry.response())

@app.route('/entry/<key>', methods=['GET'])
def get_entry(key):
    entry = Entry.query.filter_by(key=key).first()
    entry.last_accessed = datetime.now()
    db.session.commit()
    return jsonify(entry.response())

@app.route('/entries', methods=['GET'])
def get_entries():
    entries = Entry.query.all()
    return jsonify([entry.response() for entry in entries])

@app.route('/entry/<key>', methods=['DELETE'])
def delete_entry(key):
    entry = Entry.query.filter_by(key=key).first()
    db.session.delete(entry)
    db.session.commit()
    return 'entry {} deleted'.format(key)

@app.route('/entry/<key>', methods=['PATCH'])
def update_entry(key):
    data = request.get_json(force=True)
    entry = Entry.query.filter_by(key=key).first()
    if 'value' in data:
        entry.value = data['value']
        entry.last_changed = datetime.now()
        db.session.commit()

    return jsonify(entry.response())

if __name__ == '__main__':
    app.run()
