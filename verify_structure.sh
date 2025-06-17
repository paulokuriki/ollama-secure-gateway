#!/bin/bash

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

print_message "Verifying HPC directory structure..."

# Check main directories
for dir in "certificates" "src" "venv"; do
    if [ -d "$dir" ]; then
        print_success "Directory '$dir' exists"
    else
        print_error "Directory '$dir' is missing"
    fi
done

# Check source files
required_files=(
    "src/auth.py"
    "src/constants.py"
    "src/database.py"
    "src/middleware.py"
    "src/pydantic_models.py"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        print_success "File '$file' exists"
    else
        print_error "File '$file' is missing"
    fi
done

# Check SSL certificates
if [ -f "certificates/cert.pem" ] && [ -f "certificates/key.pem" ]; then
    print_success "SSL certificates exist"
else
    print_error "SSL certificates are missing"
fi

# Check database and log files
if [ -f "users_db.json" ]; then
    print_success "User database exists"
else
    print_error "User database is missing"
fi

if [ -f "api_usage.log" ]; then
    print_success "Log file exists"
else
    print_error "Log file is missing"
fi

# Check scripts
if [ -f "setup_gateway.sh" ] && [ -f "start_gateway.sh" ]; then
    print_success "Gateway scripts exist"
else
    print_error "Gateway scripts are missing"
fi

print_message "\nDirectory structure verification complete!" 