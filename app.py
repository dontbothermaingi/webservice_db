from models import db, User, Message, Order, OrderItem, MoreDetail, Service
from flask import Flask, request, jsonify, make_response
from flask_migrate import Migrate
from flask_restful import Api, Resource
from datetime import datetime
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, JWTManager, create_refresh_token, get_jwt_identity, jwt_required
import os
from openai import OpenAI
from dotenv import load_dotenv

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

migrate = Migrate(app, db)

CORS(app, supports_credentials=True)

api = Api(app)

app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret_key')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'default_jwt_secret_key')

jwt = JWTManager(app)

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# This class represents an API endpoint `/register`, which handles user registration. It extends `Resource`, so it can respond to HTTP methods like `POST`.
class UserRegister(Resource):
    def post(self):
        data = request.get_json()

        first_name = data.get('first_name')
        last_name = data.get('last_name')
        display_name = data.get('display_name')
        date_of_birth = data.get('date_of_birth')
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        role = data.get('role')

        # Convert date string to Python date object
        try:
            date_str = data.get('date_of_birth')
            date_of_birth = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Expected YYYY-MM-DD'}), 400

        # Ensure passwords is a string
        password = str(password)

        # Hash Password
        hashed_pw = generate_password_hash(password)

        new_user = User(
            first_name = first_name,
            last_name = last_name,
            display_name = display_name,
            date_of_birth = date_of_birth,
            email = email,
            username = username,
            password = hashed_pw,
            role = role
        )

        try:
            db.session.add(new_user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({'error':str(e)}), 400
        
        return {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
        }, 201

api.add_resource(UserRegister, "/register")

# This class represents an Api endpoint "/login" for loging in.
class UserLogin(Resource):
    def post(self):

        data = request.get_json()

        username = data.get('username')
        password = data.get('password')

        # Find the user by the username
        user = User.query.filter_by(username=username).first()

        if not user and not check_password_hash(user.password, password):
            return jsonify({"error": "Incorrect Password"}), 400
        
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        print(f"Access Token: {access_token}")  # Debugging step
        print(f"Refresh Token: {refresh_token}")  # Debugging step

        # Must define the response first because cookies are set by modifying the response header
        response = make_response({"message": "Login successful"})
        response.set_cookie("access_token", access_token, httponly=True, secure=True, samesite='Strict')
        response.set_cookie("refresh_token", refresh_token, httponly=True, secure=True, samesite='Strict')

        # Return the user details and tokens
        return {
            "user_id":user.id,
            "username":user.username,
            "access_token": access_token,
            "refresh_token": refresh_token
        }, 200

api.add_resource(UserLogin, "/login")

class UserLogout(Resource):
    def post(self):

        response = make_response({'Message': 'Logged Out Succefully'})
        response.set_cookie('access_token', '', expires=0)
        response.set_cookie('refresh_token', '', expires=0)

        return response

# Add the logout resource to the API
api.add_resource(UserLogout, '/logout')

class CheckSession(Resource):
    @jwt_required(optional=True)  # Allow access without token but handle it explicitly
    def get(self):
        # Retrieve user ID from token if present
        user_id = get_jwt_identity()
        
        if not user_id:
            # Respond with 401 Unauthorized for clients to redirect
            return {'message': '401: Unauthorized - Login Required'}, 401
        
        # Fetch the user by ID
        user = User.query.filter(User.id == user_id).first()
        
        if user:
            return user.to_dict(), 200
        else:
            return {'message': '401: User not found'}, 401

# Add the resource to the API
api.add_resource(CheckSession, '/check_session')

class ServiceProviders(Resource):
    def get(self):
        users = User.query.filter_by(role='Worker').all()
        return [user.to_dict() for user in users], 200

api.add_resource(ServiceProviders, '/serviceproviders')

class GetUserDetails(Resource):
    def get(self, id):
        user = User.query.filter_by(id=id).first()

        return user.to_dict(), 200
    
api.add_resource(GetUserDetails, "/getuserdetails/<int:id>")

class UserDetails(Resource):
    @jwt_required()
    def post(self):

        data = request.get_json()

        category = data.get("category")
        jobTitle =  data.get("jobTitle")
        description = data.get("description")
        detailedDescription = data.get("detailedDescription")
        payRate = data.get("payRate"),
        completionRate = data.get("completionRate")
        rating = data.get("rating")
        location = data.get("location")
        responseTime = data.get("responseTime")
        user_id = get_jwt_identity()

        new_details = MoreDetail(
            category = category,
            jobTitle = jobTitle,
            description = description,
            detailedDescription= detailedDescription,
            payRate = payRate,
            completionRate = completionRate,
            rating = rating,
            location = location,
            responseTime = responseTime,
            user_id = user_id
        )

        try:
            db.session.add(new_details)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({"Error":str(e)}), 200
        
        return jsonify({"Message": "Details Posted Successfully"}), 200
    
    def patch(self, id):

        detail = MoreDetail.query.filter_by(user_id=id)

        if not detail:
            return jsonify({'error': 'Detail not found'}), 404

        data = request.get_json()

        for key, value in data.items():
            setattr(detail, key, value)
        
        try:
            db.session.commit()
            return jsonify(detail.to_dict()), 200  # Return updated address details
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Failed to update details: {str(e)}'}), 500
        

api.add_resource(UserDetails, "/details", "/details/<int:id>")

class UserServices(Resource):
    def post(self):
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided for posting"}), 400

        user_id = get_jwt_identity()

        try:
            for item in data:
                service = item.get("service")
                if service:
                    new_service = Service(
                        service=service,
                        user_id=user_id
                    )
                    db.session.add(new_service)
            db.session.commit()
            return jsonify({"message": "Services posted successfully"}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Failed to post services: {str(e)}'}), 500

    def patch(self, id):
        service = Service.query.filter_by(user_id=id).first()

        if not service:
            return jsonify({'error': 'Service not found'}), 404

        data = request.get_json()

        try:
            for key, value in data.items():  # Assuming a single dict
                setattr(service, key, value)

            db.session.commit()
            return jsonify(service.to_dict()), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Failed to update services: {str(e)}'}), 500

api.add_resource(UserServices, "/services" ,"/service/<int:id>")

class SendMessage(Resource):
    @jwt_required()
    def post(self):

        data = request.get_json()

        message = data.get("message")
        receiver = data.get("receiver")
        sender = get_jwt_identity()

        new_message = Message(
            message = message,
            receiver = receiver,
            sender = sender
        )

        try:
            db.session.add(new_message)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {"error":str(e)}, 500
        
        return new_message.to_dict(), 200
    
api.add_resource(SendMessage, '/messages/send')

class ChatSend(Resource):
    @jwt_required()
    def post(self):
        data = request.get_json()
        sender_id = get_jwt_identity()
        user_message = data.get("message")
        receivers_id = request.args.get("user_id")

        if not user_message or not sender_id:
            return {"error": "Missing message or sender ID"}, 400

        try:
            # 1. Save user message
            user_msg_obj = Message(
                message=user_message,
                sender=sender_id,
                receiver=receivers_id
            )
            db.session.add(user_msg_obj)
            db.session.commit()

            user = User.query.filter_by(id=receivers_id).first()
            detail = MoreDetail.query.filter_by(user_id=receivers_id).first()

            if not user or not detail:
                return {"error": "Receiver not found or missing details."}, 404

            system_prompt = (
                f"You are {user.display_name}, a professional {detail.jobTitle}. "
                "You represent a trusted service provider on a client-focused platform. "
                "You help clients by answering questions, providing service details, and responding professionally. "
                "Stay focused on your area of expertise and avoid behaving like a general-purpose chatbot. "
                "Respond clearly, respectfully, and knowledgeably as a human expert in your field."
                "Break down the services one by one with their respective prices. "
                "Always calculate and present the total at the end. "
                "If you're unsure about a price, provide an estimate."
            )

            # 2. Call OpenAI with stored user message
            response = client.chat.completions.create(
                model=("gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
            )
            ai_message_text = response.choices[0].message.content

            # 3. Save AI response
            ai_msg_obj = Message(
                message=ai_message_text,
                sender=receivers_id,  # AI "sender" could be receiver_id or a special bot user ID
                receiver=sender_id
            )
            db.session.add(ai_msg_obj)
            db.session.commit()

            # 4. Return both messages or just AI message
            return {
                "user_message": user_msg_obj.to_dict(),
                "ai_response": ai_msg_obj.to_dict()
            }, 200

        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

api.add_resource(ChatSend, "/chat/send")

class GetMessages(Resource):
    @jwt_required()
    def get(self):
        current_user_id = get_jwt_identity()
        other_user_id = request.args.get('user_id')

        messages = Message.query.filter(
            ((Message.sender == current_user_id) & (Message.receiver == other_user_id)) |
            ((Message.sender == other_user_id) & (Message.receiver == current_user_id))
        ).order_by(Message.timestamp.asc()).all()

        user = User.query.filter_by(id=other_user_id).first()

        message_list = [{
            "id": m.id,
            "sender": m.sender,
            "receiver": m.receiver,
            "message": m.message,
            "receiver_name": user.display_name,
            "timestamp": m.timestamp.isoformat()
        } for m in messages]

        return message_list, 200

api.add_resource(GetMessages, '/messages')

class UserOrder(Resource):
    @jwt_required()
    def post(self):

        data = request.get_json()

        buyer = get_jwt_identity()
        seller = data.get('seller')

        new_order = Order(
            buyer = buyer,
            seller = seller
        )

        items_data = data.get("order_items", [])

        for item in items_data:

            description = item.get("description")
            price = item.get('price')

            new_order_item = OrderItem(
                description = description,
                price = price,
            )

            new_order.order_items.append(new_order_item)
        
        try:
            db.session.add(new_order)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({"Error":str(e)}), 500
        
        return jsonify({"Message":"Order Craeted successfully"})
    
    def get(self,id):

        order = Order.query.filter_by(buyer=id).first()

        if not order:
            return jsonify({"Error":"The order was not found"})
        
        return jsonify(order.to_dict()), 200

api.add_resource(UserOrder, '/order', "/order/<int:id>")

if __name__ == '__main__':
    app.run(debug=True, port=1737)