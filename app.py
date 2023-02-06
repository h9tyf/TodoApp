from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import sys
from sqlalchemy.ext.hybrid import hybrid_property

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost:5432/todoapp'
db = SQLAlchemy(app)

migrate = Migrate(app, db)

class Todo(db.Model):
  __tablename__ = 'todos'
  id = db.Column(db.Integer, primary_key=True) 
  description = db.Column(db.String(), nullable=False)
  completed = db.Column(db.Boolean, nullable=False, default=False)
  list_id = db.Column(db.Integer, db.ForeignKey('todolists.id'), nullable=False)

  def __repr__(self):
    return f'<Todo {self.id} {self.description}>'

class TodoList(db.Model):
  __tablename__ = 'todolists'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(), nullable=False)
  todos = db.relationship('Todo', backref='list', lazy=True)

  def __repr__(self):
    return f'<TodoList {self.id} {self.name}>'
  
  @hybrid_property
  def completed(self):
    todos = Todo.query.filter_by(list_id=self.id).all()
    res = True
    for todo in todos:
      res &= todo.completed
    return res



@app.route('/todos/create', methods=['POST'])
def create_todo():
  error = False
  body = {}
  try:
    description = request.get_json()['description']
    list_id = request.get_json()['list_id']
    todo = Todo(description=description)
    active_list = TodoList.query.get(list_id)
    todo.list = active_list
    db.session.add(todo)
    db.session.commit()
    body['description'] = todo.description
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    abort(400)
  else:
    return jsonify(body)

@app.route('/todos/<todo_id>/set-completed', methods=['POST'])
def set_completed_todo(todo_id):
  try:
    completed = request.get_json()['completed']
    todo = Todo.query.get(todo_id)
    todo.completed = completed
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return redirect(url_for('index'))


@app.route('/lists/<list_id>/set-completed', methods=['POST'])
def set_completed_list(list_id):
  try:
    completed = request.get_json()['completed']
    todos = Todo.query.filter_by(list_id=list_id).all()
    for todo in todos:
      todo.completed = completed
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return redirect(url_for('index'))



@app.route('/todos/<todo_id>/delete', methods=['POST'])
def delete_todo(todo_id):
  try:
    Todo.query.filter_by(id=todo_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return jsonify({'success': True})
  # return redirect(url_for('index'))

@app.route('/lists/<list_id>/delete', methods=['POST'])
def delete_list(list_id):
  try:
    print(1)
    Todo.query.filter_by(list_id=list_id).delete()
    print(2)
    TodoList.query.filter_by(id=list_id).delete()
    print(3)
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return jsonify({'success': True})
  # return redirect(url_for('index'))


@app.route('/lists/<list_id>')
def get_list_todos(list_id):
  return render_template('index.html',
    lists=TodoList.query.all(),
    active_list=TodoList.query.get(list_id),
    data=Todo.query.filter_by(list_id=list_id).order_by('id').all())

@app.route('/lists/create', methods=['POST'])
def create_list():
  error = False
  body = {}
  print(request)
  try:
    name = request.get_json()['name']
    new_list = TodoList(name=name)
    db.session.add(new_list)
    db.session.commit()
    body['name'] = new_list.name
    body['id'] = new_list.id
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    abort(400)
  else:
    return jsonify(body)

@app.route('/')
def index():
  return redirect(url_for('get_list_todos', list_id=1))

if __name__ == '__main__':
  app.run(host="0.0.0.0", port=3000)
#always include this at the bottom of your code (port 3000 is only necessary in workspaces)s
'''
with app.app_context():
    # within this block, current_app points to app.
    if __name__ == '__main__':
        db.create_all()
        app.run(host="0.0.0.0", port=3000)
'''