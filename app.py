# Import the Flask application factory function
from Board import create_app

# Call factory function to create the Flask App
app = create_app()

# Run app only if this file is executed directly
if __name__ == "__main__":
    app.run(debug=True)