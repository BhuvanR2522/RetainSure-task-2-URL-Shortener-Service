import pytest
import json
from app.main import app
from app.models import url_store

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        # Clear the store before each test
        url_store._mappings.clear()
        yield client

def test_health_check(client):
    """Test the health check endpoint"""
    response = client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['service'] == 'URL Shortener API'

def test_api_health(client):
    """Test the API health endpoint"""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'
    assert data['message'] == 'URL Shortener API is running'

def test_shorten_url_success(client):
    """Test successful URL shortening"""
    response = client.post('/api/shorten', 
                          json={'url': 'https://www.example.com/very/long/url'})
    
    assert response.status_code == 201
    data = response.get_json()
    assert 'short_code' in data
    assert 'short_url' in data
    assert len(data['short_code']) == 6
    assert data['short_url'].endswith(data['short_code'])

def test_shorten_url_missing_url(client):
    """Test URL shortening with missing URL"""
    response = client.post('/api/shorten', json={})
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == "Missing 'url' in request body"

def test_shorten_url_empty_url(client):
    """Test URL shortening with empty URL"""
    response = client.post('/api/shorten', json={'url': ''})
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == "URL cannot be empty"

def test_shorten_url_invalid_url(client):
    """Test URL shortening with invalid URL"""
    response = client.post('/api/shorten', json={'url': 'not-a-url'})
    assert response.status_code == 400
    data = response.get_json()
    assert data['error'] == "Invalid URL provided"

def test_shorten_url_normalizes_url(client):
    """Test that URLs are normalized (adds https:// if missing)"""
    response = client.post('/api/shorten', json={'url': 'example.com'})
    assert response.status_code == 201
    
    # Get the short code from response
    data = response.get_json()
    short_code = data['short_code']
    
    # Check that the stored URL is normalized
    mapping = url_store.get_mapping(short_code)
    assert mapping.original_url == 'https://example.com'

def test_redirect_success(client):
    """Test successful redirect"""
    # First create a short URL
    response = client.post('/api/shorten', 
                          json={'url': 'https://www.example.com'})
    data = response.get_json()
    short_code = data['short_code']
    
    # Test redirect
    response = client.get(f'/{short_code}', follow_redirects=False)
    assert response.status_code == 302
    assert response.location == 'https://www.example.com'

def test_redirect_not_found(client):
    """Test redirect with non-existent short code"""
    response = client.get('/nonexistent')
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == "Short code not found"

def test_stats_success(client):
    """Test getting stats for a short code"""
    # First create a short URL
    response = client.post('/api/shorten', 
                          json={'url': 'https://www.example.com'})
    data = response.get_json()
    short_code = data['short_code']
    
    # Get stats
    response = client.get(f'/api/stats/{short_code}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['url'] == 'https://www.example.com'
    assert data['clicks'] == 0
    assert 'created_at' in data

def test_stats_not_found(client):
    """Test getting stats for non-existent short code"""
    response = client.get('/api/stats/nonexistent')
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == "Short code not found"

def test_click_tracking(client):
    """Test that clicks are properly tracked"""
    # Create a short URL
    response = client.post('/api/shorten', 
                          json={'url': 'https://www.example.com'})
    data = response.get_json()
    short_code = data['short_code']
    
    # Initial stats should show 0 clicks
    response = client.get(f'/api/stats/{short_code}')
    data = response.get_json()
    assert data['clicks'] == 0
    
    # Visit the short URL
    client.get(f'/{short_code}', follow_redirects=False)
    
    # Stats should now show 1 click
    response = client.get(f'/api/stats/{short_code}')
    data = response.get_json()
    assert data['clicks'] == 1
    
    # Visit again
    client.get(f'/{short_code}', follow_redirects=False)
    
    # Stats should now show 2 clicks
    response = client.get(f'/api/stats/{short_code}')
    data = response.get_json()
    assert data['clicks'] == 2

def test_thread_safe_operations(client):
    """Test that the URL store operations are thread-safe"""
    # Test multiple operations in sequence to ensure thread safety
    short_codes = []
    
    # Create multiple short URLs
    for i in range(5):
        response = client.post('/api/shorten', 
                             json={'url': f'https://www.example{i}.com'})
        assert response.status_code == 201
        data = response.get_json()
        short_codes.append(data['short_code'])
    
    # Verify all short codes are unique
    assert len(set(short_codes)) == 5
    
    # Test that all mappings exist
    for short_code in short_codes:
        mapping = url_store.get_mapping(short_code)
        assert mapping is not None

def test_unique_short_codes(client):
    """Test that generated short codes are unique"""
    short_codes = set()
    
    # Create multiple short URLs
    for i in range(10):
        response = client.post('/api/shorten', 
                             json={'url': f'https://www.example{i}.com'})
        data = response.get_json()
        short_code = data['short_code']
        
        # Ensure short code is unique
        assert short_code not in short_codes
        short_codes.add(short_code)