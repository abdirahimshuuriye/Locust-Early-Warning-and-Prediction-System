from flask import Flask, render_template, request, redirect, url_for, session, Response
import pandas as pd
import joblib
import csv
from io import StringIO
from io import BytesIO
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email_config import EMAIL_ADDRESS, EMAIL_PASSWORD
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

from config import db, cursor

app = Flask(__name__)
app.secret_key = "locust_secret_key_2026"

lr_model = joblib.load("ml/models/logistic_regression_model.pkl")
svm_model = joblib.load("ml/models/svm_model.pkl")
model = joblib.load("ml/models/saved_model.pkl")
target_encoder = joblib.load("ml/models/target_encoder.pkl")
def calculate_model_metrics():
    df = pd.read_csv("dataset/LocustLensFinalDataset.csv")

    target_encoder_metrics = joblib.load("ml/models/target_encoder.pkl")
    df["LOCUSTPRESENT"] = target_encoder_metrics.transform(df["LOCUSTPRESENT"])

    X = df.drop("LOCUSTPRESENT", axis=1)
    y = df["LOCUSTPRESENT"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    lr_predictions = lr_model.predict(X_test)
    svm_predictions = svm_model.predict(X_test)

    metrics = {
        "lr": {
            "accuracy": round(accuracy_score(y_test, lr_predictions) * 100, 2),
            "precision": round(precision_score(y_test, lr_predictions) * 100, 2),
            "recall": round(recall_score(y_test, lr_predictions) * 100, 2),
            "f1": round(f1_score(y_test, lr_predictions) * 100, 2)
        },
        "svm": {
            "accuracy": round(accuracy_score(y_test, svm_predictions) * 100, 2),
            "precision": round(precision_score(y_test, svm_predictions) * 100, 2),
            "recall": round(recall_score(y_test, svm_predictions) * 100, 2),
            "f1": round(f1_score(y_test, svm_predictions) * 100, 2)
        }
    }

    return metrics


model_metrics = calculate_model_metrics()


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/dashboard")
def dashboard():
    if "logged_in" not in session:
        return redirect(url_for("login"))

    cursor.execute("SELECT COUNT(*) FROM predictions")
    total_predictions = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM predictions WHERE risk_level = 'High Risk'")
    high_risk_alerts = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM predictions WHERE risk_level = 'Low Risk'")
    low_risk_alerts = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    if total_predictions > 0:
        high_risk_percentage = round((high_risk_alerts / total_predictions) * 100, 2)
        low_risk_percentage = round((low_risk_alerts / total_predictions) * 100, 2)
    else:
        high_risk_percentage = 0
        low_risk_percentage = 0

    cursor.execute("""
        SELECT region, country, risk_level, prediction_date
        FROM predictions
        ORDER BY prediction_date DESC
        LIMIT 5
    """)
    recent_predictions = cursor.fetchall()

    cursor.execute("""
        SELECT start_month, COUNT(*)
        FROM predictions
        GROUP BY start_month
        ORDER BY start_month ASC
    """)
    monthly_data = cursor.fetchall()

    month_names = []
    month_counts = []

    month_map = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
        5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
        9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }

    for row in monthly_data:
        month_names.append(month_map.get(row[0], str(row[0])))
        month_counts.append(row[1])

    trend_months = month_names
    trend_counts = month_counts

    return render_template(
        "dashboard.html",
        total_predictions=total_predictions,
        high_risk_alerts=high_risk_alerts,
        low_risk_alerts=low_risk_alerts,
        total_users=total_users,
        high_risk_percentage=high_risk_percentage,
        low_risk_percentage=low_risk_percentage,
        recent_predictions=recent_predictions,
        month_names=month_names,
        month_counts=month_counts,

        trend_months=trend_months,
        trend_counts=trend_counts,

        best_model="SVM",
        model_accuracy="97.85%"
    )

