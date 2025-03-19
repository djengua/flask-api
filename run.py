import os
from app import app, register_blueprints, init_db


try:
    init_db()
except Exception as e:
    print(f"Error al inicializar la base de datos: {str(e)}")

# Registrar blueprints antes de ejecutar la aplicación
register_blueprints()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
