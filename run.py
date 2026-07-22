from app import create_app

# Create application instance via factory
app = create_app()

if __name__ == '__main__':
    # Run the development server
    app.run(debug=True)