@app.route("/register", methods=["GET", "POST"])
def register():
    success = None
    error = None

    if request.method == "POST":
        full_name = request.form["full_name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        role = request.form["role"]

        if password != confirm_password:
            error = "Passwords do not match."
        elif role not in ["Farmer", "Organization"]:
            error = "Invalid role selected."
        else:
            cursor.execute(
                "SELECT * FROM users WHERE email=%s",
                (email,)
            )
            existing_user = cursor.fetchone()

            if existing_user:
                error = "Email already exists."
            else:
                cursor.execute("""
                    INSERT INTO users (full_name, email, password, role)
                    VALUES (%s, %s, %s, %s)
                """, (
                    full_name,
                    email,
                    password,
                    role
                ))

                cursor.execute("""
                    INSERT INTO activity_logs
                    (user_name, activity)
                    VALUES (%s, %s)
                """, (
                    full_name,
                    f"Registered new {role} account"
                ))

                db.commit()

                success = "Account created successfully. You can now login."

    return render_template(
        "register.html",
        success=success,
        error=error
    )

def send_farmer_alert_email(region, country, risk_level, result, confidence_score, explanation, recommendation):
    try:
        cursor.execute("""
            SELECT full_name, email
            FROM users
            WHERE role = 'Farmer'
              AND email IS NOT NULL
              AND email != ''
        """)

        farmers = cursor.fetchall()

        if not farmers:
            return 0

        sent_count = 0

        for farmer in farmers:
            farmer_name = farmer[0]
            farmer_email = farmer[1]

            subject = "Locust Outbreak Warning Alert"

            body = f"""
Dear {farmer_name},

A high-risk locust outbreak prediction has been detected by the Locust Early Warning and Prediction System.

Prediction Details:
Region: {region}
Country: {country}
Prediction Result: {result}
Risk Level: {risk_level}
Confidence Score: {confidence_score}%

Explanation:
{explanation}

Recommended Action:
{recommendation}

Please monitor your farm area and prepare early control actions.

Locust Early Warning and Prediction System
"""

            message = MIMEMultipart()
            message["From"] = EMAIL_ADDRESS
            message["To"] = farmer_email
            message["Subject"] = subject

            message.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, farmer_email, message.as_string())
            server.quit()

            sent_count += 1

        return sent_count

    except Exception as e:
        print("Email sending error:", e)
        return 0


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        cursor.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s AND role=%s",
            (email, password, role)
        )
        user = cursor.fetchone()

        if user:
            session["logged_in"] = True
            session["user_id"] = user[0]
            session["full_name"] = user[1]
            session["email"] = user[2]
            session["role"] = user[4]

            cursor.execute("""
                INSERT INTO activity_logs
                (user_name, activity)
                VALUES (%s, %s)
            """, (
                user[1],
                "Logged into the system"
            ))

            db.commit()

            return redirect(url_for("dashboard"))

        error = "Invalid email, password, or role"

    return render_template("login.html", error=error)

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    success = None
    error = None

    if request.method == "POST":

        email = request.form["email"]

        cursor.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        user = cursor.fetchone()

        if user:

            return redirect(
                url_for(
                    "reset_password",
                    email=email
                )
            )

        else:
            error = "Email not found."

    return render_template(
        "forgot_password.html",
        success=success,
        error=error
    )


@app.route("/reset-password/<email>", methods=["GET", "POST"])
def reset_password(email):
    error = None

    if request.method == "POST":
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:
            error = "Passwords do not match."
        else:
            cursor.execute("""
                UPDATE users
                SET password=%s
                WHERE email=%s
            """, (
                new_password,
                email
            ))

            db.commit()

            return redirect(url_for("login"))

    return render_template(
        "reset_password.html",
        email=email,
        error=error
    )

@app.route("/profile")
def profile():
    if "logged_in" not in session:
        return redirect(url_for("login"))

    cursor.execute("""
        SELECT user_id, full_name, email, role, created_at
        FROM users
        WHERE email=%s
    """, (session["email"],))

    user = cursor.fetchone()

    return render_template("profile.html", user=user)


@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    if "logged_in" not in session:
        return redirect(url_for("login"))

    error = None
    success = None

    if request.method == "POST":
        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        cursor.execute(
            "SELECT password FROM users WHERE email=%s",
            (session["email"],)
        )
        user = cursor.fetchone()

        if not user:
            error = "User account not found."
        elif current_password != user[0]:
            error = "Current password is incorrect."
        elif new_password != confirm_password:
            error = "New password and confirm password do not match."
        elif len(new_password) < 4:
            error = "New password must be at least 4 characters."
        else:
            cursor.execute(
                "UPDATE users SET password=%s WHERE email=%s",
                (new_password, session["email"])
            )
            db.commit()
            success = "Password changed successfully."

    return render_template(
        "change_password.html",
        error=error,
        success=success
    )


