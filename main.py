from flask import Flask, request, jsonify
from supermarktconnector.ah import AHConnector
from supermarktconnector.jumbo import JumboConnector
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)  # Use DEBUG level for detailed logs

@app.route('/search', methods=['GET'])
def search_products():
    """
    Search for an item's price and discounted price using AHConnector.
    Request query parameters:
      - query: The item to search for (e.g., "milk").
      - size: Number of results to fetch (default: 1 for testing).
      - page: Page number for results (default: 0).
    """
    # Log the request details
    app.logger.debug(f"Accessed /search with args: {request.args}")

    # Extract query parameters
    query = request.args.get('query')
    size = int(request.args.get('size', 1))  # Set to 1 for testing one product
    page = int(request.args.get('page', 0))

    # Validate inputs
    if not query:
        app.logger.error("Missing 'query' parameter in /search request")
        return jsonify({"error": "Query parameter is required"}), 400

    try:
        # Use the AHConnector
        connector = AHConnector()
        results = connector.search_products(query=query, size=size, page=page)

        # Log raw results for debugging
        app.logger.debug(f"Raw results from AHConnector: {results}")

        # Extract relevant data from products
        product_prices = []
        for product in results.get("products", []):  # Process the "products" list
            # Extract the normal price
            normal_price = product.get("priceBeforeBonus")

            # Calculate the discounted price based on the promotion
            discounted_price = None
            if product.get("discountLabels"):
                discount = product["discountLabels"][0]  # Take the first discount
                if discount["code"] == "DISCOUNT_X_PLUS_Y_FREE":
                    # Handle "1+1 gratis" promotion: Half price for a single unit
                    discounted_price = normal_price / 2
                else:
                    # Other discounts can be handled here
                    discounted_price = normal_price  # Default to normal price if no special handling is needed

            # If no discount, default the discounted price to the normal price
            if discounted_price is None:
                discounted_price = normal_price

            # Append the processed product data
            price_data = {
                "title": product.get("title"),
                "normal_price": normal_price,
                "discounted_price": discounted_price,
                "bonus_description": product.get("bonusMechanism"),  # Optional: Add bonus description
                "sales_unit_size": product.get("salesUnitSize"),  # Sales unit size
                "unit_price_description": product.get("unitPriceDescription"),  # Unit price description
                "currency": "EUR",  # Assuming currency is EUR
                "available_online": product.get("availableOnline", False)
            }
            product_prices.append(price_data)

        app.logger.debug(f"Filtered product prices: {product_prices}")
        return jsonify({"results": product_prices})
    except Exception as e:
        app.logger.exception(f"Error occurred while fetching product prices: {e}")
        return jsonify({"error": "An error occurred while processing your request"}), 500

@app.route('/categories', methods=['GET'])
def get_categories():
    # Log access to the endpoint
    app.logger.debug("Accessed /categories")

    try:
        # Use the AHConnector
        connector = AHConnector()
        categories = connector.get_categories()
        app.logger.debug(f"Categories from AHConnector: {categories}")
        return jsonify(categories)
    except Exception as e:
        app.logger.exception(f"Error occurred while fetching categories: {e}")
        return jsonify({"error": "An error occurred while processing your request"}), 500

if __name__ == '__main__':
    # Run the Flask app
    app.logger.info("Starting Flask application on http://127.0.0.1:5000")
    app.run(port=5000, debug=True)