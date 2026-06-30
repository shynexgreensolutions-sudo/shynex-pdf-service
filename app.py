"""
Shynex Green Solutions — PDF Generation Service
Deploy this on Render.com (free tier)
This service receives quote data and returns a PDF estimate as base64.
"""
import os, base64, traceback
from flask import Flask, request, jsonify, Response
import requests as http
from pdf_generator import generate_estimate_pdf
from catalogue_generator import generate_catalogue_pdf

app = Flask(__name__)

# Simple secret key to prevent unauthorized use
API_SECRET = os.environ.get("PDF_API_SECRET", "shynex-pdf-secret-2026")

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "service": "Shynex PDF Generator"})

@app.route("/generate-pdf", methods=["POST"])
def generate():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON body"}), 400

        # Generate PDF bytes
        pdf_bytes = generate_estimate_pdf(
            est_no           = data["est_no"],
            date_str         = data["date_str"],
            customer_name    = data["customer_name"],
            customer_address = data.get("customer_address", ""),
            items            = data["items"],
            valid_for        = data.get("valid_for", "15 Days"),
            terms            = data.get("terms", None),
        )

        # Return as base64 so it can be sent over JSON
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
        return jsonify({
            "ok": True,
            "pdf_base64": pdf_b64,
            "filename": f"{data['est_no']}.pdf",
            "size_bytes": len(pdf_bytes)
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/catalogue", methods=["GET"])
def generate_catalogue():
    try:
        agent_url = os.environ.get(
            "AGENT_PRODUCTS_URL",
            "https://shynex-ai-agent.shynexgreensolutions.workers.dev/products"
        )
        resp = http.get(agent_url, timeout=20)
        resp.raise_for_status()
        products = resp.json().get("products", [])
        if not products:
            return jsonify({"error": "No products returned from agent"}), 502

        pdf_bytes = generate_catalogue_pdf(products)
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={
                "Content-Disposition":
                    'attachment; filename="Shynex-Green-Solutions-Product-Catalogue.pdf"',
                "Cache-Control": "public, max-age=3600",
            }
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
