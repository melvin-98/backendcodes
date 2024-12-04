from flask import Flask, jsonify, request
import uuid  # Import uuid to use uuid.uuid4()
from bson.objectid import ObjectId

from pymongo import MongoClient
import os
app = Flask(__name__)
import traceback

# MongoDB Atlas connection string (replace with your actual MongoDB connection URI)
client  = MongoClient("mongodb+srv://whuser:whuser123@cluster0.dyykt.mongodb.net")

# Access the database and collections
db = client.WarehouseDB
orders_collection = db.orders
transactions_collection = db.transactions
user_logs_collection = db.user_logs
notifications_collection = db.notifications
products_collection = db.products
users_collection = db.users

# Root route for health check
@app.route('/')
def home():
    return jsonify({"message": "Welcome to the E-commerce API"}), 200

# Endpoint to retrieve all orders
@app.route('/orders', methods=['GET'])
def get_all_orders():
    try:
        orders = orders_collection.find({}, {
            "_id": 0, "user_id": 1, "products": 1, "totalAmount": 1, 
            "orderDate": 1, "status": 1
        }).limit(20)
        order_list = list(orders)
        return jsonify(order_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint to search for orders by user ID
@app.route('/orders/search', methods=['GET'])
def search_orders():
    user_id = request.args.get('user_id')
    
    try:
        query = {}
        if user_id:
            query["user_id"] = user_id
        
        orders = orders_collection.find(query, {
            "_id": 0, "user_id": 1, "products": 1, "totalAmount": 1, 
            "orderDate": 1, "status": 1
        }).limit(20)
        order_list = list(orders)
        return jsonify(order_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint to retrieve all products
@app.route('/products', methods=['GET'])
def get_all_products():
    try:
        # Query MongoDB with projection
        products = products_collection.find({}, {
            "_id": 1, "name": 1, "description": 1, "price": 1, 
            "category": 1, "stock": 1, "rating": 1, "reviews": 1, 
            "status": 1  # Correctly close the projection dictionary
        })

        product_list = []
        for product in products:
            # Convert ObjectId to string
            product['_id'] = str(product['_id'])
            product_list.append(product)

        # Return the product list with a 200 status code
        return jsonify(product_list), 200

    except Exception as e:
        # Log the error for debugging
        app.logger.error(f"Error occurred: {str(e)}")
        app.logger.error(traceback.format_exc())

        # Return a 500 error response with details
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500
# Endpoint to search for products by name or category
@app.route('/products/search', methods=['GET'])
def search_products():
    name = request.args.get('name')
    category = request.args.get('category')
    
    try:
        query = {}
        if name:
            query["name"] = {"$regex": name, "$options": "i"}
        if category:
            query["category"] = {"$regex": category, "$options": "i"}
        
        products = products_collection.find(query, {
            "_id": 0, "name": 1, "description": 1, "price": 1, 
            "category": 1, "stock": 1, "rating": 1, "reviews": 1, 
            "status": 1
        }).limit(20)
        product_list = list(products)
        return jsonify(product_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint to retrieve all users
@app.route('/users', methods=['GET'])
def get_all_users():
    try:
        users = users_collection.find({}, {
            "_id": 0, "username": 1, "fullName": 1, "email": 1, 
            "roles": 1, "status": 1, "address": 1, "preferences": 1, 
            "createdAt": 1, "lastUpdated": 1, "activity": 1, 
            "notifications": 1
        }).limit(20)
        user_list = list(users)
        return jsonify(user_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint to search for users by username or email
@app.route('/users/search', methods=['GET'])
def search_users():
    username = request.args.get('username')
    email = request.args.get('email')
    
    try:
        query = {}
        if username:
            query["username"] = {"$regex": username, "$options": "i"}
        if email:
            query["email"] = {"$regex": email, "$options": "i"}
        
        users = users_collection.find(query, {
            "_id": 0, "username": 1, "fullName": 1, "email": 1, 
            "roles": 1, "status": 1, "address": 1, "preferences": 1, 
            "createdAt": 1, "lastUpdated": 1, "activity": 1, 
            "notifications": 1
        }).limit(20)
        user_list = list(users)
        return jsonify(user_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Endpoint to add a new product
@app.route('/products', methods=['POST'])
def add_product():
    try:
        # Get JSON data from the request
        
        data = request.get_json()
        app.logger.info(f"Received data: {data}")
        # Validate required fields
        required_fields = ['name', 'description', 'price', 'category', 'quantity']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"'{field}' is required"}), 400

        # Generate a unique ID for the product

        # Create the product document
        new_product = {
            
            "name": data['name'],
            "description": data['description'],
            "price": float(data['price']),
            "category": data['category'],
            "imageURL": data.get('image', None),  # Use get() to avoid KeyError

            "quantity": int(data['quantity']),
        }

        # Insert the product into the database
        inserted_product = products_collection.insert_one(new_product)

        # Retrieve the inserted document and convert ObjectId to string
        inserted_product_id = str(inserted_product.inserted_id)
        # Return the newly created product
        return jsonify({
            "message": "Product added successfully",
            "product": {**new_product, "_id": inserted_product_id}
        }), 201
    except KeyError as e:
        app.logger.error(f"KeyError: {e}")
        return jsonify({"error": f"Missing field: {e.args[0]}"}), 400
    except Exception as e:
        app.logger.error(f"Error occurred: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
@app.route('/products/<product_id>', methods=['PUT'])



def update_product(product_id):
    try:
        # Validate the product_id
        if not ObjectId.is_valid(product_id):
            return jsonify({"error": "Invalid product ID"}), 400

        # Get JSON data from the request
        data = request.get_json()
        app.logger.info(f"Received data for update: {data}")

        # Validate required fields (optional, only if some fields are mandatory for an update)
        updatable_fields = ['name', 'description', 'price', 'category', 'quantity', 'imageURL']
        update_data = {field: data[field] for field in updatable_fields if field in data}

        if not update_data:
            return jsonify({"error": "No valid fields provided for update"}), 400

        # Convert price and quantity to appropriate types if they exist
        if 'price' in update_data:
            update_data['price'] = float(update_data['price'])
        if 'quantity' in update_data:
            update_data['quantity'] = int(update_data['quantity'])

        # Update the product in the database
        result = products_collection.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": update_data}
        )

        # Check if the product was found and updated
        if result.matched_count == 0:
            return jsonify({"error": "Product not found"}), 404

        # Retrieve the updated product for confirmation
        updated_product = products_collection.find_one({"_id": ObjectId(product_id)})
        updated_product["_id"] = str(updated_product["_id"])  # Convert ObjectId to string

        return jsonify({
            "message": "Product updated successfully",
            "product": updated_product
        }), 200
    except Exception as e:
        app.logger.error(f"Error occurred while updating product: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        # Validate and convert product_id to ObjectId
        if not ObjectId.is_valid(product_id):
            return jsonify({"error": "Invalid product ID"}), 400

        # Attempt to delete the product
        result = products_collection.delete_one({"_id": ObjectId(product_id)})

        # Check if a product was deleted
        if result.deleted_count == 1:
            return jsonify({"message": "Product deleted successfully"}), 200
        else:
            return jsonify({"error": "Product not found"}), 404

    except Exception as e:
        app.logger.error(f"Error occurred while deleting product: {str(e)}")
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888)
