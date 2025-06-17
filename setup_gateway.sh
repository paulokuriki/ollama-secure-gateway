#!/bin/bash

# Exit on error
set -e

# Function to print colored messages
print_message() {
    echo -e "\e[1;34m$1\e[0m"
}

print_success() {
    echo -e "\e[1;32m✅ $1\e[0m"
}

print_error() {
    echo -e "\e[1;31m❌ $1\e[0m"
}

# Check if required arguments are provided
if [ "$#" -lt 4 ]; then
    print_error "Usage: $0 <username> <password> <full_name> <email>"
    print_error "Example: $0 admin 'secure_password' 'Admin User' 'admin@example.com'"
    exit 1
fi

USERNAME=$1
PASSWORD=$2
FULL_NAME=$3
EMAIL=$4

print_message "🚀 Starting secure gateway setup..."

# Load Python module
print_message "Loading Python module..."
module load python || { print_error "Failed to load Python module"; exit 1; }

# Create necessary directories
print_message "Creating directories..."
mkdir -p certificates
mkdir -p src

# Generate SSL certificates
print_message "Generating SSL certificates..."
if [ ! -f "certificates/cert.pem" ] || [ ! -f "certificates/key.pem" ]; then
    openssl req -x509 -newkey rsa:4096 -nodes \
        -out certificates/cert.pem \
        -keyout certificates/key.pem \
        -days 365 \
        -subj "/CN=localhost" \
        -addext "subjectAltName=DNS:localhost"
    print_success "SSL certificates created"
else
    print_success "SSL certificates already exist"
fi

# Create virtual environment
print_message "Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python -m venv venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# Activate virtual environment and install requirements
print_message "Installing requirements..."
source venv/bin/activate
pip install --upgrade pip
pip install fastapi==0.104.1 \
            uvicorn==0.24.0 \
            python-jose[cryptography]==3.3.0 \
            passlib[bcrypt]==1.7.4 \
            python-multipart==0.0.6 \
            httpx==0.25.1 \
            python-dotenv==1.0.0 \
            pydantic==2.4.2 \
            pydantic-settings==2.0.3 \
            slowapi==0.1.8 \
            email-validator==2.1.0 \
            PyJWT==2.8.0

# Copy source files from current directory
print_message "Setting up source files..."
if [ -d "src" ]; then
    print_success "Source directory already exists"
else
    print_error "Source directory not found. Please ensure you're in the correct directory."
    exit 1
fi

# Create initial user in users_db.json
print_message "Setting up initial user..."
if [ ! -f "users_db.json" ]; then
    # Create a Python script to hash the password
    cat > hash_password.py << 'EOL'
import bcrypt
import json
import sys

password = sys.argv[1]
# Generate salt and hash the password
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

# Create user entry
user = {
    "id": 1,
    "username": sys.argv[2],
    "full_name": sys.argv[3],
    "email": sys.argv[4],
    "hashed_password": hashed.decode('utf-8'),
    "is_active": True  # First user is active by default
}

# Write to users_db.json
with open('users_db.json', 'w') as f:
    json.dump([user], f, indent=4)
EOL

    # Run the Python script to create the user with hashed password
    python hash_password.py "$PASSWORD" "$USERNAME" "$FULL_NAME" "$EMAIL"
    rm hash_password.py  # Clean up the temporary script
    print_success "Initial user '$USERNAME' created successfully with hashed password"
else
    print_error "users_db.json already exists. Please add users manually or remove the file to start fresh."
    exit 1
fi

# Create startup script
print_message "Creating startup script..."
cat > start_gateway.sh << 'EOL'
#!/bin/bash

# Load Python module
module load python

# Activate virtual environment
source venv/bin/activate

# Start the gateway with rate limiting and logging
uvicorn src.middleware:app --host 0.0.0.0 --port 8000 \
    --ssl-keyfile certificates/key.pem \
    --ssl-certfile certificates/cert.pem
EOL

chmod +x start_gateway.sh
print_success "Startup script created"

print_message "\n✨ Setup complete! To start the gateway:"
print_message "1. Make sure Ollama is running on port 11434"
print_message "2. Run: ./start_gateway.sh"
print_message "\n⚠️ Important notes:"
print_message "- The gateway uses the following features from the README:"
print_message "  • JWT authentication"
print_message "  • Request logging to api_usage.log"
print_message "  • Rate limiting (5 requests per minute per route)"
print_message "  • Secure HTTPS proxying to Ollama"
print_message "- To add more users, use the /users endpoint:"
print_message "  curl -X POST https://localhost:8000/users -k -H 'Content-Type: application/json' -d '{\"username\":\"newuser\",\"password\":\"password\",\"full_name\":\"New User\",\"email\":\"user@example.com\"}'"
print_message "- New users must be manually activated by setting is_active=true in users_db.json"
print_message "- The gateway will be accessible at https://<your-ip>:8000" 
