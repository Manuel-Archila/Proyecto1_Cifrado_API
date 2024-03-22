from flask import Flask
from routes.routes import routes
import psycopg2

app = Flask(__name__)


# Registrar el Blueprint de tus rutas
app.register_blueprint(routes)

if __name__ == '__main__':
    app.run(debug=True)

