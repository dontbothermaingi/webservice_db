from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# To enable us to use Oject Relational Mapping on the classes
# The classes will be mapped to tables enabling us to use methods and objects to access or manipulate data in that table
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String)
    last_name = db.Column(db.String)
    display_name = db.Column(db.String)
    date_of_birth = db.Column(db.Date)
    email = db.Column(db.String)
    username = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    role = db.Column(db.String)

    sent_messages = db.relationship('Message', foreign_keys='Message.sender', backref='sender_user', lazy=True)
    received_messages = db.relationship('Message', foreign_keys='Message.receiver', backref='sender_receiver', lazy=True)
    more_details = db.relationship("MoreDetail", foreign_keys='MoreDetail.user_id', backref='user_detail', lazy=True)
    services = db.relationship("Service", foreign_keys='Service.user_id', backref='user_service', lazy=True)
    bought_orders = db.relationship("Order", foreign_keys="Order.buyer", backref="buyer_order", lazy=True)
    sold_orders = db.relationship("Order", foreign_keys="Order.seller", backref="seller_order", lazy=True)


    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "display_name": self.display_name,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "email": self.email,
            "username": self.username,
            "password": self.password,
            "role": self.role,
            "sent_messages":[message.to_dict() for message in self.sent_messages],
            "received_messages":[message.to_dict() for message in self.received_messages],
            "more_details":[detail.to_dict() for detail in self.more_details],
            "services":[service.to_dict() for service in self.services],
        }
    
    def __repr__(self):
        return (f"<User(id={self.id}, first_name={self.first_name}, last_name={self.last_name}, username={self.username})>")
    
class MoreDetail(db.Model):
    __tablename__ = 'more_details'
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String)
    jobTitle =  db.Column(db.String)
    description = db.Column(db.String)
    detailedDescription = db.Column(db.String)
    payRate = db.Column(db.String)
    completionRate = db.Column(db.String)
    rating = db.Column(db.String)
    location = db.Column(db.String)
    responseTime = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    def to_dict(self):
        return{
            "id": self.id,
            "category":self.category,
            "jobTitle":self.jobTitle,
            "description": self.description,
            "detailedDescription": self.detailedDescription,
            "payRate": self.payRate,
            "completionRate": self.completionRate,
            "rating":self.rating,
            "location": self.location,
            "responseTime":self.responseTime,
            "user_id": self.user_id
        }
    
    def __repr__(self):
        return (f"<MoreDetail(id={self.id} category={self.category} jobTitle={self.jobTitle} description={self.description})>")

class Service(db.Model):
    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    def to_dict(self):
        return{
            "id": self.id,
            "service": self.service,
            "user_id": self.user_id
        }
    
    def __repr__(self):
         return {f"<Service(id={self.id} service={self.service})>"}

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String)
    receiver = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sender = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return{
            'id': self.id,
            'message':self.message,
            'receiver':self.receiver,
            'sender':self.sender
        }
    
    def __repr__(self):
        return (f"<Message(id={self.id} message={self.message} receiver={self.receiver} sender={self.sender})>")


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    buyer = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    seller = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    order_items = db.relationship("OrderItem", foreign_keys="OrderItem.order_id", backref='order_item', lazy=True)

    def calculate_total_price(self):
        total_price = 0
        for item in self.order_items:
            total_price += item.price
        
        return total_price

    def to_dict(self):
        return{
            "id":self.id,
            "buyer": self.buyer,
            "seller": self.seller,
            "order_items": [
                {
                    "order_item_id":item.id,
                    "descriprion":item.descriprion,
                    "item.price":item.price
                }
                for item in self.order_items
            ],
            "total_price": self.calculate_total_price()
        }

    def __repr__(self):
        return {f"<Order(id={self.id} buyer={self.buyer} seller={self.seller})>"}
    
class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String)
    price = db.Column(db.Float)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)

    def to_dict(self):
        return{
            "id":self.id,
            "descriprion":self.description,
            "price":self.price,
            "order_id":self.order_id
        }
    
    def __repr__(self):
        return {f"<OrderItem(id={self.id} descriptio={self.description}, price={self.price})"}
