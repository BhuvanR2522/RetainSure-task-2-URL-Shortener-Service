from flask import Flask, jsonify, request, redirect, url_for
from app.models import url_store
from app.utils import is_valid_url, generate_unique_short_code, normalize_url

app = Flask(__name__)

@app.route('/')
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "URL Shortener API"
    })

@app.route('/api/health')
def api_health():
    return jsonify({
        "status": "ok",
        "message": "URL Shortener API is running"
    })

@app.route('/api/shorten', methods=['POST'])
def shorten_url():
    """
    Shorten a URL endpoint
    
    Expected JSON payload:
    {
        "url": "https://www.example.com/very/long/url"
    }
    
    Returns:
    {
        "short_code": "abc123",
        "short_url": "http://localhost:5000/abc123"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({
                "error": "Missing 'url' in request body"
            }), 400
        
        original_url = data['url'].strip()
        
        if not original_url:
            return jsonify({
                "error": "URL cannot be empty"
            }), 400
        
        # Normalize URL (add https:// if no scheme)
        normalized_url = normalize_url(original_url)
        
        # Validate URL
        if not is_valid_url(normalized_url):
            return jsonify({
                "error": "Invalid URL provided"
            }), 400
        
        # Generate unique short code
        existing_codes = set(url_store.get_all_mappings().keys())
        short_code = generate_unique_short_code(existing_codes)
        
        # Create mapping
        mapping = url_store.create_mapping(short_code, normalized_url)
        
        # Generate short URL using request host
        short_url = f"{request.host_url.rstrip('/')}/{short_code}"
        
        return jsonify({
            "short_code": short_code,
            "short_url": short_url
        }), 201
        
    except Exception as e:
        return jsonify({
            "error": "Internal server error"
        }), 500

@app.route('/<short_code>')
def redirect_to_url(short_code):
    """
    Redirect to original URL using short code
    
    Args:
        short_code: The short code to redirect from
        
    Returns:
        Redirect to original URL or 404 if not found
    """
    mapping = url_store.get_mapping(short_code)
    
    if not mapping:
        return jsonify({
            "error": "Short code not found"
        }), 404
    
    # Increment click count
    url_store.increment_clicks(short_code)
    
    # Redirect to original URL
    return redirect(mapping.original_url, code=302)

@app.route('/api/stats/<short_code>')
def get_stats(short_code):
    """
    Get analytics for a short code
    
    Args:
        short_code: The short code to get stats for
        
    Returns:
        JSON with URL, clicks, and creation timestamp
    """
    mapping = url_store.get_mapping(short_code)
    
    if not mapping:
        return jsonify({
            "error": "Short code not found"
        }), 404
    
    return jsonify({
        "url": mapping.original_url,
        "clicks": mapping.clicks,
        "created_at": mapping.created_at.isoformat()
    })

# For local development
if __name__ == '__main__':
    app.run(debug=True)