@app.route("/users")
def users():
    if "logged_in" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Admin":
        return redirect(url_for("dashboard"))

    cursor.execute("""
        SELECT user_id, full_name, email, role, created_at
        FROM users
        ORDER BY user_id DESC
    """)
    users = cursor.fetchall()

    return render_template("users.html", users=users)


@app.route("/add-user", methods=["GET", "POST"])
def add_user():
    if "logged_in" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Admin":
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        full_name = request.form["full_name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        cursor.execute(
            "INSERT INTO users (full_name, email, password, role) VALUES (%s,%s,%s,%s)",
            (full_name, email, password, role)
        )
        db.commit()

        return redirect(url_for("users"))

    return render_template("add_user.html")


@app.route("/edit-user/<int:user_id>", methods=["GET", "POST"])
def edit_user(user_id):
    if "logged_in" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Admin":
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        full_name = request.form["full_name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        cursor.execute("""
            UPDATE users
            SET full_name=%s, email=%s, password=%s, role=%s
            WHERE user_id=%s
        """, (full_name, email, password, role, user_id))
        db.commit()

        return redirect(url_for("users"))

    cursor.execute(
        "SELECT user_id, full_name, email, password, role FROM users WHERE user_id=%s",
        (user_id,)
    )
    user = cursor.fetchone()

    return render_template("edit_user.html", user=user)


@app.route("/delete-user/<int:user_id>")
def delete_user(user_id):
    if "logged_in" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Admin":
        return redirect(url_for("dashboard"))

    cursor.execute(
        "SELECT full_name FROM users WHERE user_id=%s",
        (user_id,)
    )
    deleted_user = cursor.fetchone()

    cursor.execute(
        "DELETE FROM users WHERE user_id=%s",
        (user_id,)
    )

    if deleted_user:
        cursor.execute("""
            INSERT INTO activity_logs
            (user_name, activity)
            VALUES (%s, %s)
        """, (
            session.get("full_name", session.get("email", "Unknown User")),
            f"Deleted user {deleted_user[0]}"
        ))

    db.commit()

    return redirect(url_for("users"))

@app.route("/reports")
def reports():
    if "logged_in" not in session:
        return redirect(url_for("login"))

    # Admin, Organization and Farmer can view reports
    if session["role"] not in ["Admin", "Organization", "Farmer"]:
        return redirect(url_for("dashboard"))

    region = request.args.get("region", "")
    country = request.args.get("country", "")
    risk_level = request.args.get("risk_level", "")

    sql = """
        SELECT prediction_id, region, country, start_year, start_month, ppt, tmax,
               soil_moisture, prediction_result, risk_level, prediction_date
        FROM predictions
        WHERE 1=1
    """

    values = []

    if region:
        sql += " AND region LIKE %s"
        values.append("%" + region + "%")

    if country:
        sql += " AND country LIKE %s"
        values.append("%" + country + "%")

    if risk_level:
        sql += " AND risk_level = %s"
        values.append(risk_level)

    sql += " ORDER BY prediction_date DESC"

    cursor.execute(sql, tuple(values))
    predictions = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM predictions")
    total_predictions = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM predictions WHERE risk_level = 'High Risk'")
    high_risk = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM predictions WHERE risk_level = 'Low Risk'")
    low_risk = cursor.fetchone()[0]

    return render_template(
        "reports.html",
        predictions=predictions,
        total_predictions=total_predictions,
        high_risk=high_risk,
        low_risk=low_risk,
        region=region,
        country=country,
        risk_level=risk_level
    )

@app.route("/export-csv")
def export_csv():
    if "logged_in" not in session:
        return redirect(url_for("login"))

    if session["role"] not in ["Admin", "Organization"]:
        return redirect(url_for("dashboard"))

    cursor.execute("""
        SELECT region, country, start_year, start_month, ppt, tmax,
               soil_moisture, prediction_result, risk_level, prediction_date
        FROM predictions
        ORDER BY prediction_date DESC
    """)
    rows = cursor.fetchall()

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Region", "Country", "Year", "Month", "PPT", "TMAX",
        "Soil Moisture", "Prediction", "Risk", "Date"
    ])

    for row in rows:
        writer.writerow(row)

    output.seek(0)

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=locust_report.csv"}
    )

@app.route("/export-pdf")
def export_pdf():
    if "logged_in" not in session:
        return redirect(url_for("login"))

    if session["role"] not in ["Admin", "Organization"]:
        return redirect(url_for("dashboard"))

    cursor.execute("""
        SELECT region, country, start_year, start_month, ppt, tmax,
               soil_moisture, prediction_result, risk_level, prediction_date
        FROM predictions
        ORDER BY prediction_date DESC
    """)
    rows = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM predictions")
    total_predictions = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM predictions WHERE risk_level = 'High Risk'")
    high_risk = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM predictions WHERE risk_level = 'Low Risk'")
    low_risk = cursor.fetchone()[0]

    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    elements = []

    title = Paragraph("Locust Prediction System Report", styles["Title"])
    elements.append(title)
    elements.append(Spacer(1, 12))

    summary = Paragraph(
        f"""
        Total Predictions: {total_predictions}<br/>
        High Risk: {high_risk}<br/>
        Low Risk: {low_risk}<br/>
        Best Model: SVM<br/>
        Model Accuracy: 97.85%
        """,
        styles["BodyText"]
    )

    elements.append(summary)
    elements.append(Spacer(1, 15))

    data = [[
        "Region",
        "Country",
        "Year",
        "Month",
        "PPT",
        "TMAX",
        "Soil",
        "Result",
        "Risk",
        "Date"
    ]]

    for row in rows:
        data.append(list(row))

    table = Table(data, repeatRows=1)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkgreen),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]))

    elements.append(table)

    pdf.build(elements)

    buffer.seek(0)

    return Response(
        buffer,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=locust_prediction_report.pdf"
        }
    )


@app.route("/edit-prediction/<int:prediction_id>", methods=["GET", "POST"])
def edit_prediction(prediction_id):
    if "logged_in" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Admin":
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        region = request.form["region"]
        country = request.form["country"]
        ppt = request.form["ppt"]
        tmax = request.form["tmax"]
        soil_moisture = request.form["soil_moisture"]

        cursor.execute("""
            UPDATE predictions
            SET region=%s,
                country=%s,
                ppt=%s,
                tmax=%s,
                soil_moisture=%s
            WHERE prediction_id=%s
        """, (
            region,
            country,
            ppt,
            tmax,
            soil_moisture,
            prediction_id
        ))

        cursor.execute("""
            INSERT INTO activity_logs
            (user_name, activity)
            VALUES (%s, %s)
        """, (
            session.get("full_name", session.get("email", "Unknown User")),
            f"Edited prediction for {region}"
        ))

        db.commit()

        return redirect(url_for("reports"))

    cursor.execute("""
        SELECT prediction_id, region, country, start_year, start_month, ppt,
               tmax, soil_moisture, prediction_result, risk_level, prediction_date
        FROM predictions
        WHERE prediction_id=%s
    """, (prediction_id,))

    prediction = cursor.fetchone()

    return render_template("edit_prediction.html", prediction=prediction)

@app.route("/delete-prediction/<int:prediction_id>")
def delete_prediction(prediction_id):
    if "logged_in" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Admin":
        return redirect(url_for("dashboard"))

    cursor.execute(
        "SELECT region FROM predictions WHERE prediction_id=%s",
        (prediction_id,)
    )
    prediction = cursor.fetchone()

    cursor.execute(
        "DELETE FROM predictions WHERE prediction_id=%s",
        (prediction_id,)
    )

    if prediction:
        cursor.execute("""
            INSERT INTO activity_logs
            (user_name, activity)
            VALUES (%s, %s)
        """, (
            session.get("full_name", session.get("email", "Unknown User")),
            f"Deleted prediction for {prediction[0]}"
        ))

    db.commit()

    return redirect(url_for("reports"))


@app.route("/prediction", methods=["GET", "POST"])
def prediction():
    if "logged_in" not in session:
        return redirect(url_for("login"))

    # Only Admin and Organization can create predictions
    if session["role"] not in ["Admin", "Organization"]:
        return redirect(url_for("dashboard"))

    result = None
    risk_level = None
    message = None
    explanation = None
    recommendation = None
    confidence_score = None
    selected_model_name = "Support Vector Machine (SVM)"

    accuracy_score_value = None
    precision_score_value = None
    recall_score_value = None
    f1_score_value = None

    if request.method == "POST":
        region = request.form["region"]
        country = request.form["country"]
        startyear = int(request.form["startyear"])
        startmonth = int(request.form["startmonth"])
        ppt = float(request.form["ppt"])
        tmax = float(request.form["tmax"])
        soilmoisture = float(request.form["soilmoisture"])

        selected_model = request.form["model"]

        input_data = pd.DataFrame([{
            "REGION": region,
            "COUNTRYNAME": country,
            "STARTYEAR": startyear,
            "STARTMONTH": startmonth,
            "PPT": ppt,
            "TMAX": tmax,
            "SOILMOISTURE": soilmoisture
        }])

        if selected_model == "lr":
            selected_model_name = "Logistic Regression (LR)"
            active_model = lr_model
            selected_metrics = model_metrics["lr"]
        else:
            selected_model_name = "Support Vector Machine (SVM)"
            active_model = svm_model
            selected_metrics = model_metrics["svm"]

        accuracy_score_value = selected_metrics["accuracy"]
        precision_score_value = selected_metrics["precision"]
        recall_score_value = selected_metrics["recall"]
        f1_score_value = selected_metrics["f1"]

        prediction_value = active_model.predict(input_data)
        prediction_label = target_encoder.inverse_transform(prediction_value)[0]

        if hasattr(active_model, "predict_proba"):
            probabilities = active_model.predict_proba(input_data)[0]
            confidence_score = round(max(probabilities) * 100, 2)
        else:
            confidence_score = accuracy_score_value

        result = prediction_label.upper()

        if prediction_label.lower() == "yes":
            risk_level = "High Risk"
            message = "Warning: Locust outbreak risk detected."

            explanation = (
                "The system detected environmental conditions that may support "
                "locust breeding and outbreak development. Rainfall, temperature, "
                "and soil moisture values indicate a possible high-risk situation."
            )

            recommendation = (
                "Immediate field monitoring, early warning communication, and "
                "preparedness for control actions are recommended for this region."
            )

        else:
            risk_level = "Low Risk"
            message = "No locust outbreak risk detected."

            explanation = (
                "The entered environmental conditions do not strongly indicate "
                "locust outbreak development at this time."
            )

            recommendation = (
                "Continue routine monitoring and update the system when new "
                "environmental data becomes available."
            )

        cursor.execute("""
            INSERT INTO predictions
            (
                region, country, start_year, start_month, ppt, tmax,
                soil_moisture, prediction_result, risk_level
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            region,
            country,
            startyear,
            startmonth,
            ppt,
            tmax,
            soilmoisture,
            result,
            risk_level
        ))

        cursor.execute("""
            INSERT INTO activity_logs
            (user_name, activity)
            VALUES (%s, %s)
        """, (
            session.get("full_name", session.get("email", "Unknown User")),
            f"Created prediction for {region} using {selected_model_name} - {risk_level}"
        ))

        if risk_level == "High Risk":
            sent_count = send_farmer_alert_email(
                region,
                country,
                risk_level,
                result,
                confidence_score,
                explanation,
                recommendation
            )

            cursor.execute("""
                INSERT INTO activity_logs
                (user_name, activity)
                VALUES (%s, %s)
            """, (
                session.get("full_name", session.get("email", "Unknown User")),
                f"Email alert sent to {sent_count} farmer(s) for {region}"
            ))

        db.commit()

    return render_template(
        "prediction.html",
        result=result,
        risk_level=risk_level,
        message=message,
        explanation=explanation,
        recommendation=recommendation,
        confidence_score=confidence_score,
        selected_model_name=selected_model_name,
        accuracy_score_value=accuracy_score_value,
        precision_score_value=precision_score_value,
        recall_score_value=recall_score_value,
        f1_score_value=f1_score_value
    )



