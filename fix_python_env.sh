#!/bin/bash

echo "🔧 Fixing Python environment for market-data-api..."

# Step 1: Deactivate and remove old venv
echo "📦 Removing old Python 3.13 virtual environment..."
deactivate 2>/dev/null || true
rm -rf venv

# Step 2: Check if Python 3.11 is available
echo "🐍 Checking for Python 3.11..."
if command -v python3.11 &> /dev/null; then
    echo "✅ Python 3.11 found"
    PYTHON_CMD="python3.11"
elif command -v pyenv &> /dev/null; then
    echo "📦 Installing Python 3.11 with pyenv..."
    pyenv install 3.11.9 -s
    pyenv local 3.11.9
    PYTHON_CMD="python"
else
    echo "🍺 Installing Python 3.11 with Homebrew..."
    brew install python@3.11
    PYTHON_CMD="python3.11"
fi

# Step 3: Create new virtual environment
echo "🏗️  Creating new virtual environment with Python 3.11..."
$PYTHON_CMD -m venv venv
source venv/bin/activate

# Step 4: Upgrade pip and install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Step 5: Test the installation
echo "🧪 Testing installation..."
python -c "import fastapi, pydantic, sqlalchemy; print('✅ All dependencies installed successfully!')"

echo "🎉 Environment setup complete!"
echo "💡 To activate: source venv/bin/activate"
echo "🚀 To run tests: python -m pytest"
echo "🌐 To run app: uvicorn app.main:app --reload" 