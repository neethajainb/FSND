
import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
from sqlalchemy import func

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

# utility for paginating questions
def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  CORS(app)
  
  @app.route('/')
  def hello_world():
        return jsonify({'message':'Hello, World!'})

  '''
   Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
  #   CORS(app)
  cors = CORS(app, resources={r"/api/*": {"origins": "*"}})


  '''
  Use the after_request decorator to set Access-Control-Allow
  '''
  # CORS Headers 
  @app.after_request
  def after_request(response):

      response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
      response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')
      return response

  ''' 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''

  @app.route('/questions')
  def retrieve_questions():
     selection = Question.query.order_by(Question.id).all()
     current_questions = paginate_questions(request, selection)
     categories = Category.query.order_by(Category.type).all()
     
     # no questions are found, abort with a 404 error.
     if len(current_questions) == 0:
      abort(404)
     
     # return data to view
     return jsonify({
       'success': True,
       'questions': current_questions,
       'total_questions': len(selection),
       'current_category': None,
       'categories': {category.id: category.type for category in categories}
        })

  ''' 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    # get the question by id
    question = Question.query.filter(Question.id == question_id).one_or_none()
    
    #if no question found
    if question is None:
      abort(404)

    # delete the question
    try:
      question.delete()

      all_questions = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, all_questions)
  
      # return data to view
      return jsonify({
          'success': True,
          'deleted': question_id,
          'questions': current_questions,
          'total_questions': len(all_questions)
      })
    
    except Exception as e:
      print(e)
       # if problem deleting question
      abort(422)

    
  '''
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''
  @app.route('/questions', methods=['POST'])
  def create_question():
    # load the request body
    body = request.get_json()
    new_question = body.get('question', None)
    new_answer = body.get('answer', None)
    new_difficulty = body.get('difficulty', None) 
    new_category = body.get('category', None)
    
    # ensure all fields have data
    if new_question is None or new_answer is None:
      abort(422)

    try:
      print("create_question")
       # create and insert new questions
      question = Question(question=new_question, answer=new_answer,
                          difficulty=new_difficulty, category=new_category)
      question.insert()

      selection = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, selection)
     
      # return data to view
      return jsonify({
        'success': True,
        'created': question.id,
        'question_created': question.id,
        'questions': current_questions,
        'total_questions': len(Question.query.all())
      })
    except Exception as e:
        print(e)
        # unprocessable if exception
        abort(422)
     
  '''
  Create a POST endpoint to get questions based on a search term. 
  It should return any questions for whom the search term 
  is a substring of the question. 

  TEST: Search by any phrase. The questions list will update to include 
  only question that include that string within their question. 
  Try using the word "title" to start. 
  '''
  @app.route('/questions/search', methods=['POST'])
  def search_questions():
    # load the request body
    body = request.get_json()
    search_term = body.get('searchTerm', None)

    search_results = Question.query.filter(Question.question.ilike(f'%{search_term}%')).all()

    # 404 if no results found
    if not search_results:
      abort(404)

    # paginate the selection
    paginated = paginate_questions(request, search_results)

    # return data to view
    return jsonify({
      'success': True,
      'questions': paginated,
      'total_questions': len(search_results),
      'current_category': None
    }) 

  '''
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/categories')
  def get_categories():
    categories = Category.query.order_by(Category.type).all()
    
    # abort 404 if no categories found
    if len(categories) == 0:
        abort(404)
    
    # return data to view
    return jsonify({
      'success': True,
      'categories': {category.id: category.type for category in categories}
       })

  '''
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''
  @app.route('/categories/<int:category_id>/questions')
  def get_questions_by_category(category_id):
    category = Category.query.filter_by(id=category_id).one_or_none()
    # abort 400 for bad request if category isn't found
    if (category is None):
      abort(400)

    try:
      # get the category by id
      questions = Question.query.filter(Question.category == str(category_id)).all()

      # paginate the selection
      paginated = paginate_questions(request, questions)

      # return data to view
      return jsonify({
        'success': True,
        'questions': paginated,
        'total_questions': len(questions),
        'current_category': category_id
      })
    except Exception as e:
        print(e)
        abort(404)


  '''
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  /quizzes?
  '''
  @app.route('/play', methods=['POST'])
  def play_quiz():
    body = request.get_json()
    # the request did not have a body and hence return BAD_REQUEST
    if not body:
      abort(400)

    #Now check the individiual fields to see if they are present in the request
    #if not return 400
    if body.get('previous_questions') is None:
      abort(400)
    
    if body.get('quiz_category') is None:
      abort(400)

    previous_questions = body.get('previous_questions')
    #Read the category for quizing  
    quiz_category = body.get('quiz_category')

    # convert category id to integer
    cat_id = int(quiz_category['id'])
    if cat_id == 0:
      questions_by_category = Question.query.order_by(func.random())
    else:
        #Use the category that was sent by user
        questions_by_category = Question.query.filter(Question.category == cat_id).order_by(func.random())
    
    #Check to see if there is any questions for the selected category
    if not questions_by_category.all():
        abort(404)
    else:
      #Filter out all the questions that were previously played out
      quiz_on_question = questions_by_category.filter(Question.id.notin_(previous_questions)).first()
    
    # User already played all the question in this category and hence return done
    if quiz_on_question is None:
        return jsonify({
            'success': True
        })
    # There is atleast one question that is yet to be played and return first such question
    return jsonify({
        'success': True,
        'question': quiz_on_question.format()
    })


  '''
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      "success": False,
      "error": 404,
      "message": "resource not found"
    }), 404

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      "success": False,
      "error": 422,
            "message": "unprocessable"
    }), 422

  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      "success": False,
      "error": 400,
      "message": "bad request"
    }), 400

  @app.errorhandler(405)
  def not_found(error):
    return jsonify({
      "success": False,
      "error": 405,
      "message": "method not allowed"
    }), 405
 

  return app