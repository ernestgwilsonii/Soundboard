from app import create_app

app = create_app()

if __name__ == '__main__':
    import os
    port = int(os.environ.get('FLASK_RUN_PORT', 5000))
    # Use the DEBUG setting from config to enable hot-reloading
    app.run(debug=app.config.get('DEBUG', False), port=port)