@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    if "logged_in" not in session:
        return redirect(url_for("login"))

    success = None
    error = None

    if request.method == "POST":
        full_name = request.form["full_name"]
        email = request.form["email"]
        message = request.form["message"]

        if full_name == "" or email == "" or message == "":
            error = "All fields are required."
        else:
            cursor.execute("""
                INSERT INTO feedbacks (full_name, email, message)
                VALUES (%s, %s, %s)
            """, (full_name, email, message))

            cursor.execute("""
                INSERT INTO activity_logs
                (user_name, activity)
                VALUES (%s, %s)
            """, (
                session.get("full_name", session.get("email", "Unknown User")),
                "Submitted feedback"
            ))

            db.commit()

            success = "Feedback submitted successfully."

    return render_template(
        "feedback.html",
        success=success,
        error=error
    )


@app.route("/feedbacks")
def feedbacks():
    if "logged_in" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Admin":
        return redirect(url_for("dashboard"))

    cursor.execute("""
        SELECT feedback_id, full_name, email, message, created_at
        FROM feedbacks
        ORDER BY created_at DESC
    """)

    feedback_list = cursor.fetchall()

    return render_template(
        "feedbacks.html",
        feedbacks=feedback_list
    )


@app.route("/delete-feedback/<int:feedback_id>")
def delete_feedback(feedback_id):
    if "logged_in" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Admin":
        return redirect(url_for("dashboard"))

    cursor.execute(
        "DELETE FROM feedbacks WHERE feedback_id=%s",
        (feedback_id,)
    )

    db.commit()

    return redirect(url_for("feedbacks"))
