from flask import Blueprint, request, jsonify
import os
import time
from datetime import datetime
from werkzeug.utils import secure_filename

from services.predictor import predict_image
from database.database import save_prediction, get_predictions


# ==============================
# Blueprint
# ==============================

predict_bp = Blueprint("predict", __name__)


# ==============================
# Upload Configuration
# ==============================

UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg"
}


# ==============================
# Disease Information
# ==============================

DISEASE_DETAILS = {

    "Melanoma": {
        "description":
        "Melanoma is a serious form of skin cancer that develops in melanocytes (pigment-producing cells).",

        "recommendation":
        "Consult a dermatologist immediately for proper diagnosis and treatment.",

        "risk":
        "HIGH"
    },


    "Basal Cell Carcinoma": {
        "description":
        "Basal Cell Carcinoma is the most common type of skin cancer and usually grows slowly.",

        "recommendation":
        "Visit a dermatologist for evaluation and treatment.",

        "risk":
        "MEDIUM"
    },


    "Actinic Keratoses": {
        "description":
        "Actinic Keratoses are rough, scaly skin patches caused by long-term sun exposure.",

        "recommendation":
        "Dermatologist consultation is recommended because it may develop into cancer.",

        "risk":
        "MEDIUM"
    },


    "Benign Keratosis": {
        "description":
        "Benign Keratosis is a harmless non-cancerous skin growth.",

        "recommendation":
        "Monitor changes in size, colour and shape.",

        "risk":
        "LOW"
    },


    "Dermatofibroma": {
        "description":
        "Dermatofibroma is a common benign skin nodule.",

        "recommendation":
        "Usually no treatment is required unless changes occur.",

        "risk":
        "LOW"
    },


    "Melanocytic Nevus": {
        "description":
        "Melanocytic Nevus is a common mole formed by pigment-producing cells.",

        "recommendation":
        "Monitor the mole for changes in colour, size or shape.",

        "risk":
        "LOW"
    },


    "Vascular Lesion": {
        "description":
        "Vascular lesions are skin abnormalities related to blood vessels.",

        "recommendation":
        "Consult dermatologist if the lesion changes, grows or bleeds.",

        "risk":
        "LOW"
    }

}



# ==============================
# File Validation
# ==============================

def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".",1)[1].lower()
        in ALLOWED_EXTENSIONS
    )



# ==============================
# Prediction Route
# ==============================


@predict_bp.route("/predict", methods=["POST"])
def predict():

    print("\n========== NEW REQUEST ==========")


    start_time = time.time()


    # Check image

    if "image" not in request.files:

        return jsonify({
            "error":"No image uploaded"
        }),400



    file = request.files["image"]



    if file.filename == "":

        return jsonify({
            "error":"No file selected"
        }),400



    if not allowed_file(file.filename):

        return jsonify({
            "error":"Only PNG JPG JPEG allowed"
        }),400


    # Patient details sent alongside the image from the frontend
    # form fields (#patientName / #gender). Optional so the route
    # still works if they're ever missing.

    patient_name = request.form.get("patientName", "").strip()

    gender = request.form.get("gender", "").strip()


    filename = secure_filename(file.filename)


    filepath = os.path.join(
        UPLOAD_FOLDER,
        filename
    )


    file.save(filepath)



    try:

        print("Running AI prediction...")


        # MODEL PREDICTION

        result = predict_image(filepath)


        print("MODEL RESULT:", result)



        disease = result["disease"].strip()


        confidence = float(result["confidence"])



        print("Predicted Disease:", disease)



        # ==============================
        # Disease Details Matching
        # ==============================


        details = DISEASE_DETAILS.get(disease)



        # Case insensitive search

        if details is None:

            for key in DISEASE_DETAILS:

                if key.lower() == disease.lower():

                    details = DISEASE_DETAILS[key]

                    break



        # Default

        if details is None:

            details = {

                "description":
                "No description available",

                "recommendation":
                "Consult dermatologist",

                "risk":
                "UNKNOWN"

            }




        result["description"] = details["description"]

        result["recommendation"] = details["recommendation"]

        result["risk"] = details["risk"]




        # ==============================
        # Time Details
        # ==============================


        total_time = round(
            time.time()-start_time,
            2
        )


        result["prediction_time"] = (
            f"{total_time} sec"
        )


        result["date"] = datetime.now().strftime(
            "%d %b %Y %I:%M:%S %p"
        )



        # ==============================
        # Confidence Status
        # ==============================


        if confidence >= 90:

            result["status"] = "Very High Confidence"


        elif confidence >= 75:

            result["status"] = "High Confidence"


        elif confidence >= 50:

            result["status"] = "Moderate Confidence"


        else:

            result["status"] = "Low Confidence"




        result["disclaimer"] = (
            "AI prediction only. "
            "Consult a dermatologist for medical diagnosis."
        )




        # ==============================
        # Save Database
        # ==============================


        save_prediction(

            disease=result["disease"],

            confidence=result["confidence"],

            risk=result["risk"],

            prediction_time=result["prediction_time"],

            date=result["date"],

            patient_name=patient_name,

            gender=gender

        )



        print("Prediction saved successfully")



        return jsonify(result)



    except Exception as e:


        print("ERROR:",e)


        return jsonify({

            "error":str(e)

        }),500




    finally:


        if os.path.exists(filepath):

            os.remove(filepath)

            print("Temporary file removed")





