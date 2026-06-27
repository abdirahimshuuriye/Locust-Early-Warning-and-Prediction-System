import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="locust_prediction_db",
    port=8889
)

cursor = db.cursor()