@app.route("/risk-map")
def risk_map():
    if "logged_in" not in session:
        return redirect(url_for("login"))

    somalia_regions = [
        "Awdal", "Woqooyi Galbeed", "Togdheer", "Sool", "Sanaag",
        "Bari", "Nugaal", "Mudug", "Galgaduud", "Hiiraan",
        "Middle Shabelle", "Lower Shabelle", "Bay", "Bakool",
        "Gedo", "Middle Juba", "Lower Juba", "Banadir"
    ]

    cursor.execute("""
        SELECT region, risk_level, prediction_date
        FROM predictions
        ORDER BY prediction_date DESC
    """)
    rows = cursor.fetchall()

    latest_region = None
    latest_risk = None
    latest_date = None

    if rows:
        latest_region = rows[0][0]
        latest_risk = rows[0][1]
        latest_date = rows[0][2]

    latest_risks = {}

    for row in rows:
        region = row[0]
        risk = row[1]
        date = row[2]

        if region not in latest_risks:
            latest_risks[region] = {
                "risk": risk,
                "date": date
            }

    map_data = []

    high_risk_count = 0
    low_risk_count = 0
    no_data_count = 0

    for region in somalia_regions:
        if region in latest_risks:
            risk = latest_risks[region]["risk"]
            date = latest_risks[region]["date"]
        else:
            risk = "No Data"
            date = "N/A"

        if risk == "High Risk":
            high_risk_count += 1
        elif risk == "Low Risk":
            low_risk_count += 1
        else:
            no_data_count += 1

        map_data.append({
            "region": region,
            "risk": risk,
            "date": date
        })

    total_regions = len(somalia_regions)

    return render_template(
        "risk_map.html",
        map_data=map_data,
        total_regions=total_regions,
        high_risk_count=high_risk_count,
        low_risk_count=low_risk_count,
        no_data_count=no_data_count,
        latest_region=latest_region,
        latest_risk=latest_risk,
        latest_date=latest_date
    )
@app.route("/activity-logs")
def activity_logs():

    if "logged_in" not in session:
        return redirect(url_for("login"))

    if session["role"] != "Admin":
        return redirect(url_for("dashboard"))

    cursor.execute("""
        SELECT *
        FROM activity_logs
        ORDER BY activity_date DESC
    """)

    logs = cursor.fetchall()

    return render_template(
        "activity_logs.html",
        logs=logs
    )
@app.route("/model-comparison")
def model_comparison():

    if "logged_in" not in session:
        return redirect(url_for("login"))

    if session["role"] not in ["Admin", "Organization"]:
        return redirect(url_for("dashboard"))

    logistic_accuracy = 94.20
    svm_accuracy = 97.85

    return render_template(
        "model_comparison.html",
        logistic_accuracy=logistic_accuracy,
        svm_accuracy=svm_accuracy
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)