# ==============================
# Prediction History (raw JSON — for other tools/scripts)
# ==============================


@predict_bp.route("/history", methods=["GET"])
def history():


    predictions = get_predictions()


    data=[]


    for row in predictions:

        data.append({

            "id":row[0],

            "patient_name":row[1],

            "gender":row[2],

            "disease":row[3],

            "confidence":row[4],

            "risk":row[5],

            "prediction_time":row[6],

            "date":row[7]

        })


    return jsonify(data)



# ==============================
# Prediction History (readable HTML page for you, the developer)
# Visit http://127.0.0.1:5000/history/view in a browser
# ==============================


RISK_COLORS = {
    "HIGH": "#e74c3c",
    "MEDIUM": "#f39c12",
    "LOW": "#2ecc71",
}


@predict_bp.route("/history/view", methods=["GET"])
def history_view():

    predictions = get_predictions()

    rows_html = ""

    for row in predictions:

        (
            row_id, patient_name, gender, disease,
            confidence, risk, prediction_time, date
        ) = row

        risk_color = RISK_COLORS.get((risk or "").upper(), "#777")

        rows_html += f"""
        <tr>
            <td>{row_id}</td>
            <td>{patient_name or '-'}</td>
            <td>{gender or '-'}</td>
            <td>{disease or '-'}</td>
            <td>{confidence if confidence is not None else '-'}%</td>
            <td><span style="background:{risk_color};color:#fff;
                padding:3px 10px;border-radius:12px;font-size:11px;
                font-weight:600;">{risk or '-'}</span></td>
            <td>{prediction_time or '-'}</td>
            <td>{date or '-'}</td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Prediction History</title>
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                background: #f4f7fb;
                padding: 30px;
                color: #222;
            }}
            h1 {{ color: #1565c0; }}
            table {{
                width: 100%;
                border-collapse: collapse;
                background: #fff;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 4px 20px rgba(0,0,0,.08);
            }}
            th, td {{
                padding: 10px 14px;
                text-align: left;
                font-size: 13px;
                border-bottom: 1px solid #eee;
            }}
            th {{
                background: #1565c0;
                color: #fff;
            }}
            tr:hover {{ background: #f8fbff; }}
        </style>
    </head>
    <body>
        <h1>🧬 Prediction History ({len(predictions)})</h1>
        <table>
            <tr>
                <th>ID</th>
                <th>Patient</th>
                <th>Gender</th>
                <th>Disease</th>
                <th>Confidence</th>
                <th>Risk</th>
                <th>Time</th>
                <th>Date</th>
            </tr>
            {rows_html}
        </table>
    </body>
    </html